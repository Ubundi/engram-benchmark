<p align="center">
  <img src="docs/assets/Engram Banner.png" alt="Engram — Measuring what AI agents remember" width="100%">
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/Python-3.10%2B-blue.svg" alt="Python 3.10+"></a>
  <a href="https://github.com/Ubundi/engram-benchmark/actions/workflows/ci.yml"><img src="https://github.com/Ubundi/engram-benchmark/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://huggingface.co/datasets/matthewschramm/engram-v3"><img src="https://img.shields.io/badge/%F0%9F%A4%97-Dataset-yellow.svg" alt="Dataset on HF"></a>
</p>

[Dataset](https://huggingface.co/datasets/matthewschramm/engram-v3) &nbsp;·&nbsp; [Benchmark Spec](docs/benchmark_spec.md) &nbsp;·&nbsp; [Official Release](docs/benchmark_release_v3.md) &nbsp;·&nbsp; [Evaluation Protocol](docs/evaluation_protocol.md) &nbsp;·&nbsp; [Related Work](docs/related_work.md) &nbsp;·&nbsp; [Dataset Card](docs/dataset_card.md) &nbsp;·&nbsp; [Leaderboard Policy](docs/leaderboard.md) &nbsp;·&nbsp; [Integration Guide](docs/integration_guide.md)

---

**Engram** is a runtime benchmark for evaluating long-term memory in AI agents. It measures whether an agent can recover grounded, specific knowledge from prior sessions after the original context window is gone.

Unlike static QA or retrieval-only tests, Engram runs inside the agent runtime itself: it seeds multi-turn conversation histories, waits for memory processing to settle, then probes recall in a fresh session with no haystack in context. Whatever memory architecture the agent actually uses is what gets measured.

Engram is intended to be benchmark-first and system-neutral. The benchmark defines the task format, runtime protocol, scoring rubric, and artifact requirements; systems such as OpenClaw, Cortex, or any third-party agent are evaluated against the same procedure.

## What Engram Measures

Engram is designed to answer three benchmark questions:

- Can an agent retrieve grounded project details from prior sessions?
- Can it preserve rationale, evolution, and cross-session synthesis rather than only isolated facts?
- How does it trade off grounded recall, abstention, and hallucination under a fixed runtime protocol?

Official benchmark artifacts for the current public release:

| Artifact | Value |
|----------|-------|
| Benchmark release | Engram v3.0 (`engram-v3.0`) |
| Tasks | 498 |
| Question types | 9 |
| Primary metric | Mean judge score (0-3) |
| Secondary metrics | Grounded rate, hallucination rate, abstention rate, per-category scores |
| Official protocol | Seed -> Settle -> Probe -> Judge (`engram-runtime-v1`) |

## Official Benchmark Setting

Engram v3.0 has a frozen official public setting for benchmark-comparable runs:

- Split: `v3`
- Judge model: `gpt-4.1-mini`
- Judge passes: `3`
- Judge temperature: `0.3`
- Required artifacts: `metrics.json`, `run_metadata.json`, `predictions.jsonl`, `seed_turns.jsonl`, `probes.jsonl`, `judgments.jsonl`

See [docs/benchmark_release_v3.md](docs/benchmark_release_v3.md) for the full release policy, including condition-specific settle defaults and reporting requirements.

---

## Task Categories

<p align="center">
  <img src="docs/assets/task-categories.png" alt="Engram task category examples" width="100%">
</p>

Engram v3 contains **498 tasks** spanning 9 question types, targeting failure modes that commonly stress long-term agent memory systems:

| Category | Count | What it tests |
|----------|------:|---------------|
| `multi-session` | 79 | Facts requiring information from multiple separate conversations |
| `temporal-reasoning` | 78 | Ordering and recency — distinguishing current from historical facts |
| `cross-agent-memory` | 71 | Knowledge shared or referenced across different agent instances |
| `multi-hop-reasoning` | 68 | Connecting facts via intermediate entities across the session corpus |
| `recurring-pattern` | 54 | Conventions and patterns established repeatedly across sessions |
| `knowledge-update` | 53 | Tracking how facts evolved — decisions reversed or revised over time |
| `single-session-user` | 45 | Direct recall of specifics stated by the user in a single session |
| `single-session-assistant` | 32 | Recall of specifics stated by the assistant in a single session |
| `fact-recall` | 18 | Direct retrieval of a single grounded specific fact |

---

## Dataset

The Engram v3 dataset is hosted on HuggingFace and fetched automatically on first run.

```python
from benchmark.tasks.hf import fetch_engram_dataset
path = fetch_engram_dataset()  # downloads and caches locally
```

| Property | Value |
|----------|-------|
| Tasks | 498 |
| Avg haystack sessions per task | 3.0 |
| Avg haystack turns per task | 30.1 |
| Question types | 9 |
| Format | JSON |
| HuggingFace | [matthewschramm/engram-v3](https://huggingface.co/datasets/matthewschramm/engram-v3) |

The dataset is public — no authentication required.

---

## Quickstart

### 1. Install

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh   # install uv if not already installed
source $HOME/.local/bin/env                        # add uv to PATH
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
```

### 2. Dry run (local stub, no agent required)

```bash
python3 -m benchmark.run --agent local_stub
```

### 3. Run against a live agent

Start your agent server, then point the benchmark at it:

```bash
JUDGE_API_KEY="<key>" python3 -m benchmark.run --agent http://localhost:8080
```

Engram seeds memory sessions into the agent, waits for memory processing to settle, probes recall in a fresh session, and judges responses with an LLM.

See [docs/integration_guide.md](docs/integration_guide.md) for the HTTP server contract, the OpenClaw CLI adapter, and a custom Python adapter option.

### 4. Reference runtime: OpenClaw on EC2

#### Prerequisite: enable systemd user services (fresh instances only)

On a fresh Ubuntu EC2 instance, the `systemd --user` daemon is not started by default. The OpenClaw installer runs as a user-level systemd service, and its final health check will crash if the daemon isn't initialized — even though the binaries installed correctly.

**Before running the OpenClaw installer**, run:

```bash
sudo loginctl enable-linger $USER
```

Then **disconnect and reconnect** your SSH session so PAM generates the correct D-Bus environment variables. After reconnecting, run the OpenClaw installer as normal.

<details>
<summary>Already installed and it crashed?</summary>

If the installer failed with a `systemctl is-enabled unavailable` error, you don't need to wipe the server:

```bash
# Add OpenClaw to PATH
export PATH="/home/ubuntu/.npm-global/bin:$PATH"

# Repair the missing service files
openclaw doctor --repair

# Reload and start the gateway
systemctl --user daemon-reload
openclaw gateway restart
```

</details>

#### Hatching: standardize the agent identity

After installing OpenClaw, the first run opens an interactive TUI where the agent asks you to define its identity. To ensure every benchmark instance starts from the same baseline, use these answers:

| Prompt | Answer |
|--------|--------|
| Onboarding mode | **QuickStart** |
| Model | **anthropic/claude-sonnet-4-6** |
| Channel | **Skip for now** |
| Configure skills? | **Yes** (skip all API key prompts) |
| Enable hooks? | **boot-md, session-memory** |
| How do you want to hatch? | **Hatch in TUI** |

Once the TUI opens and the agent says "Who am I?", send these messages in order:

**Message 1 — Identity:**
> Your name is Benchmark. You are a memory evaluation agent. Your emoji is 📊. Your vibe is neutral and precise — no personality flourishes, just clear and direct responses. Call me Operator.

**Message 2 — Purpose:**
> You will be used to benchmark long-term memory recall. Conversations will be seeded into you, and then you'll be asked questions about them in a fresh session. Answer questions directly from what you remember. If you don't remember, say so honestly. Do not guess or hallucinate.

**Message 3 — Finalize:**
> Update IDENTITY.md and USER.md now. Delete BOOTSTRAP.md when done. Don't modify SOUL.md.

Wait for the agent to confirm it has written the files, then exit the TUI (`Ctrl+C`).

<details>
<summary>Alternative: copy template files directly (skips TUI hatching)</summary>

If you prefer to skip the interactive hatching entirely, copy the benchmark workspace templates into the OpenClaw workspace:

```bash
cp engram-benchmark/workspace-templates/IDENTITY.md ~/.openclaw/workspace/IDENTITY.md
cp engram-benchmark/workspace-templates/USER.md ~/.openclaw/workspace/USER.md
rm -f ~/.openclaw/workspace/BOOTSTRAP.md
```

</details>

#### Step 1: Install dependencies

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
git clone https://github.com/Ubundi/engram-benchmark.git && cd engram-benchmark
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
```

#### Step 2: Dry run

Confirm everything is wired up before starting a real run:

```bash
python3 -m benchmark.run --agent local_stub --dry-run --max-tasks 3
```

#### Step 3: Start a tmux session

Benchmark runs take hours. Always run inside tmux so a disconnected SSH session doesn't kill the process:

```bash
tmux new -s benchmark
```

If you get disconnected, reconnect with `tmux attach -t benchmark`.

#### Step 4: Run a reference baseline

```bash
JUDGE_API_KEY="<your-openai-key>" python3 -m benchmark.run \
  --agent openclaw \
  --agent-id main \
  --condition baseline \
  --output-dir outputs/baseline
```

#### Step 5: Run an additional condition

```bash
JUDGE_API_KEY="<your-openai-key>" python3 -m benchmark.run \
  --agent openclaw \
  --agent-id main \
  --condition cortex \
  --output-dir outputs/cortex
```

#### Step 6: Compare results

```bash
python3 -m benchmark.run \
  --agent local_stub \
  --compare outputs/baseline/<run-id> outputs/cortex/<run-id>
```

The `JUDGE_API_KEY` is an OpenAI API key used by the LLM judge (defaults to `gpt-4.1-mini`). Run IDs are printed at the start of each run and visible as directory names under `outputs/`.

**Useful flags:**

| Flag | Default | Description |
|------|---------|-------------|
| `--condition NAME` | — | Condition (baseline/cortex/clawvault). Sets settle defaults and enables cortex features |
| `--agent-id ID` | — | OpenClaw agent ID (passed to `openclaw agent --agent`) |
| `--settle-seconds N` | auto | Wait between seed and probe (cortex=180s, baseline/clawvault=10s, other=120s) |
| `--judge-passes N` | 3 | LLM judge passes per response (scores averaged) |
| `--judge-concurrency N` | 4 | Parallel judge workers |
| `--flush-sessions` | — | Send `/new` after each seed session to trigger memory hooks |
| `--skip-seed` | — | Skip seeding; probe a pre-seeded agent only |
| `--max-tasks N` | — | Run a subset of N tasks |
| `--judge-model` | `gpt-4.1-mini` | Judge model name |
| `--openclaw-timeout N` | 120 | Timeout in seconds for `openclaw agent` CLI calls |
| `--compare DIR_A DIR_B` | — | Compare two run directories offline (no agent needed) |

---

## Evaluation Protocol

Engram uses a four-phase pipeline:

```
Seed  →  Settle  →  Probe  →  Judge
```

1. **Seed** — Replay haystack sessions into the agent turn-by-turn via the agent runtime
2. **Settle** — Wait for memory indexing and async processing to complete (cortex: 180s, baseline: 10s)
3. **Probe** — Ask evaluation questions in a fresh session with no haystack in context
4. **Judge** — Score responses 0–3 against ground truth using a multi-pass LLM judge

**Scoring rubric:**

| Score | Label | Description |
|------:|-------|-------------|
| 3 | Grounded correct | Cites the specific detail from the haystack |
| 2 | Generic correct | Right direction, missing the specific |
| 1 | Abstained | Honest "I don't have that context" |
| 0 | Hallucinated | Wrong specific stated with confidence |

See [docs/evaluation_protocol.md](docs/evaluation_protocol.md) for full protocol specification.

---

## Reference Results

The table below is a reference example showing how Engram reports results for one evaluated runtime family. It is not the definition of the benchmark, and it should not be read as the only intended use of Engram.

Reference run results on a live OpenClaw agent, reported on March 4, 2026. Scores are on a 0-3 scale.

| Condition | Overall | Rationale | Synthesis | Evolution | Temporal | Grounded | Abstained |
|-----------|--------:|----------:|----------:|----------:|---------:|---------:|----------:|
| Baseline (native memory only) | 1.10 | 1.93 | 0.54 | 1.07 | 0.62 | 4% | 64% |
| Memory-augmented | **1.95** | **3.00** | **2.00** | **2.10** | 0.67 | **48%** | **12%** |
| Δ | **+0.85** | **+1.07** | **+1.46** | **+1.03** | +0.05 | +44pp | −52pp |

Key findings:

- **Rationale recall reaches 3.00** — the reasoning behind decisions is fully preserved with memory augmentation
- **Synthesis** (facts spanning multiple sessions) improves from near-impossible (0.54) to reliable (2.00)
- **Temporal reasoning** (+0.05) is the hardest category — semantic retrieval surfaces historical and current facts without reliable recency ranking
- Memory value **compounds across runs**: a second seeding pass raised overall score from 1.81 to 1.95

Future benchmark reports should include multiple systems or conditions under the same pinned settings. See [docs/leaderboard.md](docs/leaderboard.md) for the submission and governance policy.

---

## Outputs

Each run produces `outputs/<run_id>/` containing:

| File | Contents |
|------|----------|
| `predictions.jsonl` | Per-task agent responses |
| `metrics.json` | Aggregate and per-category scores |
| `run_metadata.json` | Full run configuration, git commit, provenance |
| `seed_turns.jsonl` | Seeded conversation turns with latency |
| `probes.jsonl` | Probe session transcripts with latency |
| `judgments.jsonl` | Per-response judge scores, rationale, and pass scores |
| `report.md` | Human-readable Markdown report with full per-probe detail |

---

## Repository Structure

```
engram/
├── benchmark/           CLI, adapters, task loader, evaluators, writers
│   ├── tasks/           Task loading, HuggingFace fetch, schema validation
│   ├── adapters/        Agent adapters: local_stub, http, openclaw, openai, codex
│   ├── evaluators/      QA, retrieval, and abstention evaluators
│   └── judge.py         Multi-pass LLM judge (0–3 scoring)
├── data/
│   └── splits/          CI sample splits (*.sample.jsonl)
├── docs/                Benchmark spec, evaluation protocol, findings, integration guide
├── leaderboard/         Submission format and leaderboard policy
├── outputs/             Run artifacts (gitignored)
├── scripts/             Dataset generation pipeline
└── tests/               Import, CLI, and schema tests
```

---

## Citation

```bibtex
@software{engram2026,
  title   = {Engram: A Runtime Benchmark for Agent Long-Term Memory Recall},
  author  = {Ubundi},
  year    = {2026},
  url     = {https://github.com/Ubundi/engram-benchmark},
}
```

---

## License

MIT

---

## Built by Ubundi

<a href="https://ubundi.com">
  <img src="docs/assets/ubundi_logo.jpeg" alt="Ubundi" height="36">
</a>

Engram is an open-source project by [Ubundi](https://ubundi.com) — a South African venture studio shaping human-centred AI. Based in Cape Town, Ubundi builds at the intersection of AI capability and African context.

Engram grew out of a need to rigorously measure what memory systems actually retain. Existing benchmarks often emphasize in-context recall; Engram is built to test what survives after the context window is gone. The result is a reproducible runtime evaluation intended for internal benchmarking, public comparison, and eventual community adoption.

> [ubundi.com](https://ubundi.com)
