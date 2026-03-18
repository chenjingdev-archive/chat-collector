from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlparse

from ..models import (
    AppShellProvenance,
    CollectionPlan,
    CollectionResult,
    ConversationProvenance,
    NormalizedConversation,
    SourceDescriptor,
    SupportLevel,
    TranscriptCompleteness,
)
from .codex_rollout import resolve_input_roots, timestamp_slug, utc_timestamp

ANTIGRAVITY_EDITOR_VIEW_DESCRIPTOR = SourceDescriptor(
    key="antigravity_editor_view",
    display_name="Antigravity Editor View",
    execution_context="ide_native",
    support_level=SupportLevel.PARTIAL,
    default_input_roots=(
        "~/Library/Application Support/Antigravity",
        "~/.gemini/antigravity",
    ),
    notes=(
        "Uses ~/.gemini/antigravity/conversations/<uuid>.pb as the primary session-family discovery root.",
        "Returns explicit undecoded metadata-only rows until protobuf message field mapping is confirmed.",
        "Treats brain, annotations, browser recordings, shared state, html artifacts, and daemon logs as provenance or noise rather than transcript body.",
    ),
)

CONVERSATION_GLOBS = (
    "conversations/*.pb",
    ".gemini/antigravity/conversations/*.pb",
    "**/.gemini/antigravity/conversations/*.pb",
)
BRAIN_GLOBS = (
    "brain/*",
    ".gemini/antigravity/brain/*",
    "**/.gemini/antigravity/brain/*",
)
ANNOTATION_GLOBS = (
    "annotations/*.pbtxt",
    ".gemini/antigravity/annotations/*.pbtxt",
    "**/.gemini/antigravity/annotations/*.pbtxt",
)
BROWSER_RECORDING_GLOBS = (
    "browser_recordings/*",
    ".gemini/antigravity/browser_recordings/*",
    "**/.gemini/antigravity/browser_recordings/*",
)
DAEMON_GLOBS = (
    "daemon/*",
    ".gemini/antigravity/daemon/*",
    "**/.gemini/antigravity/daemon/*",
)
HTML_ARTIFACT_GLOBS = (
    "html_artifacts",
    ".gemini/antigravity/html_artifacts",
    "**/.gemini/antigravity/html_artifacts",
)
APPLICATION_SUPPORT_GLOBS = (
    "Antigravity",
    "Library/Application Support/Antigravity",
    "**/Library/Application Support/Antigravity",
)
LOG_ROOT_GLOBS = (
    "logs",
    "Library/Application Support/Antigravity/logs",
    "**/Library/Application Support/Antigravity/logs",
)
GLOBAL_STATE_GLOBS = (
    "User/globalStorage/state.vscdb",
    "Library/Application Support/Antigravity/User/globalStorage/state.vscdb",
    "**/Library/Application Support/Antigravity/User/globalStorage/state.vscdb",
)
WORKSPACE_STATE_GLOBS = (
    "User/workspaceStorage/*/state.vscdb",
    "Library/Application Support/Antigravity/User/workspaceStorage/*/state.vscdb",
    "**/Library/Application Support/Antigravity/User/workspaceStorage/*/state.vscdb",
)
GLOBAL_STATE_KEYS = (
    "google.antigravity",
    "chat.workspaceTransfer",
    "antigravityUnifiedStateSync.agentManagerWindow",
    "antigravityUnifiedStateSync.artifactReview",
    "antigravityUnifiedStateSync.browserPreferences",
    "antigravityUnifiedStateSync.sidebarWorkspaces",
    "antigravityUnifiedStateSync.trajectorySummaries",
)
WORKSPACE_STATE_KEYS = (
    "chat.ChatSessionStore.index",
    "history.entries",
    "antigravity.agentViewContainerId.state",
    "memento/antigravity.jetskiArtifactsEditor",
    "memento/antigravity.antigravityReviewChangesEditor",
)
UNSUPPORTED_LIMITATIONS = (
    "opaque_conversation_protobuf",
    "message_field_mapping_unconfirmed",
    "metadata_only_session_family",
)
NOISE_EXCLUSIONS = (
    "browser_recordings",
    "html_artifacts",
    "daemon_logs",
    "unified_state_sync_blobs",
)
IMAGE_SUFFIXES = frozenset({".jpg", ".jpeg", ".png", ".webp"})
UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class AntigravityArtifacts:
    application_support_roots: tuple[str, ...] = ()
    antigravity_roots: tuple[str, ...] = ()
    conversation_paths: tuple[str, ...] = ()
    brain_dirs: tuple[str, ...] = ()
    annotation_paths: tuple[str, ...] = ()
    browser_recording_dirs: tuple[str, ...] = ()
    global_state_paths: tuple[str, ...] = ()
    workspace_state_paths: tuple[str, ...] = ()
    log_roots: tuple[str, ...] = ()
    html_artifact_roots: tuple[str, ...] = ()
    daemon_artifact_paths: tuple[str, ...] = ()

    def build_app_shell(self) -> AppShellProvenance | None:
        provenance = AppShellProvenance(
            application_support_roots=self.application_support_roots,
            log_roots=self.log_roots,
            state_db_paths=tuple(
                sorted({*self.global_state_paths, *self.workspace_state_paths})
            ),
            log_paths=self.daemon_artifact_paths,
            auxiliary_paths=self.html_artifact_roots,
        )
        if not provenance.to_dict():
            return None
        return provenance


