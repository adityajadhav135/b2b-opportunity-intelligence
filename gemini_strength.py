"""
Gemini-backed strength scorer.

Replaces the manual strength=0.85-style judgment calls in run_test.py with
an LLM call that grades evidence text against the same STRENGTH_RUBRIC
already defined in scorer.py, so the rubric stays the single source of truth
and the scoring math in scorer.py doesn't change at all.

Usage:
    from gemini_strength import get_strength
    result = get_strength("recent_funding", "$25M Series A, Apr 2026 (~5mo old)")
    # -> {"strength": 0.85, "reasoning": "..."}

Requires: pip install requests
Requires: GEMINI_API_KEY environment variable (get one at ai.google.dev)
"""

import os
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()  # reads .env in the current working directory and loads it into os.environ

MAX_RETRIES = 4
RETRY_STATUS_CODES = {429, 500, 502, 503, 504}  # rate-limited / transient server errors

GEMINI_MODEL = "gemini-3.8-flash"
GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)

# Context so the model knows WHY each signal matters, not just what it is -
# this is the same table from README.md Part 1, condensed.
SIGNAL_CONTEXT = {
    "recent_funding": "Funding raised in the last 0-6 months. Stronger = larger round, more recent, more total raised.",
    "design_hiring_gap": "Hiring design/product roles but NOT a senior design leader. Stronger = more design roles relative to total roles, clearly IC-level not leadership.",
    "sales_gtm_hiring": "Actively hiring Sales/AE/GTM roles. Stronger = multiple open roles, clearly recent postings.",
    "weak_website": "Weak/generic website messaging (template feel, vague ICP, hype language without specifics). Stronger = based on direct site inspection, not just press copy; more specific examples of vagueness.",
    "repositioning_mismatch": "Repositioning/rebrand not yet reflected in visual identity. Stronger = explicit, recent, well-documented repositioning statement.",
    "leadership_change": "New CMO/Head of Growth/Marketing in the last ~90 days. Stronger = exact date, named individual, confirmed effective/start date.",
    "us_enterprise_expansion": "Expansion into US/enterprise market from a smaller/non-US base. Stronger = named enterprise customers or specific integrations, not just a stated intent.",
    "bootstrapped_low_urgency": "Bootstrapped/profitable, flat headcount, no visible trigger event. Stronger (more negative) = confirmed directly, not just inferred from absence of news.",
}

RUBRIC = """
1.0 = Strong: specific, recent, high-magnitude evidence (e.g. a large round <2 months old; a named exec change with an exact date)
0.7 = Moderate: real, on-topic evidence, but partial, near the edge of the recency window, or modest in magnitude
0.4 = Weak: plausible but thin, indirect, or borderline-out-of-window evidence
0.0 = No real evidence / evidence contradicts the signal
""".strip()

PROMPT_TEMPLATE = """You are grading the STRENGTH of evidence for a B2B sales-intelligence signal, for Brandhero (a design/branding agency selling to funded B2B SaaS startups).

Signal: {signal_key}
What this signal means and why it matters: {context}

Strength rubric (use as anchor points; you may return any value 0.0-1.0, not just these four):
{rubric}

Evidence text provided by the researcher:
\"\"\"{evidence}\"\"\"

Grade ONLY how strong/convincing this specific evidence is for this specific signal - not how good the company looks overall. Be skeptical: stale dates, vague claims, or inferred-not-confirmed evidence should score low.

Return ONLY valid JSON, no markdown fences, no preamble:
{{"strength": <float 0.0-1.0>, "reasoning": "<one sentence, cite what in the evidence drove the score>"}}
"""


def get_strength(signal_key: str, evidence: str, api_key: str = None) -> dict:
    """Call Gemini to grade evidence strength for a given signal type.

    Raises RuntimeError if no API key is set, or ValueError if Gemini's
    response can't be parsed as the expected JSON shape.
    """
    api_key = api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "No Gemini API key found. Set GEMINI_API_KEY as an environment "
            "variable, or pass api_key= explicitly."
        )

    prompt = PROMPT_TEMPLATE.format(
        signal_key=signal_key,
        context=SIGNAL_CONTEXT.get(signal_key, "(no context provided)"),
        rubric=RUBRIC,
        evidence=evidence,
    )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,  # low temp - this is a grading task, not creative
            "responseMimeType": "application/json",
        },
    }

    resp = None
    for attempt in range(MAX_RETRIES):
        resp = requests.post(f"{GEMINI_URL}?key={api_key}", json=payload, timeout=30)
        if resp.status_code not in RETRY_STATUS_CODES:
            break
        if attempt < MAX_RETRIES - 1:
            wait = 2 ** attempt  # 1s, 2s, 4s, 8s
            print(f"  (Gemini returned {resp.status_code}, retrying in {wait}s...)")
            time.sleep(wait)

    resp.raise_for_status()
    data = resp.json()

    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        parsed = json.loads(text)
        strength = max(0.0, min(1.0, float(parsed["strength"])))
        return {"strength": round(strength, 2), "reasoning": parsed.get("reasoning", "")}
    except (KeyError, IndexError, ValueError, json.JSONDecodeError) as e:
        raise ValueError(f"Couldn't parse Gemini response: {e}\nRaw response: {data}")


if __name__ == "__main__":
    # Smoke test - requires GEMINI_API_KEY to be set
    r = get_strength(
        "recent_funding",
        "$25M Series A, Apr 21 2026 (~5 months old) - total raised $29M",
    )
    print(json.dumps(r, indent=2))
