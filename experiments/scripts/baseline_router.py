"""Optional model-based baseline router with local fallback."""

import json
import os
import re
import time
import urllib.request
import importlib.util
from pathlib import Path

ALLOWED_AGENTS = ["oracle", "sentinel", "scout", "quill", "ember", "forge", "compass", "conductor"]
MODEL_ID = os.getenv("BASELINE_ROUTER_MODEL", os.getenv("CARDIAC_ROUTER_MODEL", ""))
SECRETS_FILE = os.getenv("BASELINE_ROUTER_SECRETS_FILE", os.getenv("CARDIAC_SECRETS_FILE", ""))
CACHE_PATH = Path(__file__).resolve().parents[1] / "results" / "baseline_route_cache.json"
FALLBACK_ROUTER_PATH = Path(__file__).parent / "best_router.py"
API_URL = os.getenv("BASELINE_ROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions")
USE_LIVE_ROUTER = os.getenv("BASELINE_USE_MODEL_ROUTER", os.getenv("CARDIAC_USE_LIVE_CODEX", "0")) in {
    "1", "true", "TRUE", "yes", "YES"
}

SYSTEM_PROMPT = """You are a strict task router for the production agent fleet.
Choose exactly one agent from this fixed set:
- oracle — commodity prices, futures, commodity report, crop conditions, hedging, ag market analysis
- sentinel — intelligence briefings, geopolitical risk, regulatory risk, news synthesis, threat/risk scanning
- scout — research, competitor analysis, market sizing, trend analysis, finding companies/investors/papers/news
- quill — content creation, copywriting, blog posts, social posts, scripts, newsletters, website copy
- ember — emails, outreach, follow-ups, drip/nurture/re-engagement sequences, InMail, cold outreach
- forge — code, scripts, APIs, debugging, databases, infra, CI/CD, automation, technical implementation
- compass — strategy, decision frameworks, business analysis, financial modeling, prioritization, market-entry strategy
- conductor — orchestration across multiple agents, multi-domain workflows, end-to-end coordination

Return JSON only: {"agent":"one_allowed_agent","confidence":0.0}
"""


def _read_router_api_key() -> str:
    env_key = (
        os.getenv("BASELINE_ROUTER_API_KEY")
        or os.getenv("OPENROUTER_API_KEY")
        or os.getenv("OPENROUTER_API_KEY")
    )
    if env_key:
        return env_key.strip().strip('"')

    if SECRETS_FILE and os.path.exists(SECRETS_FILE):
        with open(SECRETS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("BASELINE_ROUTER_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"')
                if line.startswith("OPENROUTER_API_KEY=") or line.startswith("OPENROUTER_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"')

    raise RuntimeError("Model-router API key not found. Set BASELINE_ROUTER_API_KEY or OPENROUTER_API_KEY.")


def _load_cache() -> dict:
    if CACHE_PATH.exists():
        try:
            return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_cache(cache: dict):
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, indent=2), encoding="utf-8")


def _parse_agent(content: str):
    if content is None:
        raise ValueError("Model content was None")
    text = str(content).strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:].strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            obj = json.loads(text[start:end + 1])
            agent = obj.get("agent")
            confidence = float(obj.get("confidence", 0.7))
            if agent in ALLOWED_AGENTS:
                return agent, max(0.0, min(1.0, confidence))
        except Exception:
            pass

    lower = text.lower()
    for a in ALLOWED_AGENTS:
        if re.search(rf"\b{re.escape(a)}\b", lower):
            return a, 0.6
    raise ValueError(f"Could not parse agent from model response: {content[:200]}")


def _route_live(task_text: str):
    if not MODEL_ID:
        raise RuntimeError("BASELINE_ROUTER_MODEL is required when BASELINE_USE_MODEL_ROUTER=1")

    key = _read_router_api_key()
    payload = {
        "model": MODEL_ID,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Task text: {task_text}\nReturn JSON only."},
        ],
        "temperature": 0,
        "max_tokens": 256,
        "response_format": {"type": "json_object"},
        "reasoning": {"effort": "low"},
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://example.com",
            "X-Title": "Cardiac Router",
        },
        method="POST",
    )

    last_err = None
    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
                msg = raw["choices"][0]["message"]
                content = msg.get("content")
                if content is None:
                    # Some providers can emit non-text messages; retry.
                    raise ValueError("No text content returned")
                return _parse_agent(content)
        except Exception as e:
            last_err = e
            time.sleep(1.5 * attempt)
    raise RuntimeError(f"Model router failed after retries: {last_err}")


def _fallback_route(task_text: str):
    """Offline-safe fallback using local best_router.py if available."""
    if FALLBACK_ROUTER_PATH.exists():
        spec = importlib.util.spec_from_file_location("best_router", str(FALLBACK_ROUTER_PATH))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        fn = getattr(mod, "route_task", None) or getattr(mod, "route", None)
        if fn:
            result = fn(task_text)
            if isinstance(result, tuple):
                return result[0], float(result[1])
            return str(result), 0.6

    # Last-resort deterministic fallback
    t = task_text.lower()
    if any(k in t for k in ["code", "script", "api", "debug", "deploy"]):
        return "forge", 0.5
    if any(k in t for k in ["email", "outreach", "follow-up", "inmail"]):
        return "ember", 0.5
    if any(k in t for k in ["content", "post", "copy", "newsletter"]):
        return "quill", 0.5
    if any(k in t for k in ["price", "commodity", "futures", "commodity report", "hedge"]):
        return "oracle", 0.5
    return "compass", 0.4


def route(task_text: str):
    """Compatible with best_router.route signature: returns (agent, confidence)."""
    task_key = task_text.strip()
    cache = _load_cache()
    if task_key in cache:
        c = cache[task_key]
        return c["agent"], c.get("confidence", 0.7)

    if USE_LIVE_ROUTER:
        try:
            agent, confidence = _route_live(task_key)
        except Exception:
            agent, confidence = _fallback_route(task_key)
    else:
        agent, confidence = _fallback_route(task_key)
    cache[task_key] = {
        "agent": agent,
        "confidence": confidence,
        "model": MODEL_ID,
        "ts": int(time.time()),
    }
    _save_cache(cache)
    return agent, confidence
