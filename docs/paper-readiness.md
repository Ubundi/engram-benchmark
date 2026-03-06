# Engram Paper Readiness Plan

This document turns the current Engram repository into a concrete plan for reaching a community-grade benchmark standard: professionally packaged, methodologically defensible, citable, and easy for outside teams to adopt.

It is based on the repository state as of March 6, 2026.

## Goal

Move Engram from a strong internal/public benchmark artifact to a benchmark that can credibly be presented in the style of LongMemEval:

- benchmark-first, not product-first
- clear task taxonomy and methodology
- reproducible and auditable
- externally legible and citable
- evaluated on multiple systems
- suitable for arXiv plus peer-reviewed submission

## Current Assessment

### Already strong

- Public benchmark docs exist and are coherent:
  - `README.md`
  - `docs/benchmark_spec.md`
  - `docs/evaluation_protocol.md`
  - `docs/dataset_card.md`
  - `docs/reproducibility.md`
  - `docs/FINDINGS.md`
- The benchmark harness is real, packaged, and tested:
  - runtime CLI
  - adapter model
  - output artifacts
  - submission validation
  - CI and tests
- The dataset is versioned as Engram v3 and distributed through Hugging Face.
- Governance has started:
  - leaderboard policy
  - submission format
  - security policy
  - contributing guide

### Main gaps to close

- The benchmark is not yet positioned against prior academic benchmarks in a formal way.
- Current results are too concentrated on one runtime family and one product comparison.
- No documented human-vs-LLM judge validation study yet.
- External validity is limited by the synthetic, single-project dataset framing.
- The public leaderboard is not yet active.

## Exit Criteria

Engram is paper-ready when all of the following are true:

- The benchmark has a frozen release and official evaluation settings.
- The README and site present Engram as a neutral benchmark.
- The paper includes related work and benchmark differentiation.
- Main results cover multiple systems or conditions beyond Cortex.
- Main tables include repeated runs with variance.
- The judge is validated against human annotations on a held-out sample.
- The dataset construction and limitations are documented tightly enough for peer review.
- A public benchmark homepage and leaderboard flow exist.
- Citation metadata and release artifacts are polished.
- A full paper draft exists in conference-style LaTeX.

## Workstreams

### 1. Benchmark Positioning

Purpose: make Engram read like a benchmark the field can adopt, not a benchmark built to justify one system.

### 2. Methodology and Evidence

Purpose: make the core claims survive skeptical academic review.

### 3. Artifact and Governance

Purpose: make the benchmark auditable, versioned, and operationally clean.

### 4. Paper and Release

Purpose: package the benchmark into a citable paper and launch bundle.

## Checklist

| ID | Task | Status | Priority | Suggested Owner | Current State | Exit Evidence |
|---|---|---|---|---|---|---|
| P1 | Rewrite the public framing so Engram is benchmark-first and Cortex is one evaluated system | Done | P0 | Research + Product | README, benchmark spec, and dataset card now present Engram as a system-neutral benchmark | Updated `README.md`, homepage copy, and docs intro pages all lead with benchmark objective, taxonomy, and protocol |
| P2 | Fix naming and citation consistency across the repo | Done | P0 | Benchmark Maintainer | `CITATION.cff` and package metadata now describe Engram as the benchmark artifact rather than a scaffold | `CITATION.cff`, package metadata, README badges, and dataset card all consistently use `Engram` |
| P3 | Freeze an official benchmark release with one canonical setting | Done | P0 | Benchmark Maintainer | Official release policy, metadata fields, and submission validation now pin Engram v3.0 and `engram-runtime-v1` | Versioned release notes, pinned split, pinned judge configuration, pinned settle defaults, and a release tag |
| P4 | Write an explicit related-work matrix against LongMemEval and other memory benchmarks | Not started | P0 | Research | Missing from repo docs | Table comparing task design, runtime setup, memory horizon, scoring, and artifact availability |
| P5 | Expand the evaluated system set beyond baseline vs Cortex | Not started | P0 | Research + Eng | Results center on OpenClaw native vs Cortex | Main benchmark table with at least 3-5 systems or conditions and reproducible run artifacts |
| P6 | Repeat benchmark runs and report variance | Not started | P0 | Research + Eng | Current docs describe a small number of runs, with only one baseline run | Reported means plus variance or confidence intervals for each main condition |
| P7 | Run a judge validation study against human labels | Not started | P0 | Research | Not yet documented | Annotation protocol, sample set, inter-annotator agreement, and judge-human agreement in paper appendix and repo docs |
| P8 | Strengthen external validity beyond one synthetic project framing | Not started | P0 | Research | Dataset card explicitly notes synthetic, single-project limitations | Either a second domain/corpus or a clearly defended benchmark-design section showing why synthetic stress tests are appropriate |
| P9 | Formalize benchmark governance and versioning policy | Not started | P1 | Benchmark Maintainer | Leaderboard policy exists but is early-stage | Public versioning doc covering benchmark changes, leaderboard eligibility, and historical comparability |
| P10 | Activate a public leaderboard or at minimum a verified submission workflow | Not started | P1 | Infra + Benchmark Maintainer | Policy exists; public leaderboard not active | Public leaderboard page or documented submission-review process with validation tooling |
| P11 | Publish benchmark homepage / docs landing page | Not started | P1 | Product + Design | Repo docs exist; no benchmark-style landing page indicated here | Stable page with benchmark summary, quickstart, metrics, leaderboard, citation, and release links |
| P12 | Add official benchmark figures and tables for the paper | Not started | P1 | Research | Some assets exist; paper figures not assembled | Final figures for taxonomy, protocol, dataset composition, and benchmark results |
| P13 | Document dataset construction in more paper-ready detail | Not started | P1 | Research | Current dataset card is good, but not yet paper-depth | Detailed construction section: generation pipeline, filtering, QA checks, anonymization, split policy |
| P14 | Add benchmark limitations and risk framing suitable for publication | Not started | P1 | Research | `docs/ethics_and_limitations.md` exists | Publication-ready limitations section with explicit threat-to-validity framing |
| P15 | Collect artifact bundles for every headline result | Not started | P1 | Eng | Output format exists | Stored, validated run artifacts for all main paper tables and leaderboard entries |
| P16 | Add a simple external reproduction path | Not started | P1 | Eng + DX | Integration guide exists | Clean outside-user flow validated by someone not on the core team |
| P17 | Create a paper draft in LaTeX with conference structure | Not started | P0 | Research | Not yet in repo | Draft with title, abstract, intro, related work, benchmark design, experiments, limitations, appendices |
| P18 | Prepare arXiv submission assets | Not started | P2 | Research | Not started | Clean source bundle, metadata, authorship, abstract, keywords, license decision |
| P19 | Target a peer-reviewed venue and back-plan deadlines | Not started | P0 | Research Lead | No venue plan documented in repo | Chosen venue, submission calendar, author responsibilities, review-readiness checklist |
| P20 | Seed early external adoption | Not started | P1 | Product + Research | Not yet evidenced in repo | At least 2 external teams or evaluators run Engram or agree to benchmark against it |

