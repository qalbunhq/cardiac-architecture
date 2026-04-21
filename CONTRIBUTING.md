# Contributing to Cardiac Architecture

Community contributions are welcome.

## What to contribute

- Bug fixes in experiment scripts or core routing logic
- Improvements to reproducibility or test coverage
- Documentation clarifications
- Additional benchmark tasks or evaluation scenarios
- Integrations with other orchestration frameworks

## How to contribute

1. Fork the repository and create a branch from `main`
2. Make your changes with clear, focused commits
3. Open a pull request with a description of what changed and why
4. Allow time for review — we aim to respond within a few business days

## Core architectural changes

Changes that modify the fundamental routing architecture — the coherence model, marker library structure, valence scoring, or the pre-cognitive routing decision boundary — should be discussed before implementation. Open an issue first describing the proposed change and the motivation. Core architectural decisions are coordinated with Qalbun to maintain the integrity of the reference implementation.

## Standards

- Keep dependencies minimal. The validation suite runs on Python standard library by design.
- Experiment scripts should remain reproducible from a fresh clone using mock telemetry.
- No changes to `mock/` data that would alter the qualitative behavior of the validation suite.

## Contact

For production deployments, commercial licensing, or architectural collaboration: contact@qalbun.com
