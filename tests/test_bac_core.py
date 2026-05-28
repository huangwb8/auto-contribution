from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
import warnings
from pathlib import Path
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bac.core.canonicalize import canonical_json
from bac.core.container import EVENT_PATH_TEMPLATE, MANIFEST_PATH, event_path
from bac.core.hash_chain import attach_event_hash, compute_event_hash
from bac.core.schema import FORMAT_VERSION
from bac.core.verify import verify_bac_file
from bac.service.event_builder import build_genesis_event, build_record_event
from bac.service.redaction import redact_data
from bac.storage.bac_file import append_event, initialize_bac_file, read_events


class BacCoreTests(unittest.TestCase):
    def test_event_hash_is_independent_of_json_key_order(self) -> None:
        event = {
            "format": FORMAT_VERSION,
            "event_id": "example",
            "event_type": "human_instruction",
            "source_type": "human",
            "trust_level": "declared",
            "created_at": "2026-05-26T10:30:00Z",
            "project": {
                "root_path": "/tmp/project",
                "root_hash": "sha256:" + "0" * 64,
                "git_remote": None,
                "git_commit": None,
                "git_branch": None,
                "worktree_dirty": False,
            },
            "actor": {"declared_name": "user", "declared_kind": "human"},
            "payload": {"b": 2, "a": 1},
            "evidence": [],
            "redactions": [],
            "prev_event_hash": None,
            "event_hash": None,
            "signature": None,
        }
        reordered = json.loads(json.dumps(event))
        reordered["payload"] = {"a": 1, "b": 2}

        self.assertEqual(compute_event_hash(event), compute_event_hash(reordered))

    def test_verify_detects_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bac_file = root / "project.bac"
            genesis = build_genesis_event(root)
            initialize_bac_file(bac_file, genesis)
            record = build_record_event(
                root=root,
                prev_event_hash=genesis["event_hash"],
                event_type="human_instruction",
                source_type="human",
                summary="Original request",
            )
            append_event(bac_file, record)

            with ZipFile(bac_file, "r") as archive:
                manifest = archive.read(MANIFEST_PATH).decode("utf-8")
                first = archive.read(event_path(1)).decode("utf-8")
                tampered = json.loads(archive.read(event_path(2)).decode("utf-8"))
            tampered["payload"]["summary"] = "Tampered request"
            with ZipFile(bac_file, "w") as archive:
                archive.writestr(MANIFEST_PATH, manifest)
                archive.writestr(event_path(1), first)
                archive.writestr(event_path(2), canonical_json(tampered))

            report = verify_bac_file(bac_file)
            self.assertEqual(report.status, "fail")
            self.assertTrue(any("event_hash mismatch" in error for error in report.errors))

    def test_init_creates_single_file_zip_container(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bac_file = root / "project.bac"
            genesis = build_genesis_event(root)
            initialize_bac_file(bac_file, genesis)

            self.assertTrue(bac_file.is_file())
            with ZipFile(bac_file, "r") as archive:
                self.assertEqual(sorted(archive.namelist()), [event_path(1), MANIFEST_PATH])
                manifest = json.loads(archive.read(MANIFEST_PATH))
                self.assertEqual(manifest["format"], "bac.container.v2")
                self.assertEqual(manifest["event_format"], FORMAT_VERSION)
            self.assertEqual(read_events(bac_file)[0]["event_hash"], genesis["event_hash"])

    def test_checkpointed_chain_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bac_file = root / "project.bac"
            genesis = build_genesis_event(root)
            initialize_bac_file(bac_file, genesis)
            record = build_record_event(
                root=root,
                prev_event_hash=genesis["event_hash"],
                event_type="ai_generation",
                source_type="ai",
                summary="Generated implementation outline",
            )
            append_event(bac_file, record)
            checkpoint = build_record_event(
                root=root,
                prev_event_hash=record["event_hash"],
                event_type="checkpoint",
                source_type="system",
                summary="Local checkpoint",
            )
            append_event(bac_file, checkpoint)

            report = verify_bac_file(bac_file)
            self.assertEqual(report.status, "pass")
            self.assertEqual(report.anchor_status, "anchored")

    def test_redaction_masks_secrets_and_records_metadata(self) -> None:
        redacted, metadata = redact_data({"command": "curl -H 'Authorization: sk-testsecret123456789012345'"})

        self.assertIn("[REDACTED]", redacted["command"])
        self.assertTrue(metadata)

    def test_verify_reports_non_object_event_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bac_file = Path(tmp) / "project.bac"
            genesis = build_genesis_event(Path(tmp))
            initialize_bac_file(bac_file, genesis)
            with ZipFile(bac_file, "w") as archive:
                archive.writestr(MANIFEST_PATH, canonical_json(_minimal_manifest(genesis)))
                archive.writestr(event_path(1), "[]")

            report = verify_bac_file(bac_file)
            self.assertEqual(report.status, "fail")
            self.assertTrue(any("event must be a JSON object" in error for error in report.errors))

    def test_verify_rejects_non_zip_container(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bac_file = Path(tmp) / "project.bac"
            bac_file.write_text("{}\n", encoding="utf-8")

            report = verify_bac_file(bac_file)
            self.assertEqual(report.status, "fail")
            self.assertTrue(any("valid v2 ZIP container" in error for error in report.errors))

    def test_verify_rejects_duplicate_event_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bac_file = root / "project.bac"
            genesis = build_genesis_event(root)
            initialize_bac_file(bac_file, genesis)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                with ZipFile(bac_file, "a") as archive:
                    archive.writestr(event_path(1), canonical_json(genesis))

            report = verify_bac_file(bac_file)
            self.assertEqual(report.status, "fail")
            self.assertTrue(any("duplicate entry" in error for error in report.errors))

    def test_verify_rejects_event_sequence_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bac_file = root / "project.bac"
            genesis = build_genesis_event(root)
            record = build_record_event(
                root=root,
                prev_event_hash=genesis["event_hash"],
                event_type="ai_generation",
                source_type="ai",
                summary="Generated implementation outline",
            )
            with ZipFile(bac_file, "w") as archive:
                archive.writestr(MANIFEST_PATH, canonical_json(_minimal_manifest(genesis)))
                archive.writestr(event_path(1), canonical_json(genesis))
                archive.writestr(event_path(3), canonical_json(record))

            report = verify_bac_file(bac_file)
            self.assertEqual(report.status, "fail")
            self.assertTrue(any("contiguous" in error for error in report.errors))

    def test_cli_e2e(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env = dict(os.environ)
            env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")

            init_result = subprocess.run(
                [sys.executable, "-m", "bac", "--root", str(root), "init", "--json"],
                check=False,
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(init_result.returncode, 0, init_result.stderr)

            record_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "bac",
                    "--root",
                    str(root),
                    "record",
                    "--event-type",
                    "checkpoint",
                    "--source-type",
                    "system",
                    "--summary",
                    "Checkpoint current head",
                    "--json",
                ],
                check=False,
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(record_result.returncode, 0, record_result.stderr)

            verify_result = subprocess.run(
                [sys.executable, "-m", "bac", "--root", str(root), "verify", "--json"],
                check=False,
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(verify_result.returncode, 0, verify_result.stderr)
            self.assertEqual(json.loads(verify_result.stdout)["status"], "pass")


class HashAttachTests(unittest.TestCase):
    def test_attach_event_hash_sets_computed_hash(self) -> None:
        event = {
            "format": FORMAT_VERSION,
            "event_id": "example",
            "event_type": "genesis",
            "source_type": "system",
            "trust_level": "observed",
            "created_at": "2026-05-26T10:30:00Z",
            "project": {
                "root_path": "/tmp/project",
                "root_hash": "sha256:" + "0" * 64,
                "git_remote": None,
                "git_commit": None,
                "git_branch": None,
                "worktree_dirty": False,
            },
            "actor": {},
            "payload": {},
            "evidence": [],
            "redactions": [],
            "prev_event_hash": None,
            "event_hash": None,
            "signature": None,
        }
        with_hash = attach_event_hash(event)
        self.assertEqual(with_hash["event_hash"], compute_event_hash(with_hash))


def _minimal_manifest(genesis: dict) -> dict:
    return {
        "format": "bac.container.v2",
        "event_format": FORMAT_VERSION,
        "project": genesis["project"],
        "genesis_event_hash": genesis["event_hash"],
        "storage": {"kind": "zip", "event_path_template": EVENT_PATH_TEMPLATE},
    }


if __name__ == "__main__":
    unittest.main()
