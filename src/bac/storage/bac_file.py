"""Read and append BAC v2 ZIP container files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from zipfile import BadZipFile, ZipFile

from bac.core.canonicalize import canonical_json
from bac.core.container import (
    MANIFEST_PATH,
    ZIP_COMPRESSION,
    build_manifest,
    duplicate_names,
    event_path,
    event_sequence,
)
from bac.core.verify import verify_bac_file


DEFAULT_BAC_FILE = "project.bac"


def read_events(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    if not path.exists():
        return events
    try:
        with ZipFile(path, "r") as archive:
            names = archive.namelist()
            duplicates = duplicate_names(names)
            if duplicates:
                raise ValueError(f"BAC container contains duplicate entries: {', '.join(duplicates)}")

            event_members = sorted(
                (event_sequence(name), name)
                for name in names
                if event_sequence(name) is not None
            )
            for sequence, name in event_members:
                if sequence is None:
                    continue
                try:
                    events.append(json.loads(archive.read(name).decode("utf-8")))
                except UnicodeDecodeError as exc:
                    raise ValueError(f"{name}: content must be UTF-8 JSON") from exc
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{name}: invalid JSON: {exc.msg}") from exc
    except BadZipFile as exc:
        raise ValueError(f"BAC file is not a valid v2 ZIP container: {path}") from exc
    return events


def current_head_hash(path: Path) -> str | None:
    events = read_events(path)
    if not events:
        return None
    return events[-1].get("event_hash")


def initialize_bac_file(path: Path, genesis_event: dict[str, Any], force: bool = False) -> None:
    if path.exists() and path.stat().st_size > 0 and not force:
        raise FileExistsError(f"BAC file already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest(genesis_event)
    with ZipFile(path, "w", compression=ZIP_COMPRESSION) as archive:
        archive.writestr(MANIFEST_PATH, canonical_json(manifest))
        archive.writestr(event_path(1), canonical_json(genesis_event))


def append_event(path: Path, event: dict[str, Any], verify_existing: bool = True) -> None:
    if not path.exists():
        raise FileNotFoundError(f"BAC file does not exist: {path}")
    if verify_existing:
        report = verify_bac_file(path)
        if report.errors:
            raise ValueError(f"cannot append to invalid BAC file: {'; '.join(report.errors)}")
    events = read_events(path)
    next_path = event_path(len(events) + 1)
    with ZipFile(path, "a", compression=ZIP_COMPRESSION) as archive:
        if next_path in archive.namelist():
            raise ValueError(f"BAC container already contains event entry: {next_path}")
        archive.writestr(next_path, canonical_json(event))
