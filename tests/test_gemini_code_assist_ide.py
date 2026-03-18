from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from llm_chat_archive.sources.gemini_code_assist_ide import (
    GeminiCodeAssistIdeCollector,
    attribute_chat_session,
    discover_gemini_code_assist_ide_artifacts,
    parse_global_state,
    parse_workspace_state,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures" / "gemini_code_assist_ide"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "llm_chat_archive", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_attribute_chat_session_detects_gemini_provider_without_exposing_body() -> None:
    chat_session_path = (
        FIXTURE_ROOT
        / "Library"
        / "Application Support"
        / "Code"
        / "User"
        / "workspaceStorage"
        / "workspace-alpha"
        / "chatSessions"
        / "gemini-candidate.json"
    )

    attribution = attribute_chat_session(chat_session_path)

    assert attribution is not None
    payload = attribution.to_dict()
    assert payload == {
        "session_id": "gemini-candidate",
        "ownership": "gemini",
        "provider": "Gemini Code Assist",
        "source_path": str(chat_session_path),
        "request_count": 1,
        "is_empty": False,
    }
    serialized = json.dumps(payload, ensure_ascii=False)
    assert "Gemini candidate request text must stay out." not in serialized


def test_parse_global_state_returns_metadata_only_unsupported_row() -> None:
    state_path = (
        FIXTURE_ROOT
        / "Library"
        / "Application Support"
        / "Code"
        / "User"
        / "globalStorage"
        / "state.vscdb"
    )
    artifacts = discover_gemini_code_assist_ide_artifacts((FIXTURE_ROOT,))

    conversation = parse_global_state(
        state_path,
        collected_at="2026-03-19T00:00:00Z",
        artifacts=artifacts,
    )

    assert conversation is not None
    payload = conversation.to_dict()
    assert payload["source"] == "gemini_code_assist_ide"
    assert payload["execution_context"] == "ide_extension"
    assert payload["messages"] == []
    assert payload["transcript_completeness"] == "unsupported"
    assert payload["limitations"] == [
        "no_confirmed_gemini_code_assist_ide_transcript_store",
        "metadata_only_ide_state",
        "chat_session_provider_attribution_required",
    ]
    assert payload["source_session_id"] == "vscode:global"
    assert payload["session_metadata"] == {
        "scope": "global_state",
        "has_run_once": True,
        "last_opened_version": "2.73.0",
        "new_chat_is_agent": True,
        "last_chat_mode_was_agent": True,
        "show_agent_tips_card": False,
        "onboarding_tooltip_invoked_once": True,
        "cloudcode_session_index_count": 2,
        "cloudcode_hats_index_count": 1,
        "chat_view_hidden": False,
        "outline_view_hidden": False,
        "credential_artifacts_present": True,
        "credential_artifact_count": 2,
        "install_artifacts_present": True,
        "install_artifact_count": 1,
    }
    assert payload["provenance"] == {
        "source": "vscode",
        "originator": "google.geminicodeassist",
        "app_shell": {
            "application_support_roots": [
                str(
                    FIXTURE_ROOT
                    / "Library"
                    / "Application Support"
                    / "cloud-code"
                ),
                str(
                    FIXTURE_ROOT
                    / "Library"
                    / "Application Support"
                    / "google-vscode-extension"
                ),
            ],
            "state_db_paths": [
                str(state_path),
            ],
        },
    }

    serialized = json.dumps(payload, ensure_ascii=False)
    assert "ya29.mock-access-token" not in serialized
    assert "mock-refresh-token" not in serialized
    assert "super-secret-client-secret" not in serialized
    assert "state-secret-should-not-appear" not in serialized
    assert "install-12345" not in serialized


def test_parse_workspace_state_filters_foreign_chat_sessions_and_keeps_metadata_only() -> None:
    state_path = (
        FIXTURE_ROOT
        / "Library"
        / "Application Support"
        / "Code"
        / "User"
        / "workspaceStorage"
        / "workspace-alpha"
        / "state.vscdb"
    )
    artifacts = discover_gemini_code_assist_ide_artifacts((FIXTURE_ROOT,))

    conversation = parse_workspace_state(
        state_path,
        collected_at="2026-03-19T00:00:00Z",
        artifacts=artifacts,
    )

    assert conversation is not None
    payload = conversation.to_dict()
    assert payload["source"] == "gemini_code_assist_ide"
    assert payload["source_session_id"] == "vscode:workspace-alpha"
    assert payload["messages"] == []
    assert payload["transcript_completeness"] == "unsupported"
    assert payload["session_metadata"] == {
        "scope": "workspace_state",
        "workspace_id": "workspace-alpha",
        "workspace_folder": "/Users/chenjing/dev/chat-collector",
        "chat_view_state": {
            "collapsed": False,
            "is_hidden": True,
            "size": 972,
        },
        "outline_view_state": {
            "collapsed": False,
            "is_hidden": False,
            "size": 256,
        },
        "chat_view_memento_keys": ["debug", "selectedTab"],
        "number_of_visible_chat_views": 1,
        "chat_session_index_version": 1,
        "indexed_session_count": 1,
        "empty_indexed_session_count": 1,
        "latest_indexed_message_at": "2026-03-14T10:05:00Z",
        "chat_session_attribution": [
            {
                "session_id": "copilot-session-1",
                "ownership": "foreign",
                "provider": "GitHub Copilot",
                "source_path": str(
                    FIXTURE_ROOT
                    / "Library"
                    / "Application Support"
                    / "Code"
                    / "User"
                    / "workspaceStorage"
                    / "workspace-alpha"
                    / "chatSessions"
                    / "copilot-session-1.json"
                ),
                "request_count": 1,
                "is_empty": True,
            }
        ],
        "gemini_owned_chat_session_count": 0,
        "foreign_chat_session_count": 1,
        "unknown_chat_session_count": 0,
        "credential_artifacts_present": True,
        "install_artifacts_present": True,
    }
    assert payload["provenance"] == {
        "source": "vscode",
        "originator": "google.geminicodeassist",
        "cwd": "/Users/chenjing/dev/chat-collector",
        "app_shell": {
            "application_support_roots": [
                str(
                    FIXTURE_ROOT
                    / "Library"
                    / "Application Support"
                    / "cloud-code"
                ),
                str(
                    FIXTURE_ROOT
                    / "Library"
                    / "Application Support"
                    / "google-vscode-extension"
                ),
            ],
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
                str(state_path),
            ],
        },
    }

    serialized = json.dumps(payload, ensure_ascii=False)
    assert "Copilot empty shell request text must stay out." not in serialized
    assert "Gemini candidate request text must stay out." not in serialized
    assert "ya29.mock-access-token" not in serialized


