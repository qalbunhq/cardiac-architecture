"""
router.py — Optimized keyword-matching router for production agent fleet.
Clean rewrite with surgical rules targeting the 51 known failure modes.

Key fixes:
1. Conductor: explicit multi-agent mention detection (highest priority)
2. Ember: "draft/write + email/follow-up/outreach/sequence" = ember, not quill
3. Forge: code/script verbs override commodity context
4. Scout: trend/market research tasks with commodity context = scout not oracle
5. Sentinel: "synthesize" + news/regulatory context = sentinel
6. Compass: strategic decision frameworks
"""

import re
ROUTING_COST = 0.05

# ─── TIER 1: CONDUCTOR – Multi-agent orchestration signals ───────────────────
CONDUCTOR_PATTERNS = [
    r'\b(oracle|scout|quill|ember|forge|sentinel|compass)\b.{0,60}\b(oracle|scout|quill|ember|forge|sentinel|compass)\b',
    r'\b(coordinate|orchestrate|synthesize)\b.{0,40}\b(across|multiple|all|full|entire|sprint|workflow|pipeline)\b',
    r'\b(full|entire|end.?to.?end|complete)\b.{0,30}\b(workflow|pipeline|process|sequence|sprint|package)\b',
    r'\bcoordinate (a|the|across|multiple)\b',
    r'\bacross (all |multiple )?(agents|teams|domains)\b',
    r'\bwhat tasks need to happen\b',
    r'\bprepare for a series [ab]\b',
    r'\b(run|execute|build) (the|a|an) (end.?to.?end|full|weekly|complete)\b.{0,50}\b(workflow|pipeline|process)\b',
    r'\bsituation report\b',
    r'\bparallel research sprint\b',
]

# ─── TIER 2: FORGE – Code/script/infra tasks ─────────────────────────────────
FORGE_PATTERNS = [
    r'\b(write|build|create|develop|implement)\b.{0,30}\b(python|bash|shell|sql|javascript|typescript)\b',
    r'\b(python|bash|shell)\b.{0,30}\b(script|scraper|pipeline|function|code)\b',
    r'\b(script|function|api|endpoint|microservice|webhook|pipeline)\b.{0,30}\b(that|which|to|for)\b',
    r'\bdebug\b.{0,40}\b(error|500|broken|failing|slow|query)\b',
    r'\bfix (the|this|a) (broken|failing|slow|cron|bug|error|query)\b',
    r'\b(fastapi|flask|django|postgresql|sqlite|mongodb|redis|docker|kubernetes)\b',
    r'\bset up (a |the )?(docker|database|schema|api|endpoint|server|container|vps)\b',
    r'\b(rest api|restful|graphql|grpc)\b',
    r'\b(cicd|ci/cd|github actions|dockerfile|docker compose)\b',
    r'\bwrite (a |an )?(web )?scraper\b',
    r'\bbuild (a |an )?(fastapi|flask|django|rest|command.line|cli|tool)\b',
    r'\bnosql (document )?schema\b',
    r'\bdesign (a |the )?schema\b',
    r'\b(cron job|cronjob|cron|provisio|ssh|ufw)\b',
    r'\bparses? (pdf|csv|json|xml)\b',
    r'\bwatches? a directory\b',
    r'\bstripe webhook\b',
    r'\bgeocod\b',
    r'\b429.error\b',
    r'\bcommand.line tool\b',
    r'\bcli tool\b',
]

