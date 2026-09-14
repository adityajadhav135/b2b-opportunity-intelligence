# B2B Opportunity Intelligence System

A proof-of-concept built for Brandhero's Founder's Office practical assignment: given a B2B SaaS company, identify how likely it is to need Brandhero's services *right now*, why, who to talk to, and what to say — instead of treating every company as an equal lead.

This is a PoC, not a production system. Signal quality and reasoning were prioritized over UI or scraping infrastructure, per the assignment brief.

---

## How it works (2 stages)

This system is deliberately split into a manual/AI-assisted research stage and an automated scoring stage. That split is intentional — see [Why is signal research manual?](#why-is-signal-research-manual) below.

```
Stage 1 (manual / AI-assisted)          Stage 2 (automated)
────────────────────────────           ────────────────────
Research a company:                     scorer.py takes your
- funding news                          structured signals and
- hiring posts                    ──▶   outputs:
- website messaging                     - a 0-100 score
- leadership changes                    - the likely business need
- expansion news                        - the relevant stakeholder
                                         - a personalized outreach angle
You write it down as a
CompanySignals object
```

### Step-by-step: what happens when you run this

1. **You research a company** — web search, funding databases, job boards, the company's own site. This takes a few minutes per company.
2. **You encode what you found** as a `CompanySignals` object in `run_test.py` (or your own script) — a structured, evidenced note, not a guess.
3. **You run `python run_test.py`.**
4. **The engine scores it automatically** — weighted signal math, a mapped "likely need," a mapped stakeholder, and a templated outreach angle, all traceable back to the evidence you gave it.
5. **You get JSON output** per company, with sources included, so anyone can verify nothing was fabricated.

If a signal has no evidence behind it, you simply leave it unset — the engine will not invent a reason to justify a higher score. See the Protexxa result below for what that looks like in practice.

---

## Part 1 — The Signals (and why each one matters *for Brandhero specifically*)

Brandhero's own positioning (from brandhero.design) is narrow and useful: conversion-focused UI/UX, branding, and Webflow/Framer websites, sold to funded startups, with proof points around helping clients raise rounds, convert better, and cut sales-cycle friction. The signals below are chosen to detect *that* need, not generic "growth potential."

| # | Signal | Direction | Why it moves the needle for Brandhero |
|---|--------|-----------|-----------|
| 1 | **Funding raised in the last 0–6 months** | ↑↑ | Fresh capital + new investor scrutiny + hiring pressure = budget and urgency to look credible, fast. This is literally Brandhero's stated value prop ("raise your next round"). |
| 2 | **Hiring design/product roles, but not a senior design leader** | ↑ | Signals unmet design need being patched with ICs, not solved with leadership — the gap an agency fills well. Hiring a *Head/VP of Design* instead means they're solving it in-house and need Brandhero less. |
| 3 | **Actively hiring Sales/AE/GTM roles** | ↑ | New sellers lean hardest on the website and collateral in their first 90 days; a weak site becomes visible pain the moment headcount grows. |
| 4 | **Weak/generic website messaging** (template feel, vague ICP, hype language without specificity) | ↑↑ | Directly diagnostic — this is the exact gap Brandhero sells against. |
| 5 | **Repositioning/rebrand not reflected in the visual identity** | ↑ | Message-product mismatch is a classic redesign trigger; the company is already in "figuring out our story" mode. |
| 6 | **New CMO/Head of Growth/Marketing in the last ~90 days** | ↑ | New leaders audit brand/website early and usually have discretionary budget for a visible quick win. |
| 7 | **Expansion into US/enterprise market from a smaller/non-US base** | ↑ | Enterprise buyers and US investors are less forgiving of amateur design; credibility-signaling need spikes. |
| 8 | **Bootstrapped/profitable, flat headcount, no visible trigger event, junior-only hiring** | ↓ | Lower urgency, lower budget, no forcing function — deprioritize even if technically in-ICP. |

**Design choice:** no single signal alone can push a company to a "hot" score. Weights are set so it takes at least 2 independent, well-evidenced signals to clear ~40 points — mirroring real sales judgment: one data point is a coincidence, two is a pattern.

---

## Part 2 — Build

### Files
- `scorer.py` — the scoring engine: signal weights, the `CompanySignals` data structure, and the scoring/mapping/outreach-angle logic.
- `run_test.py` — the 5-company test run with real, sourced signals.
- `results.json` — raw output from the test run.

### Scoring weights (out of 100; negative signal subtracts)

```
recent_funding:            22        design_hiring_gap:        12
sales_gtm_hiring:          14        weak_website:              20
repositioning_mismatch:    12        leadership_change:        10
us_enterprise_expansion:   10        bootstrapped_low_urgency: -15
```

### What score would it take to hit 80+?

Nobody hits 80 by accident — you need roughly **4–5 of the 7 positive signals firing simultaneously**. For example: recent funding (22) + weak website (20) + GTM hiring (14) + US expansion (10) = 66; add a leadership change (10) = 76. You basically need almost everything firing at once to clear 80.

This is by design, not a bug: a company that's *that* textbook-perfect a lead is genuinely rare. Most real companies show 1–2 clean, verifiable signals — which is exactly what the test run below reflects. The ceiling being hard to reach means a high score is actually meaningful instead of common and noisy.

### How to run it

```bash
python3 run_test.py
```

To score your own company, add a new `CompanySignals(...)` block to the `companies` list in `run_test.py`:

```python
CompanySignals(
    name="YOUR COMPANY", domain="example.com",
    recent_funding="e.g. $8M Seed, March 2026",  # or leave as None
    weak_website=True,
    weak_website_evidence="what you found and where",
    sources=["https://link-to-evidence.com"]
),
```

Only set a field to `True`/fill it in if you actually have a real source for it. Leaving fields at their default means the engine won't fabricate a reason.

---

## Part 3 — Test: 5 Real B2B SaaS Companies

*No companies were contacted. All facts are sourced. Where a signal couldn't be verified confidently in the research time available, it was left un-fired rather than guessed.*

| Company | Score | Signals fired | Likely need | Stakeholder |
|---|---|---|---|---|
| **Monk** (meetmonk.ai) | **32** | Recent funding: $25M Series A, Apr 21 2026 (~5mo old, total raised $29M). US enterprise expansion: landing AI-native customers (ElevenLabs, Profound) + enterprise ERP integrations (Salesforce, Rillet) through mid-2026. | Investor-grade site/brand credibility for the enterprise push | Founder/CEO (George Kurdin) |
| **Atomicwork** (atomicwork.com) | **22** | Design-hiring gap: 27 open roles incl. 2 Design + 2 Marketing & Growth, but hiring ICs not a design exec. US expansion: India-founded, now SF HQ, ongoing GTM build-out. | Project-based design capacity to cover the gap | Head of Product/CEO |
| **TeamViewer** (teamviewer.com) | **10 (rejected on manual review)** | Genuinely fresh CMO hire, announced May 28 2026. | N/A — filtered out on ICP fit despite a real, recent signal (see below) | N/A |
| **yoona.ai** (yoona.ai) | **5** | Weak website: generic hype language, no specific ICP, most recent product push over a year old. Bootstrapped/low-urgency: only intern-level hiring (BD intern, junior accountant). | Website/messaging redesign, likely price-sensitive | Head of Marketing/founder |
| **Protexxa** (protexxa.com) | **0** | None confirmed recent — funding events found (2022, possibly 2024) are both stale. | Insufficient signal — engine correctly refuses to fabricate an angle | Founder/CEO (default) |

### Notable finding: the Atomicwork staleness trap

Atomicwork's funding kept resurfacing across multiple sources as if it were current, but the actual raise was **January 2025 — ~20 months old**, well outside the 0–6-month recency window this system requires. A naive "funding mentioned" search would have scored this company much higher than it deserves. This became a live example for the recency-handling problem in Part 4.

### Notable finding: the TeamViewer ICP trap

TeamViewer's new-CMO signal is real and fresh. But TeamViewer is a large public enterprise software company with its own large in-house marketing org — completely outside Brandhero's actual ICP (funded startups). This is deliberately included to show why a raw score can't be trusted blindly: a company-size/stage filter has to sit *upstream* of the signal engine, or it will keep surfacing plausible-looking but wrong-fit leads.

### Why the scores are relatively low, and why that's intentional

A signal only fires here if it's backed by a real, dated source found during research. Most real companies don't stack 4–5 verifiable signals at once inside a short research window — so scores in the 0–35 range across 5 real companies are an honest reflection of available evidence, not a flaw in the math. The alternative — inflating scores to look more impressive — would defeat the actual point of the exercise, which is signal quality over signal theater.

---

## Part 4 — Reality Check

**1. What would break first at 500 companies?**
Signal collection, not scoring. The scoring/mapping logic is deterministic and scales fine. What breaks is getting clean, current, *deduplicated* signals per company — as seen with Atomicwork, the same funding event resurfaces in search results dated months apart. At 500 companies, manually verifying "is this actually recent" becomes impossible without a real data API (Crunchbase/PitchBook) with reliable date fields, plus deduping logic across sources.

**2. What information couldn't be obtained reliably?**
Current hiring status with real confidence (job boards go stale and duplicate across aggregators); true visual/design quality of a site (only text content was reviewed here, not actual visual polish — "weak website" is a messaging-quality proxy, not a real design audit); and almost anything about a marketing leader's actual first-90-day priorities or budget authority, which really needs a human research step (LinkedIn activity, conference talks) beyond a search pass.

**3. What was deliberately left manual, and why?**
Final go/no-go on outreach (see Part 5), and ICP/company-size fit (shown with TeamViewer) — that judgment call is cheap for a human and expensive to encode robustly, so it doesn't belong in v1 automation. Visual design audits were also left manual, since that needs either a screenshot + human eye or a vision-model call, out of scope for the time available.

**4. With another week, what would be built next?**
A real ICP/stage filter as a hard gate before scoring (headcount + funding-stage bounds); a funding-events API integration (Crunchbase or similar) with proper date fields to kill the staleness problem; and a lightweight screenshot + vision-model pass to actually score visual design quality instead of proxying it through press-release language.

---

## Part 5 — Business Judgement

*Scores: 91 / 84 / 79 / 73 / 68 — capacity for 2*

No, the top two shouldn't be taken automatically. A score is only as good as the signals behind it — the two highest could both be driven by the same easy-to-game signal (e.g. a funding headline) while #3 or #4 has a messier but more relevant story. Before deciding, verify: (1) is each signal genuinely recent and correctly dated, not a re-indexed old event (the Atomicwork trap above); (2) does the company genuinely fit Brandhero's ICP in size and stage, not just sector (the TeamViewer trap above); (3) is there a real, reachable decision-maker with budget authority, not just a plausible one; (4) does the specific evidence support a genuinely personalized angle, or would outreach be generic despite the high score. A 79 built on two clean, verified, ICP-fit signals is a better bet than a 91 built on one loud but stale headline.

---

## Why is signal research manual?

The assignment brief explicitly allows this: *"Use anything you want... manual steps where automation isn't sensible."* Given a 3-hour window, this system automates the part that's genuinely reusable and consistent — turning evidence into a score, need, stakeholder, and outreach angle the same way every time — while leaving signal-gathering to search-assisted human research, which is where a real data API (paid, out of scope here) would replace it in a v2. This split is itself an answer to Part 4, question 3.

---

## Limitations

- Not a live scraper — no company is queried automatically end-to-end. Input is structured, evidenced signals a human (optionally AI-assisted) has already gathered.
- "Weak website" is scored from readable text/messaging, not actual visual design polish.
- No deduplication or recency-verification layer — staleness has to be caught manually right now (see the Atomicwork example).
- No ICP/company-size filter is built into the scoring math itself — it's applied as a manual override (see the TeamViewer example). This is a known gap and the first thing to fix with more time.
