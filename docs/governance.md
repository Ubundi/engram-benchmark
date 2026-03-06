# Governance And Versioning Template

This document is a fill-in template for Engram's benchmark governance and versioning policy.

## Goal

Define how Engram changes over time while preserving:

- benchmark comparability
- submission eligibility clarity
- public traceability of historical results
- clear ownership over benchmark-affecting changes

## Policy Status

| Item | Status | Notes |
|---|---|---|
| Governance policy drafted | Pending | `TBD` |
| Versioning rules finalized | Pending | `TBD` |
| Result-history policy finalized | Pending | `TBD` |
| Submission eligibility policy aligned with leaderboard docs | Pending | `TBD` |
| Maintainer approval process documented | Pending | `TBD` |

## Scope

This policy should govern:

- benchmark releases
- protocol versions
- dataset versions and splits
- official scoring settings
- official submission status
- historical result visibility

This policy should not govern:

- private exploratory experiments that are not presented as official benchmark results
- local development workflows
- internal product decisions outside the benchmark standard itself

## Roles And Ownership Template

| Role | Responsibility | Current owner |
|---|---|---|
| Benchmark Maintainer | Approves benchmark-affecting changes and release decisions | `TBD` |
| Research Lead | Owns scientific framing, comparability claims, and paper alignment | `TBD` |
| Infra / DX | Owns submission flow, artifact validation, and public benchmark operations | `TBD` |
| Contributor | Proposes changes and supplies required evidence | `TBD` |

## Benchmark Identity Template

| Field | Value |
|---|---|
| Current benchmark release | `TBD` |
| Current protocol version | `TBD` |
| Canonical dataset split | `TBD` |
| Current official scoring config | `TBD` |

## Change Classification Template

Every benchmark-affecting change should be classified before merge.

### Class A: Non-comparability-breaking changes

These should not require a new benchmark release:

- typo fixes in docs
- clarifications that do not change benchmark semantics
- tooling improvements that do not affect outputs
- additional examples or guides that do not change official settings

Template:

| Change | Why it is safe | Requires new release |
|---|---|---|
| `TBD` | `TBD` | No |

### Class B: Exploratory-only changes

These may be allowed for research, but should not count as official benchmark submissions:

- alternate judge models
- alternate judge pass counts
- custom subsets
- altered settle timing
- adapter experiments that materially change run behavior without freezing a new standard

Template:

| Change | Allowed for exploratory use | Officially comparable |
|---|---|---|
| `TBD` | Yes | No |

### Class C: Comparability-breaking changes

These should require a new benchmark release, protocol version, or both:

- task content changes
- scoring rubric changes
- required artifact changes
- protocol semantic changes
- official scoring configuration changes
- benchmark split changes that affect headline evaluation

Template:

| Change | Why comparability breaks | Requires |
|---|---|---|
| `TBD` | `TBD` | `TBD` |

## Versioning Rules Template

### Release bump rules

Fill these in with final policy decisions:

| Scenario | New benchmark release | New protocol version | Notes |
|---|---|---|---|
| Dataset content changes | `TBD` | `TBD` | `TBD` |
| Official judge config changes | `TBD` | `TBD` | `TBD` |
| Runtime phase semantics change | `TBD` | `TBD` | `TBD` |
| Required artifact schema changes | `TBD` | `TBD` | `TBD` |
| Docs-only clarification | `TBD` | `TBD` | `TBD` |

### Version naming template

Use a consistent scheme:

- benchmark release: `engram-vX.Y`
- protocol version: `engram-runtime-vN`
- exploratory results should disclose any deviation from the official setting

## Comparability Rules Template

These rules should define when two results may be compared directly.

### Directly comparable if

- same benchmark release
- same protocol version
- same official scoring configuration, unless explicitly labeled exploratory
- same dataset split
- full required artifacts exist

### Not directly comparable if

- benchmark release differs
- protocol semantics differ
- judge configuration differs and the run is presented as official
- task set differs in a way that affects headline metrics
- required artifacts are missing

### Comparability table template

| Pair of results | Comparable | Why |
|---|---|---|
| `TBD` vs `TBD` | `TBD` | `TBD` |
| `TBD` vs `TBD` | `TBD` | `TBD` |

## Submission Status Template

Define submission labels clearly.

| Submission status | Meaning | Leaderboard eligible | Notes |
|---|---|---|---|
| Official | `TBD` | `TBD` | `TBD` |
| Exploratory | `TBD` | `TBD` | `TBD` |
| Invalid | `TBD` | `TBD` | `TBD` |

Recommended baseline:

- official: matches the frozen benchmark release and required artifact policy
- exploratory: useful research result with disclosed deviations
- invalid: cannot be trusted or audited because required evidence is missing

## Historical Result Policy Template

This section should define what happens to old results when the benchmark evolves.

| Case | Policy |
|---|---|
| New release supersedes old release | `TBD` |
| Old official results remain visible | `TBD` |
| Corrected result replaces earlier result | `TBD` |
| Invalidated result handling | `TBD` |

### Traceability rules

Every public result should retain:

- run identifier
- benchmark release
- protocol version
- timestamp
- system or condition identity
- artifact bundle or validated artifact reference

## Change Approval Template

Use this for benchmark-affecting changes.

| Required question | Answer |
|---|---|
| Does the change affect comparability? | `TBD` |
| Does it require a new benchmark release? | `TBD` |
| Does it require a new protocol version? | `TBD` |
| Does it invalidate any existing public results? | `TBD` |
| Who approved the change? | `TBD` |
| Where is the public changelog entry? | `TBD` |

## Public Communication Template

When a benchmark-affecting change is released, publish:

- change summary
- release identifier
- protocol identifier if changed
- comparability statement
- impact on previous leaderboard entries
- migration guidance for external users

## Paper-Ready Summary Template

Use this paragraph after filling the placeholders:

> Engram uses a frozen release and governance policy to preserve result comparability over time. Benchmark-affecting changes are classified by whether they alter task content, protocol semantics, scoring configuration, or required artifacts. Changes that break comparability require a new benchmark release or protocol version, while exploratory deviations remain allowed but are not treated as official benchmark submissions.

## Repo Deliverables

Before marking this work complete, the repo should contain:

- a public governance and versioning policy
- explicit submission status definitions
- comparability rules across releases
- historical result traceability rules
- a documented approval and communication path for benchmark-affecting changes

## Completion Checklist

- [ ] Roles and ownership filled in
- [ ] Change classes filled in with actual policy
- [ ] Version bump rules filled in
- [ ] Comparability rules filled in
- [ ] Submission status definitions finalized
- [ ] Historical result policy finalized
- [ ] Public communication template replaced with actual policy text
