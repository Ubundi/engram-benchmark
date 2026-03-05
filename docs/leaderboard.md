# Leaderboard Policy

## Current status

A public automated leaderboard is not yet active. This policy defines submission and
review expectations for future activation and for private internal leaderboards.

## Eligibility

A submission is eligible only if it includes:
- full run artifacts
- benchmark metadata (agent version, run config, timestamp)
- reproducible command sequence
- dataset reference used for evaluation

## Ranking policy

Primary metric:
- `v2.mean_score`

Secondary metrics for tie-break and diagnosis:
- per-category mean scores
- hallucination count (derived from score `0`)
- error count

## Governance

- Submissions may be rejected if artifacts are incomplete or unreproducible.
- Maintainers may request reruns with pinned settings for verification.
- Any corrected or superseded result must preserve historical traceability.
