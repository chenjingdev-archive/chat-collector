from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from llm_chat_archive.sources.cursor_cli import (
    CursorCliCollector,
    discover_cursor_cli_artifacts,
    parse_cli_log,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures" / "cursor_cli"
PARTIAL_LOG_PATH = (
    FIXTURE_ROOT
    / "Library"
    / "Application Support"
    / "Cursor"
    / "logs"
    / "20260314T120000"
    / "cli.log"
)
UNSUPPORTED_LOG_PATH = (
    FIXTURE_ROOT
    / "Library"
    / "Application Support"
    / "Cursor"
    / "logs"
    / "20260314T160000"
    / "cli.log"
)
WORKSPACE_STATE_PATH = (
    FIXTURE_ROOT
    / "Library"
    / "Application Support"
    / "Cursor"
    / "User"
    / "workspaceStorage"
    / "workspace-alpha"
    / "state.vscdb"
)


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "llm_chat_archive", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_parse_cli_log_marks_partial_and_keeps_prompt_cache_as_metadata_only() -> None:
    artifacts = discover_cursor_cli_artifacts((FIXTURE_ROOT,))

    conversation = parse_cli_log(
        PARTIAL_LOG_PATH,
        collected_at="2026-03-19T00:00:00Z",
        artifacts=artifacts,
    )

    assert conversation is not None
    payload = conversation.to_dict()
    assert payload["source"] == "cursor"
    assert payload["execution_context"] == "cli"
    assert payload["messages"] == []
    assert payload["transcript_completeness"] == "partial"
    assert payload["limitations"] == [
        "no_confirmed_cursor_cli_transcript_store",
        "workspace_prompt_evidence_attributed_by_time_proximity",
    ]
    assert payload["source_session_id"] == "20260314T120000"
    assert payload["session_metadata"] == {
        "invocation": {
            "invocation_id": "20260314T120000",
            "log_path": str(PARTIAL_LOG_PATH),
            "invoked_at": "2026-03-14T12:00:00Z",
            "logs_path": "/Users/chenjing/Library/Application Support/Cursor/logs/20260314T120000",
            "headless": False,
            "verbose": True,
            "status": False,
            "trace": False,
            "list_extensions": False,
            "show_versions": False,
        },
        "workspace_state_count": 1,
        "cli_config": {
            "version": "0.48.2",
            "editor": "cursor",
            "has_changed_default_model": False,
            "permissions": {"mode": "workspace-write"},
            "network": {"enabled": True},
        },
        "recently_viewed_files": [
            "/Users/chenjing/dev/chat-collector/docs/research/cursor-cli-local-artifacts.md",
            "/Users/chenjing/dev/chat-collector/src/llm_chat_archive/sources/cursor_cli.py",
        ],
        "bridge_servers": [
            {
                "source_path": str(
                    FIXTURE_ROOT
                    / ".cursor"
                    / "projects"
                    / "temp-probe"
                    / "mcps"
                    / "cursor-browser-extension"
                    / "SERVER_METADATA.json"
                ),
                "server_identifier": "cursor-browser-extension",
                "server_name": "Cursor Browser Extension",
            },
            {
                "source_path": str(
                    FIXTURE_ROOT
                    / ".cursor"
                    / "projects"
                    / "temp-probe"
                    / "mcps"
                    / "cursor-ide-browser"
                    / "SERVER_METADATA.json"
                ),
                "server_identifier": "cursor-ide-browser",
                "server_name": "Cursor IDE Browser",
            },
        ],
        "has_mcp_config": True,
        "workspace_prompt_evidence": {
            "match_strategy": "time_proximity",
            "workspace_id": "workspace-alpha",
            "composer_id": "composer-cli-alpha",
            "prompt_count": 2,
            "generation_count": 2,
            "partial_prompt_texts": [
                "Probe the Cursor CLI artifact layout.",
                "Keep cli.log and bridge state out of transcript messages.",
            ],
            "source_artifact_path": str(WORKSPACE_STATE_PATH),
            "workspace_folder": "/Users/chenjing/dev/chat-collector",
            "composer_name": "Cursor CLI probe",
            "composer_subtitle": "Prompt cache only",
            "created_at": "2026-03-14T11:59:55Z",
            "last_updated_at": "2026-03-14T12:00:50Z",
            "activity_at": "2026-03-14T12:00:50Z",
        },
    }
    assert payload["provenance"] == {
        "session_started_at": "2026-03-14T12:00:00Z",
        "source": "cli",
        "originator": "cursor_cli",
        "app_shell": {
            "application_support_roots": [
                str(FIXTURE_ROOT / "Library" / "Application Support" / "Cursor"),
            ],
            "log_roots": [
                str(
                    FIXTURE_ROOT
                    / "Library"
                    / "Application Support"
                    / "Cursor"
                    / "logs"
                ),
            ],
            "state_db_paths": [str(WORKSPACE_STATE_PATH)],
            "log_paths": [str(PARTIAL_LOG_PATH)],
            "preference_paths": [
                str(FIXTURE_ROOT / ".cursor" / "cli-config.json"),
                str(FIXTURE_ROOT / ".cursor" / "ide_state.json"),
            ],
            "cache_roots": [
                str(FIXTURE_ROOT / ".cursor"),
            ],
            "auxiliary_paths": [
                str(FIXTURE_ROOT / ".cursor" / "mcp.json"),
                str(
                    FIXTURE_ROOT
                    / ".cursor"
                    / "projects"
                    / "temp-probe"
                    / "mcps"
                    / "cursor-browser-extension"
                    / "INSTRUCTIONS.md"
                ),
                str(
                    FIXTURE_ROOT
                    / ".cursor"
                    / "projects"
                    / "temp-probe"
                    / "mcps"
                    / "cursor-browser-extension"
                    / "SERVER_METADATA.json"
                ),
                str(
                    FIXTURE_ROOT
                    / ".cursor"
                    / "projects"
                    / "temp-probe"
                    / "mcps"
                    / "cursor-ide-browser"
                    / "INSTRUCTIONS.md"
                ),
                str(
                    FIXTURE_ROOT
                    / ".cursor"
                    / "projects"
                    / "temp-probe"
                    / "mcps"
                    / "cursor-ide-browser"
                    / "SERVER_METADATA.json"
                ),
            ],
        },
    }

    serialized = json.dumps(payload, ensure_ascii=False)
    assert "super-secret-token" not in serialized
    assert "Bridge instructions that must stay out of transcript output." not in serialized
    assert "Browser extension instructions that must stay auxiliary." not in serialized
    assert "Metadata only generation summary that must not become a transcript reply." not in serialized
    assert "cursor cli text noise that must not be promoted into transcript messages" not in serialized


def test_parse_cli_log_marks_unsupported_when_only_invocation_metadata_is_confirmed() -> None:
    artifacts = discover_cursor_cli_artifacts((FIXTURE_ROOT,))

    conversation = parse_cli_log(
        UNSUPPORTED_LOG_PATH,
        collected_at="2026-03-19T00:00:00Z",
        artifacts=artifacts,
    )

    assert conversation is not None
    payload = conversation.to_dict()
    assert payload["messages"] == []
    assert payload["transcript_completeness"] == "unsupported"
    assert payload["limitations"] == [
        "no_confirmed_cursor_cli_transcript_store",
        "metadata_only_cli_invocation",
    ]
    assert payload["source_session_id"] == "20260314T160000"
    assert "workspace_prompt_evidence" not in payload["session_metadata"]


def test_cursor_cli_collect_writes_partial_and_unsupported_rows(tmp_path: Path) -> None:
    collector = CursorCliCollector()

    result = collector.collect(tmp_path, input_roots=(FIXTURE_ROOT,))

    assert result.source == "cursor"
    assert result.scanned_artifact_count == 2
    assert result.conversation_count == 2
    assert result.message_count == 0
    rows = read_jsonl(result.output_path)
    assert [row["source_session_id"] for row in rows] == [
        "20260314T120000",
        "20260314T160000",
    ]
    assert [row["transcript_completeness"] for row in rows] == [
        "partial",
        "unsupported",
    ]

    serialized = json.dumps(rows, ensure_ascii=False)
    assert "super-secret-token" not in serialized
    assert "status text noise that must stay out of transcript messages" not in serialized
    assert "Metadata only generation summary that must not become a transcript reply." not in serialized


def test_cli_collect_cursor_plan_and_execute(tmp_path: Path) -> None:
    plan_result = run_cli("collect", "cursor", "--archive-root", str(tmp_path))

    assert plan_result.returncode == 0
    plan_payload = json.loads(plan_result.stdout)
    assert plan_payload["source"] == "cursor"
    assert plan_payload["implemented"] is True
    assert plan_payload["support_level"] == "partial"

    execute_result = run_cli(
        "collect",
        "cursor",
        "--archive-root",
        str(tmp_path),
        "--input-root",
        str(FIXTURE_ROOT),
        "--execute",
    )

    assert execute_result.returncode == 0
    execute_payload = json.loads(execute_result.stdout)
    assert execute_payload["source"] == "cursor"
    assert execute_payload["scanned_artifact_count"] == 2
    assert execute_payload["conversation_count"] == 2
    rows = read_jsonl(Path(execute_payload["output_path"]))
    assert len(rows) == 2