@dataclass(frozen=True, slots=True)
class AntigravityEditorViewCollector:
    descriptor: SourceDescriptor = ANTIGRAVITY_EDITOR_VIEW_DESCRIPTOR

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
        artifacts = discover_antigravity_editor_view_artifacts(resolved_input_roots)
        collected_at = utc_timestamp()
        output_dir = archive_root / self.descriptor.key
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"memory_chat_v1-{timestamp_slug(collected_at)}.jsonl"

        conversation_count = 0
        with output_path.open("w", encoding="utf-8") as handle:
            for conversation_path in artifacts.conversation_paths:
                conversation = parse_conversation_blob(
                    Path(conversation_path),
                    collected_at=collected_at,
                    artifacts=artifacts,
                )
                if conversation is None:
                    continue
                handle.write(json.dumps(conversation.to_dict(), ensure_ascii=False))
                handle.write("\n")
                conversation_count += 1

        return CollectionResult(
            source=self.descriptor.key,
            archive_root=archive_root,
            output_path=output_path,
            input_roots=resolved_input_roots,
            scanned_artifact_count=len(artifacts.conversation_paths),
            conversation_count=conversation_count,
            message_count=0,
        )

    def _default_input_roots(self) -> tuple[Path, ...]:
        return tuple(Path(root) for root in self.descriptor.default_input_roots)


def discover_antigravity_editor_view_artifacts(
    input_roots: tuple[Path, ...] | None,
) -> AntigravityArtifacts:
    if not input_roots:
        return AntigravityArtifacts()

    return AntigravityArtifacts(
        application_support_roots=_discover_paths(
            input_roots,
            direct_match=_is_application_support_root,
            glob_patterns=APPLICATION_SUPPORT_GLOBS,
            expect_dir=True,
        ),
        antigravity_roots=_discover_paths(
            input_roots,
            direct_match=_is_antigravity_root,
            glob_patterns=("antigravity", ".gemini/antigravity", "**/.gemini/antigravity"),
            expect_dir=True,
        ),
        conversation_paths=_discover_paths(
            input_roots,
            direct_match=_is_conversation_blob,
            glob_patterns=CONVERSATION_GLOBS,
            expect_dir=False,
        ),
        brain_dirs=_discover_paths(
            input_roots,
            direct_match=_is_brain_dir,
            glob_patterns=BRAIN_GLOBS,
            expect_dir=True,
        ),
        annotation_paths=_discover_paths(
            input_roots,
            direct_match=_is_annotation_path,
            glob_patterns=ANNOTATION_GLOBS,
            expect_dir=False,
        ),
        browser_recording_dirs=_discover_paths(
            input_roots,
            direct_match=_is_browser_recording_dir,
            glob_patterns=BROWSER_RECORDING_GLOBS,
            expect_dir=True,
        ),
        global_state_paths=_discover_paths(
            input_roots,
            direct_match=_is_global_state_path,
            glob_patterns=GLOBAL_STATE_GLOBS,
            expect_dir=False,
        ),
        workspace_state_paths=_discover_paths(
            input_roots,
            direct_match=_is_workspace_state_path,
            glob_patterns=WORKSPACE_STATE_GLOBS,
            expect_dir=False,
        ),
        log_roots=_discover_paths(
            input_roots,
            direct_match=_is_log_root,
            glob_patterns=LOG_ROOT_GLOBS,
            expect_dir=True,
        ),
        html_artifact_roots=_discover_paths(
            input_roots,
            direct_match=_is_html_artifact_root,
            glob_patterns=HTML_ARTIFACT_GLOBS,
            expect_dir=True,
        ),
        daemon_artifact_paths=_discover_paths(
            input_roots,
            direct_match=_is_daemon_artifact_path,
            glob_patterns=DAEMON_GLOBS,
            expect_dir=False,
        ),
    )


def parse_conversation_blob(
    conversation_path: Path,
    *,
    collected_at: str | None = None,
    artifacts: AntigravityArtifacts | None = None,
) -> NormalizedConversation | None:
    resolved_path = conversation_path.expanduser().resolve(strict=False)
    if not resolved_path.is_file():
        return None

    session_id = _session_id_from_path(resolved_path)
    if session_id is None:
        return None

    artifact_view = artifacts or AntigravityArtifacts()
    brain_metadata = _brain_metadata(_match_session_path(artifact_view.brain_dirs, session_id))
    annotation_metadata = _annotation_metadata(
        _match_session_path(artifact_view.annotation_paths, session_id)
    )
    browser_recording_metadata = _browser_recording_metadata(
        _match_session_path(artifact_view.browser_recording_dirs, session_id)
    )
    shared_state_metadata, cwd = _shared_state_metadata(artifact_view, session_id)

    session_metadata: dict[str, object] = {
        "conversation_blob": {
            "path": str(resolved_path),
            "size_bytes": resolved_path.stat().st_size,
            "decode_status": "undecoded",
        },
        "noise_separation": {
            "excluded_from_messages": list(NOISE_EXCLUSIONS),
            "html_artifact_root_count": len(artifact_view.html_artifact_roots),
            "daemon_artifact_count": len(artifact_view.daemon_artifact_paths),
        },
    }
    if brain_metadata is not None:
        session_metadata["brain"] = brain_metadata
    if annotation_metadata is not None:
        session_metadata["annotation"] = annotation_metadata
    if browser_recording_metadata is not None:
        session_metadata["browser_recording"] = browser_recording_metadata
    if shared_state_metadata is not None:
        session_metadata["shared_state"] = shared_state_metadata

    return NormalizedConversation(
        source=ANTIGRAVITY_EDITOR_VIEW_DESCRIPTOR.key,
        execution_context=ANTIGRAVITY_EDITOR_VIEW_DESCRIPTOR.execution_context,
        collected_at=collected_at or utc_timestamp(),
        messages=(),
        transcript_completeness=TranscriptCompleteness.UNSUPPORTED,
        limitations=UNSUPPORTED_LIMITATIONS,
        source_session_id=session_id,
        source_artifact_path=str(resolved_path),
        session_metadata=session_metadata,
        provenance=ConversationProvenance(
            source="antigravity",
            originator="antigravity_editor_view",
            cwd=cwd,
            app_shell=artifact_view.build_app_shell(),
        ),
    )


def _brain_metadata(brain_dir_path: str | None) -> dict[str, object] | None:
    if brain_dir_path is None:
        return None

    brain_dir = Path(brain_dir_path)
    artifact_summaries: list[dict[str, object]] = []
    for metadata_path in sorted(brain_dir.glob("*.metadata.json")):
        payload = _load_json_file(metadata_path)
        summary: dict[str, object] = {
            "name": metadata_path.name.removesuffix(".metadata.json"),
        }
        artifact_type = _string_value(payload.get("artifactType")) if payload else None
        if artifact_type is not None:
            summary["artifact_type"] = artifact_type
        updated_at = _string_value(payload.get("updatedAt")) if payload else None
        if updated_at is not None:
            summary["updated_at"] = updated_at
        version = payload.get("version") if payload else None
        if isinstance(version, int):
            summary["version"] = version
        if payload and "summary" in payload:
            summary["has_summary"] = True
        artifact_summaries.append(summary)

    artifact_names = tuple(
        sorted(path.name for path in brain_dir.glob("*.md") if path.is_file())
    )
    resolved_artifact_count = sum(1 for path in brain_dir.glob("*.resolved") if path.is_file())
    image_artifact_count = sum(
        1
        for path in brain_dir.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    )

    payload: dict[str, object] = {"path": str(brain_dir)}
    if artifact_names:
        payload["artifact_names"] = list(artifact_names)
    if artifact_summaries:
        payload["artifact_summaries"] = artifact_summaries
    if resolved_artifact_count:
        payload["resolved_artifact_count"] = resolved_artifact_count
    if image_artifact_count:
        payload["image_artifact_count"] = image_artifact_count
    return payload


