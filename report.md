# Redis TTL Audit Report

## Summary

| Metric | Value |
|---|---:|
| Scanned keys | 6 |
| Keys with TTL | 1 |
| Keys without TTL | 5 |
| Disappeared during scan | 0 |
| Persistent key ratio | 83.33% |

## Top Persistent Key Groups

| Group | TTL | Count | Share | Examples |
|---|---|---:|---:|---|
| cache:user | NONE | 3 | 50.00% | `cache:user:2`, `cache:user:3`, `cache:user:1` |
| config:feature | NONE | 1 | 16.67% | `config:feature:dark-mode` |
| temp:job | NONE | 1 | 16.67% | `temp:job:991` |

## Suspicious Persistent Groups

| Group | Count | Reason | Examples |
|---|---:|---|---|
| cache:user | 3 | cache-like key group has no TTL | `cache:user:2`, `cache:user:3`, `cache:user:1` |
| temp:job | 1 | temporary/session-like key group has no TTL | `temp:job:991` |

## Top Expiring Key Groups

| Group | Count | Min TTL | Max TTL | Avg TTL | Examples |
|---|---:|---:|---:|---:|---|
| session:web | 1 | 3029s | 3029s | 3029s | `session:web:abc` |

## Disappeared Keys

No keys disappeared during the scan.

## Notes

- This tool is read-only.
- It uses Redis `SCAN`, not `KEYS`.
- `TTL = NONE` means Redis returned `-1`: the key exists but has no expiration.
- Persistent keys are not always bugs. Configuration, lookup tables, dictionaries, and metadata can be intentionally persistent.
- Cache-like, session-like, temporary, lock, queue, token, or rate-limit keys without TTL are suspicious and should be reviewed.