def test_parse_workspace_state_requires_gemini_specific_key_space() -> None:
    state_path = (
        FIXTURE_ROOT
        / "Library"
        / "Application Support"
        / "Code"
        / "User"
        / "workspaceStorage"
        / "workspace-beta"
        / "state.vscdb"
    )

    assert (
        parse_workspace_state(
            state_path,
            collected_at="2026-03-19T00:00:00Z",
            artifacts=discover_gemini_code_assist_ide_artifacts((FIXTURE_ROOT,)),
        )
        is None
    )


def test_gemini_code_assist_ide_collect_writes_global_and_workspace_rows(
    tmp_path: Path,
) -> None:
    collector = GeminiCodeAssistIdeCollector()

    result = collector.collect(tmp_path, input_roots=(FIXTURE_ROOT,))

    assert result.source == "gemini_code_assist_ide"
    assert result.scanned_artifact_count == 3
    assert result.conversation_count == 2
    assert result.message_count == 0
    rows = read_jsonl(result.output_path)
    assert [row["source_session_id"] for row in rows] == [
        "vscode:global",
        "vscode:workspace-alpha",
    ]
    serialized = json.dumps(rows, ensure_ascii=False)
    assert "Copilot empty shell request text must stay out." not in serialized
    assert "Gemini candidate request text must stay out." not in serialized
    assert "mock-refresh-token" not in serialized
    assert "install-12345" not in serialized


def test_cli_collect_gemini_code_assist_ide_plan_and_execute(tmp_path: Path) -> None:
    plan_result = run_cli("collect", "gemini_code_assist_ide", "--archive-root", str(tmp_path))

    assert plan_result.returncode == 0
    plan_payload = json.loads(plan_result.stdout)
    assert plan_payload["source"] == "gemini_code_assist_ide"
    assert plan_payload["implemented"] is True
    assert plan_payload["support_level"] == "partial"

    execute_result = run_cli(
        "collect",
        "gemini_code_assist_ide",
        "--archive-root",
        str(tmp_path),
        "--input-root",
        str(FIXTURE_ROOT),
        "--execute",
    )

    assert execute_result.returncode == 0
    execute_payload = json.loads(execute_result.stdout)
    assert execute_payload["source"] == "gemini_code_assist_ide"
    assert execute_payload["scanned_artifact_count"] == 3
    assert execute_payload["conversation_count"] == 2
    rows = read_jsonl(Path(execute_payload["output_path"]))
    assert len(rows) == 2