## Recommended Sequence

### Phase A: Fix identity and benchmark framing

Tasks:

- P1
- P2
- P3
- P4

Why first:

- This changes how people interpret the entire project.
- It forces the benchmark to stand on its own before more results are added.

Deliverables:

- benchmark-first README
- clean citation metadata
- official Engram release definition
- related-work comparison table

### Phase B: Upgrade the evidence

Tasks:

- P5
- P6
- P7
- P8
- P13
- P14

Why next:

- This is the core academic credibility layer.
- Without this, the paper will read as a product benchmark with nice packaging.

Deliverables:

- multi-system benchmark tables
- repeated-run statistics
- judge validation appendix
- stronger dataset methodology
- clear threats-to-validity section

### Phase C: Operationalize the benchmark as a public standard

Tasks:

- P9
- P10
- P11
- P15
- P16
- P20

Why next:

- This is what turns a paper into a benchmark people actually use.
- Standards come from repeatable external use, not only publication.

Deliverables:

- public versioning/governance rules
- verified submission flow
- benchmark landing page
- validated result bundles
- external reproduction proof

### Phase D: Write and ship the paper

Tasks:

- P12
- P17
- P18
- P19

Why last:

- The paper should be the packaging of the finished benchmark, not the substitute for unfinished benchmark work.

Deliverables:

- figures and tables
- full paper draft
- arXiv-ready source bundle
- conference submission plan

## Paper Outline

Use this as the default structure for the benchmark paper.

1. Abstract
2. Introduction
3. Related Work
4. Benchmark Scope and Design Goals
5. Engram Dataset Construction
6. Evaluation Protocol
7. Metrics and Judge Validation
8. Experimental Setup
9. Benchmark Results Across Systems
10. Analysis of Failure Modes
11. Limitations and Threats to Validity
12. Release and Reproducibility
13. Conclusion

Appendices:

- prompt templates
- judge rubric
- annotation protocol
- schema definitions
- additional category breakdowns
- command lines and environment settings

## Must-Have Tables

- Related benchmark comparison table
- Dataset composition by category
- Main benchmark results across systems
- Repeated-run variance table
- Human-vs-judge agreement table
- Error / hallucination / abstention breakdown table

## Must-Have Figures

- Benchmark pipeline figure: seed -> settle -> probe -> judge
- Task taxonomy figure
- Dataset composition figure
- Per-category performance figure
- Failure mode figure for temporal reasoning and hallucinations

## Risks That Will Come Up In Review

These are the issues reviewers are most likely to push on.

- "This looks like a vendor benchmark designed around one product."
- "The dataset is synthetic; why should we trust external validity?"
- "Why should we trust the LLM judge?"
- "How stable are these results across runs?"
- "How broad is the evaluated system set?"
- "How does this differ from prior memory benchmarks?"

Each of those objections should have a direct answer in the paper and in the repo.

## Suggested Owners

Use role-based ownership if people are not assigned yet.

- Research Lead: paper narrative, related work, experiments, venue selection
- Benchmark Maintainer: release policy, versioning, benchmark identity, docs consistency
- Engineering: adapters, harness reliability, run orchestration, artifact validation
- Infra: leaderboard, hosting, submission flow
- Product/Design: homepage, visuals, benchmark presentation

## Near-Term Sprint Plan

If you want the shortest path to visible improvement, do these next:

1. Fix benchmark identity:
   - P1
   - P2
   - P3
2. Build the paper evidence core:
   - P5
   - P6
   - P7
3. Make the paper easy to write:
   - P4
   - P13
   - P14
   - P17

## Definition of Done

Engram is at the target standard when an external reader can do all of the following without private context:

- understand what Engram measures and why it matters
- compare it to prior memory benchmarks
- run it on their own system
- trust the scoring and reporting methodology
- cite the benchmark paper
- submit a result to a leaderboard or equivalent public record

At that point, arXiv is useful, but the benchmark will already look professional before the upload.
