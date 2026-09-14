# B2B Opportunity Intelligence System

A proof-of-concept built for Brandhero's Founder's Office practical assignment: given a B2B SaaS company, identify how likely it is to need Brandhero's services *right now*, why, who to talk to, and what to say — instead of treating every company as an equal lead.

This is a PoC, not a production system. Signal quality and reasoning were prioritized over UI or scraping infrastructure, per the assignment brief.

---

## How it works

The system is split into two stages: a research stage (finding evidence per company) and an automated scoring stage (turning that evidence into a score, need, stakeholder, and outreach angle). The scoring stage itself has two parts — an LLM call that grades how *strong* each piece of evidence is, and a deterministic weighting engine that turns graded evidence into a final number.

```
1. Research a company            2. Type the evidence in          3. Engine scores it
   ─────────────────                 ─────────────────                ─────────────────
   web search, funding             collect_company.py prompts        Gemini grades each
   databases, job boards,   ──▶    you signal-by-signal;      ──▶    piece of evidence     ──▶  scorer.py turns
   the company's own site          you type what you found           for strength (0-1)         graded signals into
                                    (or leave blank if nothing)       against a fixed rubric     score + need +
                                                                                                   stakeholder + angle
```

**Step by step:**
1. **Research a company** — web search, funding databases, job boards, the company's own site. This takes a few minutes per company.
2. **Run `python collect_company.py`.** It asks for the company name and domain, then prompts you for evidence on each of the 8 signals below, one at a time. If you have no evidence for a signal, leave it blank — nothing is invented to fill a gap.
3. **Gemini grades each piece of evidence you type**, scoring how strong/convincing it is (0.0–1.0) against a fixed rubric, and returns a one-line reason for the score. This runs live, per signal, as you type.
4. **`scorer.py` turns the graded signals into a result** — weighted signal math, a mapped "likely need," a mapped stakeholder, and a templated outreach angle, all traceable back to the evidence you typed in and the reasoning Gemini gave for its strength score.
5. **You get JSON output** per company, with sources included, so anyone can verify nothing was fabricated.

**Signals are graduated, not binary.** A signal firing isn't worth its full weight automatically. A $25M raise one month ago and a $2M raise 5.5 months ago both count as "recent funding," but they aren't equally convincing — so each piece of evidence also carries a *strength* score that discounts weaker/edge-case evidence before it's weighted. See [Scoring weights](#scoring-weights-out-of-100-negative-signal-subtracts) below for the mechanics.

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
- `scorer.py` — the scoring engine: signal weights, the `CompanySignals` data structure, and the scoring/mapping/outreach-angle logic. Pure deterministic math — no API calls here.
- `gemini_strength.py` — calls the Gemini API to grade a piece of evidence text against the strength rubric below, returning a `(strength, reasoning)` pair. Isolated from the scoring math so the rubric stays the single source of truth.
- `collect_company.py` — the interactive entry point. Prompts for a company's evidence signal-by-signal, calls `gemini_strength.py` live as you type, then feeds the result into `scorer.py` to produce the final scored JSON.
- `results.json` — output from a test run across 5 real companies (see Part 3).

### Scoring weights (out of 100; negative signal subtracts)

```
recent_funding:            22        design_hiring_gap:        12
sales_gtm_hiring:          14        weak_website:              20
repositioning_mismatch:    12        leadership_change:        10
us_enterprise_expansion:   10        bootstrapped_low_urgency: -15
```

These are **maximum** points per signal, not flat awards. Each fired signal also carries a **strength** score (0.0–1.0) — graded automatically by Gemini from the evidence text — and the signal contributes `weight × strength` points rather than the full weight:

| Strength | Meaning |
|---|---|
| **1.0 — Strong** | Specific, recent, high-magnitude evidence (e.g. a large round <2 months old; a named exec change with an exact date) |
| **0.7 — Moderate** | Real, on-topic evidence, but partial, near the edge of the recency window, or modest in magnitude |
| **0.4 — Weak** | Plausible but thin, indirect, or borderline-out-of-window evidence |

