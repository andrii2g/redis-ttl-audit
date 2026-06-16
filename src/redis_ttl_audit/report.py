from __future__ import annotations

from collections.abc import Iterable

from redis_ttl_audit.formatting import format_int, format_percent, format_seconds
from redis_ttl_audit.models import AuditSummary, GroupStats, TtlStatus
from redis_ttl_audit.suspicious import is_suspicious_persistent_group


def render_markdown_report(summary: AuditSummary) -> str:
    lines: list[str] = [
        "# Redis TTL Audit Report",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Scanned keys | {format_int(summary.scanned_keys)} |",
        f"| Keys with TTL | {format_int(summary.expiring_keys)} |",
        f"| Keys without TTL | {format_int(summary.persistent_keys)} |",
        f"| Disappeared during scan | {format_int(summary.disappeared_keys)} |",
        f"| Persistent key ratio | {_ratio(summary.persistent_keys, summary.scanned_keys)} |",
        "",
    ]

    _append_top_persistent_groups(lines, summary)
    _append_suspicious_groups(lines, summary)
    _append_top_expiring_groups(lines, summary)
    _append_disappeared_keys(lines, summary)
    _append_notes(lines)

    return "\n".join(lines).rstrip() + "\n"


def _append_top_persistent_groups(lines: list[str], summary: AuditSummary) -> None:
    lines.extend(
        [
            "## Top Persistent Key Groups",
            "",
            "| Group | TTL | Count | Share | Examples |",
            "|---|---|---:|---:|---|",
        ]
    )

    for group in _persistent_groups(summary):
        lines.append(
            "| "
            f"{_escape_table_cell(group.group)} | "
            f"{TtlStatus.NONE.value} | "
            f"{format_int(group.persistent_count)} | "
            f"{_ratio(group.persistent_count, summary.scanned_keys)} | "
            f"{_format_examples(group.examples_persistent)} |"
        )

    lines.append("")


def _append_suspicious_groups(lines: list[str], summary: AuditSummary) -> None:
    lines.extend(["## Suspicious Persistent Groups", ""])

    suspicious_groups = [
        group
        for group in _persistent_groups(summary)
        if is_suspicious_persistent_group(group.group)
    ]

    if not suspicious_groups:
        lines.extend(
            [
                "No suspicious persistent groups were detected by the built-in heuristics.",
                "",
            ]
        )
        return

    lines.extend(
        [
            "| Group | Count | Reason | Examples |",
            "|---|---:|---|---|",
        ]
    )
    for group in suspicious_groups:
        lines.append(
            "| "
            f"{_escape_table_cell(group.group)} | "
            f"{format_int(group.persistent_count)} | "
            f"{_suspicious_reason(group.group)} | "
            f"{_format_examples(group.examples_persistent)} |"
        )

    lines.append("")


def _append_top_expiring_groups(lines: list[str], summary: AuditSummary) -> None:
    lines.extend(
        [
            "## Top Expiring Key Groups",
            "",
            "| Group | Count | Min TTL | Max TTL | Avg TTL | Examples |",
            "|---|---:|---:|---:|---:|---|",
        ]
    )

    for group in _expiring_groups(summary):
        lines.append(
            "| "
            f"{_escape_table_cell(group.group)} | "
            f"{format_int(group.expiring_count)} | "
            f"{format_seconds(group.min_ttl)} | "
            f"{format_seconds(group.max_ttl)} | "
            f"{format_seconds(group.avg_ttl)} | "
            f"{_format_examples(group.examples_expiring)} |"
        )

    lines.append("")


def _append_disappeared_keys(lines: list[str], summary: AuditSummary) -> None:
    lines.extend(["## Disappeared Keys", ""])

    if summary.disappeared_keys == 0:
        lines.extend(["No keys disappeared during the scan.", ""])
        return

    lines.extend(
        [
            f"{format_int(summary.disappeared_keys)} keys disappeared between `SCAN` and `TTL` checks.",
            "",
            "This is normal in active Redis databases where keys expire or are deleted while the audit is running.",
            "",
        ]
    )


def _append_notes(lines: list[str]) -> None:
    lines.extend(
        [
            "## Notes",
            "",
            "- This tool is read-only.",
            "- It uses Redis `SCAN`, not `KEYS`.",
            "- `TTL = NONE` means Redis returned `-1`: the key exists but has no expiration.",
            "- Persistent keys are not always bugs. Configuration, lookup tables, dictionaries, and metadata can be intentionally persistent.",
            "- Cache-like, session-like, temporary, lock, queue, token, or rate-limit keys without TTL are suspicious and should be reviewed.",
            "",
        ]
    )


def _persistent_groups(summary: AuditSummary) -> list[GroupStats]:
    return sorted(
        (group for group in summary.groups.values() if group.persistent_count > 0),
        key=lambda group: (-group.persistent_count, group.group),
    )


def _expiring_groups(summary: AuditSummary) -> list[GroupStats]:
    return sorted(
        (group for group in summary.groups.values() if group.expiring_count > 0),
        key=lambda group: (-group.expiring_count, group.group),
    )


def _ratio(value: int, total: int) -> str:
    if total == 0:
        return "0.00%"
    return format_percent(value / total * 100)


def _format_examples(examples: Iterable[str]) -> str:
    formatted = [f"`{_escape_code_span(example)}`" for example in examples]
    if not formatted:
        return "-"
    return ", ".join(formatted)


def _escape_table_cell(value: str) -> str:
    return value.replace("|", r"\|")


def _escape_code_span(value: str) -> str:
    return value.replace("`", r"\`")


def _suspicious_reason(group: str) -> str:
    normalized = group.lower()
    if "cache" in normalized:
        return "cache-like key group has no TTL"
    if "session" in normalized:
        return "temporary/session-like key group has no TTL"
    if "temp" in normalized or "tmp" in normalized:
        return "temporary/session-like key group has no TTL"
    if "rate" in normalized:
        return "rate-limit-like key group has no TTL"
    if "lock" in normalized:
        return "lock-like key group has no TTL"
    if "queue" in normalized:
        return "queue-like key group has no TTL"
    if "token" in normalized:
        return "token-like key group has no TTL"
    return "temporary/cache-like key group has no TTL"