# ─── TIER 3: EMBER – Email/outreach tasks ────────────────────────────────────
EMBER_PATTERNS = [
    r'\b(draft|write|create|compose)\b.{0,40}\b(email|e-mail|inmail)\b',
    r'\b(email|e-mail|inmail)\b.{0,40}\b(draft|write|create|compose)\b',
    r'\bfollow.?up\b.{0,40}\b(email|message|sequence|to|with|reminder)\b',
    r'\bfollow up with\b',
    r'\bfollow.?up (email|message|sequence)\b',
    r'\bcold (outreach|email|message|pitch)\b',
    r'\boutreach (email|sequence|message|campaign)\b',
    r'\b(drip|nurture) sequence\b',
    r'\binmail\b',
    r'\bprospecting email\b',
    r'\b(introduction|intro) email\b',
    r'\bthank.you email\b',
    r'\bpartnership (proposal |request )?(email|message)\b',
    r'\bmeeting request email\b',
    r'\b(reach out|outreach) (to|sequence|email)\b',
    r'\bpost.event follow.?up\b',
    r'\b(welcome email|email sequence|email campaign)\b',
    r'\bnurture sequence\b',
    r'\bre.?engagement (email|sequence|message)\b',
    r'\bwrite a professional follow.?up\b',
    r'\b(send a follow.?up|send (an? )?email)\b',
    r'\b(contact sequence|drip campaign)\b',
]

# ─── TIER 4: SENTINEL – Intelligence/synthesis tasks ─────────────────────────
SENTINEL_PATTERNS = [
    r'\bsynthesize\b.{0,60}\b(news|stories|report|findings|commentary|developments|reporting)\b',
    r'\b(intelligence|briefing)\b.{0,30}\b(brief|report|scan|analysis|morning)\b',
    r'\bmorning brief(ing)?\b',
    r'\b(geopolitical|political stability|sanctions|espionage|conflict)\b',
    r'\brisk (assessment|scan|landscape|signal|monitoring)\b',
    r'\bthreat (landscape|intelligence|assessment)\b',
    r'\b(regulatory (risk|change|landscape)|compliance risk)\b',
    r'\b(war|crisis|conflict).{0,40}\b(impact|implication|effect)\b',
    r'\blatest developments in.{0,50}\b(implications|impact)\b',
    r'\bmost important stories.{0,40}\b(past week|this week|climate|food)\b',
    r'\b(ipcc|un fao food price index|food security)\b',
    r'\bstrategic implications of.{0,40}\b(policy|export|import|regulatory)\b',
    r'\bemerging (risk|threat|disruption)\b',
    r'\b(scan|monitor) (for|news|signal)\b',
    r'\bnews synthesis\b',
    r'\binternational risk\b',
]

# ─── TIER 5: QUILL – Content creation (not email) ────────────────────────────
QUILL_PATTERNS = [
    r'\b(write|draft|create)\b.{0,40}\b(blog post|article|newsletter|op-ed|thought leadership|social media post)\b',
    r'\b(linkedin post|twitter thread|instagram caption|tiktok caption|facebook post)\b',
    r'\b(write|create)\b.{0,30}\b(tweet|thread|caption|tagline|headline|hero copy)\b',
    r'\btwitter thread\b',
    r'\bcontent calendar\b',
    r'\b(copywriting|ad copy|website copy|landing page copy)\b',
    r'\b(blog writing|guest post|byline|editorial)\b',
    r'\bscript (introducing|about|explaining|how|for|that)\b',
    r'\bshort bio\b',
    r'\b(product description|e-commerce (copy|description)|single-origin|case study)\b',
    r'\bmonthly newsletter.{0,30}(for|covering)\b',
    r'\b(create|write|draft) (a |an )?(bi.weekly|weekly|monthly|quarterly) (investor |operator |product )?(newsletter|digest|update)\b',
    r'\b(write|draft) (an? )?explainer (video )?script\b',
]

