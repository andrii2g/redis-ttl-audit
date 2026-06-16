from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from pytest import MonkeyPatch
from redis.exceptions import ConnectionError

from redis_ttl_audit import cli
from redis_ttl_audit.models import AuditSummary


class FakeRedisClient:
    def ping(self) -> bool:
        return True


def test_cli_help_mentions_read_only_scan_not_keys(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = cli.main(["--help"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "read-only" in captured.out.lower()
    assert "SCAN" in captured.out
    assert "KEYS" in captured.out


def test_cli_rejects_invalid_batch_size(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = cli.main(["--batch-size", "0"])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "Error: --batch-size must be greater than 0" in captured.err


def test_cli_rejects_invalid_group_depth(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = cli.main(["--group-depth", "0"])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "Error: --group-depth must be greater than 0" in captured.err


def test_cli_rejects_invalid_sample(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = cli.main(["--sample", "-1"])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "Error: --sample must be 0 or greater" in captured.err


def test_cli_writes_report_to_output_path(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output_path = tmp_path / "report.md"
    summary = AuditSummary(scanned_keys=1, persistent_keys=1)
    summary.get_group("cache:user").add_persistent_key("cache:user:1")

    monkeypatch.setattr(cli, "_create_redis_client", lambda url: FakeRedisClient())
    monkeypatch.setattr(cli, "scan_redis_ttl", lambda **kwargs: summary)

    exit_code = cli.main(["--output", str(output_path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "# Redis TTL Audit Report" in output_path.read_text(encoding="utf-8")
    assert "cache:user" in captured.out
    assert f"Report written to {output_path}" in captured.out


def test_cli_passes_options_to_scanner(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    output_path = tmp_path / "report.md"
    received: dict[str, Any] = {}

    def fake_scan_redis_ttl(**kwargs: Any) -> AuditSummary:
        received.update(kwargs)
        return AuditSummary()

    monkeypatch.setattr(cli, "_create_redis_client", lambda url: FakeRedisClient())
    monkeypatch.setattr(cli, "scan_redis_ttl", fake_scan_redis_ttl)

    exit_code = cli.main(
        [
            "--url",
            "redis://example.invalid:6379/2",
            "--pattern",
            "cache:*",
            "--batch-size",
            "500",
            "--group-depth",
            "1",
            "--sample",
            "10",
            "--encoding",
            "latin-1",
            "--output",
            str(output_path),
        ]
    )

    assert exit_code == 0
    assert received["pattern"] == "cache:*"
    assert received["batch_size"] == 500
    assert received["group_depth"] == 1
    assert received["sample"] == 10
    assert received["encoding"] == "latin-1"


def test_cli_connection_failure_returns_runtime_error(
    monkeypatch: MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    class FailingRedisClient:
        def ping(self) -> bool:
            raise ConnectionError("refused")

    monkeypatch.setattr(cli, "_create_redis_client", lambda url: FailingRedisClient())

    exit_code = cli.main([])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Error: Redis connection failed: refused" in captured.err


def test_module_execution_help_works() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "redis_ttl_audit", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "read-only" in result.stdout.lower()
    assert "SCAN" in result.stdout
