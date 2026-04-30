"""Build Kwanda-specific Phase 3 benchmark dataset.

Outputs data/raw/kwanda-test.json in the same schema as engram-v3-test.json.
"""
from __future__ import annotations

import json
from pathlib import Path

OUT = Path("data/raw/kwanda-test.json")


def msg(role: str, content: str, has_answer: bool = False) -> dict:
    return {"role": role, "content": content, "has_answer": has_answer}


TASKS: list[dict] = []


def task(
    qid: str,
    qtype: str,
    question: str,
    answer: str,
    question_date: str,
    sessions: list[tuple[str, str, list[dict]]],
    answer_session_ids: list[str],
    memory_type: str = "ops_decision",
    difficulty: str = "medium",
    agents_involved: list[str] | None = None,
) -> None:
    TASKS.append(
        {
            "question_id": qid,
            "question_type": qtype,
            "question": question,
            "answer": answer,
            "question_date": question_date,
            "haystack_dates": [s[1] for s in sessions],
            "haystack_session_ids": [s[0] for s in sessions],
            "haystack_sessions": [s[2] for s in sessions],
            "answer_session_ids": answer_session_ids,
            "metadata": {
                "project": "Kwanda",
                "source_dataset": "kwanda-phase3.json",
                "oracle_style": "LongMemEval-like",
                "difficulty": difficulty,
                "memory_type": memory_type,
                "agents_involved": agents_involved or ["main"],
            },
        }
    )


# =============================================================================
# Task 1: Monday investor-update routine + tweak (recurring-pattern)
# =============================================================================
task(
    qid="kwanda_ops_continuity_001",
    qtype="recurring-pattern",
    question="What is the routine for the Monday investor update, and what was the most recent change to it?",
    answer=(
        "The agent drafts the Monday investor update on Sunday evenings using prior-week metrics "
        "from the Plane dashboard. The most recent change was to also include GitHub commit volume "
        "alongside the Plane metrics."
    ),
    question_date="2026/04/06 (Mon) 09:30",
    sessions=[
        (
            "k01",
            "2026/03/16 (Mon) 08:45",
            [
                msg("user", "I want to standardize the Monday investor update prep. Right now it's chaotic — different format every week."),
                msg("assistant", "Happy to take that on as a recurring routine. Suggest: I draft the update Sunday evening, you review Monday morning before the 10am send. What metrics should it include?"),
                msg("user", "Pull last week's data from the Plane dashboard — closed tickets, cycle time, the burn-down. Keep it short, one page max."),
                msg("assistant", "Got it. So the routine is: every Sunday evening I'll pull prior-week Plane metrics — closed tickets, cycle time, burn-down — and draft a one-page update. You review Monday before the 10am send. I'll set this up as a standing weekly task.", has_answer=True),
                msg("user", "Perfect. Start this Sunday."),
            ],
        ),
        (
            "k02",
            "2026/03/30 (Mon) 09:15",
            [
                msg("user", "The investor updates have been good. One tweak — I want you to pull GitHub commit volume too, not just Plane metrics. Investors keep asking about engineering pace and Plane tickets alone don't show it."),
                msg("assistant", "Makes sense — Plane shows planned work, GitHub commits show actual throughput. I'll add commit volume from the main repos to the Sunday-evening draft starting this week. Anything else, or just additive on top of the existing format?", has_answer=True),
                msg("user", "Just additive. Don't change the rest."),
                msg("assistant", "Confirmed. Sunday evening drafts now include prior-week Plane metrics plus GitHub commit volume. Same one-page format, same Monday review window."),
            ],
        ),
    ],
    answer_session_ids=["k01", "k02"],
    memory_type="recurring_routine",
    difficulty="medium",
)


