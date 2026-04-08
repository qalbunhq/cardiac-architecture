"""
Cardiac Architecture — Experiment 1: Plateau Discovery
20 passes × 200 tasks = 4,000 routing decisions

Answers: Where does cardiac routing plateau? Does it approach the 80/20 inversion?
"""

import json
import os
import sys
import time
import copy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from marker_store import init_db, predict_valence, get_stats, store_marker, get_db
from coherence import compute_coherence, get_routing_recommendation
from validation_runtime import ensure_validation_telemetry, canonical_results_dir

# Codex-only router
from baseline_router import route as keyword_route

TASKS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tasks.json")
NUM_PASSES = 20

def run_pass(tasks, pass_num, is_bootstrap=False):
    """Run one pass through all tasks, return stats."""
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
    
    # Fresh start
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "markers.db")
    state_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "coherence_state.json")
    for f in [db_path, state_path]:
        if os.path.exists(f):
            os.remove(f)
    init_db()
    
    with open(TASKS_FILE) as f:
        tasks = json.load(f)
    
    print(f"\n🫀 CARDIAC ARCHITECTURE — Experiment 1: Plateau Discovery")
    print(f"   Tasks per pass: {len(tasks)}")
    print(f"   Passes: {NUM_PASSES}")
    print(f"   Total routing decisions: {len(tasks) * NUM_PASSES}")
    print(f"   Pass 1 = bootstrap (all LLM-routed)")
    print(f"   Pass 2-{NUM_PASSES} = cardiac active")
    print(f"   ══════════════════════════════════════════════════════")
    
    all_results = []
    
    for p in range(1, NUM_PASSES + 1):
        is_bootstrap = (p == 1)
        result = run_pass(tasks, p, is_bootstrap=is_bootstrap)
        all_results.append(result)
        
        phase = "BOOTSTRAP" if is_bootstrap else "CARDIAC"
        elapsed = time.time() - start_time
        print(f"   Pass {p:>2}/{NUM_PASSES} [{phase:>9}] | "
              f"Cardiac: {result['cardiac_ratio']:>5.1f}% (acc {result['cardiac_accuracy']:>5.1f}%) | "
              f"LLM acc: {result['llm_accuracy']:>5.1f}% | "
              f"Overall: {result['overall_accuracy']:>5.1f}% | "
              f"Markers: {result['markers_total']:>5} | "
              f"Time: {elapsed:.0f}s")
    
    elapsed = time.time() - start_time
    
    # Compounding summary
    print(f"\n   ══════════════════════════════════════════════════════")
    print(f"   🫀 PLATEAU DISCOVERY RESULTS ({elapsed:.0f}s total)")
    print(f"   ══════════════════════════════════════════════════════")
    print(f"   {'Pass':<6} {'Cardiac%':>10} {'Cardiac Acc':>12} {'LLM Acc':>10} {'Overall':>10} {'Markers':>8}")
    print(f"   {'─'*58}")
    for r in all_results:
        print(f"   {r['pass']:<6} {r['cardiac_ratio']:>9.1f}% {r['cardiac_accuracy']:>10.1f}% {r['llm_accuracy']:>9.1f}% {r['overall_accuracy']:>9.1f}% {r['markers_total']:>7}")
    
    # Identify plateau
    ratios = [r['cardiac_ratio'] for r in all_results[1:]]  # skip bootstrap
    if len(ratios) >= 3:
        last_3_delta = abs(ratios[-1] - ratios[-3])
        if last_3_delta < 2.0:
            plateau_pass = all_results[-3]['pass']
            plateau_ratio = ratios[-3]
            print(f"\n   📊 PLATEAU DETECTED at pass {plateau_pass}: ~{plateau_ratio:.1f}% cardiac routing")
            print(f"      (Last 3 passes varied by only {last_3_delta:.1f}%)")
        else:
            print(f"\n   📈 NO PLATEAU YET — cardiac ratio still increasing")
            print(f"      Last value: {ratios[-1]:.1f}%, still climbing")
    
    # Save
    results_dir = str(canonical_results_dir())
    results_path = os.path.join(results_dir, "plateau_results.json")
    with open(results_path, "w") as f:
        json.dump({
            "experiment": "plateau_discovery",
            "passes": NUM_PASSES,
            "tasks_per_pass": len(tasks),
            "total_decisions": len(tasks) * NUM_PASSES,
            "runtime_seconds": round(elapsed, 1),
            "results": all_results,
        }, f, indent=2)
    
    print(f"\n   Results saved to {results_path}")

if __name__ == "__main__":
    main()
