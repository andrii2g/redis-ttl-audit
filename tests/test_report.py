from redis_ttl_audit.models import AuditSummary
from redis_ttl_audit.report import render_markdown_report


def test_render_markdown_report_contains_required_sections() -> None:
    summary = AuditSummary(scanned_keys=6, expiring_keys=2, persistent_keys=3, disappeared_keys=1)
    cache_group = summary.get_group("cache:user")
    cache_group.add_persistent_key("cache:user:123")
    cache_group.add_persistent_key("cache:user:456")
    session_group = summary.get_group("session:web")
    session_group.add_expiring_key("session:web:abc", 0)
    session_group.add_expiring_key("session:web:def", 3600)
    vanished_group = summary.get_group("temp:job")
    vanished_group.add_disappeared_key()

    report = render_markdown_report(summary)

    assert "# Redis TTL Audit Report" in report
    assert "## Summary" in report
    assert "## Top Persistent Key Groups" in report
    assert "cache:user" in report
    assert "TTL" in report
    assert "NONE" in report
    assert "50.00%" in report
    assert "## Suspicious Persistent Groups" in report
    assert "cache-like key group has no TTL" in report
    assert "## Top Expiring Key Groups" in report
    assert "session:web" in report
    assert "| session:web | 2 | 0s | 3600s | 1800s |" in report
    assert "## Disappeared Keys" in report
    assert "1 keys disappeared between `SCAN` and `TTL` checks." in report
    assert "## Notes" in report


def test_render_markdown_report_empty_summary() -> None:
    report = render_markdown_report(AuditSummary())

    assert "| Scanned keys | 0 |" in report
    assert "| Persistent key ratio | 0.00% |" in report
    assert "No suspicious persistent groups were detected by the built-in heuristics." in report
    assert "No keys disappeared during the scan." in report


def test_render_markdown_report_sorts_groups_by_count_descending() -> None:
    summary = AuditSummary(scanned_keys=6, persistent_keys=6)
    smaller = summary.get_group("cache:small")
    larger = summary.get_group("cache:large")

    smaller.add_persistent_key("cache:small:1")
    larger.add_persistent_key("cache:large:1")
    larger.add_persistent_key("cache:large:2")

    report = render_markdown_report(summary)

    assert report.index("cache:large") < report.index("cache:small")


def test_render_markdown_report_escapes_table_cells_and_code_spans() -> None:
    summary = AuditSummary(scanned_keys=1, persistent_keys=1)
    group = summary.get_group("cache|user")
    group.add_persistent_key("cache:user:`quoted`")

    report = render_markdown_report(summary)

    assert "cache\\|user" in report
    assert "`cache:user:\\`quoted\\``" in report

