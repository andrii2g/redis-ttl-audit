from redis_ttl_audit.models import AuditSummary, GroupStats


def test_group_stats_average_ttl() -> None:
    stats = GroupStats(group="cache:user")

    stats.add_expiring_key("cache:user:1", 10)
    stats.add_expiring_key("cache:user:2", 20)

    assert stats.avg_ttl == 15
    assert stats.min_ttl == 10
    assert stats.max_ttl == 20


def test_group_stats_caps_examples() -> None:
    stats = GroupStats(group="cache:user")

    for index in range(5):
        stats.add_persistent_key(f"cache:user:{index}")
        stats.add_expiring_key(f"session:web:{index}", index)

    assert stats.examples_persistent == ["cache:user:0", "cache:user:1", "cache:user:2"]
    assert stats.examples_expiring == ["session:web:0", "session:web:1", "session:web:2"]


def test_audit_summary_get_group_reuses_existing_group() -> None:
    summary = AuditSummary()

    first = summary.get_group("cache:user")
    second = summary.get_group("cache:user")

    assert first is second
    assert list(summary.groups) == ["cache:user"]
