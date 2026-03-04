"""
Session Generator — Generates the ~300-session corpus via Claude API.

Each session is a multi-turn conversation between user and assistant,
following the patterns established in the v2 benchmark but with higher
message counts (8-20 per session) and richer content.
"""

import json
import logging
import random
from datetime import datetime, timedelta
from typing import Optional

from scripts import llm_client
from scripts.config import (
    SESSION_TEMPLATES_PATH,
    SESSION_TYPE_DISTRIBUTION,
    SESSIONS_CACHE_DIR,
    WEEKLY_SESSION_TARGETS,
)
from scripts.entity_registry import EntityRegistry, Event, Fact

logger = logging.getLogger(__name__)

# Day names for date formatting
DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# Agent name mapping
AGENT_NAMES = {
    "main": "Echo",
    "engage_x": "engage-x",
    "contentway": "contentway",
    "trustalign": "TrustAlign",
    "worker": "Worker",
}

# Session type to agent mapping
SESSION_TYPE_AGENTS = {
    "heartbeat": "main",
    "design_planning": "main",
    "inbox_review": "main",
    "social_monitoring": "engage_x",
    "content_ideation": "contentway",
    "alignment_review": "trustalign",
    "tool_execution": "worker",
    "self_improvement": "main",
}


def format_date(dt: datetime) -> str:
    """Format datetime as 'YYYY/MM/DD (Day) HH:MM'."""
    day = DAY_NAMES[dt.weekday()]
    return f"{dt.strftime('%Y/%m/%d')} ({day}) {dt.strftime('%H:%M')}"


def format_session_id(session_type: str, agent: str, dt: datetime) -> str:
    """Generate a session ID like 'main_session_20260220' or 'heartbeat_20260220_0717'."""
    date_str = dt.strftime("%Y%m%d")
    time_str = dt.strftime("%H%M")

    if session_type == "heartbeat":
        return f"heartbeat_{date_str}_{time_str}"
    elif session_type == "alignment_review":
        return f"trustalign_daily_observer_{date_str}"
    elif session_type == "social_monitoring":
        return f"engage_x_session_{date_str}_{time_str}"
    elif session_type == "content_ideation":
        return f"contentway_session_{date_str}_{time_str}"
    elif session_type == "tool_execution":
        return f"worker_task_{date_str}_{time_str}"
    elif session_type == "inbox_review":
        return f"inbox_review_{date_str}"
    else:
        return f"main_session_{date_str}_{time_str}"


class SessionGenerator:
    """Generates sessions using Claude Code CLI with entity-aware context."""

    def __init__(self, registry: EntityRegistry):
        self.registry = registry
        self.templates = self._load_templates()
        self.generated_sessions: list[dict] = []

    def _load_templates(self) -> dict:
        """Load session templates."""
        with open(SESSION_TEMPLATES_PATH) as f:
            data = json.load(f)
        return data

    def _call_api(self, system_prompt: str, user_prompt: str) -> str:
        """Call Claude via CLI with retry logic."""
        return llm_client.call(system_prompt, user_prompt)

    def generate_session_plan(self) -> list[dict]:
        """
        Plan all sessions: assign types, agents, dates, and content domains.
        Returns a list of session specs to be generated.
        """
        plan = []
        session_counter = 0

        for week_key, week_config in WEEKLY_SESSION_TARGETS.items():
            start = datetime.strptime(week_config["start"], "%Y-%m-%d")
            end = datetime.strptime(week_config["end"], "%Y-%m-%d")
            count = week_config["count"]
            theme = week_config["theme"]

            # Distribute session types for this week
            type_counts = {}
            remaining = count
            for stype, fraction in SESSION_TYPE_DISTRIBUTION.items():
                c = max(1, round(count * fraction))
                type_counts[stype] = c
                remaining -= c
            # Distribute remainder to heartbeat (most common)
            if remaining > 0:
                type_counts["heartbeat"] += remaining
            elif remaining < 0:
                type_counts["heartbeat"] = max(1, type_counts["heartbeat"] + remaining)

            # Generate session specs for each type
            for stype, scount in type_counts.items():
                agent = SESSION_TYPE_AGENTS[stype]
                template_info = self.templates.get("session_types", {}).get(stype, {})
                msg_range = template_info.get("message_range", [8, 12])
                content_domains = template_info.get("content_domains", [])

                for i in range(scount):
                    # Random date within the week
                    days_in_week = (end - start).days
                    random_day = random.randint(0, days_in_week)
                    session_date = start + timedelta(days=random_day)

                    # Random time (vary by session type)
                    if stype == "heartbeat":
                        hour = random.choice([0, 4, 7, 8, 12, 13, 15, 17, 20, 23])
                        minute = random.randint(0, 59)
                    elif stype == "alignment_review":
                        hour = random.choice([18, 19, 20, 21, 22])
                        minute = random.randint(0, 59)
                    else:
                        hour = random.randint(8, 22)
                        minute = random.randint(0, 59)

                    session_dt = session_date.replace(hour=hour, minute=minute)
                    session_id = format_session_id(stype, agent, session_dt)

                    # Pick content domain
                    domain = random.choice(content_domains) if content_domains else "general"

                    plan.append({
                        "index": session_counter,
                        "session_id": session_id,
                        "session_type": stype,
                        "agent": agent,
                        "datetime": session_dt.isoformat(),
                        "formatted_date": format_date(session_dt),
                        "week": week_key,
                        "theme": theme,
                        "content_domain": domain,
                        "target_messages": random.randint(msg_range[0], msg_range[1]),
                    })
                    session_counter += 1

        # Sort by datetime
        plan.sort(key=lambda s: s["datetime"])

        logger.info(f"Session plan: {len(plan)} sessions across 4 weeks")
        return plan

    def _build_session_prompt(self, spec: dict, recent_context: list[dict]) -> tuple[str, str]:
        """Build system and user prompts for session generation."""
        session_type = spec["session_type"]
        agent = spec["agent"]
        agent_name = AGENT_NAMES.get(agent, agent)
        theme = spec["theme"]
        domain = spec["content_domain"]
        target_msgs = spec["target_messages"]
        session_date = spec["formatted_date"]
        week = spec["week"]

        # Get relevant entity context
        entity_context = self._get_entity_context(spec)

        # Get template arc
        template = self.templates.get("session_types", {}).get(session_type, {})
        arc_phases = template.get("arc", [])
        arc_description = "\n".join(
            f"  {i+1}. [{p['phase']}] ({p['role']})"
            for i, p in enumerate(arc_phases)
        )

        # Weekly theme context
        weekly_themes = self.templates.get("weekly_themes", {}).get(week, {})
        weekly_events = weekly_themes.get("key_events", [])

        # Recent session context (for continuity)
        recent_summary = ""
        if recent_context:
            recent_items = []
            for rc in recent_context[-5:]:
                recent_items.append(f"- [{rc.get('formatted_date', '')}] {rc.get('session_type', '')}: {rc.get('content_domain', '')}")
            recent_summary = "Recent sessions:\n" + "\n".join(recent_items)

        system_prompt = f"""You are generating realistic conversation transcripts for the OpenClaw Memory Benchmark v3.

CONTEXT:
- OpenClaw is a multi-agent AI assistant system used by Beacon Studio, an AI startup
- The founder is Alex. The main agent is Echo.
- Sub-agents: engage-x (social), contentway (content), trustalign (alignment), worker (tool execution)
- This is Week {week[-1]} theme: "{theme}"
- Date: {session_date}

ENTITY CONTEXT (facts to maintain consistency):
{entity_context}

{recent_summary}

RULES:
1. Generate a natural, realistic multi-turn conversation
2. Include specific facts, numbers, dates, names, and technical details
3. Every message must be either {{"role": "user", "content": "..."}} or {{"role": "assistant", "content": "..."}}
4. The agent for this session is {agent_name}
5. Include content relevant to an AI startup that moves fast
6. Use SAST (South African Standard Time) for timestamps
7. Reference real-seeming project names, metrics, and decisions
8. Maintain consistency with the entity context provided
9. DO NOT include any real personal information or credentials
10. Use the anonymized names: Alex (founder), Beacon Studio (company), Echo (main agent), CodexAI, MemorySync, etc.

RESPONSE FORMAT:
Return ONLY a valid JSON array of message objects. Each message has:
- "role": "user" or "assistant"
- "content": the message text (use markdown formatting as the agents do)

Generate exactly {target_msgs} messages."""

        user_prompt = f"""Generate a {session_type} session for the {agent_name} agent.

Session type: {session_type}
Content domain: {domain}
Weekly theme: {theme}
Target messages: {target_msgs}

Conversation arc to follow:
{arc_description}

Weekly events to potentially reference:
{chr(10).join(f'- {e}' for e in weekly_events)}

Generate the conversation now. Return ONLY the JSON array."""

        return system_prompt, user_prompt

    def _get_entity_context(self, spec: dict) -> str:
        """Build entity context string for the session prompt."""
        lines = []
        session_date = spec["datetime"][:10]

        # Get recent facts (within the last week)
        recent_facts = self.registry.get_facts_by_date_range(
            (datetime.strptime(session_date, "%Y-%m-%d") - timedelta(days=7)).strftime("%Y-%m-%d"),
            session_date,
        )

        if recent_facts:
            lines.append("Recent facts:")
            for fact in recent_facts[-15:]:  # Last 15 facts
                lines.append(f"  - {fact.entity}.{fact.field} = {fact.value} (as of {fact.date})")

        # Get key entity states
        key_entities = ["codexai", "memorysync", "circuit_breaker", "trustalign"]
        for entity in key_entities:
            entity_facts = self.registry.get_entity_facts(entity)
            if entity_facts:
                latest = max(entity_facts, key=lambda f: f.date)
                if latest.date <= session_date:
                    lines.append(f"  - {entity}: latest known state = {latest.field}: {latest.value}")

        # Knowledge updates that happened before this session
        updates = self.registry.get_knowledge_updates()
        relevant_updates = [u for u in updates if u.new_date <= session_date]
        if relevant_updates:
            lines.append("Recent changes:")
            for u in relevant_updates[-5:]:
                lines.append(f"  - {u.entity}.{u.field}: {u.old_value} -> {u.new_value} (on {u.new_date})")

        return "\n".join(lines) if lines else "No prior context (early session)."

    def _parse_session_response(self, response_text: str) -> list[dict]:
        """Parse the API response into a list of messages."""
        # Try to extract JSON from the response
        text = response_text.strip()

        # Handle markdown code blocks
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first and last lines (```json and ```)
            json_lines = []
            in_block = False
            for line in lines:
                if line.startswith("```") and not in_block:
                    in_block = True
                    continue
                elif line.startswith("```") and in_block:
                    break
                elif in_block:
                    json_lines.append(line)
            text = "\n".join(json_lines)

        try:
            messages = json.loads(text)
            if isinstance(messages, list):
                # Validate each message
                valid = []
                for msg in messages:
                    if isinstance(msg, dict) and "role" in msg and "content" in msg:
                        valid.append({
                            "role": msg["role"],
                            "content": msg["content"],
                            "has_answer": False,  # Will be annotated later
                        })
                return valid
        except json.JSONDecodeError:
            logger.warning("Failed to parse session response as JSON, attempting recovery")

        # Fallback: try to find JSON array in the text
        start_idx = text.find("[")
        end_idx = text.rfind("]")
        if start_idx >= 0 and end_idx > start_idx:
            try:
                messages = json.loads(text[start_idx:end_idx + 1])
                if isinstance(messages, list):
                    return [
                        {"role": m["role"], "content": m["content"], "has_answer": False}
                        for m in messages
                        if isinstance(m, dict) and "role" in m and "content" in m
                    ]
            except json.JSONDecodeError:
                pass

        logger.error("Could not parse session response")
        return []

    def _extract_and_register_facts(self, session: dict, messages: list[dict]) -> None:
        """Extract facts from generated messages and register them."""
        session_id = session["session_id"]
        agent = session["agent"]
        session_date = session["datetime"][:10]

        for i, msg in enumerate(messages):
            # Register basic facts about what happened in this session
            fact = Fact(
                entity=session.get("content_domain", "general"),
                field="discussed_in",
                value=session_id,
                date=session_date,
                session_id=session_id,
                agent=agent,
                message_index=i,
                role=msg["role"],
            )
            self.registry.register_fact(fact)

        # Register an event for the session itself
        session_dt = datetime.fromisoformat(session["datetime"])
        self.registry.register_event(Event(
            description=f"{session['session_type']} session: {session.get('content_domain', 'general')}",
            date=session_date,
            time=session_dt.strftime("%H:%M"),
            session_id=session_id,
            agent=agent,
            category=session["session_type"],
        ))

    def generate_session(self, spec: dict, recent_context: list[dict]) -> Optional[dict]:
        """Generate a single session."""
        system_prompt, user_prompt = self._build_session_prompt(spec, recent_context)

        try:
            response = self._call_api(system_prompt, user_prompt)
            messages = self._parse_session_response(response)

            if not messages:
                logger.warning(f"Empty session for {spec['session_id']}, retrying...")
                response = self._call_api(system_prompt, user_prompt)
                messages = self._parse_session_response(response)

            if not messages:
                logger.error(f"Failed to generate session {spec['session_id']}")
                return None

            session = {
                **spec,
                "messages": messages,
                "message_count": len(messages),
            }

            self._extract_and_register_facts(spec, messages)
            self.generated_sessions.append(session)

            logger.info(
                f"Generated session {spec['session_id']}: "
                f"{len(messages)} messages ({spec['session_type']}/{spec['agent']})"
            )
            return session

        except Exception as e:
            logger.error(f"Error generating session {spec['session_id']}: {e}")
            return None

    def generate_all(self, plan: Optional[list[dict]] = None) -> list[dict]:
        """Generate all sessions from the plan."""
        if plan is None:
            plan = self.generate_session_plan()

        SESSIONS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        sessions = []
        recent_context = []

        for i, spec in enumerate(plan):
            # Check cache
            cache_file = SESSIONS_CACHE_DIR / f"{spec['session_id']}.json"
            if cache_file.exists():
                with open(cache_file) as f:
                    session = json.load(f)
                sessions.append(session)
                recent_context.append(spec)
                logger.info(f"Loaded cached session {spec['session_id']} ({i+1}/{len(plan)})")
                continue

            session = self.generate_session(spec, recent_context)
            if session:
                sessions.append(session)
                recent_context.append(spec)

                # Cache the session
                with open(cache_file, "w") as f:
                    json.dump(session, f, indent=2)

            if (i + 1) % 10 == 0:
                logger.info(f"Progress: {i+1}/{len(plan)} sessions generated")

        logger.info(f"Total sessions generated: {len(sessions)}")
        return sessions

    def load_cached_sessions(self) -> list[dict]:
        """Load all cached sessions."""
        sessions = []
        if SESSIONS_CACHE_DIR.exists():
            for cache_file in sorted(SESSIONS_CACHE_DIR.glob("*.json")):
                with open(cache_file) as f:
                    sessions.append(json.load(f))
        return sessions
