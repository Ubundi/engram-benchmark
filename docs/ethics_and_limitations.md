# Ethics and Limitations

## Intended use

Engram is designed for diagnostic evaluation of agent memory systems. Results should be interpreted as evidence of specific memory behaviors under controlled conditions, not as a measure of general agent intelligence or production reliability.

## Known limitations

### Temporal reasoning is unsolved

Engram's hardest category. Semantic retrieval surfaces both historical and current facts without reliable recency ranking. The Cortex condition improves temporal recall by only +0.05, and performance on this category *worsened* between run 1 and run 2 as the knowledge graph grew — more historical context creates more ambiguity. This is an architectural property of semantic retrieval, not a pipeline maturity issue.

### Hallucination rate does not decrease with memory augmentation

The hallucination rate stays at approximately 20% with and without memory augmentation. Augmentation converts abstentions to answers, but some of those answers are wrong when retrieval is partial. Systems that answer more confidently should be evaluated against both grounded accuracy and hallucination rate, not just mean score.

### Synthetic data

The haystack corpus is synthetic, not from real production sessions. Real agent deployments have more noise, topic-hopping, implicit context, and multi-user dynamics. Single-project design (consistent terminology, one tech stack) likely makes retrieval easier than a real multi-workspace deployment.

### Single baseline run

The baseline score derives from a single run. Ideally, baseline would be re-run alongside each augmented condition run to control for environmental differences (agent version, latency, compaction behavior). The improvement margin is large enough that this is unlikely to change the directional conclusion.

### Judge model imperfection

Scoring uses `gpt-4.1-mini` with multi-pass averaging. LLM judges can introduce systematic scoring biases, particularly for abstentions that are confidently phrased or for partially correct answers with good surface form. Multi-pass averaging reduces variance but does not eliminate bias.

## Data and privacy

- Benchmark datasets must remain synthetic and anonymized.
- Do not include credentials, private production logs, or personal identifiers in any dataset or artifact.
- Verify exported run artifacts are safe to share before distribution.

## Operational risks

- Memory-augmented agents answer more often; increased answer rate raises hallucination exposure when retrieval is partial.
- Runtime variability (latency, timeouts, tool availability) can affect measured quality — control for environment stability when comparing conditions.

## Responsible reporting

Any published benchmark summary should include:

- Dataset version (Engram v3)
- Settle seconds and judge configuration
- Scoring rubric
- Per-category scores, not only mean score
- Observed error rate
- Known limitations and confounds