Gemini is given this exact rubric plus a short description of *why* each signal matters (so it's grading evidence relevance, not just sentiment), and returns a continuous 0.0–1.0 value anchored to those three reference points, along with a one-sentence justification that's surfaced in the output for sanity-checking.

Only whether a signal *fires* is a human judgment call (typing evidence in, or leaving it blank) — how *strong* that evidence is, once typed, is graded consistently by Gemini rather than by researcher gut feel, so the same evidence produces the same score regardless of who's running it or how many companies they've reviewed that day.

### How to run it

```bash
pip install requests python-dotenv
# create a .env file in this folder containing: GEMINI_API_KEY=your_key_here
python collect_company.py
```

It will prompt for the company name, domain, then evidence for each of the 8 signals (leave blank for "no evidence"), then sources. Output is the same JSON shape as `results.json`.

Only type evidence for a signal if you actually have a real source for it — leaving a prompt blank means the engine won't fabricate a reason.

---

## Part 3 — Test: 5 Real B2B SaaS Companies

*No companies were contacted. All facts are sourced. Where a signal couldn't be verified confidently in the research time available, it was left un-fired rather than guessed.*

| Company | Score | Signals fired (strength → points) | Likely need | Stakeholder |
|---|---|---|---|---|
| **Monk** (meetmonk.ai) | **28** | Recent funding: $25M Series A, Apr 21 2026, ~5mo old, total raised $29M (strength 0.85 → 18.7 pts — large round, but near the edge of the 6mo window). US enterprise expansion: named AI-native customers (ElevenLabs, Profound) + enterprise ERP integrations (Salesforce, Rillet) through mid-2026 (strength 0.9 → 9.0 pts). | Investor-grade site/brand credibility for the enterprise push | Founder/CEO (George Kurdin) |
| **Atomicwork** (atomicwork.com) | **12** | Design-hiring gap: 27 open roles incl. 2 Design + 2 Marketing & Growth, hiring ICs not a design exec (strength 0.7 → 8.4 pts — real but only 2 of 27 roles are design). US expansion: India-founded, now SF HQ, but the GTM-expansion evidence is a 2024 funding note, not a fresh trigger (strength 0.4 → 4.0 pts). | Project-based design capacity to cover the gap | Head of Product/CEO |
| **TeamViewer** (teamviewer.com) | **10 (rejected on manual review)** | Genuinely fresh CMO hire, announced May 28 2026, exact date and named individual (strength 1.0 → 10.0 pts — strong evidence, but see ICP note below). | N/A — filtered out on ICP fit despite a real, recent signal (see below) | N/A |
| **yoona.ai** (yoona.ai) | **2** | Weak website: generic hype language, no specific ICP, most recent product push over a year old (strength 0.6 → 12.0 pts — real but based on press copy, not a full visual audit). Bootstrapped/low-urgency: only intern-level hiring found (strength 0.7 → −10.5 pts). | Website/messaging redesign, likely price-sensitive | Head of Marketing/founder |
| **Protexxa** (protexxa.com) | **0** | No positive signal confirmed recent — funding events found (2022, possibly 2024) are both stale. Bootstrapped/low-urgency inferred mainly from absence of activity (strength 0.4 → −6.0 pts). | Insufficient signal — engine correctly refuses to fabricate an angle | Founder/CEO (default) |

Full evidence text, sources, and per-signal Gemini reasoning for each company are in `results.json`.

### Notable finding: the Atomicwork staleness trap

Atomicwork's funding kept resurfacing across multiple sources as if it were current, but the actual raise was **January 2025 — ~20 months old**, well outside the 0–6-month recency window this system requires. A naive "funding mentioned" search would have scored this company much higher than it deserves. This became a live example for the recency-handling problem in Part 4.

### Notable finding: the TeamViewer ICP trap

TeamViewer's new-CMO signal is real and fresh. But TeamViewer is a large public enterprise software company with its own large in-house marketing org — completely outside Brandhero's actual ICP (funded startups). This is deliberately included to show why a raw score can't be trusted blindly: a company-size/stage filter has to sit *upstream* of the signal engine, or it will keep surfacing plausible-looking but wrong-fit leads.

### Why the scores are relatively low, and why that's intentional

A signal only fires here if it's backed by a real, dated source found during research. Most real companies don't stack 4–5 verifiable signals at once inside a short research window — so scores in the 0–35 range across 5 real companies are an honest reflection of available evidence, not a flaw in the math. The alternative — inflating scores to look more impressive — would defeat the actual point of the exercise, which is signal quality over signal theater.

---

## Part 4 — Reality Check

**1. What would break first at 500 companies?**
Signal collection, not scoring. The scoring math is deterministic and the strength-grading call is fast and cheap per signal, so both scale fine computationally. What breaks is getting clean, current, *deduplicated* evidence per company to type in — as seen with Atomicwork, the same funding event resurfaces in search results dated months apart. At 500 companies, manually verifying "is this actually recent" becomes impossible without a real data API (Crunchbase/PitchBook) with reliable date fields, plus deduping logic across sources. Secondarily, 500 companies × up to 8 signals each means thousands of Gemini calls, which starts to matter for rate limits and cost, though that's a solvable engineering problem (batching, caching identical evidence strings) rather than a conceptual one.

**2. What information couldn't be obtained reliably?**
Current hiring status with real confidence (job boards go stale and duplicate across aggregators); true visual/design quality of a site (only text content was reviewed here, not actual visual polish — "weak website" is a messaging-quality proxy, not a real design audit); and almost anything about a marketing leader's actual first-90-day priorities or budget authority, which really needs a human research step (LinkedIn activity, conference talks) beyond a search pass.

**3. What was deliberately left manual, and why?**
Finding and typing in the evidence itself — deciding *whether* a signal fires at all is a judgment call about source credibility and relevance that's cheap for a human researcher and risky to fully automate without a real retrieval pipeline (see Q4). Also left manual: final go/no-go on outreach (see Part 5) and ICP/company-size fit (shown with TeamViewer) — that judgment call is cheap for a human and expensive to encode robustly, so it doesn't belong in v1. Visual design audits were also left manual, since that needs either a screenshot + human eye or a vision-model call, out of scope for the time available. What's *not* manual anymore is grading how strong a given piece of evidence is once it's found — that step is now handled consistently by Gemini against a fixed rubric.

**4. With another week, what would be built next?**
A real ICP/stage filter as a hard gate before scoring (headcount + funding-stage bounds); a funding-events API integration (Crunchbase or similar) with proper date fields to kill the staleness problem; and a lightweight screenshot + vision-model pass to actually score visual design quality instead of proxying it through press-release language.

Beyond that, a genuinely retrieval-based (RAG) research stage to replace the current manual evidence-typing step: pull each company's press releases, filings, job postings, and site copy into a document store, chunk and embed them, then retrieve the top-k relevant chunks per signal (e.g. "funding announcement," "exec hire") and have an LLM extract the evidence *and* grade its strength in one pass, citing back to the exact retrieved passage. That's the natural next step from where this PoC's evidence-typing + Gemini-strength-grading pipeline currently sits — RAG is specifically about *finding* the evidence at scale from a large, unindexed corpus, which is exactly what breaks first at 500 companies (see Q1). At this PoC's scale (5 companies, evidence gathered directly via search), a full vector-store pipeline would have been over-engineering; it earns its place once the corpus is too large to search by hand.

---

## Part 5 — Business Judgement

*Scores: 91 / 84 / 79 / 73 / 68 — capacity for 2*

No, the top two shouldn't be taken automatically. A score is only as good as the signals behind it — the two highest could both be driven by the same easy-to-game signal (e.g. a funding headline) while #3 or #4 has a messier but more relevant story. Before deciding, verify: (1) is each signal genuinely recent and correctly dated, not a re-indexed old event (the Atomicwork trap above); (2) does the company genuinely fit Brandhero's ICP in size and stage, not just sector (the TeamViewer trap above); (3) is there a real, reachable decision-maker with budget authority, not just a plausible one; (4) does the specific evidence support a genuinely personalized angle, or would outreach be generic despite the high score. A 79 built on two clean, verified, ICP-fit signals is a better bet than a 91 built on one loud but stale headline.

---

## Why is signal research manual?

The assignment brief explicitly allows this: *"Use anything you want... manual steps where automation isn't sensible."* Given a 3-hour window, this system automates the parts that are genuinely reusable and consistent — grading evidence strength, and turning graded evidence into a score, need, stakeholder, and outreach angle the same way every time — while leaving evidence-gathering itself to search-assisted human research, which is where a real retrieval pipeline (out of scope here, sketched in Part 4) would take over in a v2. This split is itself an answer to Part 4, question 3.

---

## Limitations

- Not a live scraper — no company is queried automatically end-to-end. You research and type in evidence; Gemini grades it; the engine scores it.
- "Weak website" is scored from readable text/messaging, not actual visual design polish.
- No deduplication or recency-verification layer — staleness has to be caught manually right now (see the Atomicwork example).
- No ICP/company-size filter is built into the scoring math itself — it's applied as a manual override (see the TeamViewer example). This is a known gap and the first thing to fix with more time.
- Strength grading depends on Gemini API availability — a transient outage stalls collection for new companies (retried automatically with backoff, but a real outage still blocks progress).
