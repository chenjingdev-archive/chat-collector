from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from llm_chat_archive.sources.antigravity_editor_view import (
    AntigravityEditorViewCollector,
    discover_antigravity_editor_view_artifacts,
    parse_conversation_blob,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures" / "antigravity_editor_view"
SESSION_ALPHA = "11111111-1111-4111-8111-111111111111"
SESSION_BETA = "22222222-2222-4222-8222-222222222222"
SESSION_ORPHAN = "33333333-3333-4333-8333-333333333333"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "llm_chat_archive", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_discover_antigravity_editor_view_artifacts_indexes_session_sidecars() -> None:
    artifacts = discover_antigravity_editor_view_artifacts((FIXTURE_ROOT,))

    assert artifacts.conversation_paths == (
        str(
            FIXTURE_ROOT
            / ".gemini"
            / "antigravity"
            / "conversations"
            / f"{SESSION_ALPHA}.pb"
        ),
        str(
            FIXTURE_ROOT
            / ".gemini"
            / "antigravity"
            / "conversations"
            / f"{SESSION_BETA}.pb"
        ),
    )
    assert artifacts.brain_dirs == (
        str(FIXTURE_ROOT / ".gemini" / "antigravity" / "brain" / SESSION_ALPHA),
        str(FIXTURE_ROOT / ".gemini" / "antigravity" / "brain" / SESSION_ORPHAN),
    )
    assert artifacts.annotation_paths == (
        str(
            FIXTURE_ROOT
            / ".gemini"
            / "antigravity"
            / "annotations"
            / f"{SESSION_ALPHA}.pbtxt"
        ),
    )
    assert artifacts.browser_recording_dirs == (
        str(
            FIXTURE_ROOT
            / ".gemini"
            / "antigravity"
            / "browser_recordings"
            / SESSION_ALPHA
        ),
        str(
            FIXTURE_ROOT
            / ".gemini"
            / "antigravity"
            / "browser_recordings"
            / SESSION_ORPHAN
        ),
    )
    assert artifacts.global_state_paths == (
        str(
            FIXTURE_ROOT
            / "Library"
            / "Application Support"
            / "Antigravity"
            / "User"
            / "globalStorage"
            / "state.vscdb"
        ),
    )
    assert artifacts.workspace_state_paths == (
        str(
            FIXTURE_ROOT
            / "Library"
            / "Application Support"
            / "Antigravity"
            / "User"
            / "workspaceStorage"
            / "workspace-alpha"
            / "state.vscdb"
        ),
    )


def test_parse_conversation_blob_returns_undecoded_metadata_only_row() -> None:
    conversation_path = (
        FIXTURE_ROOT
        / ".gemini"
        / "antigravity"
        / "conversations"
        / f"{SESSION_ALPHA}.pb"
    )
    global_state_path = (
        FIXTURE_ROOT
        / "Library"
        / "Application Support"
        / "Antigravity"
        / "User"
        / "globalStorage"
        / "state.vscdb"
    )
    workspace_state_path = (
        FIXTURE_ROOT
        / "Library"
        / "Application Support"
        / "Antigravity"
        / "User"
        / "workspaceStorage"
        / "workspace-alpha"
        / "state.vscdb"
    )
    artifacts = discover_antigravity_editor_view_artifacts((FIXTURE_ROOT,))

    conversation = parse_conversation_blob(
        conversation_path,
        collected_at="2026-03-19T00:00:00Z",
        artifacts=artifacts,
    )

    assert conversation is not None
    payload = conversation.to_dict()
    assert payload["source"] == "antigravity_editor_view"
    assert payload["execution_context"] == "ide_native"
    assert payload["messages"] == []
    assert payload["transcript_completeness"] == "unsupported"
    assert payload["limitations"] == [
        "opaque_conversation_protobuf",
        "message_field_mapping_unconfirmed",
        "metadata_only_session_family",
    ]
    assert payload["source_session_id"] == SESSION_ALPHA
    assert payload["session_metadata"] == {
        "conversation_blob": {
            "path": str(conversation_path),
            "size_bytes": conversation_path.stat().st_size,
            "decode_status": "undecoded",
        },
        "noise_separation": {
            "excluded_from_messages": [
                "browser_recordings",
                "html_artifacts",
                "daemon_logs",
                "unified_state_sync_blobs",
            ],
            "html_artifact_root_count": 1,
            "daemon_artifact_count": 1,
        },
        "brain": {
            "path": str(FIXTURE_ROOT / ".gemini" / "antigravity" / "brain" / SESSION_ALPHA),
            "artifact_names": [
                "implementation_plan.md",
                "task.md",
                "walkthrough.md",
            ],
            "artifact_summaries": [
                {
                    "name": "implementation_plan.md",
                    "artifact_type": "ARTIFACT_TYPE_IMPLEMENTATION_PLAN",
                    "updated_at": "2026-03-14T10:06:00Z",
                    "version": 2,
                    "has_summary": True,
                },
                {
                    "name": "task.md",
                    "artifact_type": "ARTIFACT_TYPE_TASK",
                    "updated_at": "2026-03-14T10:05:00Z",
                    "version": 1,
                    "has_summary": True,
                },
                {
                    "name": "walkthrough.md",
                    "artifact_type": "ARTIFACT_TYPE_WALKTHROUGH",
                    "updated_at": "2026-03-14T10:07:00Z",
                    "version": 3,
                },
            ],
            "resolved_artifact_count": 2,
            "image_artifact_count": 1,
        },
        "annotation": {
            "path": str(
                FIXTURE_ROOT
                / ".gemini"
                / "antigravity"
                / "annotations"
                / f"{SESSION_ALPHA}.pbtxt"
            ),
            "fields": {
                "last_user_view_time": "2026-03-14T10:08:00Z",
                "annotation_version": 4,
            },
        },
        "browser_recording": {
            "path": str(
                FIXTURE_ROOT
                / ".gemini"
                / "antigravity"
                / "browser_recordings"
                / SESSION_ALPHA
            ),
            "frame_count": 2,
        },
        "shared_state": {
            "global_state": [
                {
                    "state_db_path": str(global_state_path),
                    "matched_keys": [
                        "antigravityUnifiedStateSync.artifactReview",
                        "antigravityUnifiedStateSync.trajectorySummaries",
                    ],
                }
            ],
            "workspace_state": [
                {
                    "state_db_path": str(workspace_state_path),
                    "workspace_id": "workspace-alpha",
                    "matched_keys": [
                        "memento/antigravity.jetskiArtifactsEditor",
                    ],
                    "workspace_folder": "/Users/chenjing/dev/chat-collector",
                    "chat_session_store_index_version": 1,
                    "chat_session_store_entry_count": 0,
                }
            ],
        },
    }
    assert payload["provenance"] == {
        "source": "antigravity",
        "originator": "antigravity_editor_view",
        "cwd": "/Users/chenjing/dev/chat-collector",
        "app_shell": {
            "application_support_roots": [
                str(FIXTURE_ROOT / "Library" / "Application Support" / "Antigravity"),
            ],
            "log_roots": [
                str(
                    FIXTURE_ROOT
                    / "Library"
                    / "Application Support"
                    / "Antigravity"
                    / "logs"
                ),
            ],
            "state_db_paths": [
                str(global_state_path),
                str(workspace_state_path),
            ],
            "log_paths": [
                str(
                    FIXTURE_ROOT
                    / ".gemini"
                    / "antigravity"
                    / "daemon"
                    / "ls_c318d4f90fc5aacc.log"
                ),
            ],
            "auxiliary_paths": [
                str(FIXTURE_ROOT / ".gemini" / "antigravity" / "html_artifacts"),
            ],
        },
    }

    serialized = json.dumps(payload, ensure_ascii=False)
    assert "Opaque transcript text that must stay undecoded." not in serialized
    assert "Task markdown body must stay out of transcript." not in serialized
    assert "Implementation plan resolved body must stay out of transcript." not in serialized
    assert "Browser frame text must stay out of transcript." not in serialized
    assert "Daemon log body must stay out of transcript." not in serialized
    assert "HTML artifact body must stay out of transcript." not in serialized
    assert "opaque-shared-state-blob" not in serialized


def test_antigravity_editor_view_collect_writes_one_row_per_conversation_blob(
    tmp_path: Path,
) -> None:
    collector = AntigravityEditorViewCollector()

    result = collector.collect(tmp_path, input_roots=(FIXTURE_ROOT,))

    assert result.source == "antigravity_editor_view"
    assert result.scanned_artifact_count == 2
    assert result.conversation_count == 2
    assert result.message_count == 0
    rows = read_jsonl(result.output_path)
    assert [row["source_session_id"] for row in rows] == [SESSION_ALPHA, SESSION_BETA]
    assert SESSION_ORPHAN not in {row["source_session_id"] for row in rows}
    beta_row = rows[1]
    assert beta_row["messages"] == []
    assert beta_row["transcript_completeness"] == "unsupported"
    assert "brain" not in beta_row["session_metadata"]
    assert "annotation" not in beta_row["session_metadata"]
    assert "browser_recording" not in beta_row["session_metadata"]
    serialized = json.dumps(rows, ensure_ascii=False)
    assert "Task markdown body must stay out of transcript." not in serialized
    assert "Browser frame text must stay out of transcript." not in serialized
    assert SESSION_ORPHAN not in serialized


def test_cli_collect_antigravity_editor_view_plan_and_execute(tmp_path: Path) -> None:
    plan_result = run_cli("collect", "antigravity_editor_view", "--archive-root", str(tmp_path))

    assert plan_result.returncode == 0
    plan_payload = json.loads(plan_result.stdout)
    assert plan_payload["source"] == "antigravity_editor_view"
    assert plan_payload["implemented"] is True
    assert plan_payload["support_level"] == "partial"

    execute_result = run_cli(
        "collect",
        "antigravity_editor_view",
        "--archive-root",
        str(tmp_path),
        "--input-root",
        str(FIXTURE_ROOT),
        "--execute",
    )

    assert execute_result.returncode == 0
    execute_payload = json.loads(execute_result.stdout)
    assert execute_payload["source"] == "antigravity_editor_view"
    assert execute_payload["scanned_artifact_count"] == 2
    assert execute_payload["conversation_count"] == 2
    rows = read_jsonl(Path(execute_payload["output_path"]))
    assert len(rows) == 2
