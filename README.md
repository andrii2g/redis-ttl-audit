# Redis TTL Audit

## Quickstart

From the repository root:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -c "import redis_ttl_audit; print(redis_ttl_audit.__version__)"
docker compose up -d
docker compose exec redis redis-cli FLUSHDB
docker compose exec redis redis-cli SET cache:user:1 "Alice"
docker compose exec redis redis-cli SET cache:user:2 "Bob"
docker compose exec redis redis-cli SET cache:user:3 "Carol"
docker compose exec redis redis-cli SET config:feature:dark-mode "enabled"
docker compose exec redis redis-cli SETEX session:web:abc 3600 "user-1"
docker compose exec redis redis-cli SETEX rate-limit:api:user-1 60 "10"
docker compose exec redis redis-cli SET temp:job:991 "running"
.venv/bin/python -m redis_ttl_audit --url redis://localhost:6380/0 --output report.md
```

Open `report.md`. The expected suspicious persistent groups are:

```text
cache:user
temp:job
```

The expected expiring groups are:

```text
session:web
rate-limit:api
```

Stop the local Redis container when done:

```bash
docker compose down
```

## What it does

`redis-ttl-audit` scans Redis keys and reports which grouped key prefixes have no expiration.
Redis keys without TTL are not automatically wrong. Configuration, lookup tables, dictionaries, and metadata can be intentionally persistent.

Cache-like, session-like, temporary, lock, queue, token, and rate-limit keys without TTL are more suspicious. This tool makes those groups visible before they become memory leaks.

## Installation

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e .
```

For development:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
```

On Windows, create and activate the virtual environment with:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

Use the same virtual environment for installation and running the tool.

## Usage

Run against the default local Redis database:

```bash
.venv/bin/python -m redis_ttl_audit
```

The CLI default URL is `redis://localhost:6379/0`. The bundled Docker Compose file uses host port `6380` to avoid conflicts with an existing local Redis.

If your Python scripts directory is on `PATH`, the installed console command is also available:

```bash
redis-ttl-audit --help
```

If that prints `command not found`, use `.venv/bin/python -m redis_ttl_audit` instead.

Run with explicit options:

```bash
.venv/bin/python -m redis_ttl_audit \
  --url redis://localhost:6380/0 \
  --pattern "*" \
  --batch-size 1000 \
  --group-depth 2 \
  --sample 0 \
  --output redis-ttl-report.md
```

Module execution is also supported:

```bash
.venv/bin/python -m redis_ttl_audit --help
```

## Example Output

```text
Redis TTL Audit

Scanned keys: 7
Keys with TTL: 2
Keys without TTL: 5
Disappeared: 0

Top persistent groups:
cache:user               NONE              3
config:feature           NONE              1
temp:job                 NONE              1

Report written to redis-ttl-report.md
```

## How grouping works

Keys are grouped by colon-separated prefix. With `--group-depth 2`:

| Key | Group |
|---|---|
| `cache:user:123` | `cache:user` |
| `session:web:abc` | `session:web` |
| `rate-limit:api:user-1` | `rate-limit:api` |
| `simplekey` | `simplekey` |

## TTL interpretation

| Redis TTL | Meaning | Report classification |
|---:|---|---|
| `>= 0` | Key exists and expires later, including less than one second remaining | `EXPIRES` |
| `-1` | Key exists but has no expiration | `NONE` |
| `-2` | Key disappeared before TTL check | `DISAPPEARED` |

`TTL = NONE` means Redis returned `-1`.

## Safety notes

- This tool is read-only.
- It uses Redis `SCAN`, not `KEYS`.
- It does not delete keys.
- It does not set TTLs.
- It does not call `MEMORY USAGE` or `TYPE` in v1.
- It stores grouped counters and a few examples per group, not every scanned key.

## Local test dataset

The quickstart above uses `docker compose exec` so it works without a locally installed `redis-cli`.

If you already have `redis-cli` installed on your host, you can create the same sample data this way.

Start Redis:

```bash
docker compose up -d
```

The compose file maps Redis to host port `6380` to avoid conflicts with an existing local Redis on `6379`.

Create sample keys:

```bash
redis-cli SET cache:user:1 "Alice"
redis-cli SET cache:user:2 "Bob"
redis-cli SET cache:user:3 "Carol"
redis-cli SET config:feature:dark-mode "enabled"
redis-cli SETEX session:web:abc 3600 "user-1"
redis-cli SETEX rate-limit:api:user-1 60 "10"
redis-cli SET temp:job:991 "running"
```

Run the audit:

```bash
.venv/bin/python -m redis_ttl_audit --url redis://localhost:6380/0 --output report.md
```

Expected result:

```text
cache:user and temp:job are reported as suspicious persistent groups.
config:feature is persistent but not suspicious by default heuristics.
session:web and rate-limit:api are reported as expiring groups.
```

## Development

```bash
.venv/bin/python -m pytest
.venv/bin/python -m ruff check src tests
.venv/bin/python -m mypy src/redis_ttl_audit tests
```

## Troubleshooting

### `error: externally-managed-environment`

Your Linux distribution blocks direct installs into system Python. Create a project virtual environment and install there:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
```

If `venv` is missing on Debian or Ubuntu:

```bash
sudo apt install python3-venv
```

### `/usr/bin/python3: No module named redis_ttl_audit`

Install the project into the virtual environment and run with that same interpreter:

```bash
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -c "import redis_ttl_audit; print(redis_ttl_audit.__version__)"
.venv/bin/python -m redis_ttl_audit --url redis://localhost:6380/0 --output report.md
```

If `python3 -m pip` is missing, install pip for your Python environment first. On Debian or Ubuntu:

```bash
sudo apt install python3-pip
```

For a no-install local development fallback, run with `PYTHONPATH=src` after installing dependencies in a virtual environment:

```bash
PYTHONPATH=src python3 -m redis_ttl_audit --url redis://localhost:6380/0 --output report.md
```

## License

No license has been selected yet.
