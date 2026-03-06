"""Offline comparison of two benchmark runs."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def _load_run(run_dir: str) -> dict[str, Any]:
    """Load artifacts from a run directory."""
    p = Path(run_dir)
    if not p.is_dir():
        raise FileNotFoundError(f"Run directory not found: {p}")

    def read_json(name: str) -> dict[str, Any]:
        fp = p / name
        if not fp.exists():
            return {}
        return json.loads(fp.read_text(encoding="utf-8"))

    def read_jsonl(name: str) -> list[dict[str, Any]]:
        fp = p / name
        if not fp.exists():
            return []
        rows = []
        for line in fp.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
        return rows

    return {
        "run_metadata": read_json("run_metadata.json"),
        "metrics": read_json("metrics.json"),
        "predictions": read_jsonl("predictions.jsonl"),
        "judgments": read_jsonl("judgments.jsonl"),
        "probes": read_jsonl("probes.jsonl"),
    }


def _mean_score(
    judgments: list[dict[str, Any]],
    category: str | None = None,
    tasks_by_id: dict[str, dict[str, Any]] | None = None,
) -> str:
    """Compute mean score, optionally filtered by question_type."""
    filtered = []
    for j in judgments:
        if j.get("score") is None:
            continue
        if category is not None and tasks_by_id is not None:
            t = tasks_by_id.get(j.get("task_id", ""), {})
            qtype = t.get("metadata", {}).get("question_type")
            if qtype != category:
                continue
        filtered.append(float(j["score"]))
    if not filtered:
        return "N/A"
    return f"{sum(filtered) / len(filtered):.2f}"


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


def _fmt_delta(a: str, b: str) -> str:
    if a == "N/A" or b == "N/A":
        return "  N/A"
    d = float(b) - float(a)
    return f"{'+' if d >= 0 else ''}{d:.2f}"


def _write_comparison_md(
    run_a: dict[str, Any],
    run_b: dict[str, Any],
    categories: list[str],
    tasks_by_id: dict[str, dict[str, Any]],
    output_path: Path,
) -> Path:
    """Write a detailed comparison Markdown document."""
    meta_a = run_a["run_metadata"]
    meta_b = run_b["run_metadata"]
    cfg_a = meta_a.get("config", {})
    cfg_b = meta_b.get("config", {})
    cond_a = meta_a.get("condition") or "A"
    cond_b = meta_b.get("condition") or "B"
    j_a = run_a["judgments"]
    j_b = run_b["judgments"]

    lines: list[str] = []
    push = lines.append

    push(f"# Benchmark Comparison: {cond_a.upper()} vs {cond_b.upper()}")
    push(f"Generated: {meta_a.get('timestamp_utc', '?')} vs {meta_b.get('timestamp_utc', '?')}")
    push("")

    # Config comparison
    push("## Configuration Comparison")
    push("")
    push(f"| Setting | {cond_a} | {cond_b} |")
    push("|---------|---------|---------|")
    push(f"| Agent ID | {cfg_a.get('agent_id', '?')} | {cfg_b.get('agent_id', '?')} |")
    push(f"| Judge model | {cfg_a.get('judge_model', '?')} | {cfg_b.get('judge_model', '?')} |")
    push(f"| Judge passes | {cfg_a.get('judge_passes', '?')} | {cfg_b.get('judge_passes', '?')} |")
    push(f"| Task count | {meta_a.get('task_count', '?')} | {meta_b.get('task_count', '?')} |")
    push(f"| Git commit | {meta_a.get('git_commit', '?')} | {meta_b.get('git_commit', '?')} |")
    push("")

    # Overall results
    push("## Overall Results")
    push("")
    push(f"| Category | {cond_a} | {cond_b} | Delta |")
    push("|----------|---------|---------|-------|")
    oa = _mean_score(j_a)
    ob = _mean_score(j_b)
    push(f"| **Overall Mean** | {oa} | {ob} | {_fmt_delta(oa, ob)} |")
    for cat in categories:
        a = _mean_score(j_a, cat, tasks_by_id)
        b = _mean_score(j_b, cat, tasks_by_id)
        push(f"| {cat} | {a} | {b} | {_fmt_delta(a, b)} |")
    push("")

    # Score distribution
    dist_a = _score_dist(j_a)
    dist_b = _score_dist(j_b)
    push("## Score Distribution")
    push("")
    push(f"| Score | Meaning | {cond_a} | {cond_b} |")
    push("|-------|---------|---------|---------|")
    labels = {
        "3": "Grounded correct",
        "2": "Generic correct",
        "1": "Abstained",
        "0": "Hallucinated",
    }
    for s in ("3", "2", "1", "0"):
        push(f"| {s} | {labels[s]} | {dist_a[s]} | {dist_b[s]} |")
    if dist_a["err"] or dist_b["err"]:
        push(f"| ERR | Error | {dist_a['err']} | {dist_b['err']} |")
    push("")

    # Per-task comparison
    scores_a = {j["task_id"]: j for j in j_a}
    scores_b = {j["task_id"]: j for j in j_b}

    # Collect improvements and regressions
    improved: list[dict[str, Any]] = []
    regressed: list[dict[str, Any]] = []

    all_task_ids = list(dict.fromkeys([j["task_id"] for j in j_a] + [j["task_id"] for j in j_b]))

    for tid in all_task_ids:
        sa = (scores_a.get(tid) or {}).get("score")
        sb = (scores_b.get(tid) or {}).get("score")
        if sa is not None and sb is not None:
            t = tasks_by_id.get(tid, {})
            qtype = t.get("metadata", {}).get("question_type", "?")
            question = t.get("input", "")[:50]
            if sb > sa:
                improved.append(
                    {
                        "id": tid,
                        "cat": qtype,
                        "a": sa,
                        "b": sb,
                        "q": question,
                    }
                )
            elif sb < sa:
                regressed.append(
                    {
                        "id": tid,
                        "cat": qtype,
                        "a": sa,
                        "b": sb,
                        "q": question,
                    }
                )

    if improved:
        push(f"## Where {cond_b} Improved ({len(improved)} tasks)")
        push("")
        push(f"| Task | Cat | {cond_a} | {cond_b} | Delta | Question |")
        push("|------|-----|---------|---------|-------|----------|")
        for r in improved:
            d = r["b"] - r["a"]
            push(f"| {r['id']} | {r['cat']} | {r['a']:.1f} | {r['b']:.1f} | +{d:.1f} | {r['q']} |")
        push("")

    if regressed:
        push(f"## Where {cond_a} Was Better ({len(regressed)} tasks)")
        push("")
        push(f"| Task | Cat | {cond_a} | {cond_b} | Delta | Question |")
        push("|------|-----|---------|---------|-------|----------|")
        for r in regressed:
            d = r["b"] - r["a"]
            push(f"| {r['id']} | {r['cat']} | {r['a']:.1f} | {r['b']:.1f} | {d:.1f} | {r['q']} |")
        push("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def run_comparison(dir_a: str, dir_b: str) -> int:
    """Compare two run directories. Prints to stdout and writes MD."""
    try:
        run_a = _load_run(dir_a)
        run_b = _load_run(dir_b)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    meta_a = run_a["run_metadata"]
    meta_b = run_b["run_metadata"]
    cond_a = meta_a.get("condition") or Path(dir_a).name
    cond_b = meta_b.get("condition") or Path(dir_b).name
    j_a = run_a["judgments"]
    j_b = run_b["judgments"]

    if not j_a or not j_b:
        print(
            "Error: both runs must have judgments for comparison.",
            file=sys.stderr,
        )
        return 1

    # Build task index from predictions (approximate, since we don't
    # have the original tasks file — use what's available in metadata)
    tasks_by_id: dict[str, dict[str, Any]] = {}
    for pred in run_a.get("predictions", []) + run_b.get("predictions", []):
        tid = pred.get("task_id", "")
        if tid not in tasks_by_id:
            meta = pred.get("metadata", {})
            tasks_by_id[tid] = {
                "id": tid,
                "input": "",
                "metadata": meta,
            }
    # Enrich from probes if available
    for probe in run_a.get("probes", []) + run_b.get("probes", []):
        tid = probe.get("task_id", "")
        if tid in tasks_by_id:
            tasks_by_id[tid]["input"] = probe.get("question", "")

    # Discover categories from judgments
    categories = sorted(
        {
            tasks_by_id.get(j["task_id"], {}).get("metadata", {}).get("question_type", "")
            for j in j_a + j_b
            if j.get("score") is not None
        }
        - {""}
    )

    # Console output
    print()
    print("=" * 60)
    print("         BENCHMARK COMPARISON")
    print(f"    {cond_a.upper()}  vs  {cond_b.upper()}")
    print("=" * 60)
    print()

    print("### Scores by Category (0-3 scale)")
    print()
    header = f"| {'Category':<30} | {cond_a:>8} | {cond_b:>8} | {'Delta':>6} |"
    print(header)
    print(f"|{'-' * 32}|{'-' * 10}|{'-' * 10}|{'-' * 8}|")

    oa = _mean_score(j_a)
    ob = _mean_score(j_b)
    print(f"| {'**Overall Mean**':<30} | {oa:>8} | {ob:>8} | {_fmt_delta(oa, ob):>6} |")
    for cat in categories:
        a = _mean_score(j_a, cat, tasks_by_id)
        b = _mean_score(j_b, cat, tasks_by_id)
        print(f"| {cat:<30} | {a:>8} | {b:>8} | {_fmt_delta(a, b):>6} |")

    # Score distribution
    dist_a = _score_dist(j_a)
    dist_b = _score_dist(j_b)
    print()
    print("### Score Distribution")
    print()
    print(f"| Score | {'Meaning':<20} | {cond_a:>8} | {cond_b:>8} |")
    print(f"|-------|{'-' * 22}|{'-' * 10}|{'-' * 10}|")
    labels = {
        "3": "Grounded correct",
        "2": "Generic correct",
        "1": "Abstained",
        "0": "Hallucinated",
    }
    for s in ("3", "2", "1", "0"):
        print(f"|   {s}   | {labels[s]:<20} | {dist_a[s]:>8} | {dist_b[s]:>8} |")
    print(f"| {'ERR':>5} | {'Error':<20} | {dist_a['err']:>8} | {dist_b['err']:>8} |")

    # Write comparison Markdown
    out_dir = Path(dir_b).parent
    md_path = _write_comparison_md(
        run_a,
        run_b,
        categories,
        tasks_by_id,
        out_dir / f"comparison-{cond_a}-vs-{cond_b}.md",
    )
    print(f"\nComparison report: {md_path}")

    return 0
