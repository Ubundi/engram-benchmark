"""
Validator — 10 automated validation checks for the v3 benchmark.

Run standalone: python -m scripts.validate_v3 [path_to_benchmark.json]
"""

import json
import logging
import re
import sys
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

# ── Validation constants (inlined from removed scripts.config) ─────────────────
V3_OUTPUT_PATH = Path(__file__).parent.parent / "data" / "raw" / "engram-v3.json"
TARGET_QUESTIONS = 500

QUESTION_TYPE_TARGETS = {
    "temporal-reasoning": 80,
    "multi-session": 80,
    "knowledge-update": 55,
    "single-session-user": 45,
    "single-session-assistant": 35,
    "cross-agent-memory": 80,
    "multi-hop-reasoning": 70,
    "recurring-pattern": 55,
}

DIFFICULTY_TARGETS = {
    "easy": 100,
    "medium": 250,
    "hard": 150,
}

VALIDATION = {
    "min_messages_per_session": 4,
    "max_messages_per_session": 30,
    "min_answer_length": 20,
    "max_answer_length": 1000,
    "min_question_length": 15,
    "max_question_length": 500,
    "min_sessions_per_question": 1,
    "max_sessions_per_question": 10,
    "distribution_tolerance_pct": 15,
    "dedup_similarity_threshold": 0.85,
    "target_file_size_mb_min": 8,
    "target_file_size_mb_max": 18,
}

V2_QUESTION_IDS = [
    "oc_temporal_001", "oc_cross_agent_001", "oc_fact_recall_001",
    "oc_temporal_002", "oc_cross_agent_002", "oc_multi_hop_001",
    "oc_recurring_001", "oc_project_001", "oc_agent_hierarchy_001",
    "oc_debugging_001", "oc_values_001", "oc_integration_001",
    "oc_lesson_001", "oc_receipt_001", "oc_research_001",
    "oc_investment_001", "oc_skill_001", "oc_self_improvement_001",
    "oc_dashboard_001", "oc_posting_001", "oc_team_001",
    "oc_observability_001", "oc_brian_castle_001",
    "oc_monitoring_themes_001", "oc_claw_journal_001",
    "oc_codexai_launch_001", "oc_channel_error_001",
    "oc_work_paper_001", "oc_worker_model_001",
]

logger = logging.getLogger(__name__)


class ValidationResult:
    """Result of a single validation check."""

    def __init__(self, name: str):
        self.name = name
        self.passed = True
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.stats: dict = {}

    def error(self, msg: str) -> None:
        self.passed = False
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def __str__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        result = f"[{status}] {self.name}"
        for e in self.errors:
            result += f"\n  ERROR: {e}"
        for w in self.warnings:
            result += f"\n  WARN: {w}"
        return result


