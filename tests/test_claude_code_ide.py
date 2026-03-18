from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from llm_chat_archive.sources.claude_code_ide import (
    ClaudeCodeIdeCollector,
    discover_ide_bridge_provenance,
    parse_transcript_file,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures" / "claude_code_ide"
IDE_SESSION_ID = "33333333-3333-4333-8333-333333333333"
NON_IDE_SESSION_ID = "44444444-4444-4444-8444-444444444444"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "llm_chat_archive", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_parse_transcript_file_selects_ide_session_and_keeps_bridge_evidence_in_provenance() -> None:
    transcript_path = (
        FIXTURE_ROOT
        / "projects"
        / "-Users-chenjing-dev-chat-collector"
        / f"{IDE_SESSION_ID}.jsonl"
    )
    discovery = discover_ide_bridge_provenance((FIXTURE_ROOT,))

    assert discovery.history_session_ids == frozenset({IDE_SESSION_ID})

    conversation = parse_transcript_file(
        transcript_path,
        collected_at="2026-03-19T00:00:00Z",
        discovery=discovery,
    )

    assert conversation is not None
    payload = conversation.to_dict()
    assert payload["source"] == "claude_code_ide"
    assert payload["execution_context"] == "ide_bridge"
    assert payload["source_session_id"] == IDE_SESSION_ID
    assert payload["messages"] == [
        {
            "role": "user",
            "text": "Open the collector project in Cursor.",
            "timestamp": "2026-03-14T09:00:02Z",
            "source_message_id": "user-ide-1",
        },
        {
            "role": "assistant",
            "text": "I will reuse the shared Claude session transcript and keep IDE residue out of messages.",
            "timestamp": "2026-03-14T09:00:04Z",
            "source_message_id": "asst-ide-1",
        },
        {
            "role": "user",
            "text": "Track IDE bridge evidence in provenance only.",
            "timestamp": "2026-03-14T09:00:05Z",
            "source_message_id": "user-ide-2",
        },
        {
            "role": "assistant",
            "text": "The shared Claude session JSONL will stay canonical.",
            "timestamp": "2026-03-14T09:00:07Z",
            "source_message_id": "asst-ide-2",
        },
    ]
    assert payload["provenance"] == {
        "session_started_at": "2026-03-14T09:00:00Z",
        "source": "cli",
        "originator": "claude_code_cli",
        "cwd": "/Users/chenjing/dev/chat-collector",
        "ide_bridge": {
            "hosts": ["cursor"],
            "config_paths": [str(FIXTURE_ROOT / ".claude.json")],
            "history_paths": [str(FIXTURE_ROOT / "history.jsonl")],
            "keybinding_paths": [str(FIXTURE_ROOT / "keybindings.json")],
            "log_paths": [str(FIXTURE_ROOT / "debug" / "cb94967c-1902-448e-a976-a393cf66c4d1.txt")],
            "recent_file_paths": [
                "/Users/chenjing/.claude/keybindings.json",
                "/var/folders/cg/cr4bjzw168l7bh4b87yskltc0000gn/T/claude-prompt-73430a3b-12ec-4f63-8d51-7a8ea2e2c57e.md",
            ],
        },
    }
    serialized_messages = json.dumps(payload["messages"], ensure_ascii=False)
    assert "Enabled auto-connect to IDE" not in serialized_messages
    assert "Temporary prompt export ignored" not in serialized_messages
    assert "Watching for changes to /Users/chenjing/.claude/keybindings.json" not in serialized_messages
    assert "claude-prompt-" not in serialized_messages
    assert "shift+enter" not in serialized_messages.lower()


def test_parse_transcript_file_rejects_non_ide_session() -> None:
    transcript_path = (
        FIXTURE_ROOT
        / "projects"
        / "-Users-chenjing-dev-other-repo"
        / f"{NON_IDE_SESSION_ID}.jsonl"
    )

    assert (
        parse_transcript_file(
            transcript_path,
            collected_at="2026-03-19T00:00:00Z",
            discovery=discover_ide_bridge_provenance((FIXTURE_ROOT,)),
        )
        is None
    )


def test_claude_code_ide_collect_keeps_subagents_and_bridge_noise_out_of_messages(
    tmp_path: Path,
) -> None:
    collector = ClaudeCodeIdeCollector()

    result = collector.collect(tmp_path, input_roots=(FIXTURE_ROOT,))

    assert result.source == "claude_code_ide"
    assert result.scanned_artifact_count == 3
    assert result.conversation_count == 2
    assert result.message_count == 6
    rows = read_jsonl(result.output_path)
    assert [row["source_session_id"] for row in rows] == [
        IDE_SESSION_ID,
        f"{IDE_SESSION_ID}/subagents/reviewer",
    ]
    assert rows[0]["provenance"]["ide_bridge"] == {
        "hosts": ["cursor"],
        "config_paths": [str(FIXTURE_ROOT / ".claude.json")],
        "history_paths": [str(FIXTURE_ROOT / "history.jsonl")],
        "keybinding_paths": [str(FIXTURE_ROOT / "keybindings.json")],
        "log_paths": [str(FIXTURE_ROOT / "debug" / "cb94967c-1902-448e-a976-a393cf66c4d1.txt")],
        "recent_file_paths": [
            "/Users/chenjing/.claude/keybindings.json",
            "/var/folders/cg/cr4bjzw168l7bh4b87yskltc0000gn/T/claude-prompt-73430a3b-12ec-4f63-8d51-7a8ea2e2c57e.md",
        ],
    }
    assert rows[1]["messages"] == [
        {
            "role": "user",
            "text": "Double-check the provenance filter.",
            "timestamp": "2026-03-14T09:01:01Z",
            "source_message_id": "sub-user-1",
        },
        {
            "role": "assistant",
            "text": "The IDE bridge evidence will stay in provenance.",
            "timestamp": "2026-03-14T09:01:02Z",
            "source_message_id": "sub-asst-1",
        },
    ]
    assert rows[1]["provenance"]["originator"] == "agent-reviewer"
    serialized_messages = json.dumps([row["messages"] for row in rows], ensure_ascii=False)
    assert "Enabled auto-connect to IDE" not in serialized_messages
    assert "Temporary prompt export ignored" not in serialized_messages
    assert "Official marketplace auto-install skipped" not in serialized_messages
    assert "claude-prompt-" not in serialized_messages
    assert "diffdialog" not in serialized_messages.lower()


def test_cli_collect_claude_code_ide_plan_and_execute(tmp_path: Path) -> None:
    plan_result = run_cli("collect", "claude_code_ide", "--archive-root", str(tmp_path))

    assert plan_result.returncode == 0
    plan_payload = json.loads(plan_result.stdout)
    assert plan_payload["source"] == "claude_code_ide"
    assert plan_payload["implemented"] is True

    execute_result = run_cli(
        "collect",
        "claude_code_ide",
        "--archive-root",
        str(tmp_path),
        "--input-root",
        str(FIXTURE_ROOT),
        "--execute",
    )

    assert execute_result.returncode == 0
    execute_payload = json.loads(execute_result.stdout)
    assert execute_payload["source"] == "claude_code_ide"
    assert execute_payload["scanned_artifact_count"] == 3
    assert execute_payload["conversation_count"] == 2
    rows = read_jsonl(Path(execute_payload["output_path"]))
    assert len(rows) == 2
