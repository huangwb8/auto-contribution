<div align="center">

# 🧭 Bensz Auto Contribution

**Tamper-evident contribution attribution for human-AI software collaboration**

[![Release](https://img.shields.io/github/v/tag/huangwb8/bensz-auto-contribution?label=release&color=blue)](https://github.com/huangwb8/bensz-auto-contribution/tags)
[![Python](https://img.shields.io/badge/python-3.10%2B-3776AB.svg)](https://www.python.org/)
[![BAC Format](https://img.shields.io/badge/BAC_format-v2-7C3AED.svg)](docs/bac-tutorial.md)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

[English](README.md) | [中文](README.zh-CN.md)

</div>

---

## ✨ Introduction

Bensz Auto Contribution, or **BAC**, is a contribution attribution and audit system designed for AI coding tools. Its core artifact is a `.bac` file: a project-bound, append-only, tamper-evident record of what came from humans, what came from AI, what came from tools, and what evidence was observed during development.

BAC does not claim that a file can never be modified. Instead, it makes changes detectable through structured events, canonical JSON, hash chaining, local checkpoints, project context binding, and future-ready signature and timestamp fields.

**🌟 Core Highlight**: BAC gives AI coding sessions a durable audit trail. It helps teams explain AI usage, review collaboration boundaries, verify generated work, and reconstruct development history without mixing human intent, AI generation, tool output, and file evidence into one vague blob.

### Key Features

- 🧑‍💻 **Human-AI Attribution**: Explicitly separates `human`, `ai`, `tool`, and `system` sources.
- 🧾 **Append-Only Event Model**: Records contribution history as ordered events instead of overwriting prior state.
- 🔗 **Hash-Chain Verification**: Detects modified, inserted, deleted, duplicated, or reordered events.
- 📦 **Single-File `.bac` Container**: Stores a ZIP-based v2 ledger with `manifest.json` and canonical JSON event files.
- 🛡️ **Tamper-Evident Security Boundary**: Describes integrity guarantees honestly without overstating immutability.
- 🧠 **AI Tool Ready**: Designed for Codex CLI, Claude Code, and other agentic coding environments.
- 🔍 **Evidence-Aware Records**: Captures file hashes, git diff summaries, command text, exit codes, test results, and checkpoints.
- 🧼 **Sensitive Data Redaction**: Avoids storing secrets, private prompts, or unrelated user data by default.

---

<div align="center">

### ⭐ If this project helps you, please give it a Star!

Building reliable attribution for AI-assisted work takes careful design, testing, and threat modeling. Your Star helps more builders discover BAC.

[![Star History Chart](https://api.star-history.com/svg?repos=huangwb8/bensz-auto-contribution&type=Date)](https://star-history.com/#huangwb8/bensz-auto-contribution&Date)

</div>

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- No runtime third-party dependencies

### Installation

```bash
python -m pip install -e .
```

### Basic Usage

Create a single-file `.bac` container and write the genesis event:

```bash
bac init
```

Record a human requirement:

```bash
bac record \
  --event-type human_instruction \
  --source-type human \
  --summary "Add BAC verification workflow"
```

Record AI generation or implementation intent:

```bash
bac record \
  --event-type ai_generation \
  --source-type ai \
  --summary "Implemented hash-chain verifier"
```

Record a tool result:

```bash
bac record \
  --event-type test_result \
  --source-type tool \
  --summary "Unit tests passed" \
  --command-text "python -m unittest discover -s tests -v" \
  --exit-code 0
```

Record a local checkpoint to reduce tail-truncation risk:

```bash
bac record \
  --event-type checkpoint \
  --source-type system \
  --summary "Local checkpoint"
```

Verify integrity:

```bash
bac verify
```

Inspect the contribution timeline:

```bash
bac inspect
```

All commands support `--root` for the target project root and `--bac-file` for a custom `.bac` path. `init`, `record`, `verify`, and `inspect` also support `--json` for machine-readable output.

## 🧩 Where BAC Fits

BAC is a process record and audit aid, not a final judge of contribution ownership.

In AI-assisted research, writing, and software projects, BAC can record human requirements, constraints, reviews, hand-written edits, final approvals, AI drafts, refactoring proposals, generated code, command outputs, tests, citation checks, build logs, file snapshots, and diff summaries.

These records can support AI usage disclosure, internal review, compliance notes, and dispute reconstruction. They do not automatically determine academic authorship, legal ownership, or final responsibility. Those decisions still require project policy, institutional rules, journal guidelines, and human judgment.

## 📦 `.bac` Format

The default file is `project.bac`. Externally, it is one file. Internally, it is a ZIP container with at least:

```text
manifest.json
events/000000000001.json
events/000000000002.json
```

`manifest.json` records the container version, event format, project binding information, genesis event hash, and storage conventions. Each file under `events/` is one canonical JSON event. Event filenames are continuous and start at `000000000001.json`.

A BAC event includes:

- `format`: currently `bac.event.v2`
- `event_type`: examples include `genesis`, `human_instruction`, `ai_generation`, `tool_command`, `file_change`, `test_result`, and `checkpoint`
- `source_type`: one of `human`, `ai`, `tool`, or `system`
- `trust_level`: one of `declared`, `observed`, `signed`, `verified`, or `anchored`
- `project`: root path, project binding hash, git remote, commit, branch, and dirty state
- `payload`: summary, command data, file snapshots, or event-specific content
- `evidence`: diff summaries, file hashes, command results, or other verifiable evidence
- `redactions`: fields removed or masked for safety
- `prev_event_hash` and `event_hash`: the verifiable hash chain

The verifier checks whether the file is a valid ZIP container, whether internal paths are duplicated, whether event numbering is continuous, whether the manifest matches the genesis event, and whether the hash chain can be recomputed.

For a field-by-field walkthrough, see [BAC Tutorial](docs/bac-tutorial.md).

## 🛡️ Security Model

BAC is **tamper-evident**, not tamper-proof.

It can detect common integrity problems such as edited event content, missing events, reordered events, duplicated internal ZIP paths, broken event numbering, mismatched genesis metadata, invalid hash links, and checkpoint inconsistencies.

Without an external anchor, a purely local hash chain cannot fully prevent tail truncation. BAC therefore supports local checkpoints today and keeps room for future Ed25519 signatures, git notes, release artifacts, trusted timestamps, or external transparency logs.

## 🧪 Development

Run the test suite:

```bash
python -m pytest -q
python -m unittest discover -s tests -v
```

Current coverage includes canonicalization, v2 container structure, hash-chain recomputation, tamper detection, duplicate internal path detection, checkpoint verification, sensitive data redaction, and CLI end-to-end flows.

## 🗂️ Project Structure

```text
bensz-auto-contribution/
├── AGENTS.md
├── CHANGELOG.md
├── CLAUDE.md
├── LICENSE
├── README.md
├── README.zh-CN.md
├── docs
│   ├── bac-tutorial.md
│   └── plans
├── pyproject.toml
├── src
│   └── bac
│       ├── adapters
│       ├── core
│       ├── report
│       ├── service
│       └── storage
└── tests
```

## 🤖 AI-Assisted Development

This repository includes project instructions for AI coding tools:

- `AGENTS.md` for OpenAI Codex CLI
- `CLAUDE.md` for Claude Code

When changing contribution attribution logic, keep the security boundary precise: BAC provides verifiable, tamper-evident records. It should not be described as impossible to modify.

## 🤝 Contributing

Issues and pull requests are welcome around the `.bac` file format, threat model, AI tool integration, verification logic, signing and timestamping, and developer experience.

## 📄 License

MIT License
