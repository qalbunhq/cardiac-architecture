"""
Cardiac Architecture — Experiment 2: Agent Failure Recovery
Tests self-organizing routing topology.

Phase A: 200 tasks × 5 passes (normal operation, markers accumulate)
Phase B: Disable the top-performing agent
Phase C: 200 tasks × 5 passes (does routing self-reorganize?)

Validates Patent Claim 30 (self-organizing routing topology)
and the hemispherectomy parallel from the Sutskever analysis.
"""

import json
import os
import sys
import time
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from marker_store import init_db, predict_valence, get_stats, store_marker, get_db
from coherence import compute_coherence, get_routing_recommendation
from validation_runtime import ensure_validation_telemetry, canonical_results_dir

from baseline_router import route as keyword_route

TASKS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tasks.json")

# Agent that will handle the "reassigned" tasks after the primary goes down
# Maps from disabled agent's tasks to the best alternative
FALLBACK_AGENTS = {
    "oracle": "compass",
    "sentinel": "scout",
    "quill": "echo",
    "scout": "sentinel",
    "compass": "oracle",
    "forge": "bridge",
    "echo": "quill",
    "spark": "ember",
}

def find_top_agent(tasks):
    """Find which agent handles the most tasks."""
    agent_counts = {}
    for t in tasks:
        a = t.get("correct_agent", "")
        agent_counts[a] = agent_counts.get(a, 0) + 1
    return max(agent_counts, key=agent_counts.get), agent_counts

def run_pass(tasks, pass_num, is_bootstrap=False, disabled_agent=None):
    """Run one pass. If disabled_agent is set, that agent is 'down'."""
    cardiac_correct = 0
    cardiac_total = 0
    llm_correct = 0
    llm_total = 0
    rerouted_count = 0
    
    for task in tasks:
        task_text = task.get("text", "")
        expected = task.get("correct_agent", "")
        
        # If the expected agent is disabled, the "correct" answer
        # is now the fallback agent
        if disabled_agent and expected == disabled_agent:
            expected = FALLBACK_AGENTS.get(disabled_agent, expected)
        
        coherence, _ = compute_coherence()
        predicted_valence, pred_confidence, best_agent = predict_valence(task_text)
        
        if is_bootstrap:
            route_type = "llm_with_context"
        else:
            route_type = get_routing_recommendation(coherence, predicted_valence, pred_confidence)
        
        # If cardiac routes to disabled agent, it should learn to avoid it
        if route_type == "autonomous" and best_agent:
            if disabled_agent and best_agent == disabled_agent:
                # Agent is down — this is a "failure" that generates a negative marker
                chosen = disabled_agent
                routed_by = "cardiac"
                correct = False
                rerouted_count += 1
                routing_confidence = pred_confidence
            else:
                chosen = best_agent
                routed_by = "cardiac"
                correct = chosen == expected
                routing_confidence = pred_confidence
        else:
            result = keyword_route(task_text)
            if isinstance(result, tuple):
                chosen, llm_confidence = result
            else:
                chosen, llm_confidence = result, 0.6
            routed_by = "llm"
            routing_confidence = float(llm_confidence)
            # LLM router also can't route to disabled agent
            if disabled_agent and chosen == disabled_agent:
                chosen = FALLBACK_AGENTS.get(disabled_agent, chosen)
            correct = chosen == expected
        
        if routed_by == "cardiac":
            cardiac_total += 1
            if correct:
                cardiac_correct += 1
        else:
            llm_total += 1
            if correct:
                llm_correct += 1
        
        # Store marker — if routed to disabled agent, store failure with that agent
        # This is how the cardiac layer LEARNS the agent is down
        outcome = "success" if correct else "failure"
        actual_agent = expected if correct else chosen
        store_marker(
            task_text=task_text,
            agent_used=actual_agent,
            outcome=outcome,
            confidence=routing_confidence,
            surprise=0.5 if (disabled_agent and chosen == disabled_agent) else (0.0 if correct else 0.3),
            effort=0.1 if correct else 0.8,
            coherence=coherence,
            routed_by=routed_by
        )
    
    total = len(tasks)
    total_correct = cardiac_correct + llm_correct
    
    return {
        "pass": pass_num,
        "total": total,
        "overall_accuracy": round(total_correct / total * 100, 1) if total > 0 else 0,
        "cardiac_routed": cardiac_total,
        "cardiac_accuracy": round(cardiac_correct / cardiac_total * 100, 1) if cardiac_total > 0 else 0,
        "llm_routed": llm_total,
        "llm_accuracy": round(llm_correct / llm_total * 100, 1) if llm_total > 0 else 0,
        "cardiac_ratio": round(cardiac_total / total * 100, 1) if total > 0 else 0,
        "markers_total": get_stats()["total_markers"],
        "rerouted_to_disabled": rerouted_count,
    }


