"""Generate a human-readable Markdown report for a benchmark run."""

from __future__ import annotations

from pathlib import Path
from typing import Any

_SCORE_LABELS = {
    0: "Hallucinated",
    1: "Abstained",
    2: "Generic correct",
    3: "Grounded correct",
}


def _score_label(score: float | None) -> str:
    if score is None:
        return "ERROR"
    rounded = round(score)
    label = _SCORE_LABELS.get(rounded, "?")
    return f"{rounded} ({label})"


def _mean(values: list[float]) -> str:
    if not values:
        return "N/A"
    return f"{sum(values) / len(values):.2f}"


def _score_dist(
    judgments: list[dict[str, Any]],
) -> dict[str, int]:
    dist: dict[str, int] = {"3": 0, "2": 0, "1": 0, "0": 0, "err": 0}
    for j in judgments:
        s = j.get("score")
        if s is None:
            dist["err"] += 1
        else:
            dist[str(round(s))] += 1
    return dist


def write_markdown_report(
    run_dir: Path,
    run_metadata: dict[str, Any],
    metrics: dict[str, Any],
    tasks: list[dict[str, Any]],
    predictions: list[dict[str, Any]],
    judgments: list[dict[str, Any]],
    probes: list[dict[str, Any]],
    seed_turns: list[dict[str, Any]] | None = None,
) -> Path:
    """Write ``report.md`` into the run directory. Returns the path."""
    cfg = run_metadata.get("config", {})
    condition = run_metadata.get("condition") or "unknown"
    lines: list[str] = []

    def push(s: str = "") -> None:
        lines.append(s)

    # --- Header ---
    push(f"# Benchmark Report: {condition.upper()}")
    push(
        f"Release: {run_metadata.get('benchmark_release', '?')} | "
        f"Protocol: {run_metadata.get('protocol_version', '?')} | "
        f"Generated: {run_metadata.get('timestamp_utc', '?')} | "
        f"Agent: {cfg.get('agent_id') or cfg.get('agent', '?')} | "
        f"Git: {run_metadata.get('git_commit', '?')}"
    )
    push()

    # --- Configuration ---
    push("## Configuration")
    push()
    push("| Setting | Value |")
    push("|---------|-------|")
    official = run_metadata.get("official_setting", {})
    push(f"| Benchmark release | {run_metadata.get('benchmark_release', '?')} |")
    push(f"| Protocol version | {run_metadata.get('protocol_version', '?')} |")
    push(f"| Dataset split | {cfg.get('split', '?')} |")
    push(f"| Judge model | {cfg.get('judge_model', '?')} |")
    push(f"| Judge passes | {cfg.get('judge_passes', '?')} |")
    push(f"| Judge temperature | {official.get('judge_temperature', cfg.get('judge_temperature', 'auto'))} |")
    push(f"| Judge concurrency | {cfg.get('judge_concurrency', '?')} |")
    push(f"| Task count | {run_metadata.get('task_count', '?')} |")
    push(f"| Settle seconds | {cfg.get('settle_seconds', '?')} |")
    push(f"| OpenClaw timeout | {cfg.get('openclaw_timeout', '?')}s |")
    push(f"| Flush sessions | {cfg.get('flush_sessions', False)} |")
    push(f"| Dry run | {cfg.get('dry_run', False)} |")
    push()

    # --- Seed Phase Summary ---
    push("## Seed Phase Summary")
    push()
    if seed_turns is None or len(seed_turns) == 0:
        push("Seed phase was skipped (`--skip-seed`).")
    else:
        total_turns = sum(s.get("turn_count", 0) for s in seed_turns)
        total_errors = sum(len(s.get("errors", [])) for s in seed_turns)
        total_sessions = sum(s.get("session_count", 0) for s in seed_turns)
        total_ms = sum(s.get("total_duration_ms", 0) for s in seed_turns)
        push(
            f"**{total_sessions}** sessions seeded, "
            f"**{total_turns}** turns total, "
            f"**{total_errors}** errors" + (f", **{total_ms}ms** total" if total_ms else "") + "."
        )
    push()

    # --- Summary Tables ---
    push("## Summary")
    push()

    # Scores by category
    push("### Scores by Category (0-3)")
    push()
    push("| Category | Mean | Count |")
    push("|----------|------|-------|")

    judgment_by_task: dict[str, dict[str, Any]] = {j["task_id"]: j for j in judgments}
    task_by_id: dict[str, dict[str, Any]] = {t["id"]: t for t in tasks}

    # Overall
    all_scores = [float(j["score"]) for j in judgments if j.get("score") is not None]
    push(f"| **Overall** | {_mean(all_scores)} | {len(all_scores)} |")

    # Per-category
    cat_scores: dict[str, list[float]] = {}
    for j in judgments:
        if j.get("score") is None:
            continue
        t = task_by_id.get(j["task_id"], {})
        qtype = t.get("metadata", {}).get("question_type") or "unknown"
        cat_scores.setdefault(qtype, []).append(float(j["score"]))
    for cat in sorted(cat_scores):
        vals = cat_scores[cat]
        push(f"| {cat} | {_mean(vals)} | {len(vals)} |")
    push()

    # Score distribution
    dist = _score_dist(judgments)
    total_valid = len(all_scores) or 1
    push("### Score Distribution")
    push()
    push("| Score | Meaning | Count | % |")
    push("|-------|---------|-------|---|")
    for s in ("3", "2", "1", "0"):
        c = dist[s]
        pct = int(c / total_valid * 100) if total_valid else 0
        push(f"| {s} | {_SCORE_LABELS[int(s)]} | {c} | {pct}% |")
    if dist["err"]:
        push(f"| ERR | Error | {dist['err']} | — |")
    push()

    # Latency
    latencies = sorted(p.get("duration_ms", 0) for p in probes if p.get("duration_ms", 0) > 0)
    if latencies:
        n = len(latencies)
        p50 = latencies[n // 2]
        p95 = latencies[int(n * 0.95)]
        push("### Response Latency")
        push()
        push(f"p50: {p50 / 1000:.1f}s | p95: {p95 / 1000:.1f}s | max: {latencies[-1] / 1000:.1f}s")
        push()

    # --- Probe Results (detailed) ---
    push("## Probe Results")
    push()

    pred_by_task: dict[str, dict[str, Any]] = {p["task_id"]: p for p in predictions}
    probe_by_task: dict[str, dict[str, Any]] = {p["task_id"]: p for p in probes}

    for i, task in enumerate(tasks):
        tid = task["id"]
        j = judgment_by_task.get(tid, {})
        pred = pred_by_task.get(tid, {})
        probe = probe_by_task.get(tid, {})

        score = j.get("score")
        qtype = task.get("metadata", {}).get("question_type") or "?"
        push(f"### P{i + 1:02d} — [{qtype}] {task.get('input', '')[:80]}")
        push()
        push(f"**Ground Truth:** {task.get('reference_answer', '')}")
        push()
        push("**Agent Response:**")
        output = pred.get("output", "")
        if output:
            escaped = output.replace("\n", "\n> ")
            push(f"> {escaped}")
        else:
            error = pred.get("metadata", {}).get("error", "unknown")
            push(f"> *No response — {error}*")
        push()
        push(f"**Judge Score:** {_score_label(score)}")
        if j.get("rationale"):
            push(f"**Rationale:** {j['rationale']}")
        if j.get("pass_scores"):
            push(f"**Pass Scores:** {j['pass_scores']}")
        if j.get("error"):
            push(f"**Judge Error:** {j['error']}")
        dur = probe.get("duration_ms", 0)
        if dur:
            push(f"**Latency:** {dur}ms")
        push()
        push("---")
        push()

    # --- Errors ---
    error_probes = [
        p for p in probes if "error" in (pred_by_task.get(p["task_id"], {}).get("metadata", {}))
    ]
    error_judgments = [j for j in judgments if j.get("error")]
    if error_probes or error_judgments:
        push("## Errors & Failures")
        push()
        if error_probes:
            push("### Probe Errors")
            push()
            for p in error_probes:
                err = pred_by_task.get(p["task_id"], {}).get("metadata", {}).get("error", "?")
                push(f"- **{p['task_id']}**: {err}")
            push()
        if error_judgments:
            push("### Judge Errors")
            push()
            for j in error_judgments:
                push(f"- **{j['task_id']}**: {j['error']}")
            push()

    # Write file
    md_path = run_dir / "report.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return md_path
