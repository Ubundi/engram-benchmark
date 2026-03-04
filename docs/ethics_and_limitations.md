# Ethics and Limitations

## Ethical use guidelines

- Treat benchmark output as diagnostic evidence, not a claim of broad intelligence.
- Avoid presenting synthetic benchmark scores as guarantees for real-world safety.
- Disclose benchmark conditions and limitations whenever publishing results.

## Data and privacy

- Keep benchmark datasets anonymized and non-sensitive.
- Never include credentials, private production logs, or personal identifiers.
- Ensure exported artifacts are safe to store and share before distribution.

## Operational risks

- Memory-augmented agents may answer more often; increased answer rate can increase
  confident errors when retrieval is partial.
- Judge models are imperfect and can introduce scoring bias.
- Runtime variability (latency/timeouts/tool availability) can affect measured quality.

## Benchmark limitations

- Legacy V2 dataset is historical and may not cover all modern agent behaviors.
- Comparison reporting is currently manual.
- Standard-mode adapters (`codex`, `openai`) are scaffolds, not production connectors.

## Responsible reporting standard

Any published benchmark summary should include:
- protocol and condition
- dataset version/path
- scoring rubric
- observed failure rate
- caveats and unresolved limitations
