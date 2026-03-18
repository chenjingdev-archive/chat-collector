from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

SCHEMA_VERSION = "2026-03-19"
DEFAULT_ARCHIVE_ROOT = Path("/Users/chenjing/dev/chat-history")
EXCLUDED_ARTIFACTS = (
    "tool_calls",
    "mcp_invocation_noise",
    "internal_reasoning",
    "execution_artifacts",
)


class SupportLevel(StrEnum):
    SCAFFOLD = "scaffold"
    PARTIAL = "partial"
    COMPLETE = "complete"


class TranscriptCompleteness(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    UNSUPPORTED = "unsupported"


class MessageRole(StrEnum):
    SYSTEM = "system"
    DEVELOPER = "developer"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass(frozen=True, slots=True)
class ArchiveTargetPolicy:
    repo_root: Path
    default_archive_root: Path = DEFAULT_ARCHIVE_ROOT
    mode: str = "external_only"
    fixtures_only_inside_repo: bool = True

    def validate(self, archive_root: Path) -> Path:
        candidate = archive_root.expanduser()
        if not candidate.is_absolute():
            raise ValueError("archive root must be an absolute path outside the repository")

        resolved_root = candidate.resolve(strict=False)
        resolved_repo = self.repo_root.expanduser().resolve(strict=False)
        if resolved_root == resolved_repo or resolved_repo in resolved_root.parents:
            raise ValueError(
                f"archive root must stay outside the repository: {resolved_root}"
            )
        return resolved_root

    def to_dict(self) -> dict[str, object]:
        return {
            "mode": self.mode,
            "default_archive_root": str(self.default_archive_root),
            "fixtures_only_inside_repo": self.fixtures_only_inside_repo,
            "repo_root": str(self.repo_root.resolve(strict=False)),
        }


@dataclass(frozen=True, slots=True)
class NormalizationContract:
    schema_version: str = SCHEMA_VERSION
    archive_kind: str = "memory_chat_v1"
    focus: str = "memory_usefulness"
    allowed_roles: tuple[MessageRole, ...] = (
        MessageRole.SYSTEM,
        MessageRole.DEVELOPER,
        MessageRole.USER,
        MessageRole.ASSISTANT,
    )
    excluded_artifacts: tuple[str, ...] = EXCLUDED_ARTIFACTS

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "archive_kind": self.archive_kind,
            "focus": self.focus,
            "allowed_roles": [role.value for role in self.allowed_roles],
            "excluded_artifacts": list(self.excluded_artifacts),
        }


@dataclass(frozen=True, slots=True)
class NormalizedImage:
    source: str
    mime_type: str | None = None

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {"source": self.source}
        if self.mime_type is not None:
            payload["mime_type"] = self.mime_type
        return payload


@dataclass(frozen=True, slots=True)
class NormalizedMessage:
    role: MessageRole
    text: str | None = None
    images: tuple[NormalizedImage, ...] = ()
    timestamp: str | None = None
    source_message_id: str | None = None

    def __post_init__(self) -> None:
        if self.text is None and not self.images:
            raise ValueError("normalized message requires text or images")

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {"role": self.role.value}
        if self.text is not None:
            payload["text"] = self.text
        if self.images:
            payload["images"] = [image.to_dict() for image in self.images]
        if self.timestamp is not None:
            payload["timestamp"] = self.timestamp
        if self.source_message_id is not None:
            payload["source_message_id"] = self.source_message_id
        return payload


@dataclass(frozen=True, slots=True)
class IdeBridgeProvenance:
    hosts: tuple[str, ...] = ()
    state_db_paths: tuple[str, ...] = ()
    config_paths: tuple[str, ...] = ()
    history_paths: tuple[str, ...] = ()
    keybinding_paths: tuple[str, ...] = ()
    log_paths: tuple[str, ...] = ()
    recent_file_paths: tuple[str, ...] = ()
    bridge_payload_paths: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {}
        if self.hosts:
            payload["hosts"] = list(self.hosts)
        if self.state_db_paths:
            payload["state_db_paths"] = list(self.state_db_paths)
        if self.config_paths:
            payload["config_paths"] = list(self.config_paths)
        if self.history_paths:
            payload["history_paths"] = list(self.history_paths)
        if self.keybinding_paths:
            payload["keybinding_paths"] = list(self.keybinding_paths)
        if self.log_paths:
            payload["log_paths"] = list(self.log_paths)
        if self.recent_file_paths:
            payload["recent_file_paths"] = list(self.recent_file_paths)
        if self.bridge_payload_paths:
            payload["bridge_payload_paths"] = list(self.bridge_payload_paths)
        return payload


