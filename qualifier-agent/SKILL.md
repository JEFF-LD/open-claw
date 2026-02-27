---
name: qualifier-agent
description: >
  Scores trade business leads 0-100 based on Google rating, review count, website presence,
  review recency, and review themes. Assigns tier (A/B/C/D) and determines next action.
  Disqualifies franchises, businesses with polished sites and active ads, and low-review-count
  businesses. Triggers on any new lead record or monthly re-score batch.
version: 1.0.0
metadata:
  openclaw:
    requires:
      env:
        - CRM_API_KEY
      bins:
        - jq
    primaryEnv: CRM_API_KEY
---

# Qualifier Agent

## Purpose

Score every lead 0–100 so the system automatically prioritizes the easiest wins — businesses with strong reputations but weak digital presence. Assign a tier and determine the next action in the pipeline.

## When This Skill Runs

- **Auto-trigger:** When Prospector Agent writes a new lead (status: `new`)
- **Scheduled:** Monthly re-score of all leads not in `won`, `live`, or `retained` status
- **On demand:** `/qualifier-agent <lead_id>` or `/qualifier-agent batch`

## Scoring Model (0–100 Points)

### Positive Signals

| Signal | Points | How to Check |
|--------|--------|-------------|
| Rating 4.6 or higher | +20 | `lead.rating >= 4.6` |
| 30+ Google reviews | +15 | `lead.review_count >= 30` |
| No website OR very outdated site | +25 | `lead.has_website == false` OR site fails mobile/speed check |
| Reviews in last 90 days | +10 | Check most recent review date from GBP data |
| Review themes: responsive, fair, clean, punctual | +10 | Paraphrase scan of recent review snippets |
| Service area clearly defined on GBP | +5 | GBP listing has service area cities listed |
| Email address found | +5 | `lead.email != null` |
| Phone verified (answers or has voicemail) | +5 | Optional enrichment check |
| Active on social media (Facebook/Instagram) | +5 | Profile exists with posts in last 90 days |

**Maximum possible score: 100**

### Disqualifiers (Auto-Exclude)

Apply these BEFORE scoring. If any match, set score to 0 and status to `disqualified`:

- **Franchise with corporate website** — URL belongs to a franchise domain (e.g., `mrplumber.com/locations/...`)
- **Negative review trend** — 3+ reviews at 1-2 stars in the last 60 days
- **Out of service area** — business is outside your operational geography
- **Already a client** — status is `won`, `live`, or `retained`

### Deprioritize Signals (Score Penalties)

| Signal | Penalty | Reason |
|--------|---------|--------|
| Already running Google Ads | -15 | Has marketing budget, harder sell |
| Polished, modern website | -20 | Less pain point |
| Under 10 reviews | -10 | Harder to build trust, less copy material |
| No phone number found | -10 | Can't reach them easily |

## Tier Assignment

After scoring, assign a tier:

| Tier | Score Range | Action | Expected Volume |
|------|------------|--------|----------------|
| **A** | 85–100 | Build preview IMMEDIATELY, outreach within 24 hours | 15–20% of leads |
| **B** | 60–84 | Batch preview build, outreach within 1 week | 30–40% of leads |
| **C** | 30–59 | Add to nurture drip, revisit monthly | 25–30% of leads |
| **D** | 0–29 | Archive, check quarterly | 15–25% of leads |

## Process Steps

### Step 1: Check Disqualifiers

Run disqualifier checks first. If any match → set score to 0, status to `disqualified`, stop.

### Step 2: Calculate Base Score

Apply each positive signal check. Sum the points.

### Step 3: Apply Penalties

Check for deprioritize signals. Subtract penalties. Floor at 0.

### Step 4: Extract Review Themes

From available review snippets (do NOT copy verbatim):
- Identify top 3 recurring themes (e.g., "fast response", "fair pricing", "clean work")
- Paraphrase into short phrases
- Store as `lead.review_themes[]` — these feed directly into the Creative Agent

### Step 5: Assign Tier + Next Action

Based on final score:
- **Tier A:** Set status to `qualified`, flag for immediate preview build
- **Tier B:** Set status to `qualified`, add to next preview batch
- **Tier C:** Set status to `qualified`, add to nurture queue
- **Tier D:** Set status to `qualified`, add to archive

### Step 6: Write to CRM

Update the lead record:
```
{
  "score": 87,
  "tier": "A",
  "review_themes": ["fast response times", "fair and transparent pricing", "thorough cleanup"],
  "disqualified": false,
  "disqualify_reason": null,
  "scored_date": "2026-02-27",
  "next_action": "preview_build_immediate",
  "status": "qualified"
}
```

## Guardrails

- **NEVER** copy review text verbatim — only extract paraphrased themes
- **NEVER** contact leads from this agent — scoring only
- **Re-score on data change:** if a lead gets new reviews or updates their website, re-score
- **Log every scoring decision** — store the breakdown so you can audit and improve the model

## Escalation Rules

Escalate to human when:
- **Score > 85 AND no email found** — high-value lead needs manual enrichment decision
- **Score changes by more than 30 points** on re-score — something significant changed
- **More than 50% of a batch scores below 30** — possible data quality issue or wrong metro

## Output

Each run produces:
- Updated lead records with scores, tiers, review themes
- Run summary: total scored, tier distribution (A/B/C/D counts), disqualified count
- Escalation flags if any triggers hit

## Example Usage

```
/qualifier-agent lead_12345
/qualifier-agent batch
/qualifier-agent rescore --metro "Denver, CO"
```