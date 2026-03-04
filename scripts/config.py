"""
Configuration for OpenClaw Memory Benchmark v3 generation pipeline.
"""

import os
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
ENTITY_SEED_PATH = TEMPLATES_DIR / "entity_seed.json"
SESSION_TEMPLATES_PATH = TEMPLATES_DIR / "session_templates.json"
V2_BENCHMARK_PATH = PROJECT_ROOT / "openclaw-memory-benchmark-v2.json"
V3_OUTPUT_PATH = PROJECT_ROOT / "openclaw-memory-benchmark-v3.json"
SESSIONS_CACHE_DIR = PROJECT_ROOT / "cache" / "sessions"
QUESTIONS_CACHE_DIR = PROJECT_ROOT / "cache" / "questions"

# ── CLI Configuration (uses Claude Code CLI with Max subscription) ────────────
CLI_MODEL = os.environ.get("CLI_MODEL", "sonnet")  # Model alias for claude CLI
CLI_TIMEOUT = int(os.environ.get("CLI_TIMEOUT", "120"))  # Seconds per call
CLI_MAX_BUDGET_PER_CALL = float(os.environ.get("CLI_MAX_BUDGET_PER_CALL", "0.50"))

# Rate limiting
API_REQUESTS_PER_MINUTE = 40
API_RETRY_MAX = 3
API_RETRY_BACKOFF = 2.0  # seconds, multiplied by attempt number

# ── Target Numbers ─────────────────────────────────────────────────────────────
TARGET_QUESTIONS = 500
TARGET_SESSIONS = 300
TARGET_AVG_MESSAGES_PER_SESSION = 11  # LongMemEval has 11.6

# ── Date Range ─────────────────────────────────────────────────────────────────
DATE_RANGE_START = "2026-02-19"
DATE_RANGE_END = "2026-03-18"
QUESTION_DATE = "2026/03/19 (Thu) 15:00"  # All questions asked from this date

# ── Session Distribution ───────────────────────────────────────────────────────
# Weekly targets (total ~300 sessions)
WEEKLY_SESSION_TARGETS = {
    "week_1": {"start": "2026-02-19", "end": "2026-02-25", "count": 75, "theme": "System setup & launch"},
    "week_2": {"start": "2026-02-26", "end": "2026-03-04", "count": 75, "theme": "Operational maturity"},
    "week_3": {"start": "2026-03-05", "end": "2026-03-11", "count": 80, "theme": "Rapid iteration"},
    "week_4": {"start": "2026-03-12", "end": "2026-03-18", "count": 70, "theme": "Course correction"},
}

# Session type distribution (fractions of total)
SESSION_TYPE_DISTRIBUTION = {
    "heartbeat":        0.25,  # ~75 sessions
    "design_planning":  0.12,  # ~36 sessions
    "inbox_review":     0.10,  # ~30 sessions
    "social_monitoring": 0.15, # ~45 sessions
    "content_ideation": 0.10,  # ~30 sessions
    "alignment_review": 0.12,  # ~36 sessions
    "tool_execution":   0.08,  # ~24 sessions
    "self_improvement": 0.08,  # ~24 sessions
}

# Agent distribution for sessions
AGENT_SESSION_WEIGHTS = {
    "main":       0.45,
    "engage_x":   0.18,
    "contentway": 0.10,
    "trustalign": 0.15,
    "worker":     0.12,
}

# ── Question Type Distribution ─────────────────────────────────────────────────
QUESTION_TYPE_TARGETS = {
    "temporal-reasoning":       80,
    "multi-session":            80,
    "knowledge-update":         55,
    "single-session-user":      45,
    "single-session-assistant": 35,
    "cross-agent-memory":       80,
    "multi-hop-reasoning":      70,
    "recurring-pattern":        55,
}

# ── Difficulty Distribution ────────────────────────────────────────────────────
DIFFICULTY_TARGETS = {
    "easy":   100,  # 20%
    "medium": 250,  # 50%
    "hard":   150,  # 30%
}

DIFFICULTY_WEIGHTS = {
    "easy":   1,
    "medium": 2,
    "hard":   3,
}

# ── Memory Types ───────────────────────────────────────────────────────────────
MEMORY_TYPES = [
    # Existing from v2 (24 types)
    "temporal_ordering",
    "temporal_span",
    "staleness_detection",
    "cross_agent_fact",
    "multi_hop_entity",
    "system_architecture",
    "structured_fact",
    "org_structure",
    "integration_config",
    "process_definition",
    "skill_definition",
    "task_detail",
    "product_milestone",
    "financial_detail",
    "market_research",
    "development_task",
    "research_summary",
    "evaluation_recall",
    "lesson_learned",
    "self_improvement",
    "error_correction",
    "monitoring_summary",
    "system_pattern",
    "operational_detail",
    "learning_extraction",
    # New for v3 (6 types)
    "knowledge_update",
    "config_change",
    "decision_reversal",
    "metric_drift",
    "strategy_shift",
    "agent_evolution",
]

# ── Question ID Prefixes ──────────────────────────────────────────────────────
QUESTION_ID_PREFIXES = {
    "temporal-reasoning":       "oc_temporal",
    "multi-session":            "oc_multi_session",
    "knowledge-update":         "oc_knowledge_update",
    "single-session-user":      "oc_single_user",
    "single-session-assistant": "oc_single_asst",
    "cross-agent-memory":       "oc_cross_agent",
    "multi-hop-reasoning":      "oc_multi_hop",
    "recurring-pattern":        "oc_recurring",
}

# ── Validation Thresholds ──────────────────────────────────────────────────────
VALIDATION = {
    "min_messages_per_session": 4,
    "max_messages_per_session": 30,
    "min_answer_length": 20,
    "max_answer_length": 1000,
    "min_question_length": 15,
    "max_question_length": 500,
    "min_sessions_per_question": 1,
    "max_sessions_per_question": 10,
    "distribution_tolerance_pct": 15,  # Allow 15% deviation from targets
    "dedup_similarity_threshold": 0.85,
    "target_file_size_mb_min": 8,
    "target_file_size_mb_max": 18,
}

# ── V2 Preservation ───────────────────────────────────────────────────────────
# Question IDs from v2 that must be preserved in v3
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

# V2 question types that are kept as-is in v3
# (v2 "fact-recall" is preserved — it maps to single-session-assistant for counting)
V2_TO_V3_TYPE_MAP = {
    "fact-recall": "fact-recall",  # Preserved as-is from v2
    "temporal-reasoning": "temporal-reasoning",
    "cross-agent-memory": "cross-agent-memory",
    "multi-hop-reasoning": "multi-hop-reasoning",
    "recurring-pattern": "recurring-pattern",
}

# ── Logging ────────────────────────────────────────────────────────────────────
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
VERBOSE = os.environ.get("VERBOSE", "0") == "1"
