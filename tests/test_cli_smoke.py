from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "llm_chat_archive", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def test_module_help_succeeds() -> None:
    result = run_cli("--help")

    assert result.returncode == 0
    assert "Collect local coding-agent chats" in result.stdout


def test_collect_rejects_repo_internal_archive_root() -> None:
    result = run_cli(
        "collect",
        "codex_cli",
        "--archive-root",
        str(REPO_ROOT / "tests" / "fixtures" / "archives"),
    )

    assert result.returncode == 2
    assert "outside the repository" in result.stderr


def test_collect_emits_plan_for_external_root(tmp_path: Path) -> None:
    result = run_cli("collect", "gemini", "--archive-root", str(tmp_path))

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["source"] == "gemini"
    assert payload["archive_root"] == str(tmp_path)
    assert payload["implemented"] is True
