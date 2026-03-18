from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from llm_chat_archive.sources.claude_code_cli import (
    ClaudeCodeCliCollector,
    parse_transcript_file,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures" / "claude_code_cli"
MAIN_SESSION_ID = "11111111-1111-4111-8111-111111111111"
SECOND_SESSION_ID = "22222222-2222-4222-8222-222222222222"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "llm_chat_archive", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_parse_transcript_file_filters_noise_and_keeps_human_facing_content() -> None:
    transcript_path = (
        FIXTURE_ROOT
        / "projects"
        / "-Users-chenjing-dev-chat-collector"
        / f"{MAIN_SESSION_ID}.jsonl"
    )

    conversation = parse_transcript_file(
        transcript_path,
        collected_at="2026-03-19T00:00:00Z",
    )

    assert conversation is not None
    payload = conversation.to_dict()
    assert payload["source"] == "claude"
    assert payload["source_session_id"] == MAIN_SESSION_ID
    assert payload["messages"] == [
        {
            "role": "user",
            "text": "Inspect the chat collector repository.",
            "timestamp": "2026-03-14T10:00:02Z",
            "source_message_id": "row-user-1",
        },
        {
            "role": "assistant",
            "text": "I will inspect the collector entry points.",
            "timestamp": "2026-03-14T10:00:03Z",
            "source_message_id": "asst-1",
        },
        {
            "role": "user",
            "text": "Here is the failing screenshot.",
            "images": [
                {
                    "source": "file:///tmp/collector-failure.png",
                    "mime_type": "image/png",
                }
            ],
            "timestamp": "2026-03-14T10:00:04Z",
            "source_message_id": "user-2",
        },
        {
            "role": "assistant",
            "text": "I found the Claude collector entry point.",
            "timestamp": "2026-03-14T10:00:09Z",
            "source_message_id": "row-assistant-2",
        },
    ]
    assert payload["provenance"] == {
        "session_started_at": "2026-03-14T10:00:00Z",
        "source": "cli",
        "originator": "claude_code_cli",
        "cwd": "/Users/chenjing/dev/chat-collector",
    }
    serialized = json.dumps(payload)
    assert "tool_use" not in serialized
    assert "tool_result" not in serialized
    assert "thinking" not in serialized
    assert "progress" not in serialized
    assert "queue-operation" not in serialized
    assert "file-history-snapshot" not in serialized
    assert "custom-title" not in serialized
    assert "summary" not in serialized


def test_claude_code_cli_collect_keeps_subagents_as_separate_conversations(
    tmp_path: Path,
) -> None:
    collector = ClaudeCodeCliCollector()

    result = collector.collect(tmp_path, input_roots=(FIXTURE_ROOT,))

    assert result.source == "claude"
    assert result.scanned_artifact_count == 3
    assert result.conversation_count == 3
    assert result.message_count == 8
    rows = read_jsonl(result.output_path)
    assert [row["source_session_id"] for row in rows] == [
        MAIN_SESSION_ID,
        f"{MAIN_SESSION_ID}/subagents/reviewer",
        SECOND_SESSION_ID,
    ]
    assert rows[0]["messages"][2]["images"] == [
        {
            "source": "file:///tmp/collector-failure.png",
            "mime_type": "image/png",
        }
    ]
    assert rows[1]["messages"] == [
        {
            "role": "user",
            "text": "Check the parser edge cases.",
            "timestamp": "2026-03-14T10:01:01Z",
            "source_message_id": "sub-user-1",
        },
        {
            "role": "assistant",
            "text": "The parser should keep text and images only.",
            "timestamp": "2026-03-14T10:01:02Z",
            "source_message_id": "sub-asst-1",
        },
    ]
    assert rows[1]["provenance"]["originator"] == "agent-reviewer"
    assert "/subagents/" in rows[1]["source_artifact_path"]
    assert rows[2]["messages"] == [
        {
            "role": "user",
            "text": "Summarize the last Claude CLI run.",
            "timestamp": "2026-03-14T12:00:01Z",
            "source_message_id": "user-3",
        },
        {
            "role": "assistant",
            "text": (
                "The run completed successfully.\n\n"
                "Only human-facing content was retained."
            ),
            "timestamp": "2026-03-14T12:00:02Z",
            "source_message_id": "asst-3",
        },
    ]


def test_cli_collect_claude_plan_and_execute(tmp_path: Path) -> None:
    plan_result = run_cli("collect", "claude", "--archive-root", str(tmp_path))

    assert plan_result.returncode == 0
    plan_payload = json.loads(plan_result.stdout)
    assert plan_payload["source"] == "claude"
    assert plan_payload["implemented"] is True

    execute_result = run_cli(
        "collect",
        "claude",
        "--archive-root",
        str(tmp_path),
        "--input-root",
        str(FIXTURE_ROOT),
        "--execute",
    )

    assert execute_result.returncode == 0
    execute_payload = json.loads(execute_result.stdout)
    assert execute_payload["source"] == "claude"
    assert execute_payload["scanned_artifact_count"] == 3
    assert execute_payload["conversation_count"] == 3
    output_path = Path(execute_payload["output_path"])
    rows = read_jsonl(output_path)
    assert len(rows) == 3
