"""BAC v2 ZIP container helpers."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any
from zipfile import ZIP_DEFLATED


CONTAINER_FORMAT_VERSION = "bac.container.v2"
MANIFEST_PATH = "manifest.json"
EVENTS_DIR = "events"
EVENT_PATH_RE = re.compile(r"^events/(\d{12})\.json$")
EVENT_PATH_TEMPLATE = "events/{sequence:012d}.json"
ZIP_COMPRESSION = ZIP_DEFLATED


def event_path(sequence: int) -> str:
    return f"{EVENTS_DIR}/{sequence:012d}.json"


def event_sequence(name: str) -> int | None:
    match = EVENT_PATH_RE.match(name)
    if not match:
        return None
    return int(match.group(1))


def duplicate_names(names: list[str]) -> list[str]:
    counts = Counter(names)
    return sorted(name for name, count in counts.items() if count > 1)


def build_manifest(genesis_event: dict[str, Any]) -> dict[str, Any]:
    return {
        "format": CONTAINER_FORMAT_VERSION,
        "event_format": genesis_event.get("format"),
        "created_at": genesis_event.get("created_at"),
        "project": genesis_event.get("project"),
        "genesis_event_hash": genesis_event.get("event_hash"),
        "storage": {
            "kind": "zip",
            "event_path_template": EVENT_PATH_TEMPLATE,
            "compression": "deflate",
        },
    }
