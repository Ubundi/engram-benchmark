# Phase 3 — Kwanda-Specific Task Sketches (DRAFT for review)

Goal: 10–15 probes that test memory categories Kwanda actually cares about: ops continuity, work-paper decisions, recurring user preferences, cross-system synthesis, customer context.

Each entry below is a sketch only. Before authoring full multi-turn seed conversations, please review and flag any scenarios that don't match how Kwanda actually operates (channel names, tool conventions, role names, decision style).

Format matches `engram-v3-test.json`: each task gets `question_id`, `question_type`, `question`, `answer`, `haystack_sessions` (multi-turn dialog seed). I'll author the seeds once you sign off on the scenarios.

---

## 1. ops-continuity-1 — Recurring task ownership

**Category:** Kwanda Ops task continuation
**Seed scenario:** Operator and agent discuss the weekly Monday "investor update prep" routine. Agent commits to drafting the update on Sunday evenings using the prior week's metrics from the Plane dashboard. Two follow-up sessions over 2 weeks reinforce the routine; in session 3, operator says "tweak one thing — pull GitHub commit volume too, not just Plane."
**Probe Q:** *"What does the agent do for the Monday investor update routine, and what's the latest tweak?"*
**Ground truth:** Drafts the update Sunday evenings using prior-week Plane metrics; latest tweak is to also include GitHub commit volume.

## 2. work-paper-decision-1 — Decision recall with reasoning

**Category:** Work paper decision capture
**Seed scenario:** Work-paper session about pricing. Operator and agent debate two pricing tiers (R500/mo entry vs R2000/mo agency). Decision: lead with R2000 agency tier, drop the entry tier, because feedback showed entry-tier prospects didn't convert and burned support time.
**Probe Q:** *"Which pricing tier did we decide to lead with for Kwanda, and why did we drop the other?"*
**Ground truth:** Lead with R2000/mo agency tier; dropped the R500/mo entry tier because entry-tier prospects didn't convert and consumed disproportionate support time.

## 3. slack-decision-1 — Slack channel decision capture

**Category:** Slack decision capture
**Seed scenario:** In a #kwanda-ops Slack thread, operator says "we agreed on the call yesterday — Cortex stays managed, no self-host option for v1, revisit Q3 if customer demand shows up." Agent acknowledges and saves it.
**Probe Q:** *"What did we decide about Cortex self-host on the ops call yesterday?"*
**Ground truth:** No self-host option in v1; managed-only. Revisit in Q3 if customer demand surfaces.

## 4. user-preference-1 — Recurring user style correction

**Category:** User correction / style preference
**Seed scenario:** First session, agent writes a 2-page summary of an investor meeting. User says "too long — give me 5 bullet points max, action items only, no preamble." Three sessions later (different topic), agent again writes a long summary; user corrects again with "remember: 5 bullets, action items, no preamble."
**Probe Q:** *"What summary format does the user prefer, and how strict are they about it?"*
**Ground truth:** 5 bullets max, action items only, no preamble. User has corrected this twice — strict preference.

## 5. cross-system-1 — GitHub + Plane + Slack synthesis

**Category:** Cross-system synthesis
**Seed scenario:** Bug investigation across three sources: a GitHub PR comment from engineer mentioning the regression was introduced in commit `abc123` on the cortex-api repo; a Plane ticket KWA-247 logged the customer-facing symptom; a Slack #incidents thread coordinated the fix with rollback at 22:30 SAST.
**Probe Q:** *"Walk me through the Cortex-API regression: what commit caused it, which Plane ticket tracked it, and how was the incident resolved?"*
**Ground truth:** Commit `abc123` on cortex-api caused the regression; Plane ticket KWA-247 tracked the customer symptom; resolved by rollback at 22:30 SAST coordinated in #incidents.

## 6. customer-context-1 — Customer-specific operating notes

**Category:** Customer/channel context
**Seed scenario:** Operator notes that customer "Tyrelife" prefers async written updates over calls, has two contacts (Georg as primary, Anna for finance), and that Anna is the one who actually approves invoices.
**Probe Q:** *"For Tyrelife, who handles invoice approvals and what's their preferred update channel?"*
**Ground truth:** Anna handles invoice approvals (Georg is primary contact for general comms); Tyrelife prefers async written updates over calls.

## 7. user-preference-2 — Tool/workflow preference

**Category:** User preference / recurring pattern
**Seed scenario:** Operator says "for any code review I send you, lead with the security concerns first, then performance, then style — and skip nits unless they actually matter." Two follow-up code reviews where operator reinforces this pattern.
**Probe Q:** *"What's the operator's preferred order and filter for code review feedback?"*
**Ground truth:** Security first, then performance, then style. Skip nits unless they actually matter.

## 8. recurring-decision-1 — Recurring policy

**Category:** Work paper / recurring decision
**Seed scenario:** Discussion about hiring policy: Kwanda hires only after 3+ months of revenue covering the role. Agent applies this in two later conversations (rejecting an early hire suggestion, approving a later one when criterion was met).
**Probe Q:** *"What's Kwanda's hiring trigger, and has it been applied to any specific role discussion?"*
**Ground truth:** Hire only after 3+ months of revenue covering the role. Applied to reject an early hire suggestion, then approve a later one when the criterion was met.

## 9. ops-continuity-2 — Ongoing project handoff

**Category:** Multi-session task handoff
**Seed scenario:** Session 1: agent and operator scope out the "Kwanda landing page redesign" — sections, copy, target launch by Friday. Session 2 (next day): operator asks "where are we on the landing page, what's left." Session 3 (3 days later): "we're launching tomorrow — final checklist."
**Probe Q:** *"What's the status of the Kwanda landing page redesign and what was the launch date?"*
**Ground truth:** Redesign was scoped with sections + copy and a Friday launch target; final checklist done day-of-launch.

## 10. exact-value-1 — Specific operational config

**Category:** Exact-value recall (Kwanda-flavored)
**Seed scenario:** Operator notes Kwanda's customer-facing API rate limit is 60 requests/minute per tenant, with a burst allowance of 100, and that the limit applies to all `/v1/*` routes except `/v1/health`. Mentioned twice in two sessions.
**Probe Q:** *"What's the rate limit on the Kwanda customer-facing API, including any burst or exceptions?"*
**Ground truth:** 60 req/min per tenant, burst allowance 100, applies to all `/v1/*` routes except `/v1/health`.

---

## Review questions for you

1. **Are these scenarios realistic for Kwanda?** Specifically: tool names (Plane, Slack channels, GitHub repos), customer names (Tyrelife — is that the right example or should it be a different real/fictional customer?), pricing numbers (R500 / R2000 — match your actual pricing?), policy specifics (3-month revenue rule for hiring — accurate?).
2. **Are 10 tasks enough?** Roadmap minimum is 10. We could go to 15 if you want more category coverage (I'd add: shadow-subject codex sync, cross-channel context bleed, agent self-correction recall).
3. **Anything missing from Kwanda's actual ops day-to-day** that would be a stronger probe than what's drafted?

Once you sign off, I'll author the full multi-turn seed conversations (each task = 2–4 sessions of 4–8 turns), validate the JSON against the engram-v3 schema, and run all three conditions (Cortex / Baseline / LCM, n=2 each) — about 20 hours of total compute spread over 2–3 days.
