"""
Cardiac Architecture — Coherence Score (ICNS Equivalent)
Implements Mechanism 1: The Autonomous Sensing Layer

Computes a real-time coherence score (0.0-1.0) from system telemetry.
Analogous to Heart Rate Variability (HRV) in the biological system.

The coherence score answers: "How well is this system doing right now?"
"""

import os
import json
import time
import glob
from typing import Dict, Tuple
from datetime import datetime, timezone, timedelta

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOGS_DIR = os.getenv("CARDIAC_LOGS_DIR", os.path.join(BASE_DIR, "mock", "06_CronLogs"))
SIGNALS_DIR = os.getenv("CARDIAC_SIGNALS_DIR", os.path.join(BASE_DIR, "mock", "signals"))
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "coherence_state.json")

# Coherence thresholds (from thesis Section V)
HIGH_COHERENCE = 0.65   # Route autonomously (tuned for production fleet baseline ~0.68)
LOW_COHERENCE = 0.3     # Escalate to highest capability
# Between 0.3 and 0.7 = invoke LLM with coherence context

def _load_state() -> Dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"history": [], "baseline": 0.5, "last_update": 0}

def _save_state(state: Dict):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def _agent_freshness_score() -> float:
    """Score based on how many core agents have recent logs.
    Fresh agents = high coherence. Stale agents = low coherence."""
    if not os.path.exists(LOGS_DIR):
        return 0.5
    core_agents = ["oracle", "sentinel", "scout", "quill", "compass", 
                   "forge", "bridge", "conductor"]
    fresh_count = 0
    now = time.time()
    
    for agent in core_agents:
        log_path = os.path.join(LOGS_DIR, agent, "latest.md")
        if os.path.exists(log_path):
            age_hours = (now - os.path.getmtime(log_path)) / 3600
            if age_hours < 6:  # Fresh = updated within 6 hours
                fresh_count += 1
            elif age_hours < 24:  # Warm = updated within 24 hours
                fresh_count += 0.5
    
    return fresh_count / len(core_agents)

def _signal_health_score() -> float:
    """Score based on recent signal quality.
    High-severity signals that are unaddressed = low coherence."""
    if not os.path.exists(SIGNALS_DIR):
        return 0.5  # No signal data = neutral
    
    signals = glob.glob(os.path.join(SIGNALS_DIR, "*.json"))
    if not signals:
        return 0.7  # No signals = probably fine
    
    now = time.time()
    recent_signals = 0
    high_severity = 0
    
    for sig_path in signals:
        try:
            age_hours = (now - os.path.getmtime(sig_path)) / 3600
            if age_hours < 12:
                recent_signals += 1
                with open(sig_path) as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        severity = data.get("severity", data.get("score", 5))
                        if isinstance(severity, (int, float)) and severity >= 8:
                            high_severity += 1
        except (json.JSONDecodeError, OSError):
            continue
    
    if high_severity > 2:
        return 0.3  # Multiple high-severity signals
    elif high_severity > 0:
        return 0.5
    elif recent_signals > 0:
        return 0.7
    return 0.8

def _error_rate_score() -> float:
    """Score based on recent cron job error rate.
    Check the last 10 cron log files for error indicators."""
    error_indicators = ["error", "failed", "exception", "traceback", "denied"]
    
    log_files = sorted(glob.glob(os.path.join(LOGS_DIR, "*/latest.md")),
                       key=os.path.getmtime, reverse=True)[:10]
    
    if not log_files:
        return 0.5
    
    error_count = 0
    for lf in log_files:
        try:
            with open(lf) as f:
                content = f.read(2000).lower()
                if any(ind in content for ind in error_indicators):
                    error_count += 1
        except OSError:
            continue
    
    error_rate = error_count / len(log_files)
    return max(0.0, 1.0 - error_rate * 1.5)

def compute_coherence() -> Tuple[float, Dict]:
    """Compute the current system coherence score.
    
    Returns: (coherence_score, component_breakdown)
    
    This runs in <10ms as specified in the thesis architectural constraints.
    """
    start = time.time()
    
    freshness = _agent_freshness_score()
    signals = _signal_health_score()
    errors = _error_rate_score()
    
    # Weighted combination
    coherence = (freshness * 0.4 + signals * 0.3 + errors * 0.3)
    coherence = max(0.0, min(1.0, coherence))
    
    # Update rolling history
    state = _load_state()
    state["history"].append({
        "timestamp": time.time(),
        "coherence": coherence,
        "components": {
            "freshness": round(freshness, 3),
            "signals": round(signals, 3),
            "errors": round(errors, 3)
        }
    })
    # Keep last 100 readings
    state["history"] = state["history"][-100:]
    
    # Update rolling baseline (weekly)
    if state["history"]:
        recent = [h["coherence"] for h in state["history"][-20:]]
        state["baseline"] = sum(recent) / len(recent)
    
    state["last_update"] = time.time()
    _save_state(state)
    
    elapsed_ms = (time.time() - start) * 1000
    
    components = {
        "freshness": round(freshness, 3),
        "signals": round(signals, 3),
        "errors": round(errors, 3),
        "baseline": round(state["baseline"], 3),
        "elapsed_ms": round(elapsed_ms, 1)
    }
    
    return round(coherence, 3), components

def get_routing_recommendation(coherence: float, predicted_valence: float, 
                                prediction_confidence: float) -> str:
    """The cardiac routing decision (thesis Section V / Section X).
    
    Returns: 'autonomous' | 'llm_with_context' | 'escalate'
    """
    if coherence > HIGH_COHERENCE and prediction_confidence > 0.7:
        if predicted_valence > 0.6:
            return "autonomous"  # Route without LLM
        elif predicted_valence < 0.3:
            return "escalate"  # Negative prediction, escalate
    
    if coherence < LOW_COHERENCE:
        return "escalate"  # System stressed, escalate everything
    
    return "llm_with_context"  # Default: invoke LLM with cardiac context


if __name__ == "__main__":
    coherence, components = compute_coherence()
    print(f"\n🫀 System Coherence: {coherence}")
    print(f"   Freshness:  {components['freshness']}")
    print(f"   Signals:    {components['signals']}")
    print(f"   Errors:     {components['errors']}")
    print(f"   Baseline:   {components['baseline']}")
    print(f"   Computed in: {components['elapsed_ms']}ms")
    
    # Example routing decisions
    for v, c in [(0.8, 0.9), (0.2, 0.8), (0.5, 0.4)]:
        rec = get_routing_recommendation(coherence, v, c)
        print(f"   Valence={v}, Conf={c} → {rec}")
