"""Command line adapter for BAC."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from bac.core.canonicalize import canonical_json
from bac.core.schema import EVENT_TYPES, SOURCE_TYPES, TRUST_LEVELS
from bac.core.verify import verify_bac_file
from bac.report.inspect import timeline
from bac.service.event_builder import build_genesis_event, build_record_event, default_actor
from bac.storage.bac_file import DEFAULT_BAC_FILE, append_event, current_head_hash, initialize_bac_file, read_events


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (FileExistsError, FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bac", description="BAC contribution attribution ledger")
    parser.add_argument("--root", default=".", help="project root directory")
    parser.add_argument("--bac-file", default=DEFAULT_BAC_FILE, help="BAC v2 container file path")

    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="create a BAC ledger with a genesis event")
    init.add_argument("--force", action="store_true", help="overwrite an existing BAC file")
    init.add_argument("--actor-name", default="bac")
    init.add_argument("--actor-kind", default="system_tool")
    init.add_argument("--json", action="store_true", help="print machine-readable output")
    init.set_defaults(func=_cmd_init)

    record = subparsers.add_parser("record", help="append an event to a BAC ledger")
    record.add_argument("--event-type", required=True, choices=sorted(EVENT_TYPES - {"genesis"}))
    record.add_argument("--source-type", required=True, choices=sorted(SOURCE_TYPES))
    record.add_argument("--trust-level", choices=sorted(TRUST_LEVELS))
    record.add_argument("--summary", required=True)
    record.add_argument("--path", action="append", default=[], help="project file path to snapshot")
    record.add_argument("--command-text", help="command text to record")
    record.add_argument("--exit-code", type=int, help="command exit code")
    record.add_argument("--payload-json", help="additional payload object")
    record.add_argument("--evidence-json", help="additional evidence list")
    record.add_argument("--actor-name", default=None)
    record.add_argument("--actor-kind", default=None)
    record.add_argument("--session-id")
    record.add_argument("--json", action="store_true", help="print machine-readable output")
    record.set_defaults(func=_cmd_record)

    verify = subparsers.add_parser("verify", help="verify a BAC ledger")
    verify.add_argument("--json", action="store_true", help="print machine-readable output")
    verify.set_defaults(func=_cmd_verify)

    inspect = subparsers.add_parser("inspect", help="show a contribution timeline")
    inspect.add_argument("--limit", type=int)
    inspect.add_argument("--json", action="store_true", help="print machine-readable output")
    inspect.set_defaults(func=_cmd_inspect)

    return parser


def _cmd_init(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    bac_path = _bac_path(root, args.bac_file)
    actor = default_actor(args.actor_name, args.actor_kind)
    event = build_genesis_event(root, actor)
    initialize_bac_file(bac_path, event, force=args.force)
    output = {"status": "initialized", "bac_file": str(bac_path), "head_hash": event["event_hash"]}
    _print_output(output, args.json)
    return 0


def _cmd_record(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    bac_path = _bac_path(root, args.bac_file)
    head_hash = current_head_hash(bac_path)
    if head_hash is None:
        raise FileNotFoundError(f"BAC file is empty or missing: {bac_path}")

    payload = _json_object(args.payload_json, "payload-json") if args.payload_json else {}
    evidence = _json_list(args.evidence_json, "evidence-json") if args.evidence_json else []
    actor = default_actor(
        args.actor_name or args.source_type,
        args.actor_kind or args.source_type,
        args.session_id,
    )
    event = build_record_event(
        root=root,
        prev_event_hash=head_hash,
        event_type=args.event_type,
        source_type=args.source_type,
        summary=args.summary,
        trust_level=args.trust_level,
        actor=actor,
        files=args.path,
        command=args.command_text,
        exit_code=args.exit_code,
        payload=payload,
        evidence=evidence,
    )
    append_event(bac_path, event)
    output = {
        "status": "recorded",
        "event_id": event["event_id"],
        "event_type": event["event_type"],
        "head_hash": event["event_hash"],
        "redactions": event["redactions"],
    }
    _print_output(output, args.json)
    return 0


def _cmd_verify(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    report = verify_bac_file(_bac_path(root, args.bac_file))
    if args.json:
        print(canonical_json(report.to_dict()))
    else:
        print(f"status: {report.status}")
        print(f"checked_events: {report.checked_events}")
        print(f"head_hash: {report.head_hash}")
        print(f"signature_status: {report.signature_status}")
        print(f"anchor_status: {report.anchor_status}")
        for warning in report.warnings:
            print(f"warning: {warning}")
        for error in report.errors:
            print(f"error: {error}")
    return 0 if report.status in {"pass", "warn"} else 1


def _cmd_inspect(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    events = read_events(_bac_path(root, args.bac_file))
    items = timeline(events, args.limit)
    if args.json:
        print(canonical_json(items))
    else:
        for item in items:
            print(
                f"{item['created_at']}  {item['event_type']}  "
                f"{item['source_type']}/{item['trust_level']}  {item['summary']}"
            )
    return 0


def _bac_path(root: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return root / path


def _json_object(raw: str, label: str) -> dict[str, Any]:
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def _json_list(raw: str, label: str) -> list[dict[str, Any]]:
    value = json.loads(raw)
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ValueError(f"{label} must be a JSON list of objects")
    return value


def _print_output(output: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(canonical_json(output))
    else:
        for key, value in output.items():
            print(f"{key}: {value}")
