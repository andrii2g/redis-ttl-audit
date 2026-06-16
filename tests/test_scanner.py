from __future__ import annotations

import pytest

from redis_ttl_audit.scanner import scan_redis_ttl


class FakeRedis:
    def __init__(
        self,
        scan_batches: list[tuple[int, list[bytes]]],
        ttl_values: dict[bytes, int],
    ) -> None:
        self.scan_batches = scan_batches
        self.ttl_values = ttl_values
        self.scan_calls: list[tuple[int, str | None, int | None]] = []
        self.ttl_calls: list[bytes] = []
        self.keys_called = False

    def scan(
        self,
        cursor: int = 0,
        match: str | None = None,
        count: int | None = None,
    ) -> tuple[int, list[bytes]]:
        self.scan_calls.append((cursor, match, count))
        return self.scan_batches.pop(0)

    def ttl(self, name: bytes) -> int:
        self.ttl_calls.append(name)
        return self.ttl_values[name]

    def keys(self, pattern: str = "*") -> list[bytes]:
        self.keys_called = True
        raise AssertionError(f"keys() must not be called with pattern {pattern!r}")


def test_scanner_uses_scan_and_ttl_not_keys() -> None:
    redis = FakeRedis(
        scan_batches=[(0, [b"cache:user:1", b"session:web:1"])],
        ttl_values={b"cache:user:1": -1, b"session:web:1": 60},
    )

    summary = scan_redis_ttl(
        redis_client=redis,
        pattern="*",
        batch_size=1000,
        group_depth=2,
        sample=0,
        encoding="utf-8",
    )

    assert redis.scan_calls == [(0, "*", 1000)]
    assert redis.ttl_calls == [b"cache:user:1", b"session:web:1"]
    assert redis.keys_called is False
    assert summary.scanned_keys == 2


def test_scanner_classifies_ttl_zero_as_expiring() -> None:
    redis = FakeRedis(
        scan_batches=[(0, [b"session:web:1"])],
        ttl_values={b"session:web:1": 0},
    )

    summary = scan_redis_ttl(redis, "*", 1000, 2, 0, "utf-8")

    group = summary.groups["session:web"]
    assert summary.expiring_keys == 1
    assert group.expiring_count == 1
    assert group.min_ttl == 0
    assert group.max_ttl == 0
    assert group.avg_ttl == 0


def test_scanner_classifies_persistent_and_disappeared_keys() -> None:
    redis = FakeRedis(
        scan_batches=[(0, [b"cache:user:1", b"temp:job:1"])],
        ttl_values={b"cache:user:1": -1, b"temp:job:1": -2},
    )

    summary = scan_redis_ttl(redis, "*", 1000, 2, 0, "utf-8")

    assert summary.scanned_keys == 2
    assert summary.persistent_keys == 1
    assert summary.disappeared_keys == 1
    assert summary.groups["cache:user"].persistent_count == 1
    assert summary.groups["temp:job"].disappeared_count == 1
    assert summary.groups["cache:user"].examples_persistent == ["cache:user:1"]


def test_scanner_respects_sample_limit() -> None:
    redis = FakeRedis(
        scan_batches=[
            (7, [b"cache:user:1", b"cache:user:2", b"cache:user:3"]),
            (0, [b"cache:user:4"]),
        ],
        ttl_values={
            b"cache:user:1": -1,
            b"cache:user:2": -1,
            b"cache:user:3": -1,
            b"cache:user:4": -1,
        },
    )

    summary = scan_redis_ttl(redis, "*", 1000, 2, 2, "utf-8")

    assert summary.scanned_keys == 2
    assert redis.ttl_calls == [b"cache:user:1", b"cache:user:2"]
    assert redis.scan_calls == [(0, "*", 1000)]


def test_scanner_decodes_invalid_utf8_with_replacement() -> None:
    raw_key = b"cache:user:\xff"
    redis = FakeRedis(scan_batches=[(0, [raw_key])], ttl_values={raw_key: -1})

    summary = scan_redis_ttl(redis, "*", 1000, 2, 0, "utf-8")

    assert summary.groups["cache:user"].examples_persistent == ["cache:user:�"]


def test_scanner_uses_scan_cursor_until_zero() -> None:
    redis = FakeRedis(
        scan_batches=[
            (42, [b"cache:user:1"]),
            (0, [b"cache:user:2"]),
        ],
        ttl_values={b"cache:user:1": -1, b"cache:user:2": -1},
    )

    summary = scan_redis_ttl(redis, "cache:*", 500, 2, 0, "utf-8")

    assert summary.scanned_keys == 2
    assert redis.scan_calls == [(0, "cache:*", 500), (42, "cache:*", 500)]


def test_scanner_rejects_invalid_numeric_arguments() -> None:
    redis = FakeRedis(scan_batches=[], ttl_values={})

    with pytest.raises(ValueError, match="batch_size"):
        scan_redis_ttl(redis, "*", 0, 2, 0, "utf-8")
    with pytest.raises(ValueError, match="group_depth"):
        scan_redis_ttl(redis, "*", 1000, 0, 0, "utf-8")
    with pytest.raises(ValueError, match="sample"):
        scan_redis_ttl(redis, "*", 1000, 2, -1, "utf-8")

