"""
Entity Registry — Fact consistency tracker for OpenClaw Memory Benchmark v3.

Tracks all entities, facts, and their changes across sessions to enable
structured question generation.
"""

import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from scripts.config import ENTITY_SEED_PATH

logger = logging.getLogger(__name__)


@dataclass
class Fact:
    """A single fact about an entity, with provenance."""
    entity: str
    field: str
    value: str
    date: str  # ISO format YYYY-MM-DD
    session_id: str
    agent: str
    message_index: int = 0  # Index within the session
    role: str = "assistant"  # Who stated the fact

    @property
    def date_obj(self) -> datetime:
        return datetime.strptime(self.date, "%Y-%m-%d")


@dataclass
class KnowledgeUpdate:
    """A fact that changed from old_value to new_value."""
    entity: str
    field: str
    old_value: str
    new_value: str
    old_date: str
    new_date: str
    old_session_id: str
    new_session_id: str
    old_agent: str
    new_agent: str


@dataclass
class Event:
    """A discrete event with a timestamp."""
    description: str
    date: str
    time: str  # HH:MM
    session_id: str
    agent: str
    entity: Optional[str] = None
    category: str = "general"  # general, milestone, error, decision, config_change


@dataclass
class MultiHopChain:
    """A chain of facts connected through entity links."""
    facts: list  # List of Fact objects
    entities: list  # Entity names forming the chain
    session_ids: list  # Session IDs involved
    description: str = ""


