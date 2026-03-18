from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, runtime_checkable

from .models import CollectionPlan, CollectionResult, SourceDescriptor


class Collector(Protocol):
    descriptor: SourceDescriptor

    def build_plan(self, archive_root: Path) -> CollectionPlan:
        ...


@runtime_checkable
class ExecutableCollector(Collector, Protocol):
    def collect(
        self, archive_root: Path, input_roots: tuple[Path, ...] | None = None
    ) -> CollectionResult:
        ...


@dataclass(slots=True)
class CollectorRegistry:
    _collectors: dict[str, Collector] = field(default_factory=dict)

    def register(self, collector: Collector) -> None:
        key = collector.descriptor.key
        if key in self._collectors:
            raise ValueError(f"collector already registered: {key}")
        self._collectors[key] = collector

    def get(self, key: str) -> Collector:
        try:
            return self._collectors[key]
        except KeyError as exc:
            raise KeyError(f"unknown collector source: {key}") from exc

    def list(self) -> tuple[Collector, ...]:
        return tuple(self._collectors[key] for key in sorted(self._collectors))

    def keys(self) -> tuple[str, ...]:
        return tuple(sorted(self._collectors))
