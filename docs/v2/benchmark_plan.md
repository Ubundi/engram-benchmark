# V2 Benchmark Plan (Runtime-First)

## Goal

Provide a professional, reproducible V2 benchmark implementation inside this repository,
usable by any operator running memory-enabled agents.

## Completed

- [x] V2 protocol CLI mode (`--protocol v2`)
- [x] Runtime phases: seed, settle, probe, judge
- [x] Baseline and cortex conditions
- [x] Cortex preflight (`/memories` tool presence check)
- [x] Multi-pass judge scoring
- [x] Structured run artifacts under `outputs/<run_id>/`
- [x] Dry-run path for CI and local smoke tests

## Remaining

- [ ] Built-in baseline-vs-cortex comparison report command
- [ ] Final packaged dataset replacement for legacy V2 source file
- [ ] Optional stricter schema validation for raw V2 input payloads

## Operator outcome

An operator should be able to:
1. run baseline,
2. run cortex,
3. inspect artifact-level evidence,
4. compare quality metrics with clear traceability.
