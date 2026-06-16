from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, cast

import redis
from redis.exceptions import RedisError

from redis_ttl_audit.formatting import format_int
from redis_ttl_audit.models import AuditSummary, GroupStats, TtlStatus
from redis_ttl_audit.report import render_markdown_report
from redis_ttl_audit.scanner import RedisTtlClient, scan_redis_ttl


DEFAULT_REDIS_URL = "redis://localhost:6379/0"
DEFAULT_PATTERN = "*"
DEFAULT_BATCH_SIZE = 1000
DEFAULT_GROUP_DEPTH = 2
DEFAULT_SAMPLE = 0
DEFAULT_OUTPUT = "redis-ttl-report.md"
DEFAULT_ENCODING = "utf-8"


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return _system_exit_code(exc)

    validation_error = _validate_args(args)
    if validation_error is not None:
        print(f"Error: {validation_error}", file=sys.stderr)
        return 2

    try:
        client = _create_redis_client(args.url)
        client.ping()
    except ValueError:
        print(f"Error: Could not connect to Redis at {args.url}", file=sys.stderr)
        return 1
    except (OSError, RedisError) as exc:
        print(f"Error: Redis connection failed: {exc}", file=sys.stderr)
        return 1

    try:
        summary = scan_redis_ttl(
            redis_client=cast(RedisTtlClient, client),
            pattern=args.pattern,
            batch_size=args.batch_size,
            group_depth=args.group_depth,
            sample=args.sample,
            encoding=args.encoding,
        )
        report = render_markdown_report(summary)
        Path(args.output).write_text(report, encoding="utf-8")
    except OSError as exc:
        print(f"Error: Could not write report to {args.output}: {exc}", file=sys.stderr)
        return 1
    except RedisError as exc:
        print(f"Error: Redis connection failed: {exc}", file=sys.stderr)
        return 1

    _print_console_summary(summary, args.output)
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="redis-ttl-audit",
        description=(
            "Read-only Redis TTL auditor. Uses Redis SCAN, not KEYS, and never modifies keys."
        ),
    )
    parser.add_argument("--url", default=DEFAULT_REDIS_URL, help="Redis connection URL")
    parser.add_argument(
        "--pattern",
        default=DEFAULT_PATTERN,
        help="Redis key pattern passed to SCAN MATCH",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help="Redis SCAN COUNT hint",
    )
    parser.add_argument(
        "--group-depth",
        type=int,
        default=DEFAULT_GROUP_DEPTH,
        help="Number of colon-separated key segments used for grouping",
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=DEFAULT_SAMPLE,
        help="Stop after N scanned keys; 0 means full scan",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help="Markdown report output path",
    )
    parser.add_argument(
        "--encoding",
        default=DEFAULT_ENCODING,
        help="Decode Redis keys using this text encoding",
    )
    return parser


def _create_redis_client(url: str) -> Any:
    return redis.Redis.from_url(url)


def _validate_args(args: argparse.Namespace) -> str | None:
    if args.batch_size < 1:
        return "--batch-size must be greater than 0"
    if args.group_depth < 1:
        return "--group-depth must be greater than 0"
    if args.sample < 0:
        return "--sample must be 0 or greater"
    return None


def _print_console_summary(summary: AuditSummary, output: str) -> None:
    print("Redis TTL Audit")
    print()
    print(f"Scanned keys: {format_int(summary.scanned_keys)}")
    print(f"Keys with TTL: {format_int(summary.expiring_keys)}")
    print(f"Keys without TTL: {format_int(summary.persistent_keys)}")
    print(f"Disappeared: {format_int(summary.disappeared_keys)}")
    print()
    print("Top persistent groups:")

    top_groups = _top_persistent_groups(summary)
    if not top_groups:
        print("(none)")
    for group in top_groups:
        print(
            f"{group.group:<24} {TtlStatus.NONE.value:<6} {format_int(group.persistent_count):>12}"
        )

    print()
    print(f"Report written to {output}")


def _top_persistent_groups(summary: AuditSummary) -> list[GroupStats]:
    return sorted(
        (group for group in summary.groups.values() if group.persistent_count > 0),
        key=lambda group: (-group.persistent_count, group.group),
    )[:3]


def _system_exit_code(exc: SystemExit) -> int:
    code: Any = exc.code
    if isinstance(code, int):
        return code
    if code is None:
        return 0
    return 1
