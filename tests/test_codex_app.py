from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from llm_chat_archive.models import AppShellProvenance
from llm_chat_archive.sources.codex_app import CodexAppCollector, parse_rollout_file

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures" / "codex_app"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "llm_chat_archive", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_parse_rollout_file_requires_codex_desktop_originator() -> None:
    rollout_path = (
        FIXTURE_ROOT
        / "sessions"
        / "2026"
        / "03"
        / "14"
        / "rollout-20260314T113000-cli-ignored.jsonl"
    )

    assert parse_rollout_file(rollout_path, collected_at="2026-03-19T00:00:00Z") is None


def test_parse_rollout_file_keeps_messages_and_attaches_app_shell_provenance() -> None:
    rollout_path = (
        FIXTURE_ROOT
        / "sessions"
        / "2026"
        / "03"
        / "14"
        / "rollout-20260314T110000-desktop-active.jsonl"
    )
    app_shell = AppShellProvenance(
        application_support_roots=("/tmp/mock/Application Support/Codex",),
        log_roots=("/tmp/mock/Logs/com.openai.codex",),
        preference_paths=("/tmp/mock/Preferences/com.openai.codex.plist",),
        cache_roots=("/tmp/mock/Caches/com.openai.codex",),
    )

    conversation = parse_rollout_file(
        rollout_path,
        collected_at="2026-03-19T00:00:00Z",
        app_shell=app_shell,
    )

    assert conversation is not None
    payload = conversation.to_dict()
    assert payload["source"] == "codex_app"
    assert payload["execution_context"] == "standalone_app"
    assert payload["source_session_id"] == "desktop-active"
    assert payload["messages"] == [
        {
            "role": "developer",
            "text": "Prefer the shared rollout transcript.",
            "source_message_id": "app-dev",
        },
        {
            "role": "user",
            "text": "Collect the Desktop app sessions only.",
            "source_message_id": "app-user",
        },
        {
            "role": "assistant",
            "text": "I will filter on Codex Desktop and keep shell artifacts as provenance only.",
            "source_message_id": "app-assistant",
        },
    ]
    assert payload["provenance"] == {
        "session_started_at": "2026-03-14T11:00:00Z",
        "source": "exec",
        "originator": "Codex Desktop",
        "cwd": "/Users/chenjing/dev/chat-collector",
        "cli_version": "0.32.0",
        "archived": False,
        "app_shell": {
            "application_support_roots": ["/tmp/mock/Application Support/Codex"],
            "log_roots": ["/tmp/mock/Logs/com.openai.codex"],
            "preference_paths": ["/tmp/mock/Preferences/com.openai.codex.plist"],
            "cache_roots": ["/tmp/mock/Caches/com.openai.codex"],
        },
    }
    serialized = json.dumps(payload)
    assert "function_call" not in serialized
    assert "function_call_output" not in serialized
    assert "web_search_call" not in serialized
    assert "Local storage prompt should never become a transcript." not in serialized


def test_codex_app_collect_selects_only_desktop_sessions(tmp_path: Path) -> None:
    collector = CodexAppCollector()

    result = collector.collect(tmp_path, input_roots=(FIXTURE_ROOT,))

    assert result.source == "codex_app"
    assert result.scanned_artifact_count == 3
    assert result.conversation_count == 2
    assert result.message_count == 5
    rows = read_jsonl(result.output_path)
    assert [row["source_session_id"] for row in rows] == [
        "desktop-archived",
        "desktop-active",
    ]
    assert {row["provenance"]["originator"] for row in rows} == {"Codex Desktop"}
    assert rows[0]["provenance"]["archived"] is True
    assert rows[1]["provenance"]["archived"] is False
    assert rows[0]["provenance"]["app_shell"] == {
        "application_support_roots": [
            str(
                FIXTURE_ROOT / "Library" / "Application Support" / "Codex"
            )
        ],
        "log_roots": [
            str(FIXTURE_ROOT / "Library" / "Logs" / "com.openai.codex")
        ],
        "preference_paths": [
            str(
                FIXTURE_ROOT
                / "Library"
                / "Preferences"
                / "com.openai.codex.plist"
            )
        ],
        "cache_roots": [
            str(FIXTURE_ROOT / "Library" / "Caches" / "com.openai.codex")
        ],
    }
    serialized = json.dumps(rows, ensure_ascii=False)
    assert "This CLI session should be ignored." not in serialized
    assert "Local storage prompt should never become a transcript." not in serialized
    assert "Desktop log line must stay out of transcript output." not in serialized
    assert "Preference value that should never become transcript text." not in serialized
    assert "Cache payload that should never become transcript text." not in serialized


def test_cli_collect_codex_app_plan_and_execute(tmp_path: Path) -> None:
    plan_result = run_cli("collect", "codex_app", "--archive-root", str(tmp_path))

    assert plan_result.returncode == 0
    plan_payload = json.loads(plan_result.stdout)
    assert plan_payload["source"] == "codex_app"
    assert plan_payload["implemented"] is True

    execute_result = run_cli(
        "collect",
        "codex_app",
        "--archive-root",
        str(tmp_path),
        "--input-root",
        str(FIXTURE_ROOT),
        "--execute",
    )

    assert execute_result.returncode == 0
    execute_payload = json.loads(execute_result.stdout)
    assert execute_payload["source"] == "codex_app"
    assert execute_payload["scanned_artifact_count"] == 3
    assert execute_payload["conversation_count"] == 2
    output_path = Path(execute_payload["output_path"])
    rows = read_jsonl(output_path)
    assert len(rows) == 2
