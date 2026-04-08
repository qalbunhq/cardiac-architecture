"""Validation runtime helpers for reproducible local runs."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

CORE_AGENTS = [
    "oracle",
    "sentinel",
    "scout",
    "quill",
    "compass",
    "forge",
    "bridge",
    "conductor",
]


def _write_if_missing(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(content, encoding="utf-8")


def _touch(path: Path, ts: float):
    os.utime(path, (ts, ts))


def ensure_validation_telemetry() -> dict:
    """Create and refresh deterministic mock telemetry used by validation scripts."""
    repo_root = Path(__file__).resolve().parents[2]
    mock_dir = repo_root / "mock"
    logs_dir = mock_dir / "06_CronLogs"
    signals_dir = mock_dir / "signals"

    os.environ["CARDIAC_LOGS_DIR"] = str(logs_dir)
    os.environ["CARDIAC_SIGNALS_DIR"] = str(signals_dir)

    coherence_module = sys.modules.get("coherence")
    if coherence_module is not None:
        coherence_module.LOGS_DIR = str(logs_dir)
        coherence_module.SIGNALS_DIR = str(signals_dir)

    now = time.time()
    for agent in CORE_AGENTS:
        latest = logs_dir / agent / "latest.md"
        _write_if_missing(
            latest,
            f"# {agent} health\nstatus: ok\nlast_check: validation\n",
        )
        _touch(latest, now)

    nominal_signal = signals_dir / "nominal_signal.json"
    _write_if_missing(
        nominal_signal,
        json.dumps(
            {
                "severity": 2,
                "source": "validation-runtime",
                "status": "nominal",
                "note": "Packaged mock telemetry for reproducible coherence during validation runs.",
            },
            indent=2,
        ),
    )
    _touch(nominal_signal, now)

    return {
        "mock_dir": str(mock_dir),
        "logs_dir": str(logs_dir),
        "signals_dir": str(signals_dir),
    }


def canonical_results_dir() -> Path:
    results_dir = Path(__file__).resolve().parents[1] / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    return results_dir
