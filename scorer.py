"""
Brandhero B2B Opportunity Intelligence System — PoC scoring engine.

Design intent (see written reasoning in the report for full detail):
- This does NOT try to auto-scrape everything end-to-end in 3 hours.
- It takes STRUCTURED signal input (gathered via manual + AI-assisted web research
  for this PoC; see README for what a v2 automation pipeline would look like)
  and turns it into a defensible, explainable score + recommendation.
- The point being tested is the scoring LOGIC and REASONING, not scraping infra.

GRADUATED SCORING: each signal is not simply on/off. Alongside whether a signal
fired, the researcher records a STRENGTH (0.0-1.0) reflecting how strong the
underlying evidence actually is - e.g. a $25M raise 1 month ago is stronger
funding evidence than a $2M raise 5.5 months ago, even though both fall inside
the "recent funding" window. The signal contributes weight * strength points,
not the full weight. This is a rubric/weighting change, not retrieval - the
evidence is already in hand per company; nothing is being searched or fetched
by this module. (A real retrieval-based version of this system is sketched in
the README's "what's next" section.)

Each signal carries a weight + a short justification string that gets
surfaced in the output so a founder can sanity-check *why* a company scored
the way it did, not just trust a black-box number.
"""

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Signal weights (0-100 point budget, tuned so no single signal alone can
# make a company look "hot" - needs corroboration across categories).
# These are the MAXIMUM points available per signal; the actual points
# awarded are weight * strength (see CompanySignals below).
# ---------------------------------------------------------------------------

WEIGHTS = {
    "recent_funding": 22,          # funded in last 0-6 months
    "design_hiring_gap": 12,       # hiring design/product but no senior design leader
    "sales_gtm_hiring": 14,        # actively hiring AE/SDR/GTM roles
    "weak_website": 20,            # generic/template/dated site, weak messaging
    "repositioning_mismatch": 12,  # new narrative not reflected visually
    "leadership_change": 10,       # new CMO/Head of Growth/Marketing <3mo
    "us_enterprise_expansion": 10, # expanding into US/enterprise from elsewhere
    "bootstrapped_low_urgency": -15,  # negative signal, subtracts
}

NEED_MAP = {
    "recent_funding": "Investor-grade site & brand credibility for next round / new hires",
    "design_hiring_gap": "Outsourced design capacity to cover the gap in-house hiring hasn't filled",
    "sales_gtm_hiring": "Conversion-focused website/collateral to support a growing sales team",
    "weak_website": "Full website UX/conversion redesign",
    "repositioning_mismatch": "Brand & visual identity refresh to match new positioning",
    "leadership_change": "Fast, visible brand/website win for a new marketing leader's first 90 days",
    "us_enterprise_expansion": "Enterprise-credible design system & website for a new market",
}

STAKEHOLDER_MAP = {
    "recent_funding": "Founder/CEO or Head of Marketing (funding announcements usually route through them)",
    "design_hiring_gap": "Head of Product or CEO (owns the hiring gap)",
    "sales_gtm_hiring": "Head of Sales/RevOps or CMO",
    "weak_website": "Head of Marketing / Growth",
    "repositioning_mismatch": "CMO or Founder (repositioning is usually founder-driven)",
    "leadership_change": "The new leader themselves - direct, timely outreach",
    "us_enterprise_expansion": "Head of US GTM / Regional VP",
}

# Strength rubric shown to the researcher (and to the founder reviewing output)
# so "0.7" isn't a made-up-feeling number. Applied per-signal, documented in the README too.
STRENGTH_RUBRIC = {
    1.0: "Strong: specific, recent, high-magnitude evidence (e.g. large round <2mo old; named exec with exact date)",
    0.7: "Moderate: real and on-topic evidence, but partial / edge-of-window / lower-magnitude",
    0.4: "Weak: plausible but thin, indirect, or borderline out-of-window evidence",
}


@dataclass
class CompanySignals:
    name: str
    domain: str

    recent_funding: Optional[str] = None          # e.g. "$8M Series A, Jun 2026" or None
    recent_funding_strength: float = 1.0           # 0-1: how strong is this evidence (size, recency)

    design_hiring_gap: bool = False
    design_hiring_evidence: str = ""
    design_hiring_strength: float = 1.0

    sales_gtm_hiring: bool = False
    sales_gtm_evidence: str = ""
    sales_gtm_strength: float = 1.0

    weak_website: bool = False
    weak_website_evidence: str = ""
    weak_website_strength: float = 1.0

    repositioning_mismatch: bool = False
    repositioning_evidence: str = ""
    repositioning_strength: float = 1.0

    leadership_change: bool = False
    leadership_evidence: str = ""
    leadership_strength: float = 1.0

    us_enterprise_expansion: bool = False
    expansion_evidence: str = ""
    expansion_strength: float = 1.0

    bootstrapped_low_urgency: bool = False
    bootstrapped_strength: float = 1.0

    sources: list = field(default_factory=list)


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def score_company(c: CompanySignals) -> dict:
    hits = []       # (key, evidence, strength, points_awarded) - for display
    total = 0.0

    def add(key, fired, evidence, strength):
        nonlocal total
        if not fired:
            return
        s = _clamp01(strength)
        pts = WEIGHTS[key] * s
        total += pts
        hits.append((key, evidence, round(s, 2), round(pts, 1)))

    add("recent_funding", bool(c.recent_funding), c.recent_funding, c.recent_funding_strength)
    add("design_hiring_gap", c.design_hiring_gap, c.design_hiring_evidence, c.design_hiring_strength)
    add("sales_gtm_hiring", c.sales_gtm_hiring, c.sales_gtm_evidence, c.sales_gtm_strength)
    add("weak_website", c.weak_website, c.weak_website_evidence, c.weak_website_strength)
    add("repositioning_mismatch", c.repositioning_mismatch, c.repositioning_evidence, c.repositioning_strength)
    add("leadership_change", c.leadership_change, c.leadership_evidence, c.leadership_strength)
    add("us_enterprise_expansion", c.us_enterprise_expansion, c.expansion_evidence, c.expansion_strength)
    add("bootstrapped_low_urgency", c.bootstrapped_low_urgency,
        "Bootstrapped / flat headcount / no visible trigger event", c.bootstrapped_strength)

    score = max(0, min(100, round(total)))

    # Likely need / stakeholder = signal with the highest POINTS AWARDED
    # (weight * strength), not just the highest raw weight - a weak funding
    # signal shouldn't outrank a strongly-evidenced weaker-weight signal.
    positive_hits = [h for h in hits if h[0] in NEED_MAP]
    likely_need = (NEED_MAP[max(positive_hits, key=lambda h: h[3])[0]]
                   if positive_hits else "Unclear - insufficient signal")

    stakeholder_hits = [h for h in hits if h[0] in STAKEHOLDER_MAP]
    stakeholder = (STAKEHOLDER_MAP[max(stakeholder_hits, key=lambda h: h[3])[0]]
                   if stakeholder_hits else "Founder/CEO (default for small teams)")

    return {
        "name": c.name,
        "domain": c.domain,
        "score": score,
        # each entry: [signal_key, evidence, strength_0to1, points_awarded]
        "signals_fired": hits,
        "likely_need": likely_need,
        "stakeholder": stakeholder,
        "sources": c.sources,
    }


def outreach_angle(result: dict, c: CompanySignals) -> str:
    """Lightweight template-based angle generator (no LLM call needed for PoC -
    this is where a real system would swap in an API call to draft full copy).
    Picks the signal with the highest points awarded (weight * strength)."""
    positive = [h for h in result["signals_fired"] if h[0] in NEED_MAP]
    if not positive:
        return "Insufficient signal for a personalized angle - needs manual research."
    key, evidence, strength, pts = max(positive, key=lambda h: h[3])
    templates = {
        "recent_funding": f"Congratulate on the raise ({evidence}) and frame the site/brand as the next credibility unlock for the upcoming hiring/enterprise push.",
        "design_hiring_gap": f"Reference the open design/product role ({evidence}) and offer to cover the gap on a project basis while they hire.",
        "sales_gtm_hiring": f"Reference the sales hiring push ({evidence}) and frame the website as the thing new AEs will lean on hardest in the first call.",
        "weak_website": f"Point to a specific, concrete UX/messaging gap on the live site ({evidence}) as a quick-win opportunity.",
        "repositioning_mismatch": f"Note the new positioning ({evidence}) and flag that the current site/brand doesn't yet reflect it.",
        "leadership_change": f"Reach out directly to the new leader ({evidence}) - early tenure is when brand/website budget gets unlocked.",
        "us_enterprise_expansion": f"Frame the US/enterprise push ({evidence}) as needing an enterprise-credible design bar.",
    }
    return templates.get(key, "Generic outreach - needs manual angle.")


if __name__ == "__main__":
    import json
    # Smoke test with a dummy company
    demo = CompanySignals(
        name="Demo Co", domain="demo.example.com",
        recent_funding="$5M Seed, Aug 2026", recent_funding_strength=0.8,
        weak_website=True, weak_website_evidence="Homepage uses default template hero, no clear ICP statement",
        weak_website_strength=0.6,
        sources=["https://example.com/press-release"]
    )
    r = score_company(demo)
    r["outreach_angle"] = outreach_angle(r, demo)
    print(json.dumps(r, indent=2))
