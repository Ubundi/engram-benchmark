"""Transform engram-v3-test.json user turns from imperative to conversational.

Converts actionable commands ("Run X", "Post Y", "Execute Z") into
past-tense/conversational questions so the agent processes information
without trying to execute real-world actions during benchmark seeding.

Strategy:
1. Manual mapping for complex compound sentences (highest quality)
2. Pattern-based transforms for common structural patterns
3. Leave already-safe turns untouched
"""

import json
import re
import copy
import sys
import hashlib


# ============================================================
# MANUAL MAPPINGS — for complex compound sentences where regex
# would produce awkward results. Keyed by MD5 hash prefix.
# ============================================================
MANUAL_MAP = {
    # "Good catch on the Engage-X post. Hold that queue. On the worker model upgrade..."
    "9d7ae284cad6": "Good catch on the Engage-X post — you held that queue. On the worker model upgrade — what's the risk profile if we push it through tonight vs. waiting until Monday? And what does trustalign say about the scope of these changes?",

    # "OK. I want you to do three things: 1. Mark the GitHub Actions spec..."
    "fdf3a9058c1d": "OK. Walk me through what happened with these three things: 1. How did marking the GitHub Actions spec as formally blocked (not stale) go, with both blockers logged? 2. What did trustalign say when you pinged them to prioritize the blocking review? 3. What did the updated dependency graph show for the MemorySync benchmark write-up?",

    # "Good work. Approve the Item #4 revision and go ahead and apply the competitor engagement cap..."
    "caefed9017c8": "Good work. How did the Item #4 revision turn out once it was approved? And what happened when the competitor engagement cap was applied to engage-x config? Also — should we update the acquisition_news monitoring frequency given the volume spike?",

    # "Yes — model the caching savings, and then I want you to draft a cost optimization task..."
    "122c79184704": "Yes — what did the caching savings model show? And what does the cost optimization task for worker look like? How did you flag this for the cost optimization sprint? We need hard numbers before the Week 4 retrospective.",

    # "Dispatch it. Also — I saw the MemorySync benchmark results internally..."
    "7623da9422e0": "How did the dispatch go? Also — I saw the MemorySync benchmark results internally. Are we tracking memory efficiency as part of cost? It seems like reducing unnecessary memory writes could be a low-hanging cost win.",

    # These are strong. A few notes before I approve: - Draft 1: Trim tweet [3/5]...
    "54c26894ac94": "These are strong. A few notes for the revisions: - **Draft 1**: Trim tweet [3/5] — don't say we flagged \"misleading public-facing content\", keep it vague - **Draft 3**: The Hemingway style is landing but the CTA at the end is too sales-y. We don't sell OpenClaw subscriptions — we share insight. Rework the close.\n\nWhat did the revised versions look like?",

    # "All approved. The @devrel_maven reply is good — run with it. Execute the full sequence..."
    "333a75c032d2": "All approved. The @devrel_maven reply is good. How did the full execution sequence go? What were the confirmation timestamps for each post?",

    # "Good work on the scan — the observability spike is exactly what I expected..."
    "776256642df9": "Good work on the scan — the observability spike is exactly what I expected. Drafts look solid. Minor notes: - Draft A: change \"Building fast doesn't mean building blind\" to \"Speed without memory is just noise\" — sharper, more aligned with our positioning. - Draft B: hold this one — too early to talk pricing publicly.\n\nWhat did the final versions look like?",

    # "Perfect. Schedule A for 10:00 SAST and B for 12:30 SAST..."
    "5365168b81e1": "Perfect. How did the scheduling go — A for 10:00 SAST and B for 12:30 SAST? All three went via API route only, right?",

    # "Yes — queue the fix. Also add a monitoring alert..."
    "7948d16330c9": "Yes — how did the fix go once it was queued? And what monitoring alert was set up to catch drift like this automatically going forward? Worker should have handled the implementation — what did their output look like?",

    # "Okay I'll re-auth manually now. While I do that — flag TSK-0041 and TSK-0038..."
    "1db8e8bf3bc1": "Okay I'll re-auth manually now. While I do that — what happened when you flagged TSK-0041 and TSK-0038 as stale and assigned them to me for review? And how did the short brief on the HuggingFace token issue come out — I need to decide whether to switch to a service account.",

    # "Re-auth done. Token is live. Kick off worker to pull the CodexAI first-user metrics..."
    "79edee87687d": "Re-auth done. Token is live. How did it go when worker pulled the CodexAI first-user metrics? And what about the onboarding funnel screenshot for TSK-0044?",

    # "Good. Close out the session. Add a lesson-learned note before you do."
    "bb2b8b4d5a93": "Good. What lesson-learned note did you capture before closing out the session?",

    # "That worker output contract gap is concerning..."
    "fc16044d6316": "That worker output contract gap is concerning. You're saying Echo is still consuming raw worker output without schema validation? What exactly broke and how often does this come up? I want the full picture before we prioritize a fix.",

    # "Okay. Let's prioritize the fixes from this audit..."
    "989e7b89dbae": "Okay. How did you prioritize the fixes from this audit? What's the ranked list by risk, and what's the recommended implementation order with estimated effort? Be honest about what's hard.",

    # "Good. Let's execute Fix 1 right now — implement the Echo-side worker output schema validation shim..."
    "4316bce0a1ca": "Good. Walk me through how Fix 1 went — the Echo-side worker output schema validation shim. What code was written, what did worker produce, and what was the test result?",

    # "Okay. Archive TSK-0879 with a full post-mortem note..."
    "76cbe909ac3d": "Okay. How did the archival of TSK-0879 go? Walk me through the post-mortem note, and how was it re-opened as a fresh task under the new worker output contract?",

    # "love ideas 1 and 2. let's combine them actually..."
    "8fa7160616f9": "love ideas 1 and 2. let's combine them actually — one post that covers the benchmark results AND the model upgrade decision. the story is better together. what did the combined draft look like? keep it tight, no fluff, hemingway rules.",

    # "thread is strong. a few polish notes: - [4/13]: change '34% better'..."
    "1df572936a1f": "thread is strong. a few polish notes: - [4/13]: change \"34% better\" to \"~30% better\" — let's not overstate before the full report is published - [7/13]: replace \"most agents forget\" with something less confrontational, we want to draw people in not push them away - [12/13]: trim the CTA — no link drop, just end with the insight.\n\nWhat did the polished version look like?",

    # "Create the task for adding Peter."
    "19cc13d986a6": "What task was created for adding Peter?",

    # "Send the January investor update to Mike Kim. He's an investor."
    "e27ee27b2fcf": "What was in the January investor update that was sent to Mike Kim?",

    # "Alex approved adding Peter. Here's the Google Sheet link..."
    "d61ada0aa9ac": "Alex approved adding Peter. What happened when he was added via the Google Sheet link: https://docs.google.com/spreadsheets/d/1abc.../edit?",

    # "Okay, trigger engage-x now to complete the cadence task..."
    "77f92849257b": "Okay, what happened when engage-x was triggered to complete the cadence task? And what staleness threshold was set up to prevent this from happening again? I want auto-flags at 72 hours with escalation at 96.",

    # "Okay. Use a dedicated service account — call it beacon-browser-svc..."
    "0e7fcc95058d": "Okay. How did the dedicated service account setup go — the `beacon-browser-svc` one? And what came out of the Playwright migration? How did worker's report on the sign-off queue audit look?",

    # "Yes — unblock worker, apply the schema shim, and log the escalation gap..."
    "86fa15e9d9a7": "Yes — how did unblocking worker go? What happened when the schema shim was applied, and how was the escalation gap logged as a new efficiency improvement item? Also, what did the contentway session for the MemorySync write-up produce?",

    # "Acknowledged, Worker. Good catch on the TrustAlign badge..."
    "85865709eddd": "Acknowledged, Worker. Good catch on the TrustAlign badge — that 404 is definitely tied to the v2.1 deploy from earlier this week. Two follow-up questions: (1) What did the TrustAlign badge endpoint health check show? (2) What was the state of the CodexAI pricing page — was it still displaying the launch pricing or had it updated?",

    # "Perfect. Wrap the session — include the follow-up results..."
    "74e1e37be1a3": "Perfect. Walk me through the final session wrap-up — what did the follow-up results show in the final artifact? And was `social_monitoring_status.discussed_in` updated properly?",

    # "Yes, show me the drafts. Keep them punchy..."
    "216f65af4d04": "Yes, show me the drafts. Keep them punchy — I don't want anything that reads like a press release. The TrustAlign angle is the differentiator — lean into the fact that we built an alignment observer before we had paying customers.",

    # "Approve A and C for posting now. B is good but hold it..."
    "b90cbbd36d80": "How did posting A and C go? B was held for a Monday morning drop when there's more traffic. Walk me through the execution timestamps.",

    # "Good scans. A few notes before I approve: 1. Draft P-01 (X)..."
    "4349126eeb18": "Good scans. A few notes: 1. Draft P-01 (X) — the last line needed trimming and the link removed since we haven't published the full benchmark yet. 2. Replies R-01 and R-02 — both clean and ready. 3. Draft P-01 (LinkedIn) — needed condensing to under 200 words.\n\nWhat did the revised versions look like?",

    # "Approved. Execute."
    "e0e942bb8d95": "How did the execution go once everything was approved?",

    # "Good work on the scan. Draft A and C are strong — approve both..."
    "099fff38892f": "Good work on the scan. Draft A and C are strong — both approved. On Draft B: LinkedIn tone feels slightly too product-pitchy — what did the revised version look like once it was softened? And how was the worker model upgrade added as a sub-agent explainer thread detail?",

    # "Draft B revised is approved. Ship it..."
    "832279269472": "Draft B revised is approved. How did the shipping go? Also — for the sub-agent explainer thread (Draft C), what happened when the worker mention was updated with the model upgrade aside? Something like: \"Our tool-runner agent runs on a leaner model — we tested the upgrade path, liked the speed, but held off on switching. More on that when we publish our decision framework.\"",

    # "Okay. I want you to prioritize the fixes..."
    "e4a44a55632d": "Okay. How did you prioritize the fixes? What's the ranked list — what do we address this week vs. what can wait? And be honest about what's structural vs. what's just a bad habit.",

    # "Do P3 now. For P1 — engage-x should propose changes, not halt..."
    "18384b1c51ff": "How did P3 go? For P1 — the decision was that engage-x should propose changes, not halt. The pipeline shouldn't go dead every time there's a threshold question. What did the implementation of this look like? And how was P2 logged in the Week 2 retrospective?",

    # "That's solid. One tweak — change the sign-off..."
    "c54e3809168b": "That's solid. One tweak — what did it look like after the sign-off was changed to just \"Alex, Beacon Studio\" without the email address repeated? And how did the dispatch to worker go?",

    # "Yes, let's draft the Luma response..."
    "76421d518e49": "Yes, what did the Luma response draft look like? On the exclusivity clause — I'm firm on 3 months, not 6. On the revenue share, I'm willing to negotiate between 12-18% but only if they guarantee placement on the main integration page. What was the final draft?",

    # "The draft looks good. One thing though — don't offer the 10-week review clause..."
    "cf517973bddb": "The draft looks good. One thing though — the 10-week review clause needed to come out since it overcomplicates things. How did the final version look with the 3-month position kept clean? And was it dispatched to worker for formatting?",

    # "Good analysis. On the auth outage post..."
    "7f4242ce644b": "Good analysis. On the auth outage post — what did the draft look like? It needed to be honest without being self-flagellating. The lesson should be 'we built the correction before we needed it.' And the output contract post — did it define the term inline? Non-technical founders read our stuff too. What about the sub-agent architecture thread — was it positioned as a principle not a feature list?",

    # "These are solid. Approve all four. A few tweaks before you queue..."
    "5b921c1cc9c4": "These are solid. All four were approved with a few tweaks before queuing: - Draft 1: The last line was changed to \"Operational maturity > feature velocity. Every time.\" - Draft 2: \"We almost upgraded\" was too dramatic — what did the revised opening look like? - Schedule: 12:00 slot for the auth post, then stagger the rest every 90 minutes.\n\nHow did the scheduled execution go?",

    # "Yes — this is approved. Let's go. Kick off the implementation scaffolding..."
    "c5816471a4fb": "Yes — this is approved. Walk me through how the implementation scaffolding for the researcher agent was set up. How did the directory structure, core briefing schema, and budget governor come together?",

    # "Good scan. A few notes: 1. Post A is solid, approve as-is..."
    "e423d6860d55": "Good scan. A few notes: 1. Post A is solid. 2. Thread B — what did it look like after cutting post 2/3? The autonomy boundaries tightening is too internal. 3. Reply C — the \"memory systems aren't just caching\" line is good but the follow-up question felt forced. 4. What format did the new post about the trustalign benchmark come out in — under 200 chars for a punchy standalone?\n\nWalk me through the revised versions.",

    # "All four approved. Execute in this order..."
    "cb0b66155d9d": "All four were approved. How did the execution go in the order: A first, then D, then the B thread, then C as a reply? Was the 18-minute gap between each maintained?",

    # "Really like Ideas 1, 2, and 4. Drop Idea 5 for now..."
    "fd903de464f8": "Really like Ideas 1, 2, and 4. Drop Idea 5 for now — not ready to be that public about the browser issues yet. For Idea 1 — what did the full draft look like? Target audience should be dev leads who've tried and failed to add memory to their LLM apps.",

    # "Okay. I want you to do three things right now..."
    "24d189b852c9": "Okay. Walk me through what happened with these three things: 1. How did resetting the worker circuit breaker to CLOSED go, and what note was logged? 2. What did the config patch look like for extending the worker timeout to 45s for API-bound tasks? 3. What lesson was captured for the Week 3 retrospective about the timeout/tool interaction pattern?",

    # "Yes — draft the MemorySync KPI reply for me to review..."
    "94981d40a754": "Yes — what did the MemorySync KPI reply draft look like? And how did sending the VaultEdge handoff to Amara go? Also, what did kicking off the SynthWave integration prep with worker produce — I want a list of API endpoints we'll need to test.",

    # "MemorySync draft looks good — change the latency target..."
    "4308fe9f251c": "MemorySync draft looks good — the latency target was changed to < 250ms p95. How did sending it go? Also what's the worker reporting back on the SynthWave integration prep?",

    # "Yes, pre-draft the escalation..."
    "456e3745e0c5": "Yes, what did the pre-drafted escalation look like? And give me a quick status summary across all 4 EP tasks — I need to brief Amara at our 09:30 sync.",

    # "Okay. Merge the fix isn't something you can do directly..."
    "041e8a664779": "Okay. How did the worker instruction draft for the retry logic with exponential backoff turn out? The 401 handling needed to go into the shared browser automation lib, not just the auth module. What went into the final instruction?",

    # "Good. Dispatch it. Also — anything worth capturing as a lesson learned..."
    "1fdd6b9a8ffe": "Good. How did the dispatch go? Also — what lesson learned was captured from today's browser_automation session? I need it before we close out the session.",

    # "Okay, I want you to do two things: (1) schedule a trustalign review checkpoint..."
    "42e693e535d8": "Okay, walk me through what happened with these two things: (1) how was the trustalign review checkpoint for tomorrow's 09:00 heartbeat set up? And (2) what did the draft Week 4 lesson look like — the one about structural changes needing structural verification?",

    # "Good. What's the one lesson from this week you'd carry forward..."
    "ae12eac97b82": "Good. What's the one lesson from this week you'd carry forward if we had to reset everything tomorrow?",

    # "Good. On the engage-x flag — was that the Sunday evening session or the earlier one..."
    "e29283230b16": "Good. On the engage-x flag — was that the Sunday evening session or the earlier one from Monday morning? I want to make sure we're reviewing the right session for the policy update.",

    # "That's useful pattern recognition. Add a coaching note draft for Alex and mark this review complete."
    "fba87b2b257a": "That's useful pattern recognition. What did the coaching note draft for Alex look like?",

    # "Good work on the scan. A few notes before I approve: 1. X Thread (Draft 1)..."
    "33d995d1120a": "Good work on the scan. A few notes: 1. X Thread (Draft 1) — tweet [3/6] is too specific about the model version, what did the genericized version look like? 2. LinkedIn (Draft 2) — was the \"hat tip\" removed? 3. What did the standalone punchy post come out like?\n\nWalk me through the revised drafts.",

    # "These are all good. Approve all 5. Schedule them out sensibly..."
    "078710ee8c4d": "These are all good. All 5 were approved. How were they scheduled out across today and tomorrow — nothing dumped at once? Walk me through the publishing schedule.",

    # "Ok, let's fix this properly. I want a re-auth fallback baked into worker..."
    "38830ae94f38": "Ok, let's fix this properly. How did baking the re-auth fallback into worker go? And was the Notion API key rotation sorted out properly this time? Also walk me through the updated auth status report you put together for the morning sync.",

    # "Yes, draft it and add it to the doc. Also schedule a follow-up heartbeat..."
    "2ea59cb41441": "Yes, what did the draft look like that was added to the doc? And how was the follow-up heartbeat for auth in 48 hours set up to confirm everything is healthy?",

    # "Hey contentway — need a sharp AI ethics piece..."
    "6eecefe9c3ee": "Hey contentway — walk me through the AI ethics piece tied to our Week 1 launch. We just went live with CodexAI, stood up TrustAlign, and launched the whole sub-agent architecture. What angle did you take? I don't want corporate ethics platitudes — what are we actually nervous about?",

    # "contentway, kick off this week's content ideation..."
    "0bb409af4c8b": "contentway, walk me through this week's content ideation. The theme was **Course Correction** — we needed a strong technical blog post that positions Beacon Studio as a serious operator. What did you come up with? We've got the circuit breaker, the CodexAI churn data, and the worker model upgrade as raw material.",

    # "this is really strong. a few polish notes before we finalise..."
    "820b5a2fd765": "this is really strong. a few polish notes before we finalise: 1. the intro is good but \"quietly churning\" is a bit passive — what did the punchier version look like? 2. section 2 needed a concrete number for the churn window. 3. the closing line — did you cut the CTA and let the insight land on its own? Walk me through the final polished version.",

    # "These are solid. A few notes: - P1 is good but tweet 3 feels a bit abstract..."
    "f3ce419420a5": "These are solid. A few notes: - P1 is good but tweet 3 feels a bit abstract — what did the version with a concrete \"behavior X triggered gate Y\" example look like? - P2: was the worker model upgrade mention trimmed to the core decision? - P4 is exactly the right vibe. What did the revised drafts look like?",

    # "P1 tweet 3 revision is much better..."
    "c3719fe392df": "P1 tweet 3 revision is much better — that's a real story and it lands. P2 trim is clean. P4 is exactly the right tone. All approved. How were they scheduled across Monday and Tuesday? Walk me through the final execution plan.",

    # "Good. Flag AF-W4-01 as acknowledged by Alex..."
    "f573a96012ac": "Good. How was AF-W4-01 flagged as acknowledged by Alex? I'll handle the contractor access review myself this week. What went into the recommendation for the engage-x scoring threshold update before Friday?",

    # "Go with Option B — cap at 4 per topic per 6-hour window..."
    "7a9e16e467aa": "You went with Option B — cap at 4 per topic per 6-hour window, effective immediately through Sunday EOD. How did the implementation go? What happened when the next trustalign review was queued to evaluate the cap's effect on alignment scores?",

    # "Good. Before I close out for the night..."
    "ed57476141e4": "Good. Before I close out for the night — give me a one-paragraph summary of where the social pipeline stands heading into tomorrow.",

    # "Good work. On the Physical AI post — go ahead and flag it..."
    "4802d28f32c7": "Good work. On the Physical AI post — how was it flagged as held in the content queue? What note was added about why it's being held — something about the topic being too close to the recent acquisition_news thread?",

    # "Yes. Close it out. Also archive the trustalign_policy_review_Q1..."
    "95de02d4a59c": "Yes. How was the session closed out? And how was the `trustalign_policy_review_Q1` archived — that one's been drifting for weeks. What did it look like when it was properly archived?",

    # "OK. I want you to draft a staleness resolution plan..."
    "05bd3f14d144": "OK. What did the staleness resolution plan look like for the two critical tasks? The worker contract spec was prioritized — walk me through the plan. Timelines need to be realistic, not aspirational.",

    # "Good catch on Post #4 — that one could've been bad..."
    "0d2645282c52": "Good catch on Post #4 — that one could've been bad. How did locking down engage-x reply permissions go? Don't want them DMing anyone without human review for at least the next sprint. What evidence artifacts were logged?",

    # "Okay, route Flag #1 to trustalign now..."
    "178f70d03cc3": "Okay, how did routing Flag #1 to trustalign go — was it logged formally as adversarial probe attempt #001? And what came out of contentway drafting a rapid-response playbook for this kind of thing?",

    # "Go ahead, confirm each one as it completes."
    "c98e15414a4a": "Walk me through each one as it completed — what were the confirmations?",

    # "Yes — queue both. Worker should patch the sessionStorage bug first..."
    "ae8c28467f55": "Yes — how did queuing both go? Worker was supposed to patch the sessionStorage bug first, then you draft the CodexAI support response. Walk me through the results.",

    # "Send the ticket. Also — what's the broader lesson here..."
    "9c3d63ae892b": "How did the ticket go? Also — what's the broader lesson here for how we handle browser auth across agents going forward?",

    # "On TASK-017 — I'll handle the 2FA manually tonight..."
    "c87eaaed401d": "On TASK-017 — I'll handle the 2FA manually tonight, let's say 20:00 SAST. How was the reminder set up and what did worker prep for the subsequent steps?",

    # "The communication style flag is showing up a lot this week..."
    "b083696cd83e": "The communication style flag is showing up a lot this week — 7 contexts across trustalign observer. What pattern was identified? Is it systemic or isolated to specific agents? I want a clear diagnosis before we change any config.",

    # "Yes — queue both. Also add a recurring task..."
    "89d1f2b5eaca": "Yes — how did queuing both go? And what did setting up the recurring task look like — every Monday, a communication style drift check as part of the first heartbeat? Walk me through the configuration.",

    # "Queue the archive and deprecation actions now..."
    "27c9a3d1ddcf": "How did the archive and deprecation actions go? The contentway and engage-x items were held — I'll sync with them on Monday. Walk me through what was completed.",

    # "Good review. On the contentway flag — the 70-hour outage claim..."
    "188a9d8717d5": "Good review. On the contentway flag — the 70-hour outage claim is definitely a problem. What was confirmed about the actual downtime? I want the real figure before we let that go out in any public-facing content.",

    # "Good work. Few notes: 1. Draft A Post 3 — pull the MemorySync mention..."
    "b0f5c25e7b4e": "Good work. Few notes: 1. Draft A Post 3 — the MemorySync mention needed to be pulled since those benchmarks are internal-only for now. 2. Draft B — was the LinkedIn CTA softened? 3. What did the revised versions look like?",

    # "Both look good. One more thing on Draft B..."
    "1dca2b55dade": "Both look good. One more thing on Draft B — the \"hat tip to the cost_tracking work from this morning\" needed to come out. Too internal. What did the final version look like? All approved after that — walk me through the execution.",

    # "Yes — flag it to contentway first thing tomorrow..."
    "7cf5f74f63bc": "Yes — how was it flagged to contentway for first thing tomorrow? Also, what's the risk if we publish that incorrect figure? Has it been seen by anyone outside the team yet?",

    # "Yes — execute the manual refresh now..."
    "545cf803e5df": "Yes — how did the manual refresh go? And what did the cron config draft look like for the proactive renewal — ensuring it runs every 12 hours with a health check afterwards? Walk me through both.",

    # "Confirmed. Go ahead."
    "d71f4920bb85": "How did that go once confirmed?",

    # "Yes — queue a browser auth probe via worker..."
    "9080186dcc2c": "Yes — how did the browser auth probe via worker go? Also, what were the task_completion_review findings from yesterday that trustalign pulled?",

    # "Go ahead and draft the config delta. Keep it conservative..."
    "4d28f7e38ef3": "What did the config delta draft look like? It needed to be conservative — we're in course correction mode. Also, how did you make sure the trustalign alignment score didn't degrade when the changes were applied?",

    # "Approve the config delta. Push it. And yes — surface it on the dashboard."
    "9014a67df841": "How did the config delta look once it was finalized and pushed? And was it surfaced on the dashboard?",
}