class EntityRegistry:
    """
    Core registry that tracks all entities, facts, events, and their changes.
    Provides query methods for question generators.
    """

    def __init__(self):
        self.facts: list[Fact] = []
        self.events: list[Event] = []
        self.entities: dict[str, dict] = {}  # entity_name -> {field: [Fact]}
        self._fact_index: dict[str, list[Fact]] = defaultdict(list)  # entity -> facts
        self._session_facts: dict[str, list[Fact]] = defaultdict(list)  # session_id -> facts
        self._agent_facts: dict[str, list[Fact]] = defaultdict(list)  # agent -> facts
        self._field_history: dict[str, list[Fact]] = defaultdict(list)  # "entity.field" -> facts sorted by date

    def load_seed(self, seed_path: Optional[Path] = None) -> None:
        """Load seed entities from entity_seed.json."""
        path = seed_path or ENTITY_SEED_PATH
        with open(path) as f:
            seed = json.load(f)

        # Register people
        for name, info in seed.get("people", {}).items():
            self.entities[name] = {"type": "person", **info}

        # Register companies
        for name, info in seed.get("companies", {}).items():
            self.entities[name] = {"type": "company", **info}

        # Register projects
        for name, info in seed.get("projects", {}).items():
            self.entities[name] = {"type": "project", **info}

        # Register agents
        for name, info in seed.get("agents", {}).items():
            self.entities[name] = {"type": "agent", **info}

        # Register configurations
        for name, info in seed.get("configurations", {}).items():
            self.entities[name] = {"type": "config", **info}

        # Load timeline events
        for evt in seed.get("timeline_events", []):
            self.events.append(Event(
                description=evt["event"],
                date=evt["date"],
                time="00:00",
                session_id="seed",
                agent="main",
                category="milestone",
            ))

        # Load knowledge update seeds as initial fact pairs
        for update_seed in seed.get("knowledge_update_seeds", []):
            entity = update_seed["entity"]
            field_name = update_seed["field"]
            for val_entry in update_seed["values"]:
                fact = Fact(
                    entity=entity,
                    field=field_name,
                    value=str(val_entry["value"]),
                    date=val_entry["date"],
                    session_id=f"seed_{val_entry['source'].replace(' ', '_')}",
                    agent="main",
                )
                self.register_fact(fact)

        logger.info(
            f"Loaded seed: {len(self.entities)} entities, "
            f"{len(self.facts)} facts, {len(self.events)} events"
        )

    def register_fact(self, fact: Fact) -> None:
        """Register a new fact with all indices."""
        self.facts.append(fact)
        self._fact_index[fact.entity].append(fact)
        self._session_facts[fact.session_id].append(fact)
        self._agent_facts[fact.agent].append(fact)

        key = f"{fact.entity}.{fact.field}"
        self._field_history[key].append(fact)
        self._field_history[key].sort(key=lambda f: f.date)

    def register_event(self, event: Event) -> None:
        """Register a discrete event."""
        self.events.append(event)
        self.events.sort(key=lambda e: (e.date, e.time))

    def get_entity_facts(self, entity: str) -> list[Fact]:
        """Get all facts about an entity."""
        return self._fact_index.get(entity, [])

    def get_session_facts(self, session_id: str) -> list[Fact]:
        """Get all facts from a specific session."""
        return self._session_facts.get(session_id, [])

    def get_agent_facts(self, agent: str) -> list[Fact]:
        """Get all facts from a specific agent."""
        return self._agent_facts.get(agent, [])

    # ── Query Methods for Question Generators ──────────────────────────────

    def get_temporal_pairs(self, min_gap_days: int = 0, max_gap_days: int = 30) -> list[tuple[Event, Event]]:
        """
        Get pairs of events that can be used for temporal reasoning questions.
        Returns pairs within the specified date gap range.
        """
        pairs = []
        sorted_events = sorted(self.events, key=lambda e: (e.date, e.time))

        for i in range(len(sorted_events)):
            for j in range(i + 1, len(sorted_events)):
                e1, e2 = sorted_events[i], sorted_events[j]
                d1 = datetime.strptime(e1.date, "%Y-%m-%d")
                d2 = datetime.strptime(e2.date, "%Y-%m-%d")
                gap = (d2 - d1).days

                if min_gap_days <= gap <= max_gap_days:
                    pairs.append((e1, e2))

        return pairs

    def get_knowledge_updates(self) -> list[KnowledgeUpdate]:
        """
        Find all cases where a fact about an entity changed over time.
        These are ideal for knowledge-update questions.
        """
        updates = []

        for key, facts in self._field_history.items():
            if len(facts) < 2:
                continue

            for i in range(len(facts) - 1):
                old_fact = facts[i]
                new_fact = facts[i + 1]

                if old_fact.value != new_fact.value:
                    updates.append(KnowledgeUpdate(
                        entity=old_fact.entity,
                        field=old_fact.field,
                        old_value=old_fact.value,
                        new_value=new_fact.value,
                        old_date=old_fact.date,
                        new_date=new_fact.date,
                        old_session_id=old_fact.session_id,
                        new_session_id=new_fact.session_id,
                        old_agent=old_fact.agent,
                        new_agent=new_fact.agent,
                    ))

        return updates

    def get_multi_hop_chains(self, min_hops: int = 2, max_hops: int = 4) -> list[MultiHopChain]:
        """
        Find chains of facts connected through shared entities.
        E.g., Person A -> Company B -> Project C -> Agent D.
        """
        chains = []

        # Build entity-to-entity links through shared facts/sessions
        entity_links: dict[str, set[str]] = defaultdict(set)

        for fact in self.facts:
            # Link entities that appear in the same session
            session_facts = self._session_facts[fact.session_id]
            entities_in_session = set(f.entity for f in session_facts)
            for e in entities_in_session:
                if e != fact.entity:
                    entity_links[fact.entity].add(e)

        # BFS to find chains of the right length
        visited_chains: set[str] = set()

        for start_entity in entity_links:
            self._find_chains(
                start_entity, [start_entity], entity_links,
                min_hops, max_hops, chains, visited_chains
            )

        return chains

    def _find_chains(
        self,
        current: str,
        path: list[str],
        links: dict[str, set[str]],
        min_hops: int,
        max_hops: int,
        result: list[MultiHopChain],
        visited: set[str],
    ) -> None:
        """Recursive helper for chain finding."""
        if len(path) >= min_hops + 1:
            chain_key = "->".join(sorted(path))
            if chain_key not in visited:
                visited.add(chain_key)

                # Collect facts and sessions for this chain
                chain_facts = []
                chain_sessions = set()
                for entity in path:
                    for fact in self._fact_index.get(entity, [])[:3]:
                        chain_facts.append(fact)
                        chain_sessions.add(fact.session_id)

                if chain_facts:
                    result.append(MultiHopChain(
                        facts=chain_facts,
                        entities=list(path),
                        session_ids=list(chain_sessions),
                    ))

        if len(path) >= max_hops + 1:
            return

        for neighbor in links.get(current, []):
            if neighbor not in path:
                self._find_chains(
                    neighbor, path + [neighbor], links,
                    min_hops, max_hops, result, visited
                )

    def get_cross_agent_facts(self) -> list[tuple[str, list[Fact]]]:
        """
        Find facts that originate from sub-agent sessions but would be
        queried from the main agent's perspective.
        """
        cross_agent = []
        sub_agents = {"engage_x", "contentway", "trustalign", "worker"}

        for agent in sub_agents:
            agent_facts = self._agent_facts.get(agent, [])
            if agent_facts:
                cross_agent.append((agent, agent_facts))

        return cross_agent

    def get_multi_session_entities(self, min_sessions: int = 3) -> list[tuple[str, list[str]]]:
        """
        Find entities that appear in multiple sessions.
        Returns (entity, [session_ids]) pairs.
        """
        entity_sessions: dict[str, set[str]] = defaultdict(set)

        for fact in self.facts:
            entity_sessions[fact.entity].add(fact.session_id)

        return [
            (entity, sorted(sessions))
            for entity, sessions in entity_sessions.items()
            if len(sessions) >= min_sessions
        ]

    def get_recurring_patterns(self) -> list[dict]:
        """
        Find system behaviors that recur across sessions.
        E.g., heartbeat patterns, circuit breaker states, retry policies.
        """
        patterns = []

        # Find entities with config type that have multiple state changes
        for entity_name, entity_info in self.entities.items():
            if entity_info.get("type") == "config":
                facts = self._fact_index.get(entity_name, [])
                if len(facts) >= 2:
                    patterns.append({
                        "entity": entity_name,
                        "type": "config_pattern",
                        "facts": facts,
                        "change_count": len(facts),
                    })

        # Find repeated events (same category, different dates)
        event_categories: dict[str, list[Event]] = defaultdict(list)
        for event in self.events:
            event_categories[event.category].append(event)

        for category, events in event_categories.items():
            if len(events) >= 3:
                patterns.append({
                    "entity": category,
                    "type": "recurring_event",
                    "events": events,
                    "occurrence_count": len(events),
                })

        return patterns

    def get_facts_by_date_range(self, start: str, end: str) -> list[Fact]:
        """Get all facts within a date range (inclusive)."""
        return [
            f for f in self.facts
            if start <= f.date <= end
        ]

    def get_facts_by_role(self, role: str) -> list[Fact]:
        """Get facts stated by a specific role (user or assistant)."""
        return [f for f in self.facts if f.role == role]

    def get_entity_timeline(self, entity: str) -> list[dict]:
        """Get chronological timeline of all facts/events for an entity."""
        timeline = []

        for fact in self._fact_index.get(entity, []):
            timeline.append({
                "type": "fact",
                "date": fact.date,
                "field": fact.field,
                "value": fact.value,
                "session_id": fact.session_id,
                "agent": fact.agent,
            })

        for event in self.events:
            if event.entity == entity:
                timeline.append({
                    "type": "event",
                    "date": event.date,
                    "time": event.time,
                    "description": event.description,
                    "session_id": event.session_id,
                })

        timeline.sort(key=lambda x: x["date"])
        return timeline

    def summary(self) -> dict:
        """Return a summary of the registry state."""
        return {
            "total_entities": len(self.entities),
            "total_facts": len(self.facts),
            "total_events": len(self.events),
            "entities_by_type": self._count_by_type(),
            "facts_by_agent": {
                agent: len(facts)
                for agent, facts in self._agent_facts.items()
            },
            "knowledge_updates": len(self.get_knowledge_updates()),
            "multi_session_entities": len(self.get_multi_session_entities()),
            "cross_agent_fact_groups": len(self.get_cross_agent_facts()),
        }

    def _count_by_type(self) -> dict[str, int]:
        counts: dict[str, int] = defaultdict(int)
        for info in self.entities.values():
            counts[info.get("type", "unknown")] += 1
        return dict(counts)

    def export_state(self) -> dict:
        """Export full registry state for debugging/caching."""
        return {
            "entities": self.entities,
            "facts": [
                {
                    "entity": f.entity, "field": f.field, "value": f.value,
                    "date": f.date, "session_id": f.session_id, "agent": f.agent,
                    "message_index": f.message_index, "role": f.role,
                }
                for f in self.facts
            ],
            "events": [
                {
                    "description": e.description, "date": e.date, "time": e.time,
                    "session_id": e.session_id, "agent": e.agent,
                    "entity": e.entity, "category": e.category,
                }
                for e in self.events
            ],
        }

    def import_state(self, state: dict) -> None:
        """Import registry state from exported data."""
        self.entities = state.get("entities", {})

        for fd in state.get("facts", []):
            self.register_fact(Fact(**fd))

        for ed in state.get("events", []):
            self.register_event(Event(**ed))

        logger.info(
            f"Imported state: {len(self.entities)} entities, "
            f"{len(self.facts)} facts, {len(self.events)} events"
        )