# =============================================================================
# Task 2: Pricing decision with reasoning (single-session-assistant)
# =============================================================================
task(
    qid="kwanda_work_paper_decision_001",
    qtype="single-session-assistant",
    question="Which Kwanda pricing tier did we decide to lead with, and why was the other tier dropped?",
    answer=(
        "We decided to lead with the R2000/month agency tier and drop the R500/month entry tier. "
        "The reason was that entry-tier prospects didn't convert and consumed disproportionate "
        "support time relative to their revenue."
    ),
    question_date="2026/04/12 (Sun) 14:20",
    sessions=[
        (
            "k03",
            "2026/04/03 (Fri) 16:00",
            [
                msg("user", "Pricing work paper. We have two tiers in market: R500/mo entry and R2000/mo agency. I'm thinking we should consolidate."),
                msg("assistant", "What's the data showing? Conversion rate, support load, revenue mix?"),
                msg("user", "Entry tier: 40 prospects in the funnel, 3 converted in 6 months, average ticket volume per converted user is 3x the agency tier. Agency tier: 12 prospects, 8 converted, low support load."),
                msg("assistant", "That's a clear signal — entry-tier prospects don't convert and the ones who do consume disproportionate support time. The economics on the R500 tier are net-negative once you factor in support cost. The recommendation is to drop the entry tier and lead with the R2000 agency tier. You stop paying support costs on a tier that doesn't generate matching revenue, and your sales motion becomes one focused conversation instead of two."),
                msg("user", "Agreed. So the decision is: lead with R2000/mo agency tier, drop R500/mo entry tier, reason is no conversion and disproportionate support cost. Capture that."),
                msg("assistant", "Captured: lead with R2000/month agency tier; drop the R500/month entry tier. Reason: entry-tier prospects didn't convert and consumed disproportionate support time relative to revenue. Effective immediately for new conversations; existing entry-tier customers stay on for now.", has_answer=True),
            ],
        ),
    ],
    answer_session_ids=["k03"],
    memory_type="pricing_decision",
    difficulty="medium",
)


# =============================================================================
# Task 3: Slack #kwanda-ops decision capture (single-session-assistant)
# =============================================================================
task(
    qid="kwanda_slack_decision_001",
    qtype="single-session-assistant",
    question="What did we decide about Cortex self-host on the ops call, and what's the trigger to revisit?",
    answer=(
        "We decided not to offer a self-host option for Cortex in v1 — managed-only. "
        "We will revisit in Q3 if customer demand for self-host surfaces."
    ),
    question_date="2026/04/15 (Wed) 10:00",
    sessions=[
        (
            "k04",
            "2026/04/08 (Wed) 17:30",
            [
                msg("user", "Captured from #kwanda-ops Slack thread today: 'we agreed on the call yesterday — Cortex stays managed, no self-host option for v1, revisit Q3 if customer demand shows up. Reasoning: support burden + we'd need to harden the deploy story which is not v1 scope.' Save that as a decision."),
                msg("assistant", "Saving the decision: Cortex v1 is managed-only, no self-host option. The reasoning is support burden plus the deploy hardening work that's out of scope for v1. The revisit trigger is Q3 if customer demand for self-host surfaces. Anything to add?", has_answer=True),
                msg("user", "That's it. The Slack thread is the source of truth, link is in #kwanda-ops."),
                msg("assistant", "Got it — Slack thread in #kwanda-ops is the canonical reference. Decision recorded: Cortex managed-only in v1, revisit in Q3 contingent on customer demand."),
            ],
        ),
    ],
    answer_session_ids=["k04"],
    memory_type="product_decision",
    difficulty="easy",
)


