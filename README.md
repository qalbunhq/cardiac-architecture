# Cardiac Architecture

Cardiac Architecture is a pre-inference routing layer for multi-agent AI systems that routes decisions from accumulated operational experience rather than LLM reasoning. It makes multi-agent orchestration experience-driven — routing compounds over time instead of remaining stateless, reducing inference load and improving system reliability as marker density grows.

## About

Cardiac Architecture is developed by Mohamadou Fadil and commercialized through Qalbun. The reference implementation in this repository is open-source under the MIT License. For commercial licensing, production-grade deployments, or shadow mode trials, contact: contact@qalbun.com.

## Why this matters

Most multi-agent stacks are LLM-centric at decision time. That creates three structural bottlenecks:

- recurring inference cost on every routing decision, including familiar ones
- avoidable latency from full reasoning passes on recognized tasks
- no structural experiential learning loop — systems execute tasks but do not compound from use

## Three mechanisms

**1. Coherence monitoring**
Continuously scores runtime system health. Determines whether autonomous routing is safe before committing to a cardiac decision.

**2. Marker library (valence-tagged experiential memory)**
Stores task signatures linked to outcome-weighted `valence` scores. Enables retrieval of similar prior situations and powers an *as-if body loop* that predicts outcomes before execution.

**3. Pre-cognitive routing**
Routes before LLM reasoning when coherence and confidence pass threshold. Escalates to deliberative routing when novelty or risk increases. Each decision writes a new marker — the system learns continuously from runtime.

## Validated results

Across 4,000 routing decisions (20 passes × 200 tasks):

| Result | Value |
|---|---|
| Cardiac routing plateau | **92.5%** — reached and maintained from pass 10 through pass 20 |
| Cardiac decision accuracy | **100%** on self-selected cardiac decisions at plateau |
| Overall system accuracy | **94.5%** maintained throughout plateau phase |
| Agent failure recovery | **One-pass** — system reorganized in a single pass after agent disable |
| Marker transplantation | **~84% cardiac routing on pass 1** vs 0% cold-start |
| Adversarial robustness | **No accuracy degradation** under 4.8% poison concentration |

Key qualitative findings:
- Bootstrap phase (pass 1) is LLM-heavy by design. Cardiac routing emerges and compounds across subsequent passes.
- After agent failure, the system experiences a temporary drop, then self-reorganizes to higher accuracy than pre-failure baseline in the following pass.
- Transplanted markers from a donor fleet allow a new fleet to skip the bootstrap period. Cold-start elimination is immediate.
- Cross-domain transfer shows a measurable early signal (14.6% head start vs 0% cold-start) but converges more slowly than in-domain learning — consistent with partial structural overlap.

Exact percentages vary slightly across environments due to telemetry timestamp seeding. Qualitative behavior (emergence, compounding, recovery, transfer) reproduces deterministically.

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

## Thesis and paper

The full architecture thesis is in [`paper/`](paper/). It covers the biological grounding, formal routing logic, experiment design, and discussion of failure modes.

An arXiv preprint is forthcoming. The `CITATION.cff` in this repository is the canonical citation until then.

## Reproduce the validation suite

### Environment setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run all five experiments

```bash
python experiments/scripts/experiment_plateau.py
python experiments/scripts/experiment_agent_failure.py
python experiments/scripts/experiment_transplant.py
python experiments/scripts/experiment_adversarial.py
python experiments/scripts/experiment_cross_domain.py
```

All scripts use packaged mock telemetry from `mock/`. Results write to `experiments/results/`. No external API keys or services required — the full suite runs on Python standard library.

### What to expect

- Pass 1 is LLM-only (bootstrap). Cardiac routing emerges across subsequent passes.
- Agent failure: drop at failure pass, then single-pass recovery to a new plateau.
- Transplant fleet: immediate high cardiac routing from pass 1. Cold-start fleet starts at 0%.
- Cross-domain: early transfer signal but weaker final convergence compared to in-domain learning.

## Repository structure

```text
cardiac-architecture/
├── README.md
├── LICENSE
├── CITATION.cff
├── CONTRIBUTING.md
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
    │   ├── cardiac_router.py
    │   ├── coherence.py
    │   ├── marker_store.py
    │   ├── baseline_router.py
    │   ├── best_router.py
    │   ├── validation_runtime.py
    │   ├── experiment_plateau.py
    │   ├── experiment_agent_failure.py
    │   ├── experiment_transplant.py
    │   ├── experiment_adversarial.py
    │   └── experiment_cross_domain.py
    └── results/
```

## Reference implementation

This is a reference implementation of Cardiac Architecture for reproducible validation. Production deployments benefit from additional optimization, scaling, observability, and infrastructure hardening.

The baseline router (`baseline_router.py`) provides an optional model-based routing backend. Provider and model selection are configurable via environment variables, maintaining an architecture-first, provider-neutral design.

## License

MIT. See [`LICENSE`](LICENSE).

## Citation

If you use this work, please cite the forthcoming arXiv paper (link to be added upon publication) or use [`CITATION.cff`](CITATION.cff) in this repository.
