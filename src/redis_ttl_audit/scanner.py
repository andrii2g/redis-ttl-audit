from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from redis_ttl_audit.grouping import group_key
from redis_ttl_audit.models import AuditSummary


class RedisTtlClient(Protocol):
    def scan(
        self,
        cursor: int = 0,
        match: str | None = None,
        count: int | None = None,
    ) -> tuple[int, Sequence[bytes]]: ...

    def ttl(self, name: bytes) -> int: ...


def scan_redis_ttl(
    redis_client: RedisTtlClient,
    pattern: str,
    batch_size: int,
    group_depth: int,
    sample: int,
    encoding: str,
) -> AuditSummary:
    if batch_size < 1:
        raise ValueError("batch_size must be greater than 0")
    if group_depth < 1:
        raise ValueError("group_depth must be greater than 0")
    if sample < 0:
        raise ValueError("sample must be 0 or greater")

    cursor = 0
    summary = AuditSummary()

    while True:
        cursor, raw_keys = redis_client.scan(cursor=cursor, match=pattern, count=batch_size)

        for raw_key in raw_keys:
            key = raw_key.decode(encoding, errors="replace")
            ttl = redis_client.ttl(raw_key)
            group = summary.get_group(group_key(key, group_depth))

            summary.scanned_keys += 1
            if ttl >= 0:
                summary.expiring_keys += 1
                group.add_expiring_key(key, ttl)
            elif ttl == -1:
                summary.persistent_keys += 1
                group.add_persistent_key(key)
            elif ttl == -2:
                summary.disappeared_keys += 1
                group.add_disappeared_key()
            else:
                raise ValueError(f"Unexpected Redis TTL value for key {key!r}: {ttl}")

            if sample > 0 and summary.scanned_keys >= sample:
                return summary

        if cursor == 0:
            break

    return summary