# =============================================================================
# Task 4: Recurring user preference - summary format (recurring-pattern)
# =============================================================================
task(
    qid="kwanda_user_preference_001",
    qtype="recurring-pattern",
    question="What summary format does the user prefer for meeting notes, and how strict are they about it?",
    answer=(
        "The user prefers a 5-bullet maximum format with action items only and no preamble. "
        "They have corrected the agent on this preference at least twice — it is a strict, repeated preference."
    ),
    question_date="2026/04/20 (Mon) 11:00",
    sessions=[
        (
            "k05",
            "2026/03/25 (Wed) 15:00",
            [
                msg("user", "Summarize the investor meeting we just had with Norrsken."),
                msg("assistant", "Today's meeting with Norrsken covered three main themes. First, we discussed Kwanda's traction over the past quarter, focusing on the R2000 agency tier and the conversion rates we've seen. The Norrsken team asked detailed questions about our retention numbers and unit economics. Second, the conversation moved to product roadmap, where we walked through the Cortex managed-memory direction and the differentiation argument. They were particularly interested in the codex/alignment angle and asked for follow-up materials. Third, we touched on team scaling — they pushed back on hiring before revenue covers the role, which aligns with our existing hiring policy. Action items from the call: send the retention deck by Friday, share the Cortex/codex roadmap memo, schedule a follow-up in two weeks."),
                msg("user", "Way too long. Cut it. I want 5 bullet points max, action items only, no preamble. Don't tell me 'today's meeting covered three themes' — just give me the action items."),
                msg("assistant", "Understood. Going forward: 5 bullets max, action items only, no preamble. Re-doing this one:\n- Send retention deck to Norrsken by Friday\n- Share Cortex/codex roadmap memo\n- Schedule follow-up in 2 weeks\n- Confirm hiring policy alignment\n- No further commitments made", has_answer=True),
                msg("user", "Better. Remember that for next time."),
            ],
        ),
        (
            "k06",
            "2026/04/14 (Tue) 16:30",
            [
                msg("user", "Summarize today's customer call with Tyrelife."),
                msg("assistant", "We had a good conversation with Tyrelife covering their renewal terms and a few feature requests. Anna joined for the finance portion to confirm invoice handling for the upcoming quarter. Georg led the product discussion and asked about Cortex memory features that would help their internal ops team. We also discussed support response times — they want clearer SLAs documented. Action items include sending updated SLAs by end of week, drafting a Cortex feature roadmap aligned to their ops use case, and confirming the renewal price."),
                msg("user", "Stop. I told you before — 5 bullets, action items only, no preamble. Why am I correcting this twice?"),
                msg("assistant", "You're right, my mistake. This is the second correction so I'll lock it in: format is 5 bullets max, action items only, no preamble. Always.\n- Send updated SLAs to Tyrelife by end of week\n- Draft Cortex feature roadmap for their ops use case\n- Confirm renewal pricing with Anna\n- Document support response time commitments\n- No new commitments outside of the above", has_answer=True),
                msg("user", "Yes. Stick to it."),
            ],
        ),
    ],
    answer_session_ids=["k05", "k06"],
    memory_type="user_preference",
    difficulty="medium",
)


# =============================================================================
# Task 5: Cross-system synthesis (multi-hop-reasoning)
# =============================================================================
task(
    qid="kwanda_cross_system_001",
    qtype="multi-hop-reasoning",
    question="Walk me through the Cortex-API regression incident: which commit caused it, which Plane ticket tracked the customer-facing symptom, and how was it resolved?",
    answer=(
        "The regression was introduced by commit `abc123def` on the cortex-api repo. "
        "Plane ticket KWA-247 tracked the customer-facing symptom. "
        "The incident was resolved by rolling back the deploy at 22:30 SAST, coordinated in the #incidents Slack channel."
    ),
    question_date="2026/04/22 (Wed) 09:00",
    sessions=[
        (
            "k07",
            "2026/04/18 (Sat) 21:45",
            [
                msg("user", "We have a customer escalation. Tyrelife's ops dashboard is throwing 500s on the recall endpoint. Plane ticket KWA-247 just got opened by support."),
                msg("assistant", "I'm pulling context. KWA-247 says the symptom is 500s on `/v1/recall` for tenant `tyrelife`, started about 30 minutes ago. Anything correlate on the engineering side?"),
                msg("user", "Yes — Sipho just commented on PR #142 in the cortex-api repo, says the regression looks like it was introduced in commit abc123def from this morning's deploy. The change touched the recall pipeline."),
                msg("assistant", "Got it. So we have: Plane KWA-247 tracking the customer symptom on Tyrelife's recall endpoint, and commit `abc123def` on cortex-api as the suspected cause from this morning's deploy. We should escalate to #incidents now and trigger the rollback playbook before more tenants hit it.", has_answer=True),
                msg("user", "Doing that now."),
            ],
        ),
        (
            "k08",
            "2026/04/18 (Sat) 22:45",
            [
                msg("user", "Update on the incident — we resolved it. Rolled back the cortex-api deploy at 22:30 SAST, coordinated in #incidents. Sipho confirmed the recall endpoint is healthy on all tenants now."),
                msg("assistant", "Recording the resolution: cortex-api rollback executed at 22:30 SAST, coordinated in #incidents Slack channel. Recall endpoint healthy across all tenants post-rollback. KWA-247 can be marked resolved. The bad commit `abc123def` should be reverted on the main branch and a fix-forward PR opened — want me to track that as a follow-up?", has_answer=True),
                msg("user", "Yes track it as follow-up. Sipho will own the fix-forward."),
            ],
        ),
    ],
    answer_session_ids=["k07", "k08"],
    memory_type="incident_resolution",
    difficulty="hard",
)


