#!/usr/bin/env python3
"""
Anonymize real-world entities in openclaw-memory-benchmark-v3.json.

Replaces real company names, people, handles, and emails with fictive equivalents.
Removes the oc_investment_001 question entirely (leaked real investor email).

Usage:
    python3 scripts/anonymize_dataset.py [--dry-run]

    --dry-run   Print what would change without modifying the file.
"""

import json
import re
import sys
from pathlib import Path

BENCHMARK_PATH = Path("data/raw/engram-v3.json")

# ---------------------------------------------------------------------------
# Replacement maps
# ---------------------------------------------------------------------------

# Questions to delete entirely (contain unsalvageable real data)
DELETE_QUESTION_IDS = {
    "oc_investment_001",  # Leaked real Inspire Commerce investor email
}

# Straight text replacements (applied globally via str.replace)
# Order matters: longer/more-specific strings first to avoid partial matches.
TEXT_REPLACEMENTS = [
    # --- HIGH SEVERITY: Inspire Commerce block (oc_investment_001 is deleted,
    #     but these catch any stray references elsewhere) ---
    ("Inspire Commerce", "Meridian Payments"),
    ("NavPass", "SkyRoute"),
    ("TransactCare", "CareTransact"),
    ("Value.IO", "PayGrid.io"),
    ("PointClickCare", "CarePointSys"),
    ("Mark Fischer", "David Muller"),
    ("The Real World", "The Digital Academy"),

    # --- HIGH SEVERITY: NeuraLink Labs ---
    ("neuralinklabs.com", "syntheticlabs.dev"),
    ("NeuraLink Labs", "Synthetic Labs"),
    ("NeuraLink", "Synthetic Labs"),
    ("Neuralink", "Synthetic Labs"),
    ("neuralink", "synthetic labs"),

    # --- HIGH SEVERITY: Real people's Twitter/X handles with fabricated quotes ---
    ("@karpathy_mirror", "@ml_pioneer_z"),
    ("@karpathy_dev", "@ml_pioneer_k"),
    ("@karpathy", "@ml_pioneer_k"),
    ("@swyx", "@devx_shawn"),
    ("@rauchg", "@webinfra_g"),
    ("@amasad", "@codeplatform_a"),
    ("@AnthropicEng", "@FoundationModelCo"),

    # --- HIGH SEVERITY: Real personal email ---
    ("koser.mike@gmail.com", "m.koser@umoya.ventures"),

    # --- MODERATE SEVERITY: Real VC / org references ---
    ("sequoiascout.com", "horizonscout.com"),
    ("Sequoia Scout", "Horizon Scout"),
    ("Sequoia", "Horizon"),

    ("Luma AI Ventures", "Lumina AI Ventures"),
    ("lumaaiventures.com", "luminaaiventures.com"),
    ("Luma AI", "Lumina AI"),

    # DeepMind as social credibility ("ex-DeepMind researcher", etc.)
    ("ex-DeepMind", "ex-NovaMind"),
    ("Ex-DeepMind", "Ex-NovaMind"),
    ("DeepMind", "NovaMind"),
    ("deepmind", "novamind"),

    # Stripe used as employer affiliation for fictive characters
    # Only replace "@ Stripe" / "at Stripe" patterns, not Stripe-the-product
    ("ML Infra @ Stripe", "ML Infra @ Nextera"),
    ("ML Infra at Stripe", "ML Infra at Nextera"),
    ("from Stripe", "from Nextera"),

    # Y Combinator
    ("Y Combinator", "Launchpad Accelerator"),
    ("YC Watchlist", "Launchpad Watchlist"),
]

# Regex replacements for patterns that need flexibility
REGEX_REPLACEMENTS = [
    # keiran.dlamini@neuralinklabs.com (already handled by text replacement above,
    # but catch any casing variants)
    (r"keiran\.dlamini@neuralinklabs\.com", "keiran.dlamini@syntheticlabs.dev"),
]


def load_benchmark(path: Path) -> list:
    with open(path) as f:
        return json.load(f)


def save_benchmark(path: Path, data: list) -> None:
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(data)} questions to {path}")


def apply_replacements(text: str, dry_run: bool = False) -> tuple:
    """Apply all text and regex replacements. Returns (new_text, changes)."""
    changes = []

    for old, new in TEXT_REPLACEMENTS:
        count = text.count(old)
        if count > 0:
            changes.append((old, new, count))
            if not dry_run:
                text = text.replace(old, new)

    for pattern, replacement in REGEX_REPLACEMENTS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            changes.append((pattern, replacement, len(matches)))
            if not dry_run:
                text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    return text, changes


def main():
    dry_run = "--dry-run" in sys.argv

    if not BENCHMARK_PATH.exists():
        print(f"Error: {BENCHMARK_PATH} not found")
        sys.exit(1)

    data = load_benchmark(BENCHMARK_PATH)
    original_count = len(data)
    print(f"Loaded {original_count} questions")

    # --- Step 1: Delete unsalvageable questions ---
    deleted = [q["question_id"] for q in data if q["question_id"] in DELETE_QUESTION_IDS]
    if deleted:
        print(f"\n--- Deleting {len(deleted)} question(s) with leaked real data ---")
        for qid in deleted:
            print(f"  DELETE {qid}")
        if not dry_run:
            data = [q for q in data if q["question_id"] not in DELETE_QUESTION_IDS]

    # --- Step 2: Apply text replacements ---
    # Serialize to string, replace, deserialize back
    text = json.dumps(data, ensure_ascii=False)
    text, changes = apply_replacements(text, dry_run=dry_run)

    if changes:
        print(f"\n--- Text replacements ({len(changes)} patterns matched) ---")
        for old, new, count in changes:
            print(f"  {count:>4}x  {old!r}  ->  {new!r}")

    if not dry_run:
        data = json.loads(text)

    # --- Step 3: Verify no remaining issues ---
    verify_text = json.dumps(data, ensure_ascii=False) if not dry_run else text
    remaining_issues = []
    check_terms = [
        "Inspire Commerce", "NavPass", "TransactCare", "PointClickCare",
        "Value.IO", "Mark Fischer", "The Real World",
        "NeuraLink", "neuralinklabs",
        "@karpathy", "@swyx", "@rauchg", "@amasad", "@AnthropicEng",
        "koser.mike@gmail.com",
        "Sequoia Scout", "sequoiascout",
        "DeepMind", "deepmind",
        "Luma AI Ventures", "lumaaiventures",
        "ML Infra @ Stripe", "ML Infra at Stripe",
    ]
    for term in check_terms:
        count = verify_text.count(term)
        if count > 0:
            remaining_issues.append((term, count))

    if remaining_issues:
        print(f"\n--- WARNING: {len(remaining_issues)} terms still present ---")
        for term, count in remaining_issues:
            print(f"  {count:>4}x  {term!r}")
    else:
        print("\n--- All targeted real-world entities replaced successfully ---")

    # --- Step 4: Save ---
    if not dry_run:
        save_benchmark(BENCHMARK_PATH, data)
        print(f"\nRemoved {original_count - len(data)} question(s), "
              f"applied {sum(c for _, _, c in changes)} text replacements")
    else:
        print(f"\n[DRY RUN] Would remove {len(deleted)} question(s), "
              f"apply {sum(c for _, _, c in changes)} text replacements")


if __name__ == "__main__":
    main()
