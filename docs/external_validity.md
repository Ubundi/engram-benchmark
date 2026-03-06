# External Validity Template

This document is a fill-in template for addressing external validity in Engram.

## Goal

Address the main external-validity criticism of the current benchmark:

- the dataset is synthetic
- the current framing is centered on one project-like domain
- real deployments are noisier and more heterogeneous than the current haystack corpus

There are two acceptable closure paths for this work:

- Path A: add a second domain or corpus
- Path B: provide a rigorous defense of synthetic stress-test benchmark design

Either path should be documented clearly enough that the paper can answer the question: why should a reviewer believe Engram says something useful beyond one synthetic benchmark world?

## Current Status

| Item | Status | Notes |
|---|---|---|
| Second corpus added | Pending | `TBD` |
| Synthetic-design defense written | Pending | `TBD` |
| Threats-to-validity section updated | Pending | `TBD` |
| Paper text drafted | Pending | `TBD` |

## Path Decision

Choose one primary path and document why.

| Decision field | Value |
|---|---|
| Primary path | `TBD` |
| Secondary supporting path | `TBD` |
| Decision rationale | `TBD` |

## Path A: Second Domain Or Corpus

Use this path if the team can extend the benchmark empirically.

### Candidate corpus definition

| Field | Value |
|---|---|
| Corpus name | `TBD` |
| Domain | `TBD` |
| Why it differs from Engram v3 | `TBD` |
| Synthetic or real-world derived | `TBD` |
| Privacy / licensing constraints | `TBD` |
| Planned size | `TBD` |
| Expected categories covered | `TBD` |

### What the second corpus should add

The second corpus should differ from Engram v3 in at least one meaningful way:

- domain vocabulary
- session structure
- topic noise
- number of speakers or agents
- task distribution
- update frequency or temporal complexity

Do not add a second corpus that is cosmetically different but structurally identical.

### Corpus comparison template

| Property | Engram v3 | Second corpus | Why it matters |
|---|---|---|---|
| Domain | `TBD` | `TBD` | `TBD` |
| Session style | `TBD` | `TBD` | `TBD` |
| Topic diversity | `TBD` | `TBD` | `TBD` |
| Noise level | `TBD` | `TBD` | `TBD` |
| Multi-session depth | `TBD` | `TBD` | `TBD` |
| Temporal complexity | `TBD` | `TBD` | `TBD` |
| Privacy constraints | `TBD` | `TBD` | `TBD` |

### Evaluation plan template

| Field | Value |
|---|---|
| Systems to rerun on second corpus | `TBD` |
| Frozen settings reused | `TBD` |
| Whether category taxonomy changes | `TBD` |
| Whether metrics remain identical | `TBD` |
| Minimum number of runs | `TBD` |

### Findings template

Fill this after the second corpus is actually evaluated.

| Question | Answer |
|---|---|
| Do system rankings stay similar? | `TBD` |
| Which categories transfer cleanly? | `TBD` |
| Which categories degrade most? | `TBD` |
| Does hallucination behavior change? | `TBD` |
| What does this say about benchmark generalization? | `TBD` |

## Path B: Defense Of Synthetic Stress-Test Design

Use this path if adding a second corpus is not feasible before publication.

### Core argument template

Fill this section with a benchmark-design argument, not an apology.

| Claim | Support |
|---|---|
| Synthetic data is appropriate for controlled memory stress-testing | `TBD` |
| Controlled generation improves task observability and ground truth quality | `TBD` |
| The benchmark targets diagnostic memory behaviors, not production realism | `TBD` |
| External validity is bounded and explicitly disclosed | `TBD` |
| The benchmark is valuable even if it is not a full simulator of production usage | `TBD` |

### Acceptable defense points

These are the kinds of arguments that can legitimately support the benchmark:

- synthetic data allows exact ground truth for memory-specific questions
- controlled session design isolates memory behavior from unrelated UX variation
- stress tests are useful even when they are not naturalistic in every respect
- safety and privacy constraints make public real-session corpora difficult
- benchmark value can come from comparability and diagnostic clarity, not only realism

### Weak arguments to avoid

Do not rely on arguments like:

- "real data was too hard to get"
- "synthetic should be good enough"
- "all benchmarks are unrealistic anyway"
- "we only care about our own product setting"

### Bounded-claim template

Use this structure in the paper:

> Engram is a controlled diagnostic benchmark for long-term agent memory, not a full simulation of production deployments. Its synthetic haystacks improve auditability and ground-truth precision, while its limitations in domain breadth, topic noise, and user heterogeneity are explicitly disclosed.

## Threats-To-Validity Template

This section should be filled regardless of which path is chosen.

### External validity threats

| Threat | Why it matters | Mitigation or disclosure |
|---|---|---|
| Synthetic session style | `TBD` | `TBD` |
| Single-project terminology | `TBD` | `TBD` |
| Limited domain breadth | `TBD` | `TBD` |
| Lower real-world noise | `TBD` | `TBD` |
| Single-user or limited multi-user dynamics | `TBD` | `TBD` |

### What the benchmark does and does not claim

| Claim type | Allowed | Not allowed |
|---|---|---|
| Memory diagnostics under controlled conditions | `TBD` | `TBD` |
| Cross-system comparison under fixed protocol | `TBD` | `TBD` |
| Broad production generalization | `TBD` | `TBD` |
| Product-readiness certification | `TBD` | `TBD` |

## Paper Text Template

Use this paragraph after filling the placeholders:

> Engram's external validity is bounded by its controlled synthetic design. The benchmark does not claim to fully reproduce production agent deployments, which involve broader domains, noisier interactions, and more heterogeneous users. Instead, Engram targets diagnostic evaluation of long-term memory behavior under auditable conditions. `TBD`

If using Path A, continue with:

> To test whether findings transfer beyond the original benchmark framing, we added a second corpus spanning `TBD`. Results on that corpus show `TBD`.

If using Path B, continue with:

> We argue that controlled synthetic stress tests remain useful because `TBD`.

## Repo Deliverables

Before marking this work complete, the repo should contain either:

- a documented second corpus plan plus actual comparative results

or:

- a benchmark-design section that explicitly defends the synthetic stress-test framing

In both cases, the repo should also contain:

- updated limitations language
- updated dataset-card positioning
- paper-ready threat-to-validity text

## Completion Checklist

- [ ] Primary closure path selected
- [ ] External-validity argument filled in
- [ ] Threats-to-validity section filled in
- [ ] Paper paragraph replaced with final text
- [ ] Repo docs updated to reflect the chosen path