class BenchmarkValidator:
    """Runs all 10 validation checks on the benchmark."""

    REQUIRED_FIELDS = [
        "question_id", "question_type", "question", "answer",
        "question_date", "haystack_dates", "haystack_session_ids",
        "haystack_sessions", "answer_session_ids", "metadata",
    ]

    REQUIRED_METADATA_FIELDS = ["agents_involved", "memory_type", "difficulty"]

    VALID_QUESTION_TYPES = (
        set(QUESTION_TYPE_TARGETS.keys()) | {"fact-recall"}
    )

    VALID_DIFFICULTIES = {"easy", "medium", "hard"}

    # Patterns that might indicate leaked real data
    SENSITIVE_PATTERNS = [
        r"@gmail\.com",  # Real email domains (except known anonymized ones)
        r"@yahoo\.com",
        r"@hotmail\.com",
        r"sk-[a-zA-Z0-9]{20,}",  # API keys
        r"xoxb-[a-zA-Z0-9-]+",  # Slack tokens (real ones)
        r"ghp_[a-zA-Z0-9]+",  # GitHub PATs
        r"\b\d{3}-\d{2}-\d{4}\b",  # SSN-like patterns
    ]

    # Known safe patterns (anonymized)
    SAFE_PATTERNS = [
        "koser.mike@gmail.com",  # Known anonymized investor email
        "finance@umoya.ventures",  # Known anonymized finance email
    ]

    def __init__(self, benchmark_path: Path | None = None):
        self.path = benchmark_path or V3_OUTPUT_PATH
        self.data: list[dict] = []
        self.results: list[ValidationResult] = []

    def load(self) -> bool:
        """Load the benchmark file."""
        try:
            with open(self.path) as f:
                self.data = json.load(f)
            logger.info(f"Loaded {len(self.data)} questions from {self.path}")
            return True
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"Failed to load benchmark: {e}")
            return False

    def run_all(self) -> list[ValidationResult]:
        """Run all 10 validation checks."""
        if not self.load():
            r = ValidationResult("File Loading")
            r.error(f"Could not load {self.path}")
            return [r]

        checks = [
            self.check_schema,
            self.check_answer_grounding,
            self.check_session_consistency,
            self.check_cross_references,
            self.check_distributions,
            self.check_deduplication,
            self.check_lengths,
            self.check_date_consistency,
            self.check_entity_consistency,
            self.check_anonymization,
        ]

        self.results = []
        for check in checks:
            result = check()
            self.results.append(result)

        return self.results

    def check_schema(self) -> ValidationResult:
        """Check 1: Schema validation — all required fields present."""
        r = ValidationResult("1. Schema Validation")

        if not isinstance(self.data, list):
            r.error("Root element must be a JSON array")
            return r

        r.stats["total_questions"] = len(self.data)

        for i, q in enumerate(self.data):
            qid = q.get("question_id", f"index_{i}")

            # Check required top-level fields
            for field in self.REQUIRED_FIELDS:
                if field not in q:
                    r.error(f"{qid}: Missing required field '{field}'")

            # Check metadata fields
            metadata = q.get("metadata", {})
            for field in self.REQUIRED_METADATA_FIELDS:
                if field not in metadata:
                    r.error(f"{qid}: Missing metadata field '{field}'")

            # Check field types
            if not isinstance(q.get("haystack_sessions", []), list):
                r.error(f"{qid}: haystack_sessions must be an array")
            if not isinstance(q.get("haystack_dates", []), list):
                r.error(f"{qid}: haystack_dates must be an array")
            if not isinstance(q.get("haystack_session_ids", []), list):
                r.error(f"{qid}: haystack_session_ids must be an array")
            if not isinstance(q.get("answer_session_ids", []), list):
                r.error(f"{qid}: answer_session_ids must be an array")

            # Check question_type is valid
            qtype = q.get("question_type", "")
            if qtype not in self.VALID_QUESTION_TYPES:
                r.warn(f"{qid}: Unknown question_type '{qtype}'")

            # Check difficulty is valid
            difficulty = metadata.get("difficulty", "")
            if difficulty not in self.VALID_DIFFICULTIES:
                r.error(f"{qid}: Invalid difficulty '{difficulty}'")

            # Check message structure
            for si, session in enumerate(q.get("haystack_sessions", [])):
                if not isinstance(session, list):
                    r.error(f"{qid}: haystack_sessions[{si}] must be an array")
                    continue
                for mi, msg in enumerate(session):
                    if not isinstance(msg, dict):
                        r.error(f"{qid}: session[{si}][{mi}] must be an object")
                        continue
                    if "role" not in msg:
                        r.error(f"{qid}: session[{si}][{mi}] missing 'role'")
                    if "content" not in msg:
                        r.error(f"{qid}: session[{si}][{mi}] missing 'content'")
                    if "has_answer" not in msg:
                        r.error(f"{qid}: session[{si}][{mi}] missing 'has_answer'")

        return r

    def check_answer_grounding(self) -> ValidationResult:
        """Check 2: Every answer is supported by has_answer=true messages."""
        r = ValidationResult("2. Answer Grounding")
        ungrounded = 0

        for q in self.data:
            qid = q.get("question_id", "?")
            has_grounding = False

            for session in q.get("haystack_sessions", []):
                for msg in session:
                    if msg.get("has_answer", False):
                        has_grounding = True
                        break
                if has_grounding:
                    break

            if not has_grounding:
                ungrounded += 1
                r.error(f"{qid}: No message with has_answer=true")

        r.stats["ungrounded_count"] = ungrounded
        r.stats["grounded_pct"] = (
            (len(self.data) - ungrounded) / len(self.data) * 100
            if self.data else 0
        )
        return r

    def check_session_consistency(self) -> ValidationResult:
        """Check 3: No contradictions within a session (role alternation, non-empty)."""
        r = ValidationResult("3. Session Consistency")
        issues = 0

        for q in self.data:
            qid = q.get("question_id", "?")

            for si, session in enumerate(q.get("haystack_sessions", [])):
                if not session:
                    r.warn(f"{qid}: Empty session at index {si}")
                    issues += 1
                    continue

                for mi, msg in enumerate(session):
                    # Check non-empty content
                    if not msg.get("content", "").strip():
                        r.error(f"{qid}: Empty message at session[{si}][{mi}]")
                        issues += 1

                    # Check valid role
                    if msg.get("role") not in ("user", "assistant"):
                        r.error(f"{qid}: Invalid role '{msg.get('role')}' at session[{si}][{mi}]")
                        issues += 1

        r.stats["issues_found"] = issues
        return r

    def check_cross_references(self) -> ValidationResult:
        """Check 4: answer_session_ids is a subset of haystack_session_ids."""
        r = ValidationResult("4. Cross-Reference Integrity")
        violations = 0

        for q in self.data:
            qid = q.get("question_id", "?")
            haystack_ids = set(q.get("haystack_session_ids", []))
            answer_ids = set(q.get("answer_session_ids", []))

            orphaned = answer_ids - haystack_ids
            if orphaned:
                r.error(f"{qid}: answer_session_ids not in haystack: {orphaned}")
                violations += 1

            # Check haystack_dates count matches haystack_session_ids count
            dates = q.get("haystack_dates", [])
            session_ids = q.get("haystack_session_ids", [])
            if len(dates) != len(session_ids):
                r.warn(
                    f"{qid}: haystack_dates ({len(dates)}) != "
                    f"haystack_session_ids ({len(session_ids)})"
                )

            # Check haystack_sessions count matches
            sessions = q.get("haystack_sessions", [])
            if len(sessions) != len(session_ids):
                r.error(
                    f"{qid}: haystack_sessions ({len(sessions)}) != "
                    f"haystack_session_ids ({len(session_ids)})"
                )
                violations += 1

        r.stats["violations"] = violations
        return r

    def check_distributions(self) -> ValidationResult:
        """Check 5: Question types, difficulties, and agents match targets."""
        r = ValidationResult("5. Distribution Checks")

        # Question type distribution
        type_counts = Counter(q.get("question_type", "unknown") for q in self.data)
        r.stats["type_distribution"] = dict(type_counts)

        tolerance = VALIDATION["distribution_tolerance_pct"] / 100
        for qtype, target in QUESTION_TYPE_TARGETS.items():
            actual = type_counts.get(qtype, 0)
            min_ok = int(target * (1 - tolerance))
            max_ok = int(target * (1 + tolerance))
            if actual < min_ok or actual > max_ok:
                r.warn(
                    f"Type '{qtype}': {actual} questions "
                    f"(target: {target}, range: {min_ok}-{max_ok})"
                )

        # Difficulty distribution
        diff_counts = Counter(
            q.get("metadata", {}).get("difficulty", "unknown") for q in self.data
        )
        r.stats["difficulty_distribution"] = dict(diff_counts)

        for diff, target in DIFFICULTY_TARGETS.items():
            actual = diff_counts.get(diff, 0)
            min_ok = int(target * (1 - tolerance))
            max_ok = int(target * (1 + tolerance))
            if actual < min_ok or actual > max_ok:
                r.warn(
                    f"Difficulty '{diff}': {actual} questions "
                    f"(target: {target}, range: {min_ok}-{max_ok})"
                )

        # Agent coverage
        all_agents = set()
        for q in self.data:
            all_agents.update(q.get("metadata", {}).get("agents_involved", []))
        r.stats["agents_covered"] = sorted(all_agents)

        # Accept both underscore and hyphen forms of agent names
        normalized_agents = set()
        for a in all_agents:
            normalized_agents.add(a.replace("-", "_"))
            normalized_agents.add(a)
        expected_agents = {"main", "engage_x", "contentway", "trustalign", "worker"}
        missing = expected_agents - normalized_agents
        if missing:
            r.warn(f"Missing agent coverage: {missing}")

        # V2 preservation check
        v2_ids = set(V2_QUESTION_IDS)
        present_ids = set(q.get("question_id", "") for q in self.data)
        missing_v2 = v2_ids - present_ids
        if missing_v2:
            r.warn(f"Missing v2 questions: {missing_v2}")
        r.stats["v2_preserved"] = len(v2_ids - missing_v2)

        # Total count check
        if len(self.data) < TARGET_QUESTIONS * 0.9:
            r.error(f"Only {len(self.data)} questions (target: {TARGET_QUESTIONS})")
        elif len(self.data) < TARGET_QUESTIONS:
            r.warn(f"{len(self.data)} questions (target: {TARGET_QUESTIONS})")

        return r

    def check_deduplication(self) -> ValidationResult:
        """Check 6: No duplicate or near-duplicate questions."""
        r = ValidationResult("6. Deduplication")

        # Exact ID duplicates
        id_counts = Counter(q.get("question_id", "") for q in self.data)
        for qid, count in id_counts.items():
            if count > 1:
                r.error(f"Duplicate question_id: {qid} (appears {count} times)")

        # Near-duplicate questions (by text similarity)
        threshold = VALIDATION["dedup_similarity_threshold"]
        questions = [(q.get("question_id", ""), q.get("question", "")) for q in self.data]
        near_dupes = 0

        # Only check a sample for large datasets (O(n^2) is expensive)
        check_questions = questions if len(questions) <= 200 else questions[:200]

        for i in range(len(check_questions)):
            for j in range(i + 1, len(check_questions)):
                ratio = SequenceMatcher(
                    None,
                    check_questions[i][1].lower(),
                    check_questions[j][1].lower(),
                ).ratio()
                if ratio >= threshold:
                    near_dupes += 1
                    r.warn(
                        f"Near-duplicate: {check_questions[i][0]} <-> {check_questions[j][0]} "
                        f"(similarity: {ratio:.2f})"
                    )

        r.stats["exact_duplicates"] = sum(1 for c in id_counts.values() if c > 1)
        r.stats["near_duplicates"] = near_dupes
        return r

    def check_lengths(self) -> ValidationResult:
        """Check 7: Messages, answers, and questions within target ranges."""
        r = ValidationResult("7. Length Checks")
        v = VALIDATION

        msg_counts = []
        answer_lengths = []
        question_lengths = []

        for q in self.data:
            qid = q.get("question_id", "?")

            # Answer length
            answer = q.get("answer", "")
            answer_lengths.append(len(answer))
            if len(answer) < v["min_answer_length"]:
                r.warn(f"{qid}: Answer too short ({len(answer)} chars)")
            elif len(answer) > v["max_answer_length"]:
                r.warn(f"{qid}: Answer too long ({len(answer)} chars)")

            # Question length
            question = q.get("question", "")
            question_lengths.append(len(question))
            if len(question) < v["min_question_length"]:
                r.warn(f"{qid}: Question too short ({len(question)} chars)")
            elif len(question) > v["max_question_length"]:
                r.warn(f"{qid}: Question too long ({len(question)} chars)")

            # Session message counts
            for si, session in enumerate(q.get("haystack_sessions", [])):
                count = len(session)
                msg_counts.append(count)
                if count < v["min_messages_per_session"]:
                    r.warn(f"{qid}: Session {si} has only {count} messages")
                elif count > v["max_messages_per_session"]:
                    max_msg = v["max_messages_per_session"]
                    r.warn(f"{qid}: Session {si} has {count} messages (max: {max_msg})")

            # Session count per question
            session_count = len(q.get("haystack_sessions", []))
            if session_count > v["max_sessions_per_question"]:
                r.warn(f"{qid}: {session_count} sessions (max: {v['max_sessions_per_question']})")

        r.stats["avg_messages_per_session"] = (
            sum(msg_counts) / len(msg_counts) if msg_counts else 0
        )
        r.stats["avg_answer_length"] = (
            sum(answer_lengths) / len(answer_lengths) if answer_lengths else 0
        )
        r.stats["avg_question_length"] = (
            sum(question_lengths) / len(question_lengths) if question_lengths else 0
        )

        return r

    def check_date_consistency(self) -> ValidationResult:
        """Check 8: Dates are consistent and chronological."""
        r = ValidationResult("8. Date Consistency")
        issues = 0

        date_pattern = re.compile(r"\d{4}/\d{2}/\d{2}")

        for q in self.data:
            qid = q.get("question_id", "?")

            # Check question_date format
            qdate = q.get("question_date", "")
            if not date_pattern.search(qdate):
                r.error(f"{qid}: Invalid question_date format: '{qdate}'")
                issues += 1

            # Check haystack_dates format
            for hd in q.get("haystack_dates", []):
                if not date_pattern.search(hd):
                    r.error(f"{qid}: Invalid haystack_date format: '{hd}'")
                    issues += 1

            # Check haystack dates are before question date
            q_date_str = qdate[:10].replace("/", "-") if qdate else ""
            for hd in q.get("haystack_dates", []):
                h_date_str = hd[:10].replace("/", "-") if hd else ""
                if h_date_str and q_date_str and h_date_str > q_date_str:
                    r.warn(f"{qid}: Haystack date {hd} is after question date {qdate}")

        r.stats["date_issues"] = issues
        return r

    def check_entity_consistency(self) -> ValidationResult:
        """Check 9: Facts in answers exist in referenced sessions."""
        r = ValidationResult("9. Entity Consistency")

        # Check that key entity names in answers appear in at least one session
        entity_names = [
            "Alex", "Echo", "Beacon Studio", "CodexAI", "MemorySync",
            "Catalyst", "engage-x", "contentway", "trustalign", "worker",
            "TrustAlign",
        ]

        issues = 0
        for q in self.data:
            qid = q.get("question_id", "?")
            answer = q.get("answer", "")

            # Collect all text from haystack sessions
            session_text = ""
            for session in q.get("haystack_sessions", []):
                for msg in session:
                    session_text += msg.get("content", "") + " "

            # Check entity mentions in answer exist in sessions
            for entity in entity_names:
                if entity.lower() in answer.lower():
                    if entity.lower() not in session_text.lower():
                        r.warn(
                            f"{qid}: Answer mentions '{entity}' but not found in sessions"
                        )
                        issues += 1

        r.stats["entity_issues"] = issues
        return r

    def check_anonymization(self) -> ValidationResult:
        """Check 10: No real names/domains leaked."""
        r = ValidationResult("10. Anonymization Safety")
        leaks = 0

        all_text = json.dumps(self.data)

        for pattern in self.SENSITIVE_PATTERNS:
            matches = re.findall(pattern, all_text)
            # Filter out known safe patterns
            for match in matches:
                if any(safe in match for safe in self.SAFE_PATTERNS):
                    continue
                r.warn(f"Potential sensitive data: '{match}' (pattern: {pattern})")
                leaks += 1

        r.stats["potential_leaks"] = leaks
        return r

    def print_report(self) -> None:
        """Print a formatted validation report."""
        if not self.results:
            print("No results. Run validate() first.")
            return

        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)

        print("\n" + "=" * 70)
        print("OpenClaw Memory Benchmark v3 — Validation Report")
        print("=" * 70)
        print(f"\nFile: {self.path}")
        print(f"Questions: {len(self.data)}")
        print(f"\nChecks: {passed}/{total} passed\n")

        for result in self.results:
            print(str(result))
            if result.stats:
                for key, val in result.stats.items():
                    print(f"  STAT: {key} = {val}")
            print()

        # Overall statistics
        print("-" * 70)
        print("Summary Statistics:")

        total_q = len(self.data)
        if total_q > 0:
            type_dist = Counter(q.get("question_type", "?") for q in self.data)
            diff_dist = Counter(q.get("metadata", {}).get("difficulty", "?") for q in self.data)

            print(f"\n  Total questions: {total_q}")
            print("\n  Question types:")
            for qtype, count in sorted(type_dist.items()):
                pct = count / total_q * 100
                print(f"    {qtype}: {count} ({pct:.1f}%)")

            print("\n  Difficulty:")
            for diff, count in sorted(diff_dist.items()):
                pct = count / total_q * 100
                print(f"    {diff}: {count} ({pct:.1f}%)")

            # File size
            file_size_mb = self.path.stat().st_size / (1024 * 1024)
            print(f"\n  File size: {file_size_mb:.1f} MB")

            # Average messages per session
            all_msg_counts = []
            for q in self.data:
                for session in q.get("haystack_sessions", []):
                    all_msg_counts.append(len(session))
            if all_msg_counts:
                print(f"  Avg messages/session: {sum(all_msg_counts)/len(all_msg_counts):.1f}")

        print("\n" + "=" * 70)
        status = "ALL CHECKS PASSED" if passed == total else f"{total - passed} CHECK(S) FAILED"
        print(f"Result: {status}")
        print("=" * 70 + "\n")

    def validate(self) -> bool:
        """Run all checks and return whether all passed."""
        self.run_all()
        self.print_report()
        return all(r.passed for r in self.results)


def main():
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    path = Path(sys.argv[1]) if len(sys.argv) > 1 else V3_OUTPUT_PATH
    validator = BenchmarkValidator(path)

    success = validator.validate()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
