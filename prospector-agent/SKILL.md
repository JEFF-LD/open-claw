---
name: prospector-agent
description: >
  Sources and collects local trade business leads from data providers, Google Places API,
  and public directories. Normalizes data, deduplicates against existing CRM records,
  and enriches missing fields. Targets: plumbing, HVAC, electrical, roofing, landscaping,
  arborists, carpentry, fence/deck, junk removal. Triggers on new sourcing requests
  or scheduled weekly batch runs per metro area.
version: 1.0.0
metadata:
  openclaw:
    requires:
      env:
        - GOOGLE_PLACES_API_KEY
        - CRM_API_KEY
        - DATA_PROVIDER_API_KEY
      bins:
        - curl
        - jq
    primaryEnv: GOOGLE_PLACES_API_KEY
---

# Prospector Agent

## Purpose

Find local trade businesses that match the ideal client profile: strong reputation, weak or missing digital presence. Collect structured lead data, deduplicate against the CRM, and enrich missing fields before handing off to the Qualifier Agent.

## When This Skill Runs

- **Scheduled:** Weekly batch per metro area (configurable)
- **On demand:** When a new target metro or trade category is added
- **Manual trigger:** `/prospector-agent <category> <metro>`

## Target Trade Categories

| Category | Search Terms |
|----------|-------------|
| Plumbing | plumber, plumbing, drain cleaning, water heater |
| HVAC | hvac, air conditioning, heating, furnace |
| Electrical | electrician, electrical contractor, wiring |
| Roofing | roofer, roofing contractor, roof repair |
| Landscaping | landscaper, landscaping, lawn care, hardscape |
| Arborists | arborist, tree service, tree removal, tree trimming |
| Carpentry | carpenter, carpentry, custom woodwork, framing |
| Fence/Deck | fence company, deck builder, fencing contractor |
| Junk Removal | junk removal, hauling, debris removal, cleanout |

## Data Fields to Collect (Minimum Viable)

Every lead record MUST contain these fields:

```
{
  "business_name": "",       // Exact legal/DBA name
  "phone": "",               // Primary phone number
  "email": "",               // If publicly available (null if not found)
  "category": "",            // One of the 9 target categories
  "city": "",                // Primary city
  "neighborhood": "",        // If available
  "service_area": [],        // List of cities/areas served
  "rating": 0.0,             // Google rating (1.0-5.0)
  "review_count": 0,         // Total Google reviews
  "has_website": false,      // true/false
  "website_url": "",         // If has_website is true
  "gbp_link": "",            // Google Business Profile URL or place_id
  "source": "",              // Where this lead was found
  "sourced_date": "",        // ISO date
  "status": "new"            // Always starts as "new"
}
```

## Process Steps

### Step 1: Query Data Sources

Query sources in this priority order. Stop once you hit your batch target (default: 50 leads per metro per run).

1. **Google Places API** — search by category + metro area
   - Use the `textsearch` or `nearbysearch` endpoint
   - Extract: name, phone, rating, review count, place_id, website, address
   - Respect API rate limits and quotas

2. **Licensed directories** (Data Axle, InfoGroup, Yelp API if available)
   - Cross-reference for email addresses and additional data
   - These are cleaner but may cost per query

3. **State licensing boards** (if accessible via API or structured data)
   - Use for verification, not primary sourcing
   - Adds trust signal: "licensed and verified"

4. **Industry association directories**
   - Small volume but pre-qualified leads

### Step 2: Normalize Data

- Standardize phone format to `+1XXXXXXXXXX`
- Standardize city names (no abbreviations, proper capitalization)
- Map business to exactly ONE of the 9 target categories
- Clean business name (remove "LLC", "Inc" unless it's the actual DBA)
- Validate rating is between 1.0 and 5.0
- Validate review count is a positive integer

### Step 3: Deduplicate

Before adding any lead to the CRM:

1. Check for existing record by phone number (primary key)
2. Check for existing record by business name + city (secondary)
3. If match found: skip (do NOT create duplicate)
4. If no match: proceed to Step 4

### Step 4: Enrich Missing Fields

If email is missing:
- Check the business website for contact email
- Check Facebook/LinkedIn business pages
- If still not found: set email to null (Qualifier Agent will flag for manual enrichment if score is high)

### Step 5: Write to CRM

- Create new lead record with status = `new`
- Log the data source and timestamp
- Trigger the Qualifier Agent for scoring

## Guardrails

- **NEVER** scrape Google reviews verbatim — only collect rating and review count
- **NEVER** contact a lead from this agent — that's the Outreach Agent's job
- **NEVER** create a duplicate record — always dedupe first
- **Max batch size:** 100 leads per run (prevents API cost blowouts)
- **Rate limiting:** respect all API rate limits, add exponential backoff on 429 errors
- **Data freshness:** re-source any lead that hasn't been updated in 90+ days

## Escalation Rules

Escalate to human when:
- API quota is exhausted and batch is incomplete
- Data source returns unexpected format (schema changed)
- More than 20% of leads in a batch fail validation

## Output

Each run produces:
- New lead records in CRM (status: `new`)
- Run summary: total queried, total valid, total duplicates skipped, total added
- Errors log if any leads failed validation

## Example Usage

```
/prospector-agent plumbing "Denver, CO"
/prospector-agent hvac "Austin, TX"
/prospector-agent roofing "Phoenix, AZ"
```