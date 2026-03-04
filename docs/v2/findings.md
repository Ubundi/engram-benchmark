# V2 Findings Guide

## Purpose

This document explains how to interpret V2 outputs from this repository.

## Where findings come from

For each V2 run, primary evidence lives in:
- `outputs/<run_id>/metrics.json`
- `outputs/<run_id>/judgments.jsonl`
- `outputs/<run_id>/probes.jsonl`
- `outputs/<run_id>/run_metadata.json`

Historical context is documented in:
- `docs/FINDINGS.md`

## Minimum findings summary template

For each condition, report:
- run ID
- mean score
- score distribution (`v2.score_0`..`v2.score_3`)
- per-category means
- error count

## Comparison template (baseline vs cortex)

Report:
- delta in `v2.mean_score`
- category-level deltas
- changes in abstention and hallucination buckets
- any runtime/judge failures that may bias interpretation

## Current status

- V2 run protocol is implemented and auditable.
- Automated comparison report generation is not yet built.
- Comparison is currently operator-driven from run artifacts.
