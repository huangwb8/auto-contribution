"""BAC v2 event schema validation."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from bac.core.hash_chain import is_sha256


FORMAT_VERSION = "bac.event.v2"

SOURCE_TYPES = {"human", "ai", "tool", "system"}
TRUST_LEVELS = {"declared", "observed", "signed", "verified", "anchored"}
EVENT_TYPES = {
    "genesis",
    "session_started",
    "human_instruction",
    "ai_plan",
    "ai_generation",
    "tool_command",
    "file_snapshot",
    "file_change",
    "test_result",
    "human_review",
    "human_approval",
    "checkpoint",
    "verification",
}

REQUIRED_EVENT_FIELDS = {
    "format",
    "event_id",
    "event_type",
    "source_type",
    "trust_level",
    "created_at",
    "project",
    "actor",
    "payload",
    "evidence",
    "redactions",
    "prev_event_hash",
    "event_hash",
    "signature",
}


def validate_event_schema(event: Any, line_number: int | None = None) -> list[str]:
    prefix = f"line {line_number}: " if line_number is not None else ""
    errors: list[str] = []

    if not isinstance(event, dict):
        return [f"{prefix}event must be a JSON object"]

    missing = sorted(REQUIRED_EVENT_FIELDS - set(event))
    if missing:
        errors.append(f"{prefix}missing required fields: {', '.join(missing)}")

    if event.get("format") != FORMAT_VERSION:
        errors.append(f"{prefix}format must be {FORMAT_VERSION}")

    if not isinstance(event.get("event_id"), str) or not event.get("event_id"):
        errors.append(f"{prefix}event_id must be a non-empty string")

    if event.get("event_type") not in EVENT_TYPES:
        errors.append(f"{prefix}event_type is not supported: {event.get('event_type')!r}")

    if event.get("source_type") not in SOURCE_TYPES:
        errors.append(f"{prefix}source_type must be one of {sorted(SOURCE_TYPES)}")

    if event.get("trust_level") not in TRUST_LEVELS:
        errors.append(f"{prefix}trust_level must be one of {sorted(TRUST_LEVELS)}")

    created_at = event.get("created_at")
    if not isinstance(created_at, str) or not _is_utc_timestamp(created_at):
        errors.append(f"{prefix}created_at must be an ISO-8601 UTC timestamp ending with Z")

    project = event.get("project")
    if not isinstance(project, dict):
        errors.append(f"{prefix}project must be an object")
    else:
        _validate_project(project, prefix, errors)

    if not isinstance(event.get("actor"), dict):
        errors.append(f"{prefix}actor must be an object")

    if not isinstance(event.get("payload"), dict):
        errors.append(f"{prefix}payload must be an object")

    if not isinstance(event.get("evidence"), list):
        errors.append(f"{prefix}evidence must be a list")

    if not isinstance(event.get("redactions"), list):
        errors.append(f"{prefix}redactions must be a list")

    prev_hash = event.get("prev_event_hash")
    if prev_hash is not None and not is_sha256(prev_hash):
        errors.append(f"{prefix}prev_event_hash must be null or sha256:<hex>")

    if not is_sha256(event.get("event_hash")):
        errors.append(f"{prefix}event_hash must be sha256:<hex>")

    signature = event.get("signature")
    if signature is not None and not isinstance(signature, dict):
        errors.append(f"{prefix}signature must be null or an object")

    return errors


def parse_created_at(value: str) -> datetime:
    return datetime.fromisoformat(value.removesuffix("Z") + "+00:00")


def _is_utc_timestamp(value: str) -> bool:
    if not value.endswith("Z"):
        return False
    try:
        parse_created_at(value)
    except ValueError:
        return False
    return True


def _validate_project(project: dict[str, Any], prefix: str, errors: list[str]) -> None:
    if not is_sha256(project.get("root_hash")):
        errors.append(f"{prefix}project.root_hash must be sha256:<hex>")
    if not isinstance(project.get("root_path"), str) or not project.get("root_path"):
        errors.append(f"{prefix}project.root_path must be a non-empty string")
    for key in ("git_remote", "git_commit", "git_branch"):
        value = project.get(key)
        if value is not None and not isinstance(value, str):
            errors.append(f"{prefix}project.{key} must be null or a string")
    if not isinstance(project.get("worktree_dirty"), bool):
        errors.append(f"{prefix}project.worktree_dirty must be a boolean")
