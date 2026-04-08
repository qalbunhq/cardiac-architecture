"""
Cardiac Architecture — Experiment 5: Cross-Domain Transfer
Tests whether markers from one task domain transfer to another.

Domain A: "Operations" agents (oracle, forge, sentinel, compass) — data/analysis/infra tasks
Domain B: "Creative" agents (quill, ember, scout, echo/conductor) — content/outreach/research tasks

Phase 1: Train markers ONLY on Domain A tasks (5 passes)
Phase 2: Test on Domain B tasks — do Domain A markers help at all?
Phase 3: Control — cold start on Domain B (no prior markers)

Validates Patent Claim 19 (cross-domain transfer)
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from marker_store import init_db, predict_valence, get_stats, store_marker, get_db
from coherence import compute_coherence, get_routing_recommendation
from validation_runtime import ensure_validation_telemetry, canonical_results_dir

from baseline_router import route as keyword_route

TASKS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tasks.json")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Domain split
DOMAIN_A_AGENTS = {"oracle", "forge", "sentinel", "compass"}  # Operations/Analysis
DOMAIN_B_AGENTS = {"quill", "ember", "scout", "conductor"}     # Creative/Outreach


def fresh_start():
    db_path = os.path.join(BASE_DIR, "markers.db")
    state_path = os.path.join(BASE_DIR, "coherence_state.json")
    for f in [db_path, state_path]:
        if os.path.exists(f):
            os.remove(f)
    init_db()


def split_tasks(tasks):
    domain_a = [t for t in tasks if t.get("correct_agent", "") in DOMAIN_A_AGENTS]
    domain_b = [t for t in tasks if t.get("correct_agent", "") in DOMAIN_B_AGENTS]
    return domain_a, domain_b


def run_pass(tasks, pass_num, is_bootstrap=False):
    cardiac_correct = 0
    cardiac_total = 0
    llm_correct = 0
    llm_total = 0
    
    for task in tasks:
        task_text = task.get("text", "")
        expected = task.get("correct_agent", "")
        
        coherence, _ = compute_coherence()
        predicted_valence, pred_confidence, best_agent = predict_valence(task_text)
        
        if is_bootstrap:
            route_type = "llm_with_context"
        else:
            route_type = get_routing_recommendation(coherence, predicted_valence, pred_confidence)
        
        if route_type == "autonomous" and best_agent:
            chosen = best_agent
            routed_by = "cardiac"
            routing_confidence = pred_confidence
        else:
            result = keyword_route(task_text)
            if isinstance(result, tuple):
                chosen, llm_confidence = result
            else:
                chosen, llm_confidence = result, 0.6
            routed_by = "llm"
            routing_confidence = float(llm_confidence)
        
        correct = chosen == expected
        
        if routed_by == "cardiac":
            cardiac_total += 1
            if correct:
                cardiac_correct += 1
        else:
            llm_total += 1
            if correct:
                llm_correct += 1
        
        outcome = "success" if correct else "failure"
        store_marker(
            task_text=task_text,
            agent_used=expected,
            outcome=outcome,
            confidence=routing_confidence,
            surprise=0.0 if correct else 0.5,
            effort=0.1,
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
    }


def main():
    start_time = time.time()
    ensure_validation_telemetry()
    
    with open(TASKS_FILE) as f:
        tasks = json.load(f)
    
    domain_a, domain_b = split_tasks(tasks)
    
    print(f"\n🫀 CARDIAC ARCHITECTURE — Experiment 5: Cross-Domain Transfer")
    print(f"   Domain A (Operations): {len(domain_a)} tasks — agents: {', '.join(sorted(DOMAIN_A_AGENTS))}")
    print(f"   Domain B (Creative):   {len(domain_b)} tasks — agents: {', '.join(sorted(DOMAIN_B_AGENTS))}")
    print(f"   ══════════════════════════════════════════════════════")
    
    # ===== Phase 1: Train on Domain A only =====
    print(f"\n   PHASE 1: Train on Domain A only (5 passes, {len(domain_a)} tasks/pass)")
    print(f"   ──────────────────────────────────────────────────────")
    fresh_start()
    
    domain_a_results = []
    for p in range(1, 6):
        is_bootstrap = (p == 1)
        result = run_pass(domain_a, p, is_bootstrap=is_bootstrap)
        result["phase"] = "train_domain_a"
        domain_a_results.append(result)
        phase = "BOOTSTRAP" if is_bootstrap else "CARDIAC"
        print(f"   Pass {p} [{phase:>9}] | Cardiac: {result['cardiac_ratio']:>5.1f}% (acc {result['cardiac_accuracy']:>5.1f}%) | Overall: {result['overall_accuracy']:>5.1f}% | Markers: {result['markers_total']}")
    
    trained_markers = get_stats()["total_markers"]
    print(f"\n   📦 Domain A markers accumulated: {trained_markers}")
    
    # ===== Phase 2: Test on Domain B (with Domain A markers) =====
    print(f"\n   PHASE 2: Test Domain B with Domain A markers (5 passes, {len(domain_b)} tasks/pass)")
    print(f"   ──────────────────────────────────────────────────────")
    
    cross_domain_results = []
    for p in range(6, 11):
        # No bootstrap — we want to see if Domain A markers help with Domain B
        result = run_pass(domain_b, p, is_bootstrap=False)
        result["phase"] = "cross_domain_test"
        cross_domain_results.append(result)
        print(f"   Pass {p} [CROSS-DOM] | Cardiac: {result['cardiac_ratio']:>5.1f}% (acc {result['cardiac_accuracy']:>5.1f}%) | Overall: {result['overall_accuracy']:>5.1f}% | Markers: {result['markers_total']}")
    
    # ===== Phase 3: Control — cold start on Domain B =====
    print(f"\n   PHASE 3: Control — Domain B cold start (5 passes, {len(domain_b)} tasks/pass)")
    print(f"   ──────────────────────────────────────────────────────")
    fresh_start()
    
    control_results = []
    for p in range(1, 6):
        is_bootstrap = (p == 1)
        result = run_pass(domain_b, p, is_bootstrap=is_bootstrap)
        result["phase"] = "control_cold_start"
        control_results.append(result)
        phase = "BOOTSTRAP" if is_bootstrap else "CARDIAC"
        print(f"   Pass {p} [{phase:>9}] | Cardiac: {result['cardiac_ratio']:>5.1f}% (acc {result['cardiac_accuracy']:>5.1f}%) | Overall: {result['overall_accuracy']:>5.1f}% | Markers: {result['markers_total']}")
    
    elapsed = time.time() - start_time
    
    # Comparison
    print(f"\n   ══════════════════════════════════════════════════════")
    print(f"   🫀 CROSS-DOMAIN TRANSFER RESULTS ({elapsed:.0f}s total)")
    print(f"   ══════════════════════════════════════════════════════")
    
    print(f"\n   Domain B performance comparison (Cardiac %):")
    print(f"   {'Pass':<6} {'Cross-Domain (A→B)':>20} {'Cold Start (B only)':>22} {'Advantage':>12}")
    print(f"   {'─'*62}")
    for i in range(5):
        cross_ratio = cross_domain_results[i]['cardiac_ratio']
        cold_ratio = control_results[i]['cardiac_ratio']
        advantage = cross_ratio - cold_ratio
        print(f"   {i+1:<6} {cross_ratio:>19.1f}% {cold_ratio:>21.1f}% {advantage:>+10.1f}%")
    
    print(f"\n   Domain B accuracy comparison:")
    print(f"   {'Pass':<6} {'Cross-Domain':>14} {'Cold Start':>14}")
    print(f"   {'─'*36}")
    for i in range(5):
        cross_acc = cross_domain_results[i]['overall_accuracy']
        cold_acc = control_results[i]['overall_accuracy']
        print(f"   {i+1:<6} {cross_acc:>13.1f}% {cold_acc:>13.1f}%")
    
    # Analysis
    cross_pass1_cardiac = cross_domain_results[0]['cardiac_ratio']
    cold_pass1_cardiac = control_results[0]['cardiac_ratio']
    cross_pass1_acc = cross_domain_results[0]['cardiac_accuracy']
    
    print(f"\n   📊 KEY FINDINGS:")
    print(f"      Cross-domain cardiac at pass 1: {cross_pass1_cardiac}%")
    print(f"      Cold-start cardiac at pass 1:   {cold_pass1_cardiac}%")
    
    if cross_pass1_cardiac > cold_pass1_cardiac:
        print(f"      ✅ CROSS-DOMAIN TRANSFER DETECTED: {cross_pass1_cardiac - cold_pass1_cardiac:.1f}% head start")
        print(f"         Domain A markers provided useful signal for Domain B tasks")
    elif cross_pass1_cardiac == cold_pass1_cardiac and cross_pass1_cardiac > 0:
        print(f"      ⚠️ NO CLEAR ADVANTAGE: Both started at {cross_pass1_cardiac}%")
    else:
        print(f"      📊 DOMAIN SEPARATION CONFIRMED: Markers are domain-specific")
        print(f"         This is actually a useful finding — it means markers encode")
        print(f"         domain knowledge, not just generic routing heuristics")
    
    # Save
    results_dir = str(canonical_results_dir())
    results_path = os.path.join(results_dir, "cross_domain_results.json")
    with open(results_path, "w") as f:
        json.dump({
            "experiment": "cross_domain_transfer",
            "domain_a_agents": sorted(DOMAIN_A_AGENTS),
            "domain_b_agents": sorted(DOMAIN_B_AGENTS),
            "domain_a_tasks": len(domain_a),
            "domain_b_tasks": len(domain_b),
            "runtime_seconds": round(elapsed, 1),
            "domain_a_training": domain_a_results,
            "cross_domain_test": cross_domain_results,
            "control_cold_start": control_results,
        }, f, indent=2)
    
    print(f"\n   Results saved to {results_path}")

if __name__ == "__main__":
    main()
