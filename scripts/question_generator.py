"""
Question Generator — Generates 500 questions across 8 types.

Uses the entity registry and generated sessions to create grounded
questions with verified answers.
"""

import json
import logging
import random
import re
from datetime import datetime
from typing import Optional

from scripts import llm_client
from scripts.config import (
    DIFFICULTY_TARGETS,
    MEMORY_TYPES,
    QUESTION_DATE,
    QUESTION_ID_PREFIXES,
    QUESTION_TYPE_TARGETS,
    QUESTIONS_CACHE_DIR,
    V2_BENCHMARK_PATH,
    V2_QUESTION_IDS,
    V2_TO_V3_TYPE_MAP,
)
from scripts.entity_registry import EntityRegistry

logger = logging.getLogger(__name__)


class QuestionGenerator:
    """Generates benchmark questions against the session corpus."""

    def __init__(self, registry: EntityRegistry, sessions: list[dict]):
        self.registry = registry
        self.sessions = sessions
        self.session_index = {s["session_id"]: s for s in sessions}
        self.generated_questions: list[dict] = []
        self._question_counters: dict[str, int] = {}

    def _call_api(self, system_prompt: str, user_prompt: str) -> str:
        """Call Claude via CLI with retry logic."""
        return llm_client.call(system_prompt, user_prompt)

    def _next_question_id(self, question_type: str) -> str:
        """Generate the next question ID for a type."""
        prefix = QUESTION_ID_PREFIXES.get(question_type, "oc_misc")
        count = self._question_counters.get(question_type, 0) + 1
        self._question_counters[question_type] = count
        return f"{prefix}_{count:03d}"

    def _assign_difficulty(self, question_type: str, session_count: int, agent_count: int) -> str:
        """Heuristically assign difficulty based on question characteristics."""
        score = 0

        # More sessions = harder
        if session_count >= 4:
            score += 2
        elif session_count >= 2:
            score += 1

        # More agents = harder
        if agent_count >= 3:
            score += 2
        elif agent_count >= 2:
            score += 1

        # Some types are inherently harder
        hard_types = {"multi-hop-reasoning", "knowledge-update", "recurring-pattern"}
        medium_types = {"temporal-reasoning", "multi-session", "cross-agent-memory"}

        if question_type in hard_types:
            score += 1
        elif question_type in medium_types:
            score += 0.5

        if score >= 3:
            return "hard"
        elif score >= 1.5:
            return "medium"
        return "easy"

    def _select_memory_type(self, question_type: str, content_domain: str) -> str:
        """Select an appropriate memory type for the question."""
        type_to_memory = {
            "temporal-reasoning": ["temporal_ordering", "temporal_span", "staleness_detection"],
            "multi-session": ["structured_fact", "product_milestone", "operational_detail"],
            "knowledge-update": ["knowledge_update", "config_change", "decision_reversal", "metric_drift"],
            "single-session-user": ["task_detail", "integration_config", "skill_definition"],
            "single-session-assistant": ["structured_fact", "research_summary", "system_architecture"],
            "cross-agent-memory": ["cross_agent_fact", "evaluation_recall", "monitoring_summary"],
            "multi-hop-reasoning": ["multi_hop_entity", "financial_detail", "org_structure"],
            "recurring-pattern": ["system_pattern", "process_definition", "agent_evolution"],
        }
        options = type_to_memory.get(question_type, MEMORY_TYPES)
        return random.choice(options)

    def load_v2_questions(self) -> list[dict]:
        """Load existing v2 questions to preserve in v3."""
        with open(V2_BENCHMARK_PATH) as f:
            v2_data = json.load(f)

        preserved = []
        for q in v2_data:
            if q["question_id"] in V2_QUESTION_IDS:
                # Map v2 types to v3 types where needed
                original_type = q["question_type"]
                if original_type in V2_TO_V3_TYPE_MAP:
                    q["question_type"] = V2_TO_V3_TYPE_MAP.get(original_type, original_type)
                preserved.append(q)

        logger.info(f"Loaded {len(preserved)} v2 questions to preserve")
        return preserved

    def _build_question_prompt(
        self,
        question_type: str,
        target_sessions: list[dict],
        context_data: dict,
    ) -> tuple[str, str]:
        """Build prompts for generating a specific question type."""

        # Serialize target session messages for the prompt
        session_texts = []
        for s in target_sessions:
            msgs = s.get("messages", [])
            text = f"\n--- Session: {s['session_id']} ({s.get('formatted_date', '')}) [{s.get('agent', '')}] ---\n"
            for m in msgs:
                text += f"[{m['role']}]: {m['content']}\n\n"
            session_texts.append(text)

        sessions_context = "\n".join(session_texts)

        type_instructions = {
            "temporal-reasoning": """Generate a question about the ORDERING or TIMING of events.
The question should require understanding when things happened relative to each other.
Examples: "Which happened first: X or Y?", "How long after X did Y happen?", "What was the status of X on date Y?"
The answer must include specific dates/times from the sessions.""",

            "multi-session": """Generate a question that requires SYNTHESIZING information from MULTIPLE sessions.
The answer cannot be found in any single session alone - it requires combining facts across sessions.
Examples: "What was the progression of X across these dates?", "How did the team's approach to X evolve?"
Reference at least 2-3 sessions in the answer.""",

            "knowledge-update": """Generate a question about a FACT THAT CHANGED over time.
The question should test whether the system knows the MOST RECENT value vs an older one.
Examples: "What is the current status of X?" (when it changed), "How has X changed since Y?"
The answer should mention both old and new values with dates.""",

            "single-session-user": """Generate a question about a fact that was STATED BY THE USER in a single session.
The fact should be something the user instructed, requested, or provided as input.
Examples: "What did Alex ask Echo to do regarding X?", "What instruction was given about Y?"
The answer must come from a user message.""",

            "single-session-assistant": """Generate a question about a fact REPORTED BY THE ASSISTANT in a single session.
The fact should be a specific detail the assistant provided (not just echoing the user).
Examples: "What did Echo report about X?", "What configuration was set up for Y?"
The answer must come from an assistant message.""",

            "cross-agent-memory": """Generate a question about information from a SUB-AGENT session, asked from the main agent's perspective.
The question should test whether the main agent can recall what a sub-agent did or reported.
Examples: "What did TrustAlign score for X?", "What did engage-x find during monitoring?"
The answer should reference the sub-agent's specific output.""",

            "multi-hop-reasoning": """Generate a question that requires CHAINING 2-4 facts across sessions via entity links.
The answer requires connecting: person -> company, project -> metric -> date, etc.
Examples: "Person A works at company B. What project did company B invest in?"
Each hop should be grounded in a different session or message.""",

            "recurring-pattern": """Generate a question about a SYSTEM BEHAVIOR or PATTERN that recurs.
Examples: circuit breaker logic, heartbeat patterns, retry policies, workflow contracts.
The answer should describe the pattern/mechanism with specific parameters.""",
        }

        system_prompt = f"""You are generating benchmark questions for the OpenClaw Memory Benchmark v3.

Your task: Generate ONE high-quality question of type "{question_type}" based on the provided session transcripts.

RULES:
1. The question must be answerable ONLY from the provided sessions
2. The answer must be specific, factual, and verifiable against the session content
3. Include specific numbers, dates, names, and technical details in the answer
4. The question should be natural — something a user would actually ask their AI assistant
5. Do NOT mention session IDs, message indices, or benchmark metadata in the question
6. The answer should be 1-4 sentences long
7. Use the OpenClaw anonymized names (Alex, Beacon Studio, Echo, CodexAI, etc.)

TYPE-SPECIFIC INSTRUCTIONS:
{type_instructions.get(question_type, "Generate a factual question.")}

ADDITIONAL CONTEXT:
{json.dumps(context_data, indent=2) if context_data else "None"}

RESPONSE FORMAT:
Return a JSON object with exactly these fields:
{{
  "question": "The benchmark question",
  "answer": "The ground truth answer",
  "answer_message_indices": [list of [session_index, message_index] pairs that contain the answer]
}}"""

        user_prompt = f"""Here are the session transcripts to generate a question from:

{sessions_context}

Generate ONE {question_type} question now. Return ONLY the JSON object."""

        return system_prompt, user_prompt

    def _parse_question_response(self, response_text: str) -> Optional[dict]:
        """Parse the API response into a question dict."""
        text = response_text.strip()

        # Handle markdown code blocks
        if "```" in text:
            match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
            if match:
                text = match.group(1).strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON object
            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end > start:
                try:
                    return json.loads(text[start:end + 1])
                except json.JSONDecodeError:
                    pass

        logger.warning("Failed to parse question response")
        return None

    def _annotate_has_answer(
        self,
        sessions: list[dict],
        answer_indices: list[list[int]],
    ) -> tuple[list[list[dict]], list[str]]:
        """
        Annotate messages with has_answer=True based on answer indices.
        Returns (annotated_haystack_sessions, answer_session_ids).
        """
        haystack_sessions = []
        answer_session_ids = set()

        for si, session in enumerate(sessions):
            messages = []
            for mi, msg in enumerate(session.get("messages", [])):
                has_answer = False
                for idx_pair in answer_indices:
                    if len(idx_pair) == 2 and idx_pair[0] == si and idx_pair[1] == mi:
                        has_answer = True
                        answer_session_ids.add(session["session_id"])
                        break
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"],
                    "has_answer": has_answer,
                })
            haystack_sessions.append(messages)

        return haystack_sessions, sorted(answer_session_ids)

    def generate_questions_for_type(
        self,
        question_type: str,
        target_count: int,
    ) -> list[dict]:
        """Generate questions of a specific type."""
        questions = []

        # Strategy varies by question type
        if question_type == "temporal-reasoning":
            questions = self._generate_temporal_questions(target_count)
        elif question_type == "multi-session":
            questions = self._generate_multi_session_questions(target_count)
        elif question_type == "knowledge-update":
            questions = self._generate_knowledge_update_questions(target_count)
        elif question_type == "single-session-user":
            questions = self._generate_single_session_questions(target_count, role="user")
        elif question_type == "single-session-assistant":
            questions = self._generate_single_session_questions(target_count, role="assistant")
        elif question_type == "cross-agent-memory":
            questions = self._generate_cross_agent_questions(target_count)
        elif question_type == "multi-hop-reasoning":
            questions = self._generate_multi_hop_questions(target_count)
        elif question_type == "recurring-pattern":
            questions = self._generate_recurring_pattern_questions(target_count)

        logger.info(f"Generated {len(questions)} {question_type} questions (target: {target_count})")
        return questions

    def _select_sessions_for_question(
        self,
        count: int = 3,
        agent_filter: Optional[str] = None,
        date_range: Optional[tuple[str, str]] = None,
        session_type_filter: Optional[str] = None,
    ) -> list[dict]:
        """Select sessions for question generation with optional filters."""
        candidates = self.sessions

        if agent_filter:
            candidates = [s for s in candidates if s.get("agent") == agent_filter]
        if date_range:
            candidates = [
                s for s in candidates
                if date_range[0] <= s.get("datetime", "")[:10] <= date_range[1]
            ]
        if session_type_filter:
            candidates = [s for s in candidates if s.get("session_type") == session_type_filter]

        if len(candidates) < count:
            return candidates

        return random.sample(candidates, min(count, len(candidates)))

    def _generate_temporal_questions(self, count: int) -> list[dict]:
        """Generate temporal-reasoning questions."""
        questions = []

        for _ in range(count * 2):  # Generate extras, then filter
            if len(questions) >= count:
                break

            # Pick 2-4 sessions from different dates
            sessions = self._select_sessions_for_question(count=random.randint(2, 4))
            if len(sessions) < 2:
                continue

            context_data = {
                "dates_involved": [s.get("formatted_date", "") for s in sessions],
                "event_pairs": [(s.get("session_type", ""), s.get("content_domain", "")) for s in sessions],
            }

            q = self._generate_single_question("temporal-reasoning", sessions, context_data)
            if q:
                questions.append(q)

        return questions[:count]

    def _generate_multi_session_questions(self, count: int) -> list[dict]:
        """Generate multi-session questions."""
        questions = []

        # Find entities that appear in multiple sessions
        multi_entities = self.registry.get_multi_session_entities(min_sessions=2)

        for _ in range(count * 2):
            if len(questions) >= count:
                break

            sessions = self._select_sessions_for_question(count=random.randint(3, 5))
            if len(sessions) < 3:
                continue

            context_data = {}
            if multi_entities:
                entity, session_ids = random.choice(multi_entities)
                context_data["focus_entity"] = entity
                context_data["entity_sessions"] = session_ids

            q = self._generate_single_question("multi-session", sessions, context_data)
            if q:
                questions.append(q)

        return questions[:count]

    def _generate_knowledge_update_questions(self, count: int) -> list[dict]:
        """Generate knowledge-update questions using entity registry."""
        questions = []
        updates = self.registry.get_knowledge_updates()

        for _ in range(count * 2):
            if len(questions) >= count:
                break

            if updates:
                update = random.choice(updates)
                # Find sessions for old and new values
                old_sessions = [
                    s for s in self.sessions
                    if s["session_id"] == update.old_session_id
                    or s.get("datetime", "")[:10] == update.old_date
                ]
                new_sessions = [
                    s for s in self.sessions
                    if s["session_id"] == update.new_session_id
                    or s.get("datetime", "")[:10] == update.new_date
                ]
                sessions = (old_sessions[:2] + new_sessions[:2])
                if not sessions:
                    sessions = self._select_sessions_for_question(count=3)
            else:
                sessions = self._select_sessions_for_question(count=3)

            context_data = {}
            if updates:
                u = random.choice(updates)
                context_data["knowledge_update"] = {
                    "entity": u.entity,
                    "field": u.field,
                    "old_value": u.old_value,
                    "new_value": u.new_value,
                    "old_date": u.old_date,
                    "new_date": u.new_date,
                }

            q = self._generate_single_question("knowledge-update", sessions, context_data)
            if q:
                questions.append(q)

        return questions[:count]

    def _generate_single_session_questions(self, count: int, role: str) -> list[dict]:
        """Generate single-session questions for user or assistant facts."""
        questions = []
        qtype = f"single-session-{role}"

        for _ in range(count * 2):
            if len(questions) >= count:
                break

            session = random.choice(self.sessions)
            # Ensure session has messages from the target role
            has_role = any(m.get("role") == role for m in session.get("messages", []))
            if not has_role:
                continue

            context_data = {"target_role": role}
            q = self._generate_single_question(qtype, [session], context_data)
            if q:
                questions.append(q)

        return questions[:count]

    def _generate_cross_agent_questions(self, count: int) -> list[dict]:
        """Generate cross-agent-memory questions."""
        questions = []
        sub_agent_types = {"social_monitoring", "content_ideation", "alignment_review", "tool_execution"}

        for _ in range(count * 2):
            if len(questions) >= count:
                break

            # Pick a sub-agent session + a main session for context
            sub_sessions = [
                s for s in self.sessions
                if s.get("session_type") in sub_agent_types
            ]
            main_sessions = [s for s in self.sessions if s.get("agent") == "main"]

            if not sub_sessions:
                continue

            sub_session = random.choice(sub_sessions)
            main_context = random.choice(main_sessions) if main_sessions else None

            sessions = [sub_session]
            if main_context:
                sessions.append(main_context)

            context_data = {
                "sub_agent": sub_session.get("agent", ""),
                "perspective": "main agent asking about sub-agent activity",
            }

            q = self._generate_single_question("cross-agent-memory", sessions, context_data)
            if q:
                questions.append(q)

        return questions[:count]

    def _generate_multi_hop_questions(self, count: int) -> list[dict]:
        """Generate multi-hop reasoning questions."""
        questions = []
        chains = self.registry.get_multi_hop_chains(min_hops=2, max_hops=4)

        for _ in range(count * 2):
            if len(questions) >= count:
                break

            sessions = self._select_sessions_for_question(count=random.randint(3, 5))
            if len(sessions) < 2:
                continue

            context_data = {}
            if chains:
                chain = random.choice(chains)
                context_data["entity_chain"] = chain.entities
                context_data["chain_sessions"] = chain.session_ids

            q = self._generate_single_question("multi-hop-reasoning", sessions, context_data)
            if q:
                questions.append(q)

        return questions[:count]

    def _generate_recurring_pattern_questions(self, count: int) -> list[dict]:
        """Generate recurring-pattern questions."""
        questions = []
        patterns = self.registry.get_recurring_patterns()

        for _ in range(count * 2):
            if len(questions) >= count:
                break

            # Prefer sessions that show recurring behaviors
            heartbeat_sessions = [
                s for s in self.sessions
                if s.get("session_type") in {"heartbeat", "alignment_review", "self_improvement"}
            ]
            sessions = random.sample(
                heartbeat_sessions,
                min(random.randint(3, 5), len(heartbeat_sessions))
            ) if heartbeat_sessions else self._select_sessions_for_question(count=3)

            context_data = {}
            if patterns:
                pattern = random.choice(patterns)
                context_data["pattern"] = {
                    "entity": pattern["entity"],
                    "type": pattern["type"],
                    "occurrences": pattern.get("change_count", pattern.get("occurrence_count", 0)),
                }

            q = self._generate_single_question("recurring-pattern", sessions, context_data)
            if q:
                questions.append(q)

        return questions[:count]

    def _generate_single_question(
        self,
        question_type: str,
        sessions: list[dict],
        context_data: dict,
    ) -> Optional[dict]:
        """Generate a single question using the API."""
        system_prompt, user_prompt = self._build_question_prompt(
            question_type, sessions, context_data
        )

        try:
            response = self._call_api(system_prompt, user_prompt)
            parsed = self._parse_question_response(response)

            if not parsed or "question" not in parsed or "answer" not in parsed:
                return None

            # Get answer indices (default to marking last assistant message)
            answer_indices = parsed.get("answer_message_indices", [])
            if not answer_indices:
                # Default: mark the last assistant message in each session
                for si, s in enumerate(sessions):
                    for mi in range(len(s.get("messages", [])) - 1, -1, -1):
                        if s["messages"][mi].get("role") == "assistant":
                            answer_indices.append([si, mi])
                            break

            # Build haystack sessions with has_answer annotations
            haystack_sessions, answer_session_ids = self._annotate_has_answer(
                sessions, answer_indices
            )

            if not answer_session_ids:
                answer_session_ids = [s["session_id"] for s in sessions[:1]]

            # Determine agents involved
            agents = list(set(s.get("agent", "main") for s in sessions))

            # Assign difficulty
            difficulty = self._assign_difficulty(question_type, len(sessions), len(agents))

            # Select memory type
            memory_type = self._select_memory_type(
                question_type,
                sessions[0].get("content_domain", "general") if sessions else "general",
            )

            question_id = self._next_question_id(question_type)

            return {
                "question_id": question_id,
                "question_type": question_type,
                "question": parsed["question"],
                "answer": parsed["answer"],
                "question_date": QUESTION_DATE,
                "haystack_dates": [s.get("formatted_date", "") for s in sessions],
                "haystack_session_ids": [s["session_id"] for s in sessions],
                "haystack_sessions": haystack_sessions,
                "answer_session_ids": answer_session_ids,
                "metadata": {
                    "agents_involved": agents,
                    "memory_type": memory_type,
                    "difficulty": difficulty,
                },
            }

        except Exception as e:
            logger.error(f"Error generating {question_type} question: {e}")
            return None

    def generate_all(self) -> list[dict]:
        """Generate all 500 questions."""
        QUESTIONS_CACHE_DIR.mkdir(parents=True, exist_ok=True)

        # Start with preserved v2 questions
        all_questions = self.load_v2_questions()
        v2_count = len(all_questions)

        # Track how many we need per type (subtract v2 contributions)
        v2_type_counts: dict[str, int] = {}
        for q in all_questions:
            qtype = q["question_type"]
            v2_type_counts[qtype] = v2_type_counts.get(qtype, 0) + 1

        # Generate new questions per type
        for qtype, target in QUESTION_TYPE_TARGETS.items():
            existing = v2_type_counts.get(qtype, 0)
            needed = max(0, target - existing)

            if needed == 0:
                logger.info(f"Type {qtype}: already have {existing}/{target}")
                continue

            # Check cache
            cache_file = QUESTIONS_CACHE_DIR / f"{qtype}.json"
            if cache_file.exists():
                with open(cache_file) as f:
                    cached = json.load(f)
                all_questions.extend(cached)
                logger.info(f"Loaded {len(cached)} cached {qtype} questions")
                continue

            logger.info(f"Generating {needed} {qtype} questions...")
            new_questions = self.generate_questions_for_type(qtype, needed)

            # Cache
            with open(cache_file, "w") as f:
                json.dump(new_questions, f, indent=2)

            all_questions.extend(new_questions)

        # Balance difficulty distribution
        all_questions = self._balance_difficulty(all_questions)

        self.generated_questions = all_questions
        logger.info(
            f"Total questions: {len(all_questions)} "
            f"(v2 preserved: {v2_count}, new: {len(all_questions) - v2_count})"
        )
        return all_questions

    def _balance_difficulty(self, questions: list[dict]) -> list[dict]:
        """Adjust difficulty distribution to match targets."""
        diff_counts = {"easy": 0, "medium": 0, "hard": 0}
        for q in questions:
            d = q.get("metadata", {}).get("difficulty", "medium")
            diff_counts[d] = diff_counts.get(d, 0) + 1

        # Reassign difficulties to match target distribution
        total = len(questions)
        target_easy = int(total * 0.20)
        target_medium = int(total * 0.50)
        # hard gets the rest

        # Sort by a heuristic complexity score, then assign
        def complexity_score(q):
            score = 0
            score += len(q.get("haystack_session_ids", []))
            score += len(q.get("metadata", {}).get("agents_involved", []))
            if q.get("question_type") in {"multi-hop-reasoning", "knowledge-update"}:
                score += 2
            elif q.get("question_type") in {"temporal-reasoning", "multi-session"}:
                score += 1
            return score

        sorted_q = sorted(questions, key=complexity_score)

        for i, q in enumerate(sorted_q):
            if i < target_easy:
                q["metadata"]["difficulty"] = "easy"
            elif i < target_easy + target_medium:
                q["metadata"]["difficulty"] = "medium"
            else:
                q["metadata"]["difficulty"] = "hard"

        return sorted_q
