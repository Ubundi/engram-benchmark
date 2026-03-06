# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly.

**Do not open a public GitHub issue for security vulnerabilities.**

Instead, email **security@ubundi.com** with:

- A description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

We will acknowledge your report within 48 hours and aim to provide a fix or mitigation plan within 7 days.

## Scope

This policy covers:

- The benchmark harness code (`benchmark/`)
- Dataset generation and validation scripts (`scripts/`)
- CI/CD workflows (`.github/`)
- Published dataset artifacts on HuggingFace

## Known Considerations

- The benchmark dataset is **synthetic** — it does not contain real personal data. An anonymization pass (`scripts/anonymize_dataset.py`) replaced all real-world entities with fictive equivalents.
- HuggingFace dataset access requires authentication. Do not commit `HF_TOKEN` values to the repository.
- The `JUDGE_API_KEY` environment variable is used for LLM judge API calls. Treat it as a secret.

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |
