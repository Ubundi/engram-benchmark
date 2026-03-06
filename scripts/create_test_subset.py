#!/usr/bin/env python3
"""
Create a ~50-question test subset of the v3 benchmark.

Maintains proportional representation of question types and difficulties.
Picks questions with the shortest haystack_sessions to keep file size small.

Usage:
    python3 scripts/create_test_subset.py
"""

import json
import random
from collections import defaultdict
from pathlib import Path

FULL_PATH = Path("data/raw/engram-v3.json")
TEST_PATH = Path("data/raw/engram-v3-test.json")
TARGET = 50
SEED = 42


def session_size(q: dict) -> int:
    """Total messages across all sessions — prefer smaller questions."""
    return sum(len(s) for s in q.get("haystack_sessions", []))


def main():
    random.seed(SEED)

    with open(FULL_PATH) as f:
        data = json.load(f)

    # Group by question_type
    by_type: dict[str, list] = defaultdict(list)
    for q in data:
        by_type[q["question_type"]].append(q)

    # Calculate proportional targets per type (minimum 2 each)
    total = len(data)
    targets = {}
    for qtype, questions in by_type.items():
        proportion = len(questions) / total
        targets[qtype] = max(2, round(proportion * TARGET))

    # Adjust to hit exactly TARGET
    while sum(targets.values()) > TARGET:
        # Reduce the type with the most allocated
        biggest = max(targets, key=lambda t: targets[t])
        targets[biggest] -= 1
    while sum(targets.values()) < TARGET:
        # Increase the type with the most remaining questions
        biggest = max(targets, key=lambda t: len(by_type[t]) - targets[t])
        targets[biggest] += 1

    # Select questions: pick smallest ones first for compact test file,
    # but ensure difficulty spread
    selected = []
    for qtype, target_count in targets.items():
        pool = by_type[qtype]

        # Group by difficulty
        by_diff = defaultdict(list)
        for q in pool:
            by_diff[q["metadata"]["difficulty"]].append(q)

        # Try to get at least 1 of each difficulty present in the pool
        picked = []
        for diff in ["easy", "medium", "hard"]:
            if by_diff[diff] and len(picked) < target_count:
                # Pick the smallest question of this difficulty
                by_diff[diff].sort(key=session_size)
                picked.append(by_diff[diff].pop(0))

        # Fill remaining slots from all difficulties, preferring small
        remaining = [q for qs in by_diff.values() for q in qs]
        remaining.sort(key=session_size)
        for q in remaining:
            if len(picked) >= target_count:
                break
            picked.append(q)

        selected.extend(picked)

    # Sort by question_id for stable output
    selected.sort(key=lambda q: q["question_id"])

    # Stats
    from collections import Counter
    type_counts = Counter(q["question_type"] for q in selected)
    diff_counts = Counter(q["metadata"]["difficulty"] for q in selected)

    print(f"Selected {len(selected)} questions from {len(data)} total\n")
    print("Type distribution:")
    for t, c in sorted(type_counts.items()):
        print(f"  {t}: {c}")
    print("\nDifficulty distribution:")
    for d, c in sorted(diff_counts.items()):
        print(f"  {d}: {c}")

    # File size estimate
    text = json.dumps(selected, indent=2, ensure_ascii=False)
    size_mb = len(text.encode()) / (1024 * 1024)
    print(f"\nOutput size: {size_mb:.1f} MB")

    with open(TEST_PATH, "w") as f:
        f.write(text)

    print(f"Saved to {TEST_PATH}")


if __name__ == "__main__":
    main()