# =============================================================================
# Task 6: Customer-specific operating notes (single-session-user)
# =============================================================================
task(
    qid="kwanda_customer_context_001",
    qtype="single-session-user",
    question="For the customer Tyrelife, who handles invoice approvals and what is their preferred channel for routine updates?",
    answer=(
        "For Tyrelife, Anna handles invoice approvals (Georg is the primary contact for general communication). "
        "Tyrelife prefers async written updates over calls."
    ),
    question_date="2026/04/16 (Thu) 13:30",
    sessions=[
        (
            "k09",
            "2026/04/02 (Thu) 11:00",
            [
                msg("user", "Operational notes on Tyrelife customer — capture these. Two contacts: Georg is the primary for product and general comms. Anna handles all finance, including invoice approval — she's the one who actually authorizes payment, not Georg. Don't send invoices through Georg, they'll just sit."),
                msg("assistant", "Captured: Tyrelife has two contacts. Georg is primary for product and general comms. Anna handles finance and authorizes invoice payments — invoices must go directly to Anna, not Georg. Anything else on their preferences?", has_answer=True),
                msg("user", "Yes — they prefer async written updates over calls. Don't propose calls unless they ask. Email or Slack DM is fine for routine stuff."),
                msg("assistant", "Added: Tyrelife prefers async written updates (email or Slack DM) over calls. Default to written for routine communication; only schedule calls if they explicitly request one. So the full picture: Georg primary for product/general, Anna for invoices and finance, and async-written as the preferred update channel.", has_answer=True),
                msg("user", "Right. Apply that going forward."),
            ],
        ),
    ],
    answer_session_ids=["k09"],
    memory_type="customer_context",
    difficulty="easy",
)


# =============================================================================
# Task 7: Code review style preference (recurring-pattern)
# =============================================================================
task(
    qid="kwanda_user_preference_002",
    qtype="recurring-pattern",
    question="What is the operator's preferred order for code review feedback, and what should be filtered out?",
    answer=(
        "The operator prefers code review feedback ordered as: security concerns first, then performance, then style. "
        "Nits should be skipped unless they actually matter."
    ),
    question_date="2026/04/19 (Sun) 17:00",
    sessions=[
        (
            "k10",
            "2026/04/05 (Sun) 14:30",
            [
                msg("user", "I'm going to start sending you code review tasks. Here's how I want them: lead with security concerns first, then performance, then style. And skip nits unless they actually matter — I don't need 'consider const vs let' notes."),
                msg("assistant", "Locked in: code review feedback ordered security → performance → style, with nits filtered out unless materially impactful. I'll apply this to every review you send.", has_answer=True),
                msg("user", "First one: review this PR for the recall pipeline rate limiter."),
                msg("assistant", "Reviewing.\n\nSecurity: the rate-limit key is constructed from `req.headers['x-tenant-id']` without validation — a malicious client can spoof another tenant's quota. Validate against the JWT-derived tenant ID instead.\n\nPerformance: the rate-limit check makes a Redis call on every request even for endpoints that don't need limiting (like `/v1/health`). Add a route allowlist to skip the check for known-safe endpoints.\n\nStyle: the timeout constant is hardcoded; lift it to config. (Not a nit — this affects ops ability to tune in production.)"),
                msg("user", "Good. That's the format."),
            ],
        ),
        (
            "k11",
            "2026/04/12 (Sun) 11:00",
            [
                msg("user", "Another review — PR #156 on cortex-api, the new auto-capture filter."),
                msg("assistant", "Reviewing PR #156 in security → performance → style order.\n\nSecurity: the filter accepts user-supplied patterns and compiles them as regex. Untrusted input compiled to regex is a ReDoS risk — wrap it in a timeout-bounded matcher or restrict to a safe regex subset.\n\nPerformance: the filter runs synchronously in the auto-capture hot path. Even at 1ms per check, this adds 30+ms to a 30-message capture. Move to async batching.\n\nStyle: function names are inconsistent (`shouldFilter` vs `is_excluded`). Pick one casing.\n\nNits skipped per your preference."),
                msg("user", "Good. Keep doing exactly this."),
            ],
        ),
    ],
    answer_session_ids=["k10", "k11"],
    memory_type="user_preference",
    difficulty="medium",
)


