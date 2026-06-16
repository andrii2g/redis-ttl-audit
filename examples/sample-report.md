# Redis TTL Audit Report

## Summary

| Metric | Value |
|---|---:|
| Scanned keys | 7 |
| Keys with TTL | 2 |
| Keys without TTL | 5 |
| Disappeared during scan | 0 |
| Persistent key ratio | 71.43% |

## Top Persistent Key Groups

| Group | TTL | Count | Share | Examples |
|---|---|---:|---:|---|
| cache:user | NONE | 3 | 42.86% | `cache:user:1`, `cache:user:2`, `cache:user:3` |
| config:feature | NONE | 1 | 14.29% | `config:feature:dark-mode` |
| temp:job | NONE | 1 | 14.29% | `temp:job:991` |

## Suspicious Persistent Groups

| Group | Count | Reason | Examples |
|---|---:|---|---|
| cache:user | 3 | cache-like key group has no TTL | `cache:user:1`, `cache:user:2`, `cache:user:3` |
| temp:job | 1 | temporary/session-like key group has no TTL | `temp:job:991` |

## Top Expiring Key Groups

| Group | Count | Min TTL | Max TTL | Avg TTL | Examples |
|---|---:|---:|---:|---:|---|
| rate-limit:api | 1 | 60s | 60s | 60s | `rate-limit:api:user-1` |
| session:web | 1 | 3600s | 3600s | 3600s | `session:web:abc` |

## Disappeared Keys

No keys disappeared during the scan.

## Notes

- This tool is read-only.
- It uses Redis `SCAN`, not `KEYS`.
- `TTL = NONE` means Redis returned `-1`: the key exists but has no expiration.
- Persistent keys are not always bugs. Configuration, lookup tables, dictionaries, and metadata can be intentionally persistent.
- Cache-like, session-like, temporary, lock, queue, token, or rate-limit keys without TTL are suspicious and should be reviewed.