def _annotation_metadata(annotation_path: str | None) -> dict[str, object] | None:
    if annotation_path is None:
        return None

    fields = _parse_pbtxt_fields(Path(annotation_path))
    payload: dict[str, object] = {"path": annotation_path}
    if fields:
        payload["fields"] = fields
    return payload


def _browser_recording_metadata(browser_recording_dir: str | None) -> dict[str, object] | None:
    if browser_recording_dir is None:
        return None

    recording_dir = Path(browser_recording_dir)
    frame_count = sum(
        1
        for path in recording_dir.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    )
    return {
        "path": str(recording_dir),
        "frame_count": frame_count,
    }


def _shared_state_metadata(
    artifacts: AntigravityArtifacts,
    session_id: str,
) -> tuple[dict[str, object] | None, str | None]:
    if not artifacts.global_state_paths and not artifacts.workspace_state_paths:
        return None, None

    global_matches: list[dict[str, object]] = []
    for global_state_path in artifacts.global_state_paths:
        state_values = _read_state_values(Path(global_state_path), GLOBAL_STATE_KEYS)
        matched_keys = sorted(
            key
            for key, value in state_values.items()
            if _value_mentions_session(value, session_id)
        )
        global_matches.append(
            {
                "state_db_path": global_state_path,
                "matched_keys": matched_keys,
            }
        )

    workspace_entries: list[dict[str, object]] = []
    cwd: str | None = None
    for workspace_state_path in artifacts.workspace_state_paths:
        state_values = _read_state_values(Path(workspace_state_path), WORKSPACE_STATE_KEYS)
        workspace_folder = _read_workspace_folder(
            Path(workspace_state_path).parent / "workspace.json"
        )
        matched_keys = sorted(
            key
            for key, value in state_values.items()
            if key != "chat.ChatSessionStore.index"
            and _value_mentions_session(value, session_id)
        )
        if cwd is None and matched_keys and workspace_folder is not None:
            cwd = workspace_folder

        workspace_entry: dict[str, object] = {
            "state_db_path": workspace_state_path,
            "workspace_id": Path(workspace_state_path).parent.name,
            "matched_keys": matched_keys,
        }
        if workspace_folder is not None:
            workspace_entry["workspace_folder"] = workspace_folder

        index_version = _chat_session_store_index_version(
            state_values.get("chat.ChatSessionStore.index")
        )
        if index_version is not None:
            workspace_entry["chat_session_store_index_version"] = index_version

        entry_count = _chat_session_store_entry_count(
            state_values.get("chat.ChatSessionStore.index")
        )
        if entry_count is not None:
            workspace_entry["chat_session_store_entry_count"] = entry_count
        workspace_entries.append(workspace_entry)

    return (
        {
            "global_state": global_matches,
            "workspace_state": workspace_entries,
        },
        cwd,
    )


def _chat_session_store_index_version(payload: object) -> int | None:
    if not isinstance(payload, dict):
        return None
    version = payload.get("version")
    if isinstance(version, int):
        return version
    return None


def _chat_session_store_entry_count(payload: object) -> int | None:
    if not isinstance(payload, dict):
        return None
    entries = payload.get("entries")
    if not isinstance(entries, dict):
        return None
    return len(entries)


def _parse_pbtxt_fields(annotation_path: Path) -> dict[str, object]:
    try:
        lines = annotation_path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return {}

    fields: dict[str, object] = {}
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, raw_value = line.split(":", 1)
        field_name = key.strip()
        field_value = raw_value.strip()
        if not field_name:
            continue
        if field_value.startswith('"') and field_value.endswith('"'):
            fields[field_name] = field_value[1:-1]
            continue
        if field_value in {"true", "false"}:
            fields[field_name] = field_value == "true"
            continue
        try:
            fields[field_name] = int(field_value)
        except ValueError:
            fields[field_name] = field_value
    return fields


