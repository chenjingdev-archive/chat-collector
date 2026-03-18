from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from .models import ArchiveTargetPolicy, DEFAULT_ARCHIVE_ROOT, NormalizationContract
from .registry import ExecutableCollector
from .sources import build_registry


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def build_parser() -> argparse.ArgumentParser:
    registry = build_registry()
    parser = argparse.ArgumentParser(
        prog="llm_chat_archive",
        description=(
            "Collect local coding-agent chats into normalized archives stored outside "
            "this repository."
        ),
    )
    subparsers = parser.add_subparsers(dest="command")

    sources_parser = subparsers.add_parser("sources", help="List registered collectors")
    sources_parser.set_defaults(handler=handle_sources)

    contract_parser = subparsers.add_parser(
        "contract",
        help="Show the normalization schema and archive target policy",
    )
    contract_parser.set_defaults(handler=handle_contract)

    collect_parser = subparsers.add_parser(
        "collect",
        help="Emit a collection plan or execute a collector against local artifacts",
    )
    collect_parser.add_argument("source", choices=registry.keys())
    collect_parser.add_argument(
        "--archive-root",
        type=Path,
        default=DEFAULT_ARCHIVE_ROOT,
        help=(
            "Absolute archive root outside the repository. "
            f"Default: {DEFAULT_ARCHIVE_ROOT}"
        ),
    )
    collect_parser.add_argument(
        "--input-root",
        action="append",
        type=Path,
        default=[],
        help=(
            "Optional source artifact root. Repeat to override default roots or point "
            "at test fixtures."
        ),
    )
    collect_parser.add_argument(
        "--execute",
        action="store_true",
        help="Run the collector and write normalized output to the archive root.",
    )
    collect_parser.set_defaults(handler=handle_collect)

    return parser


def handle_sources(_args: argparse.Namespace) -> int:
    registry = build_registry()
    for collector in registry.list():
        roots = ", ".join(collector.descriptor.default_input_roots)
        print(
            f"{collector.descriptor.key}\t"
            f"{collector.descriptor.support_level.value}\t"
            f"{roots}"
        )
    return 0


def handle_contract(_args: argparse.Namespace) -> int:
    policy = ArchiveTargetPolicy(repo_root=repository_root())
    payload = {
        "archive_target_policy": policy.to_dict(),
        "normalization_contract": NormalizationContract().to_dict(),
        "sources": [
            collector.descriptor.to_dict() for collector in build_registry().list()
        ],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def handle_collect(args: argparse.Namespace) -> int:
    policy = ArchiveTargetPolicy(repo_root=repository_root())
    try:
        archive_root = policy.validate(args.archive_root)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    collector = build_registry().get(args.source)
    input_roots = tuple(
        input_root.expanduser().resolve(strict=False) for input_root in args.input_root
    )

    if args.execute:
        if not isinstance(collector, ExecutableCollector):
            print(
                f"real collection writes are not implemented for source: {args.source}",
                file=sys.stderr,
            )
            return 1
        result = collector.collect(archive_root, input_roots=input_roots or None)
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return 0

    plan = collector.build_plan(archive_root)
    payload = plan.to_dict()
    if input_roots:
        payload["input_roots"] = [str(input_root) for input_root in input_roots]
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 0
    return handler(args)