def main():
    start_time = time.time()
    ensure_validation_telemetry()
    
    # Fresh start
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "markers.db")
    state_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "coherence_state.json")
    for f in [db_path, state_path]:
        if os.path.exists(f):
            os.remove(f)
    init_db()
    
    with open(TASKS_FILE) as f:
        tasks = json.load(f)
    
    top_agent, agent_counts = find_top_agent(tasks)
    
    print(f"\n🫀 CARDIAC ARCHITECTURE — Experiment 2: Agent Failure Recovery")
    print(f"   Tasks per pass: {len(tasks)}")
    print(f"   Agent distribution: {json.dumps(agent_counts, indent=6)}")
    print(f"   Top agent: {top_agent} ({agent_counts[top_agent]} tasks)")
    print(f"   Will disable: {top_agent} after Phase A")
    print(f"   Fallback: {FALLBACK_AGENTS.get(top_agent, 'none')}")
    print(f"   ══════════════════════════════════════════════════════")
    
    all_results = []
    
    # Phase A: Normal operation (5 passes)
    print(f"\n   PHASE A: Normal Operation (5 passes)")
    print(f"   ──────────────────────────────────────")
    for p in range(1, 6):
        is_bootstrap = (p == 1)
        result = run_pass(tasks, p, is_bootstrap=is_bootstrap)
        result["phase"] = "A_normal"
        all_results.append(result)
        
        phase = "BOOTSTRAP" if is_bootstrap else "CARDIAC"
        print(f"   Pass {p:>2} [{phase:>9}] | "
              f"Cardiac: {result['cardiac_ratio']:>5.1f}% (acc {result['cardiac_accuracy']:>5.1f}%) | "
              f"Overall: {result['overall_accuracy']:>5.1f}% | "
              f"Markers: {result['markers_total']:>5}")
    
    # Phase B: Disable top agent
    print(f"\n   ⚡ DISABLING AGENT: {top_agent}")
    print(f"   Tasks that targeted {top_agent}: {agent_counts[top_agent]}")
    print(f"   Fallback agent: {FALLBACK_AGENTS.get(top_agent, 'none')}")
    
    # Phase C: Recovery (5 passes with disabled agent)
    print(f"\n   PHASE B: Recovery After Agent Failure (5 passes)")
    print(f"   ──────────────────────────────────────────────────")
    for p in range(6, 11):
        result = run_pass(tasks, p, disabled_agent=top_agent)
        result["phase"] = "B_recovery"
        result["disabled_agent"] = top_agent
        all_results.append(result)
        
        print(f"   Pass {p:>2} [RECOVERY ] | "
              f"Cardiac: {result['cardiac_ratio']:>5.1f}% (acc {result['cardiac_accuracy']:>5.1f}%) | "
              f"Overall: {result['overall_accuracy']:>5.1f}% | "
              f"Markers: {result['markers_total']:>5} | "
              f"Sent to disabled: {result['rerouted_to_disabled']}")
    
    elapsed = time.time() - start_time
    
    # Summary
    print(f"\n   ══════════════════════════════════════════════════════")
    print(f"   🫀 AGENT FAILURE RECOVERY RESULTS ({elapsed:.0f}s total)")
    print(f"   ══════════════════════════════════════════════════════")
    print(f"   {'Pass':<6} {'Phase':<12} {'Cardiac%':>10} {'Cardiac Acc':>12} {'Overall':>10} {'→Disabled':>10}")
    print(f"   {'─'*62}")
    for r in all_results:
        phase_label = "Normal" if r.get("phase") == "A_normal" else "Recovery"
        disabled_count = r.get("rerouted_to_disabled", 0)
        print(f"   {r['pass']:<6} {phase_label:<12} {r['cardiac_ratio']:>9.1f}% {r['cardiac_accuracy']:>10.1f}% {r['overall_accuracy']:>9.1f}% {disabled_count:>9}")
    
    # Recovery analysis
    phase_a_final = all_results[4]
    phase_b_first = all_results[5]
    phase_b_last = all_results[-1]
    
    print(f"\n   📊 RECOVERY ANALYSIS:")
    print(f"      Pre-failure accuracy:     {phase_a_final['overall_accuracy']}%")
    print(f"      Immediate post-failure:   {phase_b_first['overall_accuracy']}%")
    print(f"      After 5 recovery passes:  {phase_b_last['overall_accuracy']}%")
    print(f"      Misroutes to disabled (first): {phase_b_first.get('rerouted_to_disabled', 0)}")
    print(f"      Misroutes to disabled (last):  {phase_b_last.get('rerouted_to_disabled', 0)}")
    
    if phase_b_last.get('rerouted_to_disabled', 0) < phase_b_first.get('rerouted_to_disabled', 0):
        print(f"      ✅ SELF-HEALING CONFIRMED: System learned to avoid disabled agent")
    elif phase_b_last.get('rerouted_to_disabled', 0) == 0:
        print(f"      ✅ SELF-HEALING CONFIRMED: Zero misroutes by final pass")
    else:
        print(f"      ⚠️ PARTIAL RECOVERY: System still routing to disabled agent")
    
    # Save
    results_dir = str(canonical_results_dir())
    results_path = os.path.join(results_dir, "agent_failure_results.json")
    with open(results_path, "w") as f:
        json.dump({
            "experiment": "agent_failure_recovery",
            "disabled_agent": top_agent,
            "fallback_agent": FALLBACK_AGENTS.get(top_agent),
            "runtime_seconds": round(elapsed, 1),
            "results": all_results,
        }, f, indent=2)
    
    print(f"\n   Results saved to {results_path}")

if __name__ == "__main__":
    main()
