from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from llm_chat_archive.sources.gemini_cli import (
    GeminiCliCollector,
    discover_project_sessions,
    gemini_project_hash,
    parse_transcript_file,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures" / "gemini_cli"
PROJECT_HASH = "405eda4350775ff5078564a943938aa644a52df29bb6db3f5ef29353e3d79edb"
MAIN_SESSION_PATH = (
    FIXTURE_ROOT
    / "tmp"
    / PROJECT_HASH
    / "chats"
    / "session-2026-03-14T10-00-11111111.json"
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


def test_gemini_project_hash_matches_research_notes() -> None:
    assert gemini_project_hash(REPO_ROOT) == PROJECT_HASH


def test_discover_project_sessions_scopes_to_repo_hash_and_reports_negative_result() -> None:
    discovery = discover_project_sessions(REPO_ROOT, (FIXTURE_ROOT,))

    assert discovery.matched is True
    assert discovery.project_hash == PROJECT_HASH
    assert discovery.chat_root == FIXTURE_ROOT / "tmp" / PROJECT_HASH / "chats"
    assert [path.name for path in discovery.session_paths] == [
        "session-2026-03-14T10-00-11111111.json",
        "session-2026-03-14T11-30-22222222.json",
    ]

    missing = discover_project_sessions(Path("/Users/chenjing/dev/missing-repo"), (FIXTURE_ROOT,))

    assert missing.matched is False
    assert missing.negative_reason == "missing_project_hash_dir"
    assert missing.session_paths == ()


def test_parse_transcript_file_filters_noise_and_keeps_human_facing_content() -> None:
    conversation = parse_transcript_file(
        MAIN_SESSION_PATH,
        repo_path=REPO_ROOT,
        collected_at="2026-03-19T00:00:00Z",
    )

    assert conversation is not None
    payload = conversation.to_dict()
    assert payload["source"] == "gemini"
    assert payload["source_session_id"] == "11111111-1111-4111-8111-111111111111"
    assert payload["messages"] == [
        {
            "role": "user",
            "text": "Inspect the chat collector repository.",
            "timestamp": "2026-03-14T10:00:02Z",
            "source_message_id": "user-1",
        },
        {
            "role": "assistant",
            "text": "I will inspect the collector entry points.",
            "timestamp": "2026-03-14T10:00:03Z",
            "source_message_id": "gemini-1",
        },
        {
            "role": "user",
            "text": "Summarize the Gemini artifact layout.",
            "timestamp": "2026-03-14T10:00:05Z",
            "source_message_id": "user-2",
        },
        {
            "role": "assistant",
            "text": (
                "Session JSON under ~/.gemini/tmp/<hash>/chats is the clean transcript root.\n\n"
                "logs.json and history are noise for memory output."
            ),
            "timestamp": "2026-03-14T10:00:06Z",
            "source_message_id": "gemini-2",
        },
    ]
    assert payload["provenance"] == {
        "session_started_at": "2026-03-14T10:00:00Z",
        "source": "cli",
        "originator": "gemini_cli",
        "cwd": str(REPO_ROOT),
    }

    serialized = json.dumps(payload)
    assert "thoughts" not in serialized
    assert "toolCalls" not in serialized
    assert "tokens" not in serialized
    assert "summary" not in serialized
    assert "Session initialized" not in serialized
    assert "hook output" not in serialized


def test_gemini_cli_collect_writes_only_matching_repo_sessions(tmp_path: Path) -> None:
    collector = GeminiCliCollector(repo_path=REPO_ROOT)

    result = collector.collect(tmp_path, input_roots=(FIXTURE_ROOT,))

    assert result.source == "gemini"
    assert result.scanned_artifact_count == 2
    assert result.conversation_count == 2
    assert result.message_count == 6
    rows = read_jsonl(result.output_path)
    assert [row["source_session_id"] for row in rows] == [
        "11111111-1111-4111-8111-111111111111",
        "22222222-2222-4222-8222-222222222222",
    ]
    assert rows[1]["messages"] == [
        {
            "role": "user",
            "text": "Keep only human-facing text.\n\nDrop tool call residue.",
            "timestamp": "2026-03-14T11:30:01Z",
            "source_message_id": "user-3",
        },
        {
            "role": "assistant",
            "text": "Understood.\n\nI will keep user and assistant text only.",
            "timestamp": "2026-03-14T11:30:02Z",
            "source_message_id": "gemini-3",
        },
    ]

    serialized = json.dumps(rows)
    assert "other-user-1" not in serialized
    assert "This logs.json row must not be merged into the transcript." not in serialized
    assert "mcp-oauth-tokens-v2.json" not in serialized


def test_cli_collect_gemini_plan_and_execute(tmp_path: Path) -> None:
    plan_result = run_cli("collect", "gemini", "--archive-root", str(tmp_path))

    assert plan_result.returncode == 0
    plan_payload = json.loads(plan_result.stdout)
    assert plan_payload["source"] == "gemini"
    assert plan_payload["implemented"] is True

    execute_result = run_cli(
        "collect",
        "gemini",
        "--archive-root",
        str(tmp_path),
        "--input-root",
        str(FIXTURE_ROOT),
        "--execute",
    )

    assert execute_result.returncode == 0
    execute_payload = json.loads(execute_result.stdout)
    assert execute_payload["source"] == "gemini"
    assert execute_payload["scanned_artifact_count"] == 2
    assert execute_payload["conversation_count"] == 2
    output_path = Path(execute_payload["output_path"])
    rows = read_jsonl(output_path)
    assert len(rows) == 2