# =============================================================================
# Task 8: Hiring policy (knowledge-update)
# =============================================================================
task(
    qid="kwanda_recurring_decision_001",
    qtype="knowledge-update",
    question="What is Kwanda's hiring policy trigger, and how has it been applied in specific role discussions?",
    answer=(
        "Kwanda's policy is to hire only after 3+ months of revenue covering the role. "
        "The policy was applied to reject hiring a customer success lead in March (revenue criterion not met) "
        "and to approve hiring a backend engineer in April once the criterion was met."
    ),
    question_date="2026/04/25 (Fri) 10:00",
    sessions=[
        (
            "k12",
            "2026/02/20 (Fri) 09:30",
            [
                msg("user", "Setting our hiring policy formally. Rule: we hire only after 3+ months of revenue covering the role. Not three months of pipeline, not three months of contracted ARR — actual revenue collected for three months."),
                msg("assistant", "Recording: Kwanda's hiring trigger is 3+ months of *collected revenue* covering the role's fully-loaded cost, not pipeline or contracted ARR. I'll apply this whenever a hiring discussion comes up.", has_answer=True),
                msg("user", "Yes. Strict on this."),
            ],
        ),
        (
            "k13",
            "2026/03/12 (Thu) 14:00",
            [
                msg("user", "We're considering hiring a customer success lead. We have two enterprise customers signed and one almost-closed. Should we move?"),
                msg("assistant", "Applying the hiring policy: we need 3+ months of *collected* revenue covering the role's cost. Two signed customers and one almost-closed is contracted/pipeline, not collected revenue. The policy says no on this hire right now. Revisit once those contracts have generated three months of actual collections.", has_answer=True),
                msg("user", "Right call. Holding off."),
            ],
        ),
        (
            "k14",
            "2026/04/18 (Sat) 11:00",
            [
                msg("user", "Backend engineer hire — we've been at agency-tier MRR covering this role for over four months now. What's the policy say?"),
                msg("assistant", "The hiring policy is satisfied: 4+ months of collected revenue covering the role's fully-loaded cost exceeds the 3-month threshold. This hire is approved under the policy. Different from March's customer-success lead discussion where collected revenue wasn't there yet.", has_answer=True),
                msg("user", "Good. Moving forward with the hire."),
            ],
        ),
    ],
    answer_session_ids=["k12", "k13", "k14"],
    memory_type="company_policy",
    difficulty="hard",
)


