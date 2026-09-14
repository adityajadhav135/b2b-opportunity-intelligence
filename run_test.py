from scorer import CompanySignals, score_company, outreach_angle
import json

# STRENGTH GUIDE (applied per-signal below, see STRENGTH_RUBRIC in scorer.py):
#   1.0 = strong, specific, high-magnitude, well within window
#   0.7 = moderate — real and on-topic, but partial/edge-of-window/lower-magnitude
#   0.4 = weak — plausible but thin or borderline evidence
# Strength is a judgment call made by the researcher at data-entry time,
# same as deciding whether a signal fires at all — it's not invented after
# the fact to hit a target score.

companies = [
    CompanySignals(
        name="Monk", domain="meetmonk.ai",
        recent_funding="$25M Series A, Apr 21 2026 (~5 months old) — total raised $29M",
        recent_funding_strength=0.85,  # large round, but ~5mo puts it near the edge of the 0-6mo window
        sales_gtm_hiring=False,  # not directly verified — left off deliberately, see notes
        us_enterprise_expansion=True,
        expansion_evidence="NYC-based, actively expanding into AI-native customer segment (ElevenLabs, Profound) and enterprise ERP integrations (Salesforce, Rillet) as of Jun-Jul 2026",
        expansion_strength=0.9,  # named enterprise customers + specific integrations, not just a stated intent
        sources=[
            "https://axios.com/pro/fintech-deals/2026/04/21/monk-25-million-startups-ai-accounts-receivable",
            "https://www.fintechfutures.com/venture-capital-funding/ar-start-up-monk-bags-25m-series-a",
            "https://simplify.jobs/c/Monk",
        ]
    ),
    CompanySignals(
        name="Atomicwork", domain="atomicwork.com",
        recent_funding=None,  # last raise Jan 2025 Series A $25M -> ~20mo old, NOT within 6mo window
        design_hiring_gap=True,
        design_hiring_evidence="27 open roles incl. 2 Design and 2 Marketing & Growth listed on job board (snapshot 2026); hiring Product Designer/Lead Product Designer rather than a senior design/brand executive",
        design_hiring_strength=0.7,  # real gap, but only 2 of 27 roles are design — moderate not overwhelming
        us_enterprise_expansion=True,
        expansion_evidence="India-founded, HQ now San Francisco; Sep 2024 funding note cited 'expand GTM teams in the United States over next three years' — ongoing but not a fresh trigger",
        expansion_strength=0.4,  # real but stale/ongoing, not a fresh event — explicitly weaker evidence
        sources=[
            "https://inc42.com/company/atomicwork/funding/",
            "https://www.trueup.io/co/atomicwork",
            "https://www.peoplematters.in/amp/news/funding-investment/atomicwork-secures-3-million-in-seed-funding-42889",
        ]
    ),
    CompanySignals(
        name="TeamViewer", domain="teamviewer.com",
        leadership_change=True,
        leadership_evidence="New CMO Peter Ruchatz announced May 28 2026, effective Sep 2026 — genuinely recent",
        leadership_strength=1.0,  # exact date, named individual, unambiguous — strong evidence on its own terms
        sources=["https://www.teamviewer.com/ru-cis/global/company/press/2026/teamviewer-appoints-peter-ruchatz-as-chief-marketing-officer/"]
        # Note: strong signal strength ≠ good lead. This is rejected on manual
        # ICP review below (public enterprise company, in-house marketing org,
        # outside Brandhero's funded-startup ICP) — see README "TeamViewer trap".
    ),
    CompanySignals(
        name="yoona.ai", domain="yoona.ai",
        weak_website=True,
        weak_website_evidence="Public press copy leans on generic hype language ('game-changer', 'revolutionize', vague % stats) rather than a specific ICP or buyer pain point; most recent major product push (yoona 3.0) was Oct 2024, over a year old",
        weak_website_strength=0.6,  # real and on-topic, but based on press copy, not a full visual/UX audit
        design_hiring_gap=False,
        bootstrapped_low_urgency=True,
        bootstrapped_strength=0.7,  # only intern-level hiring found — decent but not exhaustive evidence of low urgency
        sources=[
            "https://websummit.com/wp-media/2024/10/yoona.ai-Press-Release-1.pdf",
            "https://yoona.ai/careers?job=7",
        ]
    ),
    CompanySignals(
        name="Protexxa", domain="protexxa.com",
        recent_funding=None,  # seed 2022, one source claims a 2024 round -- both stale
        bootstrapped_low_urgency=True,
        bootstrapped_strength=0.4,  # inferred mainly from absence of activity, not a direct confirmed data point
        sources=[
            "https://www.businesswire.com/news/home/20221027005716/en/5314977/",
            "https://api-dev.kscope.io/private-data/companies/protexxa-com",
        ]
    ),
]

results = []
for c in companies:
    r = score_company(c)
    r["outreach_angle"] = outreach_angle(r, c)
    results.append(r)

print(json.dumps(results, indent=2))
