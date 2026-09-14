"""
Interactive company signal collector.

Difference from run_test.py's approach: you no longer hand-pick strength=0.85
yourself. You type the company name, domain, and evidence text for whichever
signals you found - leave a prompt blank if you have no evidence for that
signal. Gemini grades each piece of evidence against the same STRENGTH_RUBRIC
from scorer.py/README.md and returns a strength score + one-line reasoning,
which is then fed straight into the existing, UNCHANGED score_company() logic.

This keeps a clean separation: Gemini only ever judges "how strong is this
evidence", never "should this signal fire" (that's still your call as the
researcher - if you don't type anything, the signal doesn't fire, same as
before) and never touches the scoring weights/math itself.

Usage:
    export GEMINI_API_KEY=your_key_here
    python collect_company.py
"""

import json
from scorer import CompanySignals, score_company, outreach_angle
from gemini_strength import get_strength

# (signal_key, prompt, bool_field, evidence_field, strength_field)
# recent_funding is special-cased below: the text itself IS the evidence field.
SIGNAL_SPECS = [
    ("design_hiring_gap", "Design hiring gap", "design_hiring_gap", "design_hiring_evidence", "design_hiring_strength"),
    ("sales_gtm_hiring", "Sales/GTM hiring", "sales_gtm_hiring", "sales_gtm_evidence", "sales_gtm_strength"),
    ("weak_website", "Weak website", "weak_website", "weak_website_evidence", "weak_website_strength"),
    ("repositioning_mismatch", "Repositioning mismatch", "repositioning_mismatch", "repositioning_evidence", "repositioning_strength"),
    ("leadership_change", "Leadership change", "leadership_change", "leadership_evidence", "leadership_strength"),
    ("us_enterprise_expansion", "US/enterprise expansion", "us_enterprise_expansion", "expansion_evidence", "expansion_strength"),
    ("bootstrapped_low_urgency", "Bootstrapped / low urgency", "bootstrapped_low_urgency", None, "bootstrapped_strength"),
]


def collect_company() -> CompanySignals:
    name = input("Company name: ").strip()
    domain = input("Domain: ").strip()
    kwargs = {"name": name, "domain": domain}

    # --- recent_funding (special: the text IS the field, per scorer.py) ---
    funding_text = input("Recent funding evidence (blank = none): ").strip()
    if funding_text:
        kwargs["recent_funding"] = funding_text
        r = get_strength("recent_funding", funding_text)
        print(f"  -> strength {r['strength']}  ({r['reasoning']})")
        kwargs["recent_funding_strength"] = r["strength"]

    # --- everything else ---
    for signal_key, label, bool_field, evidence_field, strength_field in SIGNAL_SPECS:
        text = input(f"{label} evidence (blank = none): ").strip()
        if not text:
            continue
        kwargs[bool_field] = True
        if evidence_field:
            kwargs[evidence_field] = text
        r = get_strength(signal_key, text)
        print(f"  -> strength {r['strength']}  ({r['reasoning']})")
        kwargs[strength_field] = r["strength"]

    sources_raw = input("Sources (comma-separated URLs): ").strip()
    kwargs["sources"] = [s.strip() for s in sources_raw.split(",") if s.strip()]

    return CompanySignals(**kwargs)


if __name__ == "__main__":
    company = collect_company()
    result = score_company(company)
    result["outreach_angle"] = outreach_angle(result, company)
    print("\n" + json.dumps(result, indent=2))