# =============================================================================
# Task 9: Multi-session project handoff (multi-session)
# =============================================================================
task(
    qid="kwanda_ops_continuity_002",
    qtype="multi-session",
    question="What is the status of the Kwanda landing-page redesign and what was the launch date?",
    answer=(
        "The Kwanda landing-page redesign was scoped with sections and copy targeting a Friday launch. "
        "The launch date was Friday 2026-04-24. The final checklist was completed the day of launch."
    ),
    question_date="2026/04/27 (Mon) 09:00",
    sessions=[
        (
            "k15",
            "2026/04/19 (Sun) 16:00",
            [
                msg("user", "Scoping the Kwanda landing-page redesign. I want hero, three feature sections, social proof, pricing, FAQ, footer. Launch by Friday this week — the 24th."),
                msg("assistant", "Scoping: hero, three feature sections, social proof, pricing, FAQ, footer. Launch target Friday 2026-04-24. I'll draft copy for each section and have it back to you by Wednesday for review. Want me to also handle the pricing-tier copy reflecting the agency-tier-only decision from earlier this month?"),
                msg("user", "Yes, agency-tier only on the pricing section. Don't show the dropped entry tier."),
                msg("assistant", "Confirmed. Draft copy by Wednesday, agency-tier-only pricing, launch Friday 2026-04-24.", has_answer=True),
            ],
        ),
        (
            "k16",
            "2026/04/22 (Wed) 11:30",
            [
                msg("user", "Where are we on the landing page? What's left?"),
                msg("assistant", "Status: copy draft is complete for all six sections — hero, three features, social proof, pricing, FAQ, footer. Pricing reflects agency-tier-only as agreed. Sent it to you Tuesday evening. What's left: your review pass, any copy edits, then engineering handoff for the build. Friday launch still on track if review comes back today.", has_answer=True),
                msg("user", "Reviewing now. Will turn around tonight."),
            ],
        ),
        (
            "k17",
            "2026/04/24 (Fri) 09:00",
            [
                msg("user", "Launching today. Final checklist."),
                msg("assistant", "Launch checklist for the landing-page redesign, Friday 2026-04-24:\n- All six sections built and reviewed: ✓\n- Pricing shows agency-tier only: ✓\n- Social proof testimonials confirmed with customers: ✓\n- Mobile responsive verified: ✓\n- Analytics tracking installed: ✓\n- DNS/redirect from old page configured: ✓\n- Slack #launches announcement drafted: pending your sign-off\n\nReady to go live once you approve the announcement.", has_answer=True),
                msg("user", "Approved. Ship it."),
            ],
        ),
    ],
    answer_session_ids=["k15", "k16", "k17"],
    memory_type="project_milestone",
    difficulty="medium",
)


# =============================================================================
# Task 10: Exact-value config (fact-recall)
# =============================================================================
task(
    qid="kwanda_exact_value_001",
    qtype="fact-recall",
    question="What is the rate limit on the Kwanda customer-facing API, including any burst allowance and exceptions?",
    answer=(
        "Kwanda's customer-facing API rate limit is 60 requests per minute per tenant, "
        "with a burst allowance of 100, and the limit applies to all `/v1/*` routes except `/v1/health`."
    ),
    question_date="2026/04/26 (Sun) 14:00",
    sessions=[
        (
            "k18",
            "2026/04/10 (Fri) 15:30",
            [
                msg("user", "Setting the Kwanda customer API rate limit. We agreed: 60 requests per minute per tenant, with a burst allowance up to 100. Applies to all `/v1/*` routes except `/v1/health` which stays unlimited because uptime probes hammer it."),
                msg("assistant", "Recording the rate limit: 60 req/min per tenant, burst allowance 100, applied to all `/v1/*` routes with one exception — `/v1/health` is unlimited because uptime probes need it that way. I'll reference these exact numbers if anyone asks about the limits.", has_answer=True),
                msg("user", "Yes. These numbers are firm."),
            ],
        ),
        (
            "k19",
            "2026/04/22 (Wed) 17:00",
            [
                msg("user", "Tyrelife is asking about our API rate limits for their integration planning. What do we tell them?"),
                msg("assistant", "Pulling the limits from earlier — Kwanda customer API is 60 requests per minute per tenant, with a burst allowance of 100. Applies to all `/v1/*` routes except `/v1/health` which is unlimited for uptime probes. That's what we agreed on April 10th, those numbers are firm.", has_answer=True),
                msg("user", "Send those exact numbers to Anna and Georg."),
            ],
        ),
    ],
    answer_session_ids=["k18", "k19"],
    memory_type="api_config",
    difficulty="medium",
)


# =============================================================================
# Write
# =============================================================================
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(TASKS, indent=2, ensure_ascii=False))
print(f"Wrote {len(TASKS)} tasks to {OUT}")
print("\nCategory distribution:")
from collections import Counter
for cat, n in Counter(t["question_type"] for t in TASKS).most_common():
    print(f"  {cat}: {n}")