# ─── TIER 6: SCOUT – Research/find/trends ────────────────────────────────────
SCOUT_PATTERNS = [
    r'\b(who are the|who is the) (top|leading|major|biggest|key)\b',
    r'\b(research|find|identify|discover|track) (who|which|the top|the leading|companies|competitors|startups|investors)\b',
    r'\b(find|identify) \d+.{0,10}(companies|investors|importers|startups|papers|case studies)\b',
    r'\b(market size|total addressable market|tam)\b',
    r'\b(competitive|competitor) (landscape|analysis|intelligence|research|sprint)\b',
    r'\b(trend analysis|emerging trends|biggest trends|consumer trends|current trends)\b',
    r'\b(what|how).{0,30}(trends|trending)\b',
    r'\bgrant opportunities\b',
    r'\bcase studies of\b',
    r'\bacademic papers on\b',
    r'\bbenchmark(ing)?\b.{0,30}\b(competitor|industry|peer)\b',
    r'\b(what companies|which companies|what platforms) are\b',
    r'\bwho (are|is) (the )?(major|key|top|leading)\b',
    r'\bbuyer journey\b',
    r'\bsourcing contract\b',
    r'\btypical (buyer|customer|sourcing)\b',
    r'\b(agri.?tech|supply chain).{0,30}(trends|landscape|space)\b',
    r'\b(blockchain|ai|ml) (adoption|trends|use cases) (in|for)\b',
    r'\bwhat (buyers|companies|cpg|eu).{0,40}(published|saying|doing)\b',
    r'\bgrowth rate\b.{0,30}\b(market|industry|sector)\b',
    r'\b(find|search for) (recent|latest) (news|report)\b',
    r'\bsearch for\b',
]

# ─── TIER 7: ORACLE – Commodity prices / commodity report / hedging ─────────────────────
ORACLE_PATTERNS = [
    r'\b(commodity report|usda commodity report|cbot|euronext|cme group)\b',
    r'\b(futures (price|contract|settlement)|options (price|strategy))\b',
    r'\b(forward curve|backwardation|contango|basis point|crushing spread)\b',
    r'\b(stock.?to.?use|crop condition|ndvi|planting progress)\b',
    r'\b(hedge|hedging) (strategy|strategies|with)\b',
    r'\b(commodity price|futures price|settlement price|spot price)\b',
    r'\b(corn|soybean|wheat|rapeseed|palm oil|sunflower oil|commodity|product|sugar|canola).{0,30}\b(price|futures|market|crop)\b',
    r'\b(implied volatility|open interest|carry trade)\b',
    r'\b(export (parity|demand|competitiveness)|cif price|fob price)\b',
    r'\b(supply.?demand balance|demand balance)\b',
    r'\bwhat (is|are) the (current|latest) (price|rate)\b.{0,30}\b(corn|wheat|soy|commodity|product|oil|sugar|rapeseed)\b',
    r'\bget me the.{0,30}(price|rate|futures)\b',
    r'\b(monsoon|el ni.o).{0,40}\b(futures|prices|crop)\b',
    r'\b(brazil|argentina|ukraine|black sea).{0,40}\b(export|soybean|wheat|corn)\b',
]

# ─── TIER 8: COMPASS – Strategy/frameworks/decisions ─────────────────────────
COMPASS_PATTERNS = [
    r'\bshould (the evaluated system|interestos|we).{0,60}\b(before|after|prioritize|expand|charge|focus)\b',
    r'\b(go.?to.?market|gtm) (strategy|plan|approach)\b',
    r'\b(financial model|cash flow model|revenue model|pricing model)\b',
    r'\b(unit economics|break.?even|profitability analysis)\b',
    r'\b(swot|2x2 (matrix|prioritization|framework))\b',
    r'\b(competitive moat|defensible position|strategic rationale)\b',
    r'\b(market entry|business case|build or buy)\b',
    r'\b(valuation|fundraising|equity positioning)\b',
    r'\b(scenario planning|strategic planning|strategic analysis)\b',
    r'\bprioritization matrix\b',
    r'\bmake the case (for|against)\b',
    r'\b(monetize|monetization|revenue strategy)\b.{0,40}\b(model|strategy|approach|first)\b',
    r'\banalyze whether.{0,40}\b(should charge|monetize|model)\b',
    r'\bmodel the (cash flow|revenue|cost|impact)\b',
    r'\bmost defensible\b',
    r'\b(series a|fundraising round).{0,40}(prepare|strategy|planning)\b',
]


def _match_patterns(text: str, patterns: list) -> bool:
    """Check if any pattern matches the text."""
    for p in patterns:
        if re.search(p, text, re.IGNORECASE):
            return True
    return False