@dataclass(frozen=True, slots=True)
class AppShellProvenance:
    application_support_roots: tuple[str, ...] = ()
    log_roots: tuple[str, ...] = ()
    state_db_paths: tuple[str, ...] = ()
    log_paths: tuple[str, ...] = ()
    preference_paths: tuple[str, ...] = ()
    cache_roots: tuple[str, ...] = ()
    auxiliary_paths: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {}
        if self.application_support_roots:
            payload["application_support_roots"] = list(self.application_support_roots)
        if self.log_roots:
            payload["log_roots"] = list(self.log_roots)
        if self.state_db_paths:
            payload["state_db_paths"] = list(self.state_db_paths)
        if self.log_paths:
            payload["log_paths"] = list(self.log_paths)
        if self.preference_paths:
            payload["preference_paths"] = list(self.preference_paths)
        if self.cache_roots:
            payload["cache_roots"] = list(self.cache_roots)
        if self.auxiliary_paths:
            payload["auxiliary_paths"] = list(self.auxiliary_paths)
        return payload


@dataclass(frozen=True, slots=True)
class ConversationProvenance:
    session_started_at: str | None = None
    source: str | None = None
    originator: str | None = None
    cwd: str | None = None
    cli_version: str | None = None
    archived: bool | None = None
    ide_bridge: IdeBridgeProvenance | None = None
    app_shell: AppShellProvenance | None = None

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {}
        if self.session_started_at is not None:
            payload["session_started_at"] = self.session_started_at
        if self.source is not None:
            payload["source"] = self.source
        if self.originator is not None:
            payload["originator"] = self.originator
        if self.cwd is not None:
            payload["cwd"] = self.cwd
        if self.cli_version is not None:
            payload["cli_version"] = self.cli_version
        if self.archived is not None:
            payload["archived"] = self.archived
        if self.ide_bridge is not None:
            ide_bridge_payload = self.ide_bridge.to_dict()
            if ide_bridge_payload:
                payload["ide_bridge"] = ide_bridge_payload
        if self.app_shell is not None:
            app_shell_payload = self.app_shell.to_dict()
            if app_shell_payload:
                payload["app_shell"] = app_shell_payload
        return payload


@dataclass(frozen=True, slots=True)
class NormalizedConversation:
    source: str
    execution_context: str
    collected_at: str
    messages: tuple[NormalizedMessage, ...]
    contract: NormalizationContract = field(default_factory=NormalizationContract)
    transcript_completeness: TranscriptCompleteness = TranscriptCompleteness.COMPLETE
    limitations: tuple[str, ...] = ()
    source_session_id: str | None = None
    source_artifact_path: str | None = None
    session_metadata: dict[str, object] | None = None
    provenance: ConversationProvenance | None = None

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "source": self.source,
            "execution_context": self.execution_context,
            "collected_at": self.collected_at,
            "messages": [message.to_dict() for message in self.messages],
            "contract": self.contract.to_dict(),
        }
        if self.transcript_completeness != TranscriptCompleteness.COMPLETE:
            payload["transcript_completeness"] = self.transcript_completeness.value
        if self.limitations:
            payload["limitations"] = list(self.limitations)
        if self.source_session_id is not None:
            payload["source_session_id"] = self.source_session_id
        if self.source_artifact_path is not None:
            payload["source_artifact_path"] = self.source_artifact_path
        if self.session_metadata is not None:
            payload["session_metadata"] = self.session_metadata
        if self.provenance is not None:
            payload["provenance"] = self.provenance.to_dict()
        return payload


@dataclass(frozen=True, slots=True)
class SourceDescriptor:
    key: str
    display_name: str
    execution_context: str
    support_level: SupportLevel
    default_input_roots: tuple[str, ...]
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "key": self.key,
            "display_name": self.display_name,
            "execution_context": self.execution_context,
            "support_level": self.support_level.value,
            "default_input_roots": list(self.default_input_roots),
            "notes": list(self.notes),
        }


@dataclass(frozen=True, slots=True)
class CollectionPlan:
    source: str
    display_name: str
    archive_root: Path
    execution_context: str
    support_level: SupportLevel
    default_input_roots: tuple[str, ...]
    contract: NormalizationContract = field(default_factory=NormalizationContract)
    write_mode: str = "dry_run"
    implemented: bool = False
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "source": self.source,
            "display_name": self.display_name,
            "archive_root": str(self.archive_root),
            "execution_context": self.execution_context,
            "support_level": self.support_level.value,
            "default_input_roots": list(self.default_input_roots),
            "contract": self.contract.to_dict(),
            "write_mode": self.write_mode,
            "implemented": self.implemented,
            "notes": list(self.notes),
        }


@dataclass(frozen=True, slots=True)
class CollectionResult:
    source: str
    archive_root: Path
    output_path: Path
    input_roots: tuple[Path, ...]
    scanned_artifact_count: int
    conversation_count: int
    message_count: int

    def to_dict(self) -> dict[str, object]:
        return {
            "source": self.source,
            "archive_root": str(self.archive_root),
            "output_path": str(self.output_path),
            "input_roots": [str(root) for root in self.input_roots],
            "scanned_artifact_count": self.scanned_artifact_count,
            "conversation_count": self.conversation_count,
            "message_count": self.message_count,
        }
