from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from ..models import CollectionPlan, CollectionResult, SourceDescriptor, SupportLevel
from .codex_rollout import (
    iter_rollout_paths,
    parse_codex_rollout_file,
    resolve_input_roots,
    timestamp_slug,
    utc_timestamp,
)

CODEX_CLI_DESCRIPTOR = SourceDescriptor(
    key="codex_cli",
    display_name="Codex CLI",
    execution_context="cli",
    support_level=SupportLevel.COMPLETE,
    default_input_roots=("~/.codex",),
    notes=(
        "Scans ~/.codex/sessions/**/rollout-*.jsonl and ~/.codex/archived_sessions/rollout-*.jsonl.",
        "Keeps response_item message rows for developer, user, and assistant roles only.",
        "Excludes event, reasoning, tool, search, and turn-context noise from normalized output.",
    ),
)


@dataclass(frozen=True, slots=True)
class CodexCliCollector:
    descriptor: SourceDescriptor = CODEX_CLI_DESCRIPTOR

    def build_plan(self, archive_root: Path) -> CollectionPlan:
        return CollectionPlan(
            source=self.descriptor.key,
            display_name=self.descriptor.display_name,
            archive_root=archive_root,
            execution_context=self.descriptor.execution_context,
            support_level=self.descriptor.support_level,
            default_input_roots=self.descriptor.default_input_roots,
            implemented=True,
            notes=self.descriptor.notes,
        )

    def collect(
        self, archive_root: Path, input_roots: tuple[Path, ...] | None = None
    ) -> CollectionResult:
        resolved_input_roots = resolve_input_roots(input_roots or self._default_input_roots())
        rollout_paths = tuple(iter_rollout_paths(resolved_input_roots))
        collected_at = utc_timestamp()
        output_dir = archive_root / self.descriptor.key
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"memory_chat_v1-{timestamp_slug(collected_at)}.jsonl"

        conversation_count = 0
        message_count = 0
        with output_path.open("w", encoding="utf-8") as handle:
            for rollout_path in rollout_paths:
                conversation = parse_rollout_file(rollout_path, collected_at=collected_at)
                if conversation is None:
                    continue
                handle.write(json.dumps(conversation.to_dict(), ensure_ascii=False))
                handle.write("\n")
                conversation_count += 1
                message_count += len(conversation.messages)

        return CollectionResult(
            source=self.descriptor.key,
            archive_root=archive_root,
            output_path=output_path,
            input_roots=resolved_input_roots,
            scanned_artifact_count=len(rollout_paths),
            conversation_count=conversation_count,
            message_count=message_count,
        )

    def _default_input_roots(self) -> tuple[Path, ...]:
        return tuple(Path(root) for root in self.descriptor.default_input_roots)


def parse_rollout_file(
    rollout_path: Path, *, collected_at: str | None = None
):
    return parse_codex_rollout_file(
        rollout_path,
        descriptor=CODEX_CLI_DESCRIPTOR,
        collected_at=collected_at,
    )


__all__ = [
    "CODEX_CLI_DESCRIPTOR",
    "CodexCliCollector",
    "parse_rollout_file",
]
