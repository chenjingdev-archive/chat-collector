from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from llm_chat_archive.models import IdeBridgeProvenance
from llm_chat_archive.sources.codex_ide_extension import (
    CodexIdeExtensionCollector,
    parse_rollout_file,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures" / "codex_ide_extension"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "llm_chat_archive", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_parse_rollout_file_requires_codex_vscode_originator() -> None:
    rollout_path = (
        FIXTURE_ROOT
        / "sessions"
        / "2026"
        / "03"
        / "14"
        / "rollout-20260314T111500-cli-ignored.jsonl"
    )

    assert parse_rollout_file(rollout_path, collected_at="2026-03-19T00:00:00Z") is None


def test_parse_rollout_file_keeps_messages_and_attaches_bridge_provenance() -> None:
    rollout_path = (
        FIXTURE_ROOT
        / "sessions"
        / "2026"
        / "03"
        / "14"
        / "rollout-20260314T103000-ide-active.jsonl"
    )
    ide_bridge = IdeBridgeProvenance(
        hosts=("vscode",),
        state_db_paths=("/tmp/mock/state.vscdb",),
        log_paths=("/tmp/mock/Codex.log",),
        bridge_payload_paths=("/tmp/mock/Visual Studio Code-bridge-123",),
    )

    conversation = parse_rollout_file(
        rollout_path,
        collected_at="2026-03-19T00:00:00Z",
        ide_bridge=ide_bridge,
    )

    assert conversation is not None
    payload = conversation.to_dict()
    assert payload["source"] == "codex_ide_extension"
    assert payload["execution_context"] == "ide_extension"
    assert payload["source_session_id"] == "ide-active"
    assert payload["messages"] == [
        {
            "role": "developer",
            "text": "Prefer the shared rollout transcript.",
            "source_message_id": "ide-dev",
        },
        {
            "role": "user",
            "text": "Add the IDE extension collector.",
            "source_message_id": "ide-user",
        },
        {
            "role": "assistant",
            "text": "I will filter on codex_vscode and keep bridge files as provenance only.",
            "source_message_id": "ide-assistant",
        },
    ]
    assert payload["provenance"] == {
        "session_started_at": "2026-03-14T10:30:00Z",
        "source": "vscode",
        "originator": "codex_vscode",
        "cwd": "/Users/chenjing/dev/chat-collector",
        "cli_version": "0.32.0",
        "archived": False,
        "ide_bridge": {
            "hosts": ["vscode"],
            "state_db_paths": ["/tmp/mock/state.vscdb"],
            "log_paths": ["/tmp/mock/Codex.log"],
            "bridge_payload_paths": ["/tmp/mock/Visual Studio Code-bridge-123"],
        },
    }
    serialized = json.dumps(payload)
    assert "function_call" not in serialized
    assert "function_call_output" not in serialized
    assert "web_search_call" not in serialized
    assert "summary_text" not in serialized


def test_codex_ide_extension_collect_selects_only_vscode_sessions(tmp_path: Path) -> None:
    collector = CodexIdeExtensionCollector()

    result = collector.collect(tmp_path, input_roots=(FIXTURE_ROOT,))

    assert result.source == "codex_ide_extension"
    assert result.scanned_artifact_count == 3
    assert result.conversation_count == 2
    assert result.message_count == 5
    rows = read_jsonl(result.output_path)
    assert [row["source_session_id"] for row in rows] == [
        "ide-archived",
        "ide-active",
    ]
    assert {row["provenance"]["originator"] for row in rows} == {"codex_vscode"}
    assert rows[0]["provenance"]["archived"] is True
    assert rows[1]["provenance"]["archived"] is False
    assert rows[0]["provenance"]["ide_bridge"] == {
        "hosts": ["cursor", "vscode"],
        "state_db_paths": [
            str(
                FIXTURE_ROOT
                / "Library"
                / "Application Support"
                / "Code"
                / "User"
                / "globalStorage"
                / "state.vscdb"
            ),
            str(
                FIXTURE_ROOT
                / "Library"
                / "Application Support"
                / "Code"
                / "User"
                / "workspaceStorage"
                / "workspace-a"
                / "state.vscdb"
            ),
            str(
                FIXTURE_ROOT
                / "Library"
                / "Application Support"
                / "Cursor"
                / "User"
                / "workspaceStorage"
                / "workspace-b"
                / "state.vscdb"
            ),
        ],
        "log_paths": [
            str(
                FIXTURE_ROOT
                / "Library"
                / "Application Support"
                / "Code"
                / "logs"
                / "20260314T103500"
                / "window1"
                / "exthost"
                / "openai.chatgpt"
                / "Codex.log"
            ),
            str(
                FIXTURE_ROOT
                / "Library"
                / "Application Support"
                / "Cursor"
                / "logs"
                / "20260314T104000"
                / "window2"
                / "exthost"
                / "openai.chatgpt"
                / "Codex.log"
            ),
        ],
        "bridge_payload_paths": [
            str(
                FIXTURE_ROOT
                / "Library"
                / "Application Support"
                / "com.openai.chat"
                / "app_pairing_extensions"
                / "Cursor-bridge-456"
            ),
            str(
                FIXTURE_ROOT
                / "Library"
                / "Application Support"
                / "com.openai.chat"
                / "app_pairing_extensions"
                / "Visual Studio Code-bridge-123"
            ),
        ],
    }
    serialized = json.dumps(rows, ensure_ascii=False)
    assert "This should not be collected." not in serialized
    assert "state db prompt should never become a transcript" not in serialized
    assert "Workspace state should stay provenance-only" not in serialized
    assert "This log line must never become a transcript." not in serialized
    assert "Cursor log text should never become a transcript." not in serialized
    assert "Bridge payload text must stay out of messages." not in serialized
    assert "Cursor bridge payload text must stay out of messages." not in serialized


def test_cli_collect_codex_ide_extension_plan_and_execute(tmp_path: Path) -> None:
    plan_result = run_cli("collect", "codex_ide_extension", "--archive-root", str(tmp_path))

    assert plan_result.returncode == 0
    plan_payload = json.loads(plan_result.stdout)
    assert plan_payload["source"] == "codex_ide_extension"
    assert plan_payload["implemented"] is True

    execute_result = run_cli(
        "collect",
        "codex_ide_extension",
        "--archive-root",
        str(tmp_path),
        "--input-root",
        str(FIXTURE_ROOT),
        "--execute",
    )

    assert execute_result.returncode == 0
    execute_payload = json.loads(execute_result.stdout)
    assert execute_payload["source"] == "codex_ide_extension"
    assert execute_payload["scanned_artifact_count"] == 3
    assert execute_payload["conversation_count"] == 2
    output_path = Path(execute_payload["output_path"])
    rows = read_jsonl(output_path)
    assert len(rows) == 2
