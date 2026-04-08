"""
Cardiac Architecture — Marker Store (Somatic Marker Library)
Implements Mechanism 2: Valence-Tagged Decision Memory

Each task execution generates a marker with multi-dimensional valence.
The marker library is queried BEFORE LLM routing to enable pre-cognitive routing.
"""

import sqlite3
import json
import time
import hashlib
import os
import math
from typing import Optional, List, Dict, Tuple

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "markers.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS markers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_signature TEXT NOT NULL,
            task_text TEXT,
            agent_used TEXT NOT NULL,
            outcome TEXT CHECK(outcome IN ('success', 'partial', 'failure')) DEFAULT 'success',
            confidence REAL DEFAULT 0.5,
            surprise REAL DEFAULT 0.0,
            effort REAL DEFAULT 0.0,
            downstream_impact REAL DEFAULT 0.0,
            cost_ratio REAL DEFAULT 1.0,
            coherence_at_decision REAL DEFAULT 0.5,
            valence REAL DEFAULT 0.5,
            latency_ms REAL DEFAULT 0,
            routed_by TEXT CHECK(routed_by IN ('llm', 'cardiac', 'fallback')) DEFAULT 'llm',
            created_at REAL DEFAULT (strftime('%s', 'now')),
            marker_weight REAL DEFAULT 1.0
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_task_sig ON markers(task_signature)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_agent ON markers(agent_used)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_valence ON markers(valence)
    """)
    conn.commit()
    conn.close()

def compute_task_signature(task_text: str) -> str:
    """Compress task into a signature for matching.
    Uses first 200 chars normalized + hash for exact dedup."""
    normalized = task_text.lower().strip()[:200]
    return hashlib.md5(normalized.encode()).hexdigest()[:16]

def compute_valence(outcome: str, confidence: float, surprise: float, 
                    effort: float, cost_ratio: float) -> float:
    """Compute composite valence score (0.0 = terrible, 1.0 = excellent).
    
    Valence is NOT just success/failure. A successful task that was 
    surprisingly hard and expensive has lower valence than one that 
    was easy and cheap. This is the 'affect' the thesis describes.
    """
    # Base from outcome
    outcome_score = {"success": 1.0, "partial": 0.5, "failure": 0.0}[outcome]
    
    # Modifiers
    confidence_bonus = confidence * 0.2  # High confidence = slightly better
    surprise_penalty = abs(surprise) * 0.15  # Surprise (either direction) = slightly worse
    effort_penalty = min(effort, 1.0) * 0.15  # High effort = worse
    cost_penalty = max(0, (cost_ratio - 1.0)) * 0.1  # Over-budget = worse
    
    valence = (outcome_score * 0.5 + confidence_bonus 
               - surprise_penalty - effort_penalty - cost_penalty)
    return max(0.0, min(1.0, valence))

def store_marker(task_text: str, agent_used: str, outcome: str = "success",
                 confidence: float = 0.5, surprise: float = 0.0,
                 effort: float = 0.0, downstream_impact: float = 0.0,
                 cost_ratio: float = 1.0, coherence: float = 0.5,
                 latency_ms: float = 0, routed_by: str = "llm") -> int:
    """Store a somatic marker after task execution."""
    sig = compute_task_signature(task_text)
    valence = compute_valence(outcome, confidence, surprise, effort, cost_ratio)
    
    conn = get_db()
    cursor = conn.execute("""
        INSERT INTO markers (task_signature, task_text, agent_used, outcome,
                           confidence, surprise, effort, downstream_impact,
                           cost_ratio, coherence_at_decision, valence,
                           latency_ms, routed_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (sig, task_text[:500], agent_used, outcome, confidence, surprise,
          effort, downstream_impact, cost_ratio, coherence, valence,
          latency_ms, routed_by))
    marker_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return marker_id

