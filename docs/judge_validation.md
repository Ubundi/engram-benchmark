# Judge Validation Template

This document is a fill-in template for validating the Engram LLM judge against human annotations on a held-out sample.

## Goal

Show that the benchmark's `0-3` scoring rubric is reliable enough for publication by measuring:

- human-human agreement
- judge-human agreement
- where disagreements concentrate

## Study Status

| Item | Status | Notes |
|---|---|---|
| Held-out sample selected | Pending | `TBD` |
| Annotation instructions finalized | Pending | `TBD` |
| Human annotation complete | Pending | `TBD` |
| Inter-annotator agreement computed | Pending | `TBD` |
| Judge-human agreement computed | Pending | `TBD` |
| Appendix text drafted | Pending | `TBD` |

## Scoring Rubric

Use the same rubric already defined for benchmark scoring.

| Score | Label | Definition |
|---:|---|---|
| 3 | Grounded correct | Response contains the specific project detail from the ground truth |
| 2 | Generic correct | Response is directionally correct but lacks the specific detail |
| 1 | Abstained | Response says it lacks context or otherwise does not answer |
| 0 | Hallucinated | Response gives a specific but wrong claim |

Annotators should score the agent response only against:

- question
- ground-truth answer
- agent response

Annotators should not see the model name, condition label, or benchmark hypothesis.

## Sample Selection Template

### Planned sample

| Field | Value |
|---|---|
| Sample source | `TBD` |
| Sample size | `TBD` |
| Conditions covered | `TBD` |
| Categories covered | `TBD` |
| Selection method | `TBD` |
| Excluded examples | `TBD` |

### Selection notes

- Prefer a held-out sample that is not used to tune the judge prompt.
- Include examples from the hardest categories, especially `temporal-reasoning`.
- Include examples across all main conditions, not only the best-performing system.
- Include clear positives, clear abstentions, and ambiguous borderline cases.

### Sample composition table

| Slice | Target count | Actual count | Notes |
|---|---:|---:|---|
| `temporal-reasoning` | `TBD` | `TBD` | `TBD` |
| `multi-session` | `TBD` | `TBD` | `TBD` |
| `knowledge-update` | `TBD` | `TBD` | `TBD` |
| `cross-agent-memory` | `TBD` | `TBD` | `TBD` |
| `other categories` | `TBD` | `TBD` | `TBD` |
| Total | `TBD` | `TBD` | `TBD` |

## Annotation Protocol Template

### Annotator pool

| Field | Value |
|---|---|
| Number of annotators | `TBD` |
| Annotator background | `TBD` |
| Training procedure | `TBD` |
| Pilot round completed | `TBD` |
| Adjudication used | `TBD` |

### Instructions to annotators

Use this block as the starting point for the human annotation sheet:

> You will read a benchmark question, the benchmark ground truth, and an agent response. Assign one label from `0, 1, 2, 3` using the Engram rubric. Judge whether the response contains the specific factual content required by the ground truth, not whether it sounds fluent or plausible. If the response refuses, says it lacks memory, or otherwise avoids answering, use `1`. If it contains a wrong specific claim, use `0`. If it is broadly right but misses the key specific detail, use `2`. If it contains the required specific detail, use `3`.

### Annotation fields

Each annotated example should capture:

- `example_id`
- `task_id`
- `condition`
- `question_type`
- `question`
- `ground_truth`
- `agent_response`
- `annotator_id`
- `human_score`
- `optional_notes`

### Annotation log template

| Example ID | Task ID | Condition | Category | Annotator | Human score | Notes |
|---|---|---|---|---|---:|---|
| `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` |
| `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` |
| `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` |

## Agreement Metrics Template

Use at least one human-human agreement measure and one judge-human agreement measure.

### Planned metrics

| Comparison | Metric | Value | Notes |
|---|---|---|---|
| Human vs human | `TBD` | `TBD` | `TBD` |
| Judge vs majority-human label | `TBD` | `TBD` | `TBD` |
| Judge vs adjudicated human label | `TBD` | `TBD` | `TBD` |
| Judge vs human, exact-match rate | `TBD` | `TBD` | `TBD` |
| Judge vs human, within-1 agreement | `TBD` | `TBD` | `TBD` |

Recommended practice:

- Use a chance-corrected agreement metric for ordinal labels.
- Report exact agreement and within-1 agreement in addition to the primary statistic.
- If adjudication is used, report both pre-adjudication and post-adjudication comparisons.

## Main Results Template

### Human-human agreement

| Metric | Value | Interpretation |
|---|---|---|
| `TBD` | `TBD` | `TBD` |
| Exact agreement | `TBD` | `TBD` |
| Within-1 agreement | `TBD` | `TBD` |

### Judge-human agreement

| Metric | Value | Interpretation |
|---|---|---|
| `TBD` | `TBD` | `TBD` |
| Exact agreement | `TBD` | `TBD` |
| Within-1 agreement | `TBD` | `TBD` |

### Confusion table template

Rows are majority-human labels. Columns are judge labels.

| Human \ Judge | 0 | 1 | 2 | 3 |
|---|---:|---:|---:|---:|
| 0 | `TBD` | `TBD` | `TBD` | `TBD` |
| 1 | `TBD` | `TBD` | `TBD` | `TBD` |
| 2 | `TBD` | `TBD` | `TBD` | `TBD` |
| 3 | `TBD` | `TBD` | `TBD` | `TBD` |

## Disagreement Analysis Template

Summarize where the judge diverges from humans.

### Planned slices

| Slice | Judge-human issue to inspect | Notes |
|---|---|---|
| `temporal-reasoning` | borderline `2` vs `3` | `TBD` |
| `knowledge-update` | stale fact counted as correct | `TBD` |
| `abstentions` | polite refusal interpreted as generic answer | `TBD` |
| `hallucinations` | plausible but unsupported specifics | `TBD` |

### Example disagreements

| Example ID | Human label | Judge label | Category | Short explanation |
|---|---:|---:|---|---|
| `TBD` | `TBD` | `TBD` | `TBD` | `TBD` |
| `TBD` | `TBD` | `TBD` | `TBD` | `TBD` |
| `TBD` | `TBD` | `TBD` | `TBD` | `TBD` |

## Threats To Validity Template

Fill this section after the study is complete.

- `TBD`: Sample size limitations
- `TBD`: Whether annotators had benchmark-specific training
- `TBD`: Whether some categories were underrepresented
- `TBD`: Whether the judge model being validated is the same model family used elsewhere in the benchmark pipeline
- `TBD`: Whether adjudication changed conclusions materially

## Appendix Text Template

Use this paragraph in the paper appendix after filling the placeholders:

> We validated the Engram judge on a held-out sample of `TBD` benchmark responses spanning `TBD` conditions and `TBD` question categories. Each example was independently labeled by `TBD` human annotators using the benchmark's `0-3` rubric. Human-human agreement was `TBD`, and agreement between the LLM judge and the `TBD` human reference label was `TBD`. Most disagreements occurred in `TBD`, especially borderline cases between scores `TBD` and `TBD`.

## Repo Deliverables

Before marking this work complete, the repo should contain:

- annotation protocol
- sample definition
- agreement summary table
- confusion matrix
- disagreement examples
- appendix-ready writeup

## Completion Checklist

- [ ] Held-out sample selected and documented
- [ ] Human annotation instructions finalized
- [ ] Annotation complete for all sampled examples
- [ ] Human-human agreement computed
- [ ] Judge-human agreement computed
- [ ] Disagreement analysis filled in
- [ ] Appendix text replaced with actual study results