def _discover_paths(
    input_roots: tuple[Path, ...],
    *,
    direct_match,
    glob_patterns: tuple[str, ...],
    expect_dir: bool,
) -> tuple[str, ...]:
    seen: set[Path] = set()
    candidates: list[str] = []

    for input_root in input_roots:
        matches: list[Path] = []
        if direct_match(input_root):
            matches.append(input_root)
        if input_root.is_dir():
            for pattern in glob_patterns:
                matches.extend(input_root.glob(pattern))

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


def _read_state_values(
    state_db_path: Path,
    keys: tuple[str, ...],
) -> dict[str, object]:
    if not state_db_path.is_file():
        return {}

    try:
        with sqlite3.connect(str(state_db_path)) as connection:
            rows = connection.execute(
                "SELECT key, value FROM ItemTable WHERE key IN ({})".format(
                    ",".join("?" for _ in keys)
                ),
                keys,
            ).fetchall()
    except sqlite3.DatabaseError:
        return {}

    payload: dict[str, object] = {}
    for key, raw_value in rows:
        if not isinstance(key, str) or not isinstance(raw_value, str):
            continue
        try:
            payload[key] = json.loads(raw_value)
        except json.JSONDecodeError:
            payload[key] = raw_value
    return payload


def _read_workspace_folder(workspace_json_path: Path) -> str | None:
    payload = _load_json_file(workspace_json_path)
    if payload is None:
        return None

    folder_uri = _string_value(payload.get("folder"))
    if folder_uri is None:
        return None
    if folder_uri.startswith("file://"):
        parsed = urlparse(folder_uri)
        return unquote(parsed.path) or None
    return folder_uri


def _load_json_file(path: Path) -> dict[str, object] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _value_mentions_session(value: object, session_id: str) -> bool:
    if isinstance(value, str):
        return session_id in value
    try:
        serialized = json.dumps(value, ensure_ascii=False, sort_keys=True)
    except TypeError:
        return False
    return session_id in serialized


def _match_session_path(paths: tuple[str, ...], session_id: str) -> str | None:
    for raw_path in paths:
        candidate = Path(raw_path)
        candidate_session_id = _session_id_from_path(candidate)
        if candidate_session_id == session_id:
            return str(candidate)
    return None


def _session_id_from_path(path: Path) -> str | None:
    candidate = path.stem if path.is_file() else path.name
    if UUID_PATTERN.match(candidate):
        return candidate.lower()
    return None


def _is_antigravity_root(path: Path) -> bool:
    return path.name == "antigravity" and ".gemini" in path.parts


def _is_application_support_root(path: Path) -> bool:
    return path.name == "Antigravity" and "Application Support" in path.parts


def _is_log_root(path: Path) -> bool:
    return path.name == "logs" and "Antigravity" in path.parts


def _is_html_artifact_root(path: Path) -> bool:
    return path.name == "html_artifacts" and "antigravity" in path.parts


def _is_daemon_artifact_path(path: Path) -> bool:
    return path.parent.name == "daemon" and "antigravity" in path.parts


def _is_conversation_blob(path: Path) -> bool:
    return path.suffix == ".pb" and path.parent.name == "conversations"


def _is_brain_dir(path: Path) -> bool:
    return path.parent.name == "brain" and _session_id_from_path(path) is not None


def _is_annotation_path(path: Path) -> bool:
    return path.suffix == ".pbtxt" and path.parent.name == "annotations"


def _is_browser_recording_dir(path: Path) -> bool:
    return path.parent.name == "browser_recordings" and _session_id_from_path(path) is not None


def _is_global_state_path(path: Path) -> bool:
    return path.name == "state.vscdb" and path.parent.name == "globalStorage"


def _is_workspace_state_path(path: Path) -> bool:
    return path.name == "state.vscdb" and path.parent.parent.name == "workspaceStorage"


def _string_value(value: object) -> str | None:
    if isinstance(value, str):
        return value
    return None


__all__ = [
    "ANTIGRAVITY_EDITOR_VIEW_DESCRIPTOR",
    "AntigravityArtifacts",
    "AntigravityEditorViewCollector",
    "discover_antigravity_editor_view_artifacts",
    "parse_conversation_blob",
]