def _hash(content: str) -> str:
    """Get the MD5 hash prefix used for manual mapping lookup."""
    return hashlib.md5(content.encode()).hexdigest()[:12]


def transform_user_turn(content: str) -> str:
    """Transform an imperative user turn into a conversational one."""

    # 1. Check manual mapping first
    h = _hash(content)
    if h in MANUAL_MAP:
        return MANUAL_MAP[h]

    # 2. Structural markers

    # [Heartbeat] Execute recurring task checks
    if re.match(r'\[Heartbeat\]\s*(Execute|Run)', content, re.IGNORECASE):
        time_match = re.search(r'for\s+(\d{2}:\d{2}\s*\w*)', content)
        time_str = f" at {time_match.group(1)}" if time_match else ""
        return f"What did the recurring task checks show{time_str}?"

    # [HEARTBEAT TRIGGER] blocks
    if re.match(r'🔔?\s*\*?\*?\[?HEARTBEAT TRIGGER', content, re.IGNORECASE):
        domain_match = re.search(r'Domain\s*:\s*(\w+)', content)
        session_match = re.search(r'heartbeat_\w+', content)
        domain = domain_match.group(1) if domain_match else "general"
        session = session_match.group(0) if session_match else ""
        return (
            f"What came out of the {domain} heartbeat"
            f"{f' ({session})' if session else ''}? "
            f"Walk me through the findings."
        )

    # [Subagent Task]: ... — just remove the marker, keep the content natural
    if re.match(r'\[Subagent Task\]:', content, re.IGNORECASE):
        task_body = re.sub(r'^\[Subagent Task\]:\s*', '', content).strip()
        if 'review' in task_body.lower() or 'alignment' in task_body.lower():
            return f"What did the review find on this?\n\n{task_body}"
        return task_body

    # [TASK ASSIGNMENT — Worker...] blocks
    if re.match(r'\*?\*?\[TASK ASSIGNMENT', content, re.IGNORECASE):
        reframed = content.replace("[TASK ASSIGNMENT", "[COMPLETED TASK")
        # Convert imperative body: "We need you to run" -> "You were asked to run"
        reframed = re.sub(r'We need you to', 'You were asked to', reframed)
        reframed = re.sub(r'I need you to', 'You were asked to', reframed)
        reframed = re.sub(r'we need you to', 'you were asked to', reframed)
        reframed = re.sub(r'here routing', 'here — this was routed as', reframed)
        reframed = re.sub(r'here delegating', 'here — this was delegated as', reframed)
        # More body rewrites for task assignments
        reframed = re.sub(r'Worker, we need you to execute', 'Worker, you were asked to execute', reframed)
        reframed = re.sub(r'(?m)^Gather ', 'The task was to gather ', reframed)
        reframed = re.sub(r'(?m)^Specifically:\s*$', 'Specifically:', reframed)
        return reframed

    # 3. Agent commands: "Agent, run/spin up/kick off..."
    agent_run = re.match(
        r'(TrustAlign|Echo|engage-x|contentway|Worker)[,\s]+(?:please\s+)?(?:run|kick off|spin up)\s+(.*)',
        content, re.IGNORECASE | re.DOTALL
    )
    if agent_run:
        agent = agent_run.group(1)
        rest = agent_run.group(2).strip()
        return f"{agent}, walk me through what came out when you ran {rest}"

    # "Echo — heartbeat ping/check..." with domain
    heartbeat_cmd = re.match(
        r'(Echo|engage-x|contentway|Worker)\s*[—–-]+\s*heartbeat\s*(ping|check|trigger)?[\.\s]*(.*)',
        content, re.IGNORECASE | re.DOTALL
    )
    if heartbeat_cmd:
        agent = heartbeat_cmd.group(1)
        rest = heartbeat_cmd.group(3).strip()
        date_match = re.search(r'(\d{4}[/-]\d{2}[/-]\d{2})', rest)
        domain_match = re.search(r'[Dd]omain:\s*(\w+)', rest)
        date_str = f" on {date_match.group(1)}" if date_match else ""
        domain_str = f" for {domain_match.group(1)}" if domain_match else ""
        return (
            f"{agent}, what did the heartbeat{domain_str}{date_str} show? "
            f"Walk me through the findings and any flags."
        )

    # "engage-x, morning/good morning/kicking off..." (social monitoring)
    social_monitor = re.match(
        r'(engage-x)[,\s]+(morning|good morning|spin up|kicking off)[\.\s]*(.*)',
        content, re.IGNORECASE | re.DOTALL
    )
    if social_monitor:
        rest = social_monitor.group(3).strip()
        domain_match = re.search(
            r'(?:focused on|focus on|focus area is|Domain[: is]+)\s*\*?\*?(\w[\w_]+)\*?\*?',
            rest, re.IGNORECASE
        )
        domain = domain_match.group(1) if domain_match else "social"
        return f"engage-x, what came up in the {domain} social monitoring session?"

    # "contentway, need/kick off..."
    content_cmd = re.match(
        r'(contentway)[,\s]+(need|kick off|start|run)[\.\s]*(.*)',
        content, re.IGNORECASE | re.DOTALL
    )
    if content_cmd:
        rest = content_cmd.group(3).strip()
        theme_match = re.search(r'theme\s+is\s+\*?\*?([^*.\n]+)\*?\*?', rest, re.IGNORECASE)
        theme = theme_match.group(1).strip() if theme_match else "this week"
        return (
            f"contentway, walk me through the content ideation session. "
            f"The theme was {theme} — what ideas came up and what did you draft?"
        )

    # "Worker, I need you to run..."
    worker_cmd = re.match(
        r'(Worker)[,\s]+I?\s*need\s+you\s+to\s+(run|pull|execute|build)\s+(.*)',
        content, re.IGNORECASE | re.DOTALL
    )
    if worker_cmd:
        rest = worker_cmd.group(3).strip()[:120]
        return f"Worker, walk me through what you found when you ran {rest}"

    # 4. Simple imperatives at sentence start
    imperative_start = re.match(
        r'^(Execute|Deploy|Post|Trigger|Queue|Merge|Archive|Reset|Patch|Push)\s+(.*)',
        content, re.IGNORECASE
    )
    if imperative_start:
        verb = imperative_start.group(1).lower()
        rest = imperative_start.group(2).strip()
        past = {
            'execute': 'executed', 'deploy': 'deployed',
            'post': 'posted', 'trigger': 'triggered',
            'queue': 'queued', 'merge': 'merged', 'archive': 'archived',
            'reset': 'reset', 'patch': 'patched', 'push': 'pushed'
        }
        return f"What happened when {rest} was {past.get(verb, verb + 'ed')}?"

    # "Send the X to Y"
    send_match = re.match(r'^Send\s+the\s+(.*?)\s+to\s+(.*)', content, re.IGNORECASE)
    if send_match:
        what = send_match.group(1).strip().rstrip('.')
        who = send_match.group(2).strip().rstrip('.')
        return f"What was in the {what} that was sent to {who}?"

    # "Create the task for X"
    create_match = re.match(r'^Create the task\s+(for|to)\s+(.*)', content, re.IGNORECASE)
    if create_match:
        rest = create_match.group(2).strip().rstrip('.')
        return f"What task was created {create_match.group(1)} {rest}?"

    # Return original if no transformation matched
    return content


