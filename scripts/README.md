# Scripts

Utility and pipeline scripts for dataset generation, validation, and maintenance.

## Dataset Generation Pipeline

These scripts produce the Engram v3 benchmark dataset. They are run once (or when regenerating the dataset) and are **not** needed for running the benchmark.

```
config.py → entity_registry.py → session_generator.py → question_generator.py → generate_v3.py
                                                                                       ↓
                                                                              anonymize_dataset.py
                                                                                       ↓
                                                                              validate_v3.py
                                                                                       ↓
                                                                           create_test_subset.py
```

| Script | Purpose | When to use |
|--------|---------|-------------|
| `config.py` | Shared configuration: paths, targets, thresholds, weekly schedules | Imported by other scripts — not run directly |
| `entity_registry.py` | Tracks entities, facts, and changes across sessions for grounded question generation | Imported by `generate_v3.py` |
| `session_generator.py` | Generates the ~300-session conversation corpus via Claude CLI | Called by `generate_v3.py` |
| `question_generator.py` | Generates 500 questions across 8+ types using the entity registry and sessions | Called by `generate_v3.py` |
| `llm_client.py` | Thin wrapper around `claude -p` CLI for text generation | Imported by generators |
| `generate_v3.py` | **Main orchestrator** — runs the full generation pipeline end-to-end | `python -m scripts.generate_v3` |

## Post-Generation

| Script | Purpose | When to use |
|--------|---------|-------------|
| `anonymize_dataset.py` | Replaces real entities with fictive equivalents | After generation, before publishing |
| `validate_v3.py` | Runs 10 automated validation checks on the dataset | After any dataset modification: `python -m scripts.validate_v3 data/raw/engram-v3.json` |
| `create_test_subset.py` | Creates a proportionally sampled 50-question test split | After validating the full dataset |

## CI / Maintenance

| Script | Purpose | When to use |
|--------|---------|-------------|
| `ci_validate_hf_dataset.py` | Fetches dataset from HuggingFace and validates it | Run by CI — ensures published dataset passes all checks |

## Typical Workflows

**Regenerate the full dataset:**
```bash
python -m scripts.generate_v3
python scripts/anonymize_dataset.py
python -m scripts.validate_v3 data/raw/engram-v3.json
python scripts/create_test_subset.py
```

**Validate an existing dataset:**
```bash
python -m scripts.validate_v3 data/raw/engram-v3.json
```

**Regenerate only the test subset:**
```bash
python scripts/create_test_subset.py
```