def query_similar_markers(task_text: str, k: int = 5) -> List[Dict]:
    """Find K most similar past markers by task signature.
    
    For the prototype, we use exact signature match + keyword overlap.
    Production would use embedding distance (as specified in thesis).
    """
    sig = compute_task_signature(task_text)
    conn = get_db()
    
    # First: exact signature matches
    rows = conn.execute("""
        SELECT * FROM markers WHERE task_signature = ? 
        ORDER BY created_at DESC LIMIT ?
    """, (sig, k)).fetchall()
    
    if len(rows) < k:
        # Fallback: keyword overlap (prototype approximation of embedding distance)
        words = set(task_text.lower().split()[:20])
        all_rows = conn.execute("""
            SELECT * FROM markers ORDER BY created_at DESC LIMIT 500
        """).fetchall()
        
        scored = []
        for row in all_rows:
            if row['task_signature'] == sig:
                continue  # Already included
            row_words = set((row['task_text'] or '').lower().split()[:20])
            overlap = len(words & row_words) / max(len(words | row_words), 1)
            if overlap > 0.2:  # At least 20% keyword overlap
                scored.append((overlap, row))
        
        scored.sort(key=lambda x: -x[0])
        for _, row in scored[:k - len(rows)]:
            rows.append(row)
    
    conn.close()
    return [dict(row) for row in rows]

def predict_valence(task_text: str, k: int = 5) -> Tuple[float, float, str]:
    """As-if body loop: predict valence for a new task from similar markers.
    
    Returns: (predicted_valence, prediction_confidence, best_agent)
    
    This is Mechanism 2 from the thesis — combining markers from 
    similar tasks to predict outcomes without execution.
    """
    neighbors = query_similar_markers(task_text, k)
    
    if not neighbors:
        return 0.5, 0.0, ""  # No data — novel task, zero confidence
    
    # Distance-weighted valence combination (thesis spec)
    # For prototype, weight by recency instead of embedding distance
    total_weight = 0.0
    weighted_valence = 0.0
    agent_votes = {}
    valences = []
    
    for i, marker in enumerate(neighbors):
        # More recent = higher weight
        age_days = (time.time() - marker['created_at']) / 86400
        weight = marker['marker_weight'] / (1.0 + age_days * 0.1)
        
        weighted_valence += marker['valence'] * weight
        total_weight += weight
        valences.append(marker['valence'])
        
        agent = marker['agent_used']
        if agent not in agent_votes:
            agent_votes[agent] = 0
        agent_votes[agent] += weight
    
    predicted_valence = weighted_valence / total_weight if total_weight > 0 else 0.5
    
    # Prediction confidence = inverse of variance (thesis spec)
    if len(valences) > 1:
        mean_v = sum(valences) / len(valences)
        variance = sum((v - mean_v) ** 2 for v in valences) / len(valences)
        confidence = 1.0 / (1.0 + variance)
    else:
        confidence = 0.3  # Single marker = low confidence
    
    # Best agent by weighted vote
    best_agent = max(agent_votes, key=agent_votes.get) if agent_votes else ""
    
    return predicted_valence, confidence, best_agent

def get_stats() -> Dict:
    """Get marker library statistics."""
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) as n FROM markers").fetchone()['n']
    by_route = conn.execute("""
        SELECT routed_by, COUNT(*) as n, AVG(valence) as avg_valence
        FROM markers GROUP BY routed_by
    """).fetchall()
    by_agent = conn.execute("""
        SELECT agent_used, COUNT(*) as n, AVG(valence) as avg_valence
        FROM markers GROUP BY agent_used ORDER BY n DESC
    """).fetchall()
    avg_valence = conn.execute("SELECT AVG(valence) as v FROM markers").fetchone()['v'] or 0
    conn.close()
    
    return {
        "total_markers": total,
        "avg_valence": round(avg_valence, 3),
        "by_route": [dict(r) for r in by_route],
        "by_agent": [dict(r) for r in by_agent],
    }

# Initialize on import
init_db()

if __name__ == "__main__":
    # Quick test
    init_db()
    mid = store_marker("Research competitor commodity prices in EU market", "scout",
                       outcome="success", confidence=0.8, effort=0.3)
    print(f"Stored marker #{mid}")
    
    v, c, agent = predict_valence("Find competitor commodity pricing data")
    print(f"Predicted valence: {v:.2f}, confidence: {c:.2f}, best agent: {agent}")
    
    stats = get_stats()
    print(f"Library stats: {json.dumps(stats, indent=2)}")
