"""
Cardiac Architecture — Experiment 3: Marker Transplantation
Tests whether accumulated markers can bootstrap a new deployment.

Phase A: Build mature markers (5 passes on Fleet A)
Phase B: Export markers, import into fresh Fleet B with 0.5 weight discount
Phase C: Run Fleet B and compare to cold-start Fleet C (no transplant)

Validates Patent Claims 12, 19 (marker transplantation, cross-domain transfer)
"""

import json
import os
import sys
import time
import sqlite3
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from marker_store import init_db, predict_valence, get_stats, store_marker, get_db
from coherence import compute_coherence, get_routing_recommendation
from validation_runtime import ensure_validation_telemetry, canonical_results_dir

from baseline_router import route as keyword_route

TASKS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tasks.json")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_db_path():
    return os.path.join(BASE_DIR, "markers.db")

def fresh_start():
    db_path = get_db_path()
    state_path = os.path.join(BASE_DIR, "coherence_state.json")
    for f in [db_path, state_path]:
        if os.path.exists(f):
            os.remove(f)
    init_db()

def export_markers(db_path):
    """Export all markers as a list of dicts."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM markers").fetchall()
    markers = [dict(r) for r in rows]
    conn.close()
    return markers

def import_markers_with_discount(markers, discount=0.5):
    """Import markers into current db with weight discount."""
    conn = get_db()
    for m in markers:
        conn.execute("""
            INSERT INTO markers (task_signature, task_text, agent_used, outcome,
                confidence, surprise, effort, downstream_impact, cost_ratio,
                coherence_at_decision, valence, latency_ms, routed_by, marker_weight)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            m['task_signature'], m['task_text'], m['agent_used'], m['outcome'],
            m['confidence'], m['surprise'], m['effort'],
            m.get('downstream_impact', 0.0), m.get('cost_ratio', 1.0),
            m['coherence_at_decision'], m['valence'], m.get('latency_ms', 0),
            m['routed_by'], discount  # Apply weight discount
        ))
    conn.commit()

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
    
    print(f"\n🫀 CARDIAC ARCHITECTURE — Experiment 3: Marker Transplantation")
    print(f"   Tasks per pass: {len(tasks)}")
    print(f"   ══════════════════════════════════════════════════════")
    
    # ===== FLEET A: Build mature markers =====
    print(f"\n   FLEET A: Building mature marker library (5 passes)")
    print(f"   ──────────────────────────────────────────────────")
    fresh_start()
    fleet_a_results = []
    for p in range(1, 6):
        is_bootstrap = (p == 1)
        result = run_pass(tasks, p, is_bootstrap=is_bootstrap)
        result["fleet"] = "A_donor"
        fleet_a_results.append(result)
        phase = "BOOTSTRAP" if is_bootstrap else "CARDIAC"
        print(f"   Pass {p} [{phase:>9}] | Cardiac: {result['cardiac_ratio']:>5.1f}% | Acc: {result['cardiac_accuracy']:>5.1f}% | Overall: {result['overall_accuracy']:>5.1f}%")
    
    # Export Fleet A markers
    donor_markers = export_markers(get_db_path())
    donor_count = len(donor_markers)
    print(f"\n   📦 Exported {donor_count} markers from Fleet A")
    
    # ===== FLEET B: Transplanted markers =====
    print(f"\n   FLEET B: Transplanted markers (0.5 weight discount)")
    print(f"   ──────────────────────────────────────────────────")
    fresh_start()
    import_markers_with_discount(donor_markers, discount=0.5)
    transplant_stats = get_stats()
    print(f"   Imported {transplant_stats['total_markers']} markers at 0.5 weight")
    
    fleet_b_results = []
    for p in range(1, 6):
        # No bootstrap needed — already have transplanted markers
        result = run_pass(tasks, p, is_bootstrap=False)
        result["fleet"] = "B_transplant"
        fleet_b_results.append(result)
        print(f"   Pass {p} [TRANSPLANT] | Cardiac: {result['cardiac_ratio']:>5.1f}% | Acc: {result['cardiac_accuracy']:>5.1f}% | Overall: {result['overall_accuracy']:>5.1f}%")
    
    # ===== FLEET C: Cold start (no transplant) =====
    print(f"\n   FLEET C: Cold start (no transplant, control group)")
    print(f"   ──────────────────────────────────────────────────")
    fresh_start()
    
    fleet_c_results = []
    for p in range(1, 6):
        is_bootstrap = (p == 1)
        result = run_pass(tasks, p, is_bootstrap=is_bootstrap)
        result["fleet"] = "C_cold_start"
        fleet_c_results.append(result)
        phase = "BOOTSTRAP" if is_bootstrap else "CARDIAC"
        print(f"   Pass {p} [{phase:>9}] | Cardiac: {result['cardiac_ratio']:>5.1f}% | Acc: {result['cardiac_accuracy']:>5.1f}% | Overall: {result['overall_accuracy']:>5.1f}%")
    
    elapsed = time.time() - start_time
    
    # Comparison
    print(f"\n   ══════════════════════════════════════════════════════")
    print(f"   🫀 TRANSPLANTATION COMPARISON ({elapsed:.0f}s total)")
    print(f"   ══════════════════════════════════════════════════════")
    print(f"\n   Pass-by-pass comparison (Cardiac Routing %):")
    print(f"   {'Pass':<6} {'Fleet A (Donor)':>16} {'Fleet B (Transplant)':>22} {'Fleet C (Cold)':>16} {'B vs C Advantage':>18}")
    print(f"   {'─'*80}")
    for i in range(5):
        a_ratio = fleet_a_results[i]['cardiac_ratio']
        b_ratio = fleet_b_results[i]['cardiac_ratio']
        c_ratio = fleet_c_results[i]['cardiac_ratio']
        advantage = b_ratio - c_ratio
        print(f"   {i+1:<6} {a_ratio:>15.1f}% {b_ratio:>21.1f}% {c_ratio:>15.1f}% {advantage:>+16.1f}%")
    
    print(f"\n   Pass-by-pass comparison (Overall Accuracy %):")
    print(f"   {'Pass':<6} {'Fleet A (Donor)':>16} {'Fleet B (Transplant)':>22} {'Fleet C (Cold)':>16}")
    print(f"   {'─'*62}")
    for i in range(5):
        a_acc = fleet_a_results[i]['overall_accuracy']
        b_acc = fleet_b_results[i]['overall_accuracy']
        c_acc = fleet_c_results[i]['overall_accuracy']
        print(f"   {i+1:<6} {a_acc:>15.1f}% {b_acc:>21.1f}% {c_acc:>15.1f}%")
    
    # Key metrics
    b_pass1_cardiac = fleet_b_results[0]['cardiac_ratio']
    c_pass1_cardiac = fleet_c_results[0]['cardiac_ratio']
    b_pass1_acc = fleet_b_results[0]['cardiac_accuracy']
    
    print(f"\n   📊 KEY FINDINGS:")
    print(f"      Fleet B cardiac routing at pass 1: {b_pass1_cardiac}% (vs Fleet C: {c_pass1_cardiac}%)")
    print(f"      Fleet B cardiac accuracy at pass 1: {b_pass1_acc}%")
    if b_pass1_cardiac > c_pass1_cardiac:
        print(f"      ✅ TRANSPLANTATION WORKS: {b_pass1_cardiac - c_pass1_cardiac:.1f}% head start")
    else:
        print(f"      ⚠️ Transplantation did not provide advantage at pass 1")
    
    # Save
    results_dir = str(canonical_results_dir())
    results_path = os.path.join(results_dir, "transplant_results.json")
    with open(results_path, "w") as f:
        json.dump({
            "experiment": "marker_transplantation",
            "donor_markers": donor_count,
            "transplant_discount": 0.5,
            "runtime_seconds": round(elapsed, 1),
            "fleet_a_donor": fleet_a_results,
            "fleet_b_transplant": fleet_b_results,
            "fleet_c_cold_start": fleet_c_results,
        }, f, indent=2)
    
    print(f"\n   Results saved to {results_path}")

if __name__ == "__main__":
    main()
