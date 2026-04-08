# Cardiac Architecture: A New Control Layer for Multi-Agent AI Systems

Cardiac Architecture introduces a new control layer for multi-agent AI systems.
Instead of routing every decision through an LLM, it adds a pre-cognitive layer that routes from accumulated operational experience.
This shifts multi-agent orchestration from stateless reasoning to compounding system intelligence.
The result is lower inference load, faster routing, and measurable adaptation over deployment time.

## Why this matters

Most multi-agent stacks are still LLM-centric at decision time.
That creates three bottlenecks:
- high recurring inference cost
- avoidable latency from full reasoning passes
- no structural experiential learning loop

In short, many systems execute tasks, but do not materially improve from use.

## What this architecture does

Cardiac Architecture adds three mechanisms:

1. **Coherence monitoring**
   - continuously scores runtime system health (`coherence`)
   - determines whether autonomous routing is safe

2. **Marker library (valence-tagged experiential memory)**
   - stores task signatures and outcome-linked `valence`
   - enables retrieval of similar prior situations
   - powers the **as-if body loop** for predicted outcomes before execution

3. **Pre-cognitive routing**
   - routes before LLM reasoning when coherence and confidence allow
   - escalates to deliberative routing when novelty/risk increases

## Key validation results

- **92.5% cardiac routing first achieved at pass 9 and maintained through pass 20** (pre-cognitive layer handling)
- **High accuracy on self-selected tasks** under learned routing conditions
- **One-pass self-reorganization after agent failure**
- **Compounding performance over time** as marker density increases

## How it works

```text
Task arrives
  -> Coherence check (system state)
  -> Marker library query (similar prior tasks + valence)
  -> Pre-cognitive routing decision
      -> Autonomous route when conditions pass
      -> Escalate to LLM-assisted routing otherwise
  -> Execute
  -> Write new marker (experience update)
```

## Repository structure

```text
github-upload-package/
├── README.md
├── LICENSE
├── CITATION.cff
├── .gitignore
├── requirements.txt
├── paper/
│   ├── Cardiac_Architecture_Thesis.md
│   └── Cardiac_Architecture_Thesis.pdf
├── docs/
│   ├── ARCHITECTURE.md
│   └── EXPERIMENTS.md
├── mock/
│   ├── 06_CronLogs/       # Packaged telemetry for reproducible coherence
│   └── signals/
└── experiments/
    ├── tasks.json
    ├── scripts/
    │   ├── best_router.py
    │   ├── cardiac_router.py
    │   ├── coherence.py
    │   ├── baseline_router.py
    │   ├── validation_runtime.py
    │   ├── experiment_plateau.py
    │   ├── experiment_agent_failure.py
    │   ├── experiment_transplant.py
    │   ├── experiment_adversarial.py
    │   ├── experiment_cross_domain.py
    │   └── marker_store.py
    └── results/
        ├── plateau_results.json
        ├── agent_failure_results.json
        ├── transplant_results.json
        ├── adversarial_results.json
        └── cross_domain_results.json
```

## Reference implementation

This repository is a **reference implementation** of Cardiac Architecture for reproducible multi-agent validation.
Production deployments may include additional optimization, scaling, observability, and infrastructure hardening.

The baseline router (`baseline_router.py`) provides an optional model-based routing backend. Provider and model selection are configurable via environment variables, maintaining architecture-first, provider-neutral design.

## Future work and extensions

- distributed marker library systems
- real-time / streaming coherence pipelines
- enterprise orchestration layer for multi-tenant deployments
- cross-domain marker transfer at production scale

## Reproducibility

### Environment setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run validation suite

```bash
python experiments/scripts/experiment_plateau.py
python experiments/scripts/experiment_agent_failure.py
python experiments/scripts/experiment_transplant.py
python experiments/scripts/experiment_adversarial.py
python experiments/scripts/experiment_cross_domain.py
```

### Validation runtime behavior

- Validation scripts use packaged mock telemetry in `mock/`.
- The runtime refreshes telemetry timestamps each run to keep coherence deterministic in fresh and repeated local runs.
- Validation outputs are written to the single canonical directory: `experiments/results/`.

### What to expect

- Pass 1 starts LLM-heavy (bootstrap), then cardiac routing should emerge across subsequent passes.
- Agent-failure runs should show a temporary drop and then recovery.
- Transplant runs should show faster cardiac activation than cold start.
- Cross-domain transfer can vary by task distribution and is expected to be weaker than in-domain learning.

Exact percentages may vary slightly across environments, but qualitative behavior (emergence, compounding, recovery, and transfer patterns) should reproduce.

The repository is a reference implementation of the architecture, and the validation setup is intentionally deterministic enough for reproducible local checks.

## Citation

Use `CITATION.cff`.