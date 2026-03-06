# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/) and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] — 2026-03-06

### Added
- Full Seed → Settle → Probe → Judge benchmark pipeline
- HTTP agent adapter for evaluating live agent endpoints
- Local stub adapter for dry runs without an agent
- Multi-pass LLM judge with 0–3 scoring rubric
- HuggingFace dataset hosting with automatic fetch on first run
- 50-question test split for development and quick validation
- CI workflow with lint, test, and HuggingFace dataset validation
- Dataset validation script (`scripts/validate_v3.py`) with 10 automated checks
- Reproducibility documentation and run artifact provenance
- Integration guide with HTTP server contract and Python adapter examples

### Dataset — Engram v3

- **498 tasks** across 9 question types, generated from synthetic multi-turn conversation histories
- Initial generation produced 517 questions from anonymized session corpus
- Validation identified and fixed:
  - 14 messages with invalid `role` values (hallucinated `prioritize_request` → `user`)
  - 6 exact duplicate question IDs (second occurrence removed)
  - 8 near-duplicate questions (similarity ≥ 0.85, lower-quality copy removed)
  - 11 ungrounded answers fixed in-place (`has_answer` flag set on best-matching message)
  - 5 ungroundable questions deleted (no session message contained the answer)
- Final dataset: 498 questions, 10/10 validation checks pass
- Published to HuggingFace: [`matthewschramm/engram-v3`](https://huggingface.co/datasets/matthewschramm/engram-v3)
