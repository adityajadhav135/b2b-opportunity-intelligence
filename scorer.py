"""
Brandhero B2B Opportunity Intelligence System — PoC scoring engine.

Design intent (see written reasoning in the report for full detail):
- This does NOT try to auto-scrape everything end-to-end in 3 hours.
- It takes STRUCTURED signal input (gathered via manual + AI-assisted web research
  for this PoC; see README for what a v2 automation pipeline would look like)
  and turns it into a defensible, explainable score + recommendation.
- The point being tested is the scoring LOGIC and REASONING, not scraping infra.

Each signal is boolean/tiered and carries a weight + a short justification string
that gets surfaced in the output so a founder can sanity-check *why* a company
scored the way it did, not just trust a black-box number.
"""

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Signal weights (0-100 point budget, tuned so no single signal alone can
# make a company look "hot" — needs corroboration across categories)
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
    "leadership_change": "The new leader themselves — direct, timely outreach",
    "us_enterprise_expansion": "Head of US GTM / Regional VP",
}


@dataclass
class CompanySignals:
    name: str
    domain: str
    recent_funding: Optional[str] = None          # e.g. "$8M Series A, Jun 2026" or None
    design_hiring_gap: bool = False
    design_hiring_evidence: str = ""
    sales_gtm_hiring: bool = False
    sales_gtm_evidence: str = ""
    weak_website: bool = False
    weak_website_evidence: str = ""
    repositioning_mismatch: bool = False
    repositioning_evidence: str = ""
    leadership_change: bool = False
    leadership_evidence: str = ""
    us_enterprise_expansion: bool = False
    expansion_evidence: str = ""
    bootstrapped_low_urgency: bool = False
    sources: list = field(default_factory=list)


def score_company(c: CompanySignals) -> dict:
    hits = []
    total = 0

    if c.recent_funding:
        total += WEIGHTS["recent_funding"]
        hits.append(("recent_funding", c.recent_funding))
    if c.design_hiring_gap:
        total += WEIGHTS["design_hiring_gap"]
        hits.append(("design_hiring_gap", c.design_hiring_evidence))
    if c.sales_gtm_hiring:
        total += WEIGHTS["sales_gtm_hiring"]
        hits.append(("sales_gtm_hiring", c.sales_gtm_evidence))
    if c.weak_website:
        total += WEIGHTS["weak_website"]
        hits.append(("weak_website", c.weak_website_evidence))
    if c.repositioning_mismatch:
        total += WEIGHTS["repositioning_mismatch"]
        hits.append(("repositioning_mismatch", c.repositioning_evidence))
    if c.leadership_change:
        total += WEIGHTS["leadership_change"]
        hits.append(("leadership_change", c.leadership_evidence))
    if c.us_enterprise_expansion:
        total += WEIGHTS["us_enterprise_expansion"]
        hits.append(("us_enterprise_expansion", c.expansion_evidence))
    if c.bootstrapped_low_urgency:
        total += WEIGHTS["bootstrapped_low_urgency"]
        hits.append(("bootstrapped_low_urgency", "Bootstrapped / flat headcount / no visible trigger event"))

    score = max(0, min(100, total))

    # Likely need = highest-weighted hit that fired (proxy for "most urgent")
    fired_needs = [(k, WEIGHTS.get(k, 0)) for k, _ in hits if k in NEED_MAP]
    likely_need = NEED_MAP[max(fired_needs, key=lambda x: x[1])[0]] if fired_needs else "Unclear — insufficient signal"

    fired_stakeholders = [(k, WEIGHTS.get(k, 0)) for k, _ in hits if k in STAKEHOLDER_MAP]
    stakeholder = STAKEHOLDER_MAP[max(fired_stakeholders, key=lambda x: x[1])[0]] if fired_stakeholders else "Founder/CEO (default for small teams)"

    return {
        "name": c.name,
        "domain": c.domain,
        "score": score,
        "signals_fired": hits,
        "likely_need": likely_need,
        "stakeholder": stakeholder,
        "sources": c.sources,
    }


def outreach_angle(result: dict, c: CompanySignals) -> str:
    """Very lightweight template-based angle generator (no LLM call needed for PoC —
    this is where a real system would swap in an API call to draft full copy)."""
    top_signal = max(result["signals_fired"], key=lambda h: WEIGHTS.get(h[0], 0)) if result["signals_fired"] else None
    if not top_signal:
        return "Insufficient signal for a personalized angle — needs manual research."
    key, evidence = top_signal
    templates = {
        "recent_funding": f"Congratulate on the raise ({evidence}) and frame the site/brand as the next credibility unlock for the upcoming hiring/enterprise push.",
        "design_hiring_gap": f"Reference the open design/product role ({evidence}) and offer to cover the gap on a project basis while they hire.",
        "sales_gtm_hiring": f"Reference the sales hiring push ({evidence}) and frame the website as the thing new AEs will lean on hardest in the first call.",
        "weak_website": f"Point to a specific, concrete UX/messaging gap on the live site ({evidence}) as a quick-win opportunity.",
        "repositioning_mismatch": f"Note the new positioning ({evidence}) and flag that the current site/brand doesn't yet reflect it.",
        "leadership_change": f"Reach out directly to the new leader ({evidence}) — early tenure is when brand/website budget gets unlocked.",
        "us_enterprise_expansion": f"Frame the US/enterprise push ({evidence}) as needing an enterprise-credible design bar.",
    }
    return templates.get(key, "Generic outreach — needs manual angle.")


if __name__ == "__main__":
    import json
    # Smoke test with a dummy company
    demo = CompanySignals(
        name="Demo Co", domain="demo.example.com",
        recent_funding="$5M Seed, Aug 2026",
        weak_website=True, weak_website_evidence="Homepage uses default template hero, no clear ICP statement",
        sources=["https://example.com/press-release"]
    )
    r = score_company(demo)
    r["outreach_angle"] = outreach_angle(r, demo)
    print(json.dumps(r, indent=2))