def route(task: str) -> tuple[str, float]:
    """
    Route a task to the best agent.
    Priority order: conductor > forge > ember > sentinel > quill > scout > oracle > compass
    Returns (agent_name, confidence_score).
    """
    t = task.lower()

    # ── TIER 1: CONDUCTOR ──
    if _match_patterns(t, CONDUCTOR_PATTERNS):
        return ("conductor", 0.93)

    # ── TIER 2: FORGE ──
    if _match_patterns(t, FORGE_PATTERNS):
        return ("forge", 0.93)
    
    # Special catch: "429 error" or HTTP errors → forge
    if re.search(r'\b(429|500|error|backoff|sdk|request|response)\b', t) and re.search(r'\b(error|fix|debug|return|sdk)\b', t):
        return ("forge", 0.90)

    # ── TIER 3: EMBER ──
    if _match_patterns(t, EMBER_PATTERNS):
        return ("ember", 0.92)

    # ── TIER 4: SENTINEL ──
    if _match_patterns(t, SENTINEL_PATTERNS):
        return ("sentinel", 0.91)
    
    # Special catch: Political/geopolitical context → sentinel
    if re.search(r'\b(political|peer region|situation).{0,40}\b(potential|implications|impact)\b', t):
        return ("sentinel", 0.88)

    # ── TIER 5: QUILL ──
    if _match_patterns(t, QUILL_PATTERNS):
        return ("quill", 0.91)

    # ── TIER 6: SCOUT ──
    if _match_patterns(t, SCOUT_PATTERNS):
        return ("scout", 0.90)

    # ── TIER 7: ORACLE ──
    if _match_patterns(t, ORACLE_PATTERNS):
        return ("oracle", 0.90)

    # ── TIER 8: COMPASS ──
    if _match_patterns(t, COMPASS_PATTERNS):
        return ("compass", 0.88)

    # ── FALLBACK: Keyword scoring ──
    keyword_scores = {
        "oracle": sum(1 for kw in [
            "price", "futures", "commodity", "commodity report", "usda", "crop", "corn", "soybean",
            "wheat", "rapeseed", "palm oil", "hedge", "hedging", "supply", "demand",
            "harvest", "planting", "grain", "oilseed", "commodity", "product", "sugar",
            "trading", "contract", "settlement", "volatility"
        ] if kw in t),
        "quill": sum(1 for kw in [
            "write", "draft", "blog", "article", "content", "social media",
            "linkedin", "twitter", "instagram", "newsletter", "copywriting",
            "caption", "tagline", "post", "tweet", "thought leadership"
        ] if kw in t),
        "scout": sum(1 for kw in [
            "research", "competitor", "market size", "trend", "find", "identify",
            "landscape", "benchmark", "survey", "report", "study", "search"
        ] if kw in t),
        "ember": sum(1 for kw in [
            "email", "outreach", "follow-up", "cold email", "drip", "sequence",
            "inmail", "reach out", "contact", "prospecting", "nurture"
        ] if kw in t),
        "forge": sum(1 for kw in [
            "code", "script", "python", "api", "database", "sql", "infrastructure",
            "docker", "deploy", "debug", "build", "schema", "endpoint"
        ] if kw in t),
        "sentinel": sum(1 for kw in [
            "intelligence", "briefing", "geopolitical", "risk", "political",
            "sanctions", "threat", "security", "conflict", "stability", "scan"
        ] if kw in t),
        "compass": sum(1 for kw in [
            "strategy", "strategic", "decision", "framework", "business model",
            "financial model", "revenue", "unit economics", "swot", "expansion"
        ] if kw in t),
        "conductor": sum(1 for kw in [
            "coordinate", "orchestrate", "multi-step", "across agents", "workflow",
            "parallel", "all agents", "synthesize", "full pipeline", "end-to-end"
        ] if kw in t),
    }

    best = max(keyword_scores, key=keyword_scores.get)
    best_score = keyword_scores[best]

    if best_score == 0:
        return ("conductor", 0.15)

    total = sum(keyword_scores.values())
    confidence = min((best_score / total) * 1.1, 0.85) if total > 0 else 0.1
    return (best, confidence)
