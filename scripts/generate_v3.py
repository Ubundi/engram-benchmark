"""
OpenClaw Memory Benchmark v3 — Main Pipeline Orchestrator

Runs the full generation pipeline (uses Claude Code CLI, no API key needed):
  Phase 1: Load entity seed → initialize registry
  Phase 2: Generate session corpus (300 sessions via Claude Code CLI)
  Phase 3: Generate questions (500 questions against corpus)
  Phase 4: Run validation
  Phase 5: Export to openclaw-memory-benchmark-v3.json
  Phase 6: Generate statistics report

Usage:
    python -m scripts.generate_v3
    python -m scripts.generate_v3 --skip-sessions  # Use cached sessions
    python -m scripts.generate_v3 --skip-questions  # Use cached questions
    python -m scripts.generate_v3 --validate-only   # Only run validation
    python -m scripts.generate_v3 --stats-only      # Only print stats
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

from scripts.config import (
    DIFFICULTY_TARGETS,
    ENTITY_SEED_PATH,
    QUESTION_TYPE_TARGETS,
    QUESTIONS_CACHE_DIR,
    SESSIONS_CACHE_DIR,
    TARGET_QUESTIONS,
    TARGET_SESSIONS,
    V2_BENCHMARK_PATH,
    V3_OUTPUT_PATH,
    VALIDATION,
)
from scripts.entity_registry import EntityRegistry
from scripts.question_generator import QuestionGenerator
from scripts.session_generator import SessionGenerator
from scripts.validate_v3 import BenchmarkValidator

logger = logging.getLogger(__name__)


def phase_1_init_registry() -> EntityRegistry:
    """Phase 1: Load entity seed and initialize registry."""
    logger.info("=" * 60)
    logger.info("PHASE 1: Initialize Entity Registry")
    logger.info("=" * 60)

    registry = EntityRegistry()
    registry.load_seed(ENTITY_SEED_PATH)

    summary = registry.summary()
    logger.info(f"Registry initialized:")
    logger.info(f"  Entities: {summary['total_entities']}")
    logger.info(f"  Facts: {summary['total_facts']}")
    logger.info(f"  Events: {summary['total_events']}")
    logger.info(f"  By type: {summary['entities_by_type']}")
    logger.info(f"  Knowledge updates: {summary['knowledge_updates']}")

    return registry


def phase_2_generate_sessions(
    registry: EntityRegistry,
    skip: bool = False,
) -> list[dict]:
    """Phase 2: Generate session corpus."""
    logger.info("=" * 60)
    logger.info("PHASE 2: Generate Session Corpus")
    logger.info("=" * 60)

    generator = SessionGenerator(registry)

    if skip:
        sessions = generator.load_cached_sessions()
        if sessions:
            logger.info(f"Loaded {len(sessions)} cached sessions (skipping generation)")
            return sessions
        logger.warning("No cached sessions found, generating from scratch")

    plan = generator.generate_session_plan()
    logger.info(f"Session plan: {len(plan)} sessions")

    # Show plan summary
    type_counts = {}
    week_counts = {}
    for spec in plan:
        stype = spec["session_type"]
        week = spec["week"]
        type_counts[stype] = type_counts.get(stype, 0) + 1
        week_counts[week] = week_counts.get(week, 0) + 1

    logger.info("Plan by type:")
    for stype, count in sorted(type_counts.items()):
        logger.info(f"  {stype}: {count}")

    logger.info("Plan by week:")
    for week, count in sorted(week_counts.items()):
        logger.info(f"  {week}: {count}")

    sessions = generator.generate_all(plan)
    logger.info(f"Generated {len(sessions)} sessions total")

    return sessions


def phase_3_generate_questions(
    registry: EntityRegistry,
    sessions: list[dict],
    skip: bool = False,
) -> list[dict]:
    """Phase 3: Generate questions against the corpus."""
    logger.info("=" * 60)
    logger.info("PHASE 3: Generate Questions")
    logger.info("=" * 60)

    generator = QuestionGenerator(registry, sessions)

    if skip:
        # Load cached questions
        all_questions = generator.load_v2_questions()
        for cache_file in sorted(QUESTIONS_CACHE_DIR.glob("*.json")):
            with open(cache_file) as f:
                cached = json.load(f)
            all_questions.extend(cached)

        if len(all_questions) > 0:
            logger.info(f"Loaded {len(all_questions)} cached questions")
            return all_questions
        logger.warning("No cached questions found, generating from scratch")

    questions = generator.generate_all()
    logger.info(f"Generated {len(questions)} questions total")

    return questions


def phase_4_validate(benchmark_path: Path) -> bool:
    """Phase 4: Run validation checks."""
    logger.info("=" * 60)
    logger.info("PHASE 4: Validation")
    logger.info("=" * 60)

    validator = BenchmarkValidator(benchmark_path)
    return validator.validate()


def phase_5_export(questions: list[dict], output_path: Path) -> None:
    """Phase 5: Export to final JSON file."""
    logger.info("=" * 60)
    logger.info("PHASE 5: Export")
    logger.info("=" * 60)

    # Sort questions by question_id for consistent output
    questions.sort(key=lambda q: q.get("question_id", ""))

    with open(output_path, "w") as f:
        json.dump(questions, f, indent=4, ensure_ascii=False)

    file_size = output_path.stat().st_size
    file_size_mb = file_size / (1024 * 1024)

    logger.info(f"Exported {len(questions)} questions to {output_path}")
    logger.info(f"File size: {file_size_mb:.1f} MB ({file_size:,} bytes)")

    # Check file size against targets
    if file_size_mb < VALIDATION["target_file_size_mb_min"]:
        logger.warning(
            f"File size {file_size_mb:.1f} MB is below target "
            f"({VALIDATION['target_file_size_mb_min']} MB)"
        )
    elif file_size_mb > VALIDATION["target_file_size_mb_max"]:
        logger.warning(
            f"File size {file_size_mb:.1f} MB is above target "
            f"({VALIDATION['target_file_size_mb_max']} MB)"
        )


def phase_6_statistics(questions: list[dict]) -> dict:
    """Phase 6: Generate and print statistics report."""
    logger.info("=" * 60)
    logger.info("PHASE 6: Statistics Report")
    logger.info("=" * 60)

    stats = {
        "total_questions": len(questions),
        "question_types": {},
        "difficulty": {},
        "agents": {},
        "sessions": {
            "total_unique": 0,
            "avg_messages_per_session": 0,
            "max_messages": 0,
            "min_messages": 0,
        },
        "memory_types": {},
        "date_range": {"earliest": "", "latest": ""},
    }

    # Question type distribution
    for q in questions:
        qtype = q.get("question_type", "unknown")
        stats["question_types"][qtype] = stats["question_types"].get(qtype, 0) + 1

    # Difficulty distribution
    for q in questions:
        diff = q.get("metadata", {}).get("difficulty", "unknown")
        stats["difficulty"][diff] = stats["difficulty"].get(diff, 0) + 1

    # Agent coverage
    for q in questions:
        for agent in q.get("metadata", {}).get("agents_involved", []):
            stats["agents"][agent] = stats["agents"].get(agent, 0) + 1

    # Memory types
    for q in questions:
        mtype = q.get("metadata", {}).get("memory_type", "unknown")
        stats["memory_types"][mtype] = stats["memory_types"].get(mtype, 0) + 1

    # Session statistics
    all_session_ids = set()
    all_msg_counts = []
    all_dates = []

    for q in questions:
        for sid in q.get("haystack_session_ids", []):
            all_session_ids.add(sid)
        for session in q.get("haystack_sessions", []):
            all_msg_counts.append(len(session))
        for hd in q.get("haystack_dates", []):
            all_dates.append(hd)

    stats["sessions"]["total_unique"] = len(all_session_ids)
    if all_msg_counts:
        stats["sessions"]["avg_messages_per_session"] = round(
            sum(all_msg_counts) / len(all_msg_counts), 1
        )
        stats["sessions"]["max_messages"] = max(all_msg_counts)
        stats["sessions"]["min_messages"] = min(all_msg_counts)

    if all_dates:
        sorted_dates = sorted(all_dates)
        stats["date_range"]["earliest"] = sorted_dates[0]
        stats["date_range"]["latest"] = sorted_dates[-1]

    # Weighted score
    weight_map = {"easy": 1, "medium": 2, "hard": 3}
    total_weighted = sum(
        weight_map.get(q.get("metadata", {}).get("difficulty", "medium"), 2)
        for q in questions
    )
    stats["weighted_total_points"] = total_weighted

    # Print report
    print("\n" + "=" * 70)
    print("OpenClaw Memory Benchmark v3 — Statistics")
    print("=" * 70)

    print(f"\nTotal questions: {stats['total_questions']}")
    print(f"Weighted total points: {stats['weighted_total_points']}")

    print(f"\nQuestion types ({len(stats['question_types'])} types):")
    for qtype, count in sorted(stats["question_types"].items(), key=lambda x: -x[1]):
        target = QUESTION_TYPE_TARGETS.get(qtype, "?")
        pct = count / stats["total_questions"] * 100
        print(f"  {qtype:30s}: {count:4d} ({pct:5.1f}%)  target: {target}")

    print(f"\nDifficulty:")
    for diff in ["easy", "medium", "hard"]:
        count = stats["difficulty"].get(diff, 0)
        target = DIFFICULTY_TARGETS.get(diff, "?")
        pct = count / stats["total_questions"] * 100
        print(f"  {diff:10s}: {count:4d} ({pct:5.1f}%)  target: {target}")

    print(f"\nAgent coverage ({len(stats['agents'])} agents):")
    for agent, count in sorted(stats["agents"].items(), key=lambda x: -x[1]):
        print(f"  {agent:15s}: appears in {count} questions")

    print(f"\nMemory types ({len(stats['memory_types'])} types):")
    for mtype, count in sorted(stats["memory_types"].items(), key=lambda x: -x[1])[:15]:
        print(f"  {mtype:25s}: {count}")
    if len(stats["memory_types"]) > 15:
        print(f"  ... and {len(stats['memory_types']) - 15} more")

    print(f"\nSession statistics:")
    print(f"  Unique sessions: {stats['sessions']['total_unique']}")
    print(f"  Avg messages/session: {stats['sessions']['avg_messages_per_session']}")
    print(f"  Min messages: {stats['sessions']['min_messages']}")
    print(f"  Max messages: {stats['sessions']['max_messages']}")

    print(f"\nDate range: {stats['date_range']['earliest']} → {stats['date_range']['latest']}")

    # LongMemEval comparison
    print(f"\nLongMemEval Comparison:")
    print(f"  Questions: {stats['total_questions']} (LongMemEval: 500) {'✓' if stats['total_questions'] >= 450 else '✗'}")
    print(f"  Avg msgs/session: {stats['sessions']['avg_messages_per_session']} (LongMemEval: 11.6) {'✓' if stats['sessions']['avg_messages_per_session'] >= 10 else '✗'}")
    print(f"  Question types: {len(stats['question_types'])} (LongMemEval: 5, ours: 8) ✓")

    print("=" * 70 + "\n")

    return stats


def main():
    """Main pipeline orchestrator."""
    parser = argparse.ArgumentParser(
        description="OpenClaw Memory Benchmark v3 Generation Pipeline"
    )
    parser.add_argument(
        "--skip-sessions", action="store_true",
        help="Skip session generation, use cached sessions",
    )
    parser.add_argument(
        "--skip-questions", action="store_true",
        help="Skip question generation, use cached questions",
    )
    parser.add_argument(
        "--validate-only", action="store_true",
        help="Only run validation on existing output",
    )
    parser.add_argument(
        "--stats-only", action="store_true",
        help="Only print statistics for existing output",
    )
    parser.add_argument(
        "--output", type=Path, default=V3_OUTPUT_PATH,
        help="Output file path",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Enable verbose logging",
    )
    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    start_time = time.time()

    print("\n" + "=" * 70)
    print("OpenClaw Memory Benchmark v3 — Generation Pipeline")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70 + "\n")

    # Handle validate-only and stats-only modes
    if args.validate_only:
        success = phase_4_validate(args.output)
        sys.exit(0 if success else 1)

    if args.stats_only:
        with open(args.output) as f:
            questions = json.load(f)
        phase_6_statistics(questions)
        sys.exit(0)

    # Full pipeline
    try:
        # Phase 1: Initialize registry
        registry = phase_1_init_registry()

        # Phase 2: Generate sessions
        sessions = phase_2_generate_sessions(registry, skip=args.skip_sessions)
        logger.info(f"Phase 2 complete: {len(sessions)} sessions")

        # Phase 3: Generate questions
        questions = phase_3_generate_questions(
            registry, sessions, skip=args.skip_questions
        )
        logger.info(f"Phase 3 complete: {len(questions)} questions")

        # Phase 5: Export (before validation, so we can validate the file)
        phase_5_export(questions, args.output)

        # Phase 4: Validate
        valid = phase_4_validate(args.output)

        # Phase 6: Statistics
        stats = phase_6_statistics(questions)

        elapsed = time.time() - start_time
        print(f"\nPipeline completed in {elapsed:.0f}s ({elapsed/60:.1f}m)")

        if not valid:
            print("\nWARNING: Validation checks did not all pass. Review the report above.")
            sys.exit(1)

        print("\nSUCCESS: Benchmark v3 generated and validated.")
        sys.exit(0)

    except KeyboardInterrupt:
        print("\n\nPipeline interrupted by user.")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
