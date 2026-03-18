from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path

from ..models import (
    AppShellProvenance,
    CollectionPlan,
    CollectionResult,
    SourceDescriptor,
    SupportLevel,
)
from .codex_rollout import (
    CodexSessionMetadata,
    build_conversation_provenance,
    iter_rollout_paths,
    parse_codex_rollout_file,
    resolve_input_roots,
    timestamp_slug,
    utc_timestamp,
)

CODEX_APP_DESCRIPTOR = SourceDescriptor(
    key="codex_app",
    display_name="Codex Desktop App",
    execution_context="standalone_app",
    support_level=SupportLevel.COMPLETE,
    default_input_roots=(
        "~/.codex",
        "~/Library/Application Support/Codex",
        "~/Library/Logs/com.openai.codex",
        "~/Library/Preferences/com.openai.codex.plist",
        "~/Library/Caches/com.openai.codex",
    ),
    notes=(
        "Uses shared ~/.codex rollout JSONL as the canonical transcript source.",
        'Selects only sessions whose session_meta payload originator is "Codex Desktop".',
        "Treats app shell support roots under ~/Library as provenance only, not transcript body.",
    ),
)


@dataclass(frozen=True, slots=True)
class CodexAppCollector:
    descriptor: SourceDescriptor = CODEX_APP_DESCRIPTOR

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
        app_shell = discover_app_shell_provenance(resolved_input_roots)
        collected_at = utc_timestamp()
        output_dir = archive_root / self.descriptor.key
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"memory_chat_v1-{timestamp_slug(collected_at)}.jsonl"

        conversation_count = 0
        message_count = 0
        with output_path.open("w", encoding="utf-8") as handle:
            for rollout_path in rollout_paths:
                conversation = parse_rollout_file(
                    rollout_path,
                    collected_at=collected_at,
                    app_shell=app_shell,
                )
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
    rollout_path: Path,
    *,
    collected_at: str | None = None,
    app_shell: AppShellProvenance | None = None,
):
    return parse_codex_rollout_file(
        rollout_path,
        descriptor=CODEX_APP_DESCRIPTOR,
        collected_at=collected_at,
        session_filter=_is_codex_desktop_session,
        provenance_factory=lambda metadata, _path: _build_provenance(metadata, app_shell),
    )


def discover_app_shell_provenance(
    input_roots: tuple[Path, ...] | None,
) -> AppShellProvenance | None:
    if not input_roots:
        return None

    application_support_roots = _discover_paths(
        input_roots,
        direct_match=_is_codex_application_support_root,
        glob_pattern="**/Application Support/Codex",
        expect_dir=True,
    )
    log_roots = _discover_paths(
        input_roots,
        direct_match=_is_codex_log_root,
        glob_pattern="**/Logs/com.openai.codex",
        expect_dir=True,
    )
    preference_paths = _discover_paths(
        input_roots,
        direct_match=_is_codex_preference_path,
        glob_pattern="**/Preferences/com.openai.codex.plist",
        expect_dir=False,
    )
    cache_roots = _discover_paths(
        input_roots,
        direct_match=_is_codex_cache_root,
        glob_pattern="**/Caches/com.openai.codex",
        expect_dir=True,
    )

    if (
        not application_support_roots
        and not log_roots
        and not preference_paths
        and not cache_roots
    ):
        return None

    return AppShellProvenance(
        application_support_roots=application_support_roots,
        log_roots=log_roots,
        preference_paths=preference_paths,
        cache_roots=cache_roots,
    )


def _build_provenance(
    session_metadata: CodexSessionMetadata,
    app_shell: AppShellProvenance | None,
):
    return replace(build_conversation_provenance(session_metadata), app_shell=app_shell)


def _is_codex_desktop_session(
    session_metadata: CodexSessionMetadata, _rollout_path: Path
) -> bool:
    return session_metadata.originator == "Codex Desktop"


def _discover_paths(
    input_roots: tuple[Path, ...],
    *,
    direct_match,
    glob_pattern: str,
    expect_dir: bool,
) -> tuple[str, ...]:
    seen: set[Path] = set()
    candidates: list[str] = []

    for input_root in input_roots:
        matches: list[Path] = []
        if direct_match(input_root):
            matches.append(input_root)
        if input_root.is_dir():
            matches.extend(input_root.glob(glob_pattern))

        for candidate in matches:
            if expect_dir and not candidate.is_dir():
                continue
            if not expect_dir and not candidate.is_file():
                continue

            resolved = candidate.resolve(strict=False)
            if resolved in seen:
                continue

            seen.add(resolved)
            candidates.append(str(resolved))

    return tuple(sorted(candidates))


def _is_codex_application_support_root(path: Path) -> bool:
    return path.name == "Codex" and "Application Support" in path.parts


def _is_codex_log_root(path: Path) -> bool:
    return path.name == "com.openai.codex" and "Logs" in path.parts


def _is_codex_preference_path(path: Path) -> bool:
    return path.name == "com.openai.codex.plist" and "Preferences" in path.parts


def _is_codex_cache_root(path: Path) -> bool:
    return path.name == "com.openai.codex" and "Caches" in path.parts


__all__ = [
    "CODEX_APP_DESCRIPTOR",
    "CodexAppCollector",
    "discover_app_shell_provenance",
    "parse_rollout_file",
]