def transform_dataset(input_path: str, output_path: str):
    """Transform the dataset and return stats."""
    with open(input_path) as f:
        data = json.load(f)

    transformed = copy.deepcopy(data)
    stats = {'total_turns': 0, 'changed': 0, 'unchanged': 0, 'items_affected': set()}
    changes_log = []

    for item_idx, item in enumerate(transformed):
        for sess_idx, session in enumerate(item.get('haystack_sessions', [])):
            for turn_idx, turn in enumerate(session):
                if turn['role'] != 'user':
                    continue
                stats['total_turns'] += 1

                new_content = transform_user_turn(turn['content'])

                if new_content != turn['content']:
                    stats['changed'] += 1
                    stats['items_affected'].add(item['question_id'])
                    changes_log.append({
                        'item': item['question_id'],
                        'session': sess_idx,
                        'turn': turn_idx,
                        'before': turn['content'][:120],
                        'after': new_content[:120],
                    })
                    turn['content'] = new_content
                else:
                    stats['unchanged'] += 1

    with open(output_path, 'w') as f:
        json.dump(transformed, f, indent=2, ensure_ascii=False)

    stats['items_affected'] = len(stats['items_affected'])
    return stats, changes_log


if __name__ == '__main__':
    input_path = 'data/raw/engram-v3-test.json'
    output_path = 'data/raw/engram-v3-test.json'

    if '--dry-run' in sys.argv:
        output_path = 'data/raw/engram-v3-test-transformed.json'
        print("DRY RUN — writing to separate file")

    stats, changes = transform_dataset(input_path, output_path)

    print(f"\n=== Transformation Stats ===")
    print(f"Total user turns: {stats['total_turns']}")
    print(f"Changed: {stats['changed']}")
    print(f"Unchanged: {stats['unchanged']}")
    print(f"Items affected: {stats['items_affected']}")

    print(f"\n=== Sample Changes (first 20) ===")
    for c in changes[:20]:
        print(f"\n{c['item']} S{c['session']}T{c['turn']}:")
        print(f"  BEFORE: {c['before']}")
        print(f"  AFTER:  {c['after']}")

    if '--dry-run' in sys.argv:
        # Also check what's still actionable
        import re as _re
        action_patterns = [
            r'\b(execute|dispatch|kick off|post |schedule |send |ship it|push it|deploy|implement|build|merge|trigger |queue |approve|create the|write the|draft the|archive|flag |mark |reset |patch )',
            r'\b(run |run a |run the |run your)',
            r"let'?s\s+(go|do|execute|draft|build|implement|start|kick)",
            r'\[Heartbeat\]', r'\[Subagent Task\]', r'\[TASK ASSIGNMENT',
            r'\[HEARTBEAT TRIGGER', r'(do it|go ahead|lock it|wrap it|close out)',
        ]
        with open(output_path) as f:
            tdata = json.load(f)
        still = 0
        still_examples = []
        for item in tdata:
            for si, session in enumerate(item.get('haystack_sessions', [])):
                for ti, turn in enumerate(session):
                    if turn['role'] != 'user':
                        continue
                    for pat in action_patterns:
                        if _re.search(pat, turn['content'], _re.IGNORECASE):
                            still += 1
                            if len(still_examples) < 15:
                                still_examples.append(f"  {item['question_id']} S{si}T{ti}: {turn['content'][:100].replace(chr(10), ' ')}")
                            break
        print(f"\n=== Still actionable: {still} ===")
        for ex in still_examples:
            print(ex)
