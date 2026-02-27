---
name: creative-agent
description: >
  Generates website copy, page structure, and audit PDF content for trade business
  preview sites. Uses 3 personalization inputs (trade type, city/service area, review themes)
  to customize 80% templated content into business-specific assets. Produces copy for
  Home, Services, Service Area, Reviews, Quote Request, and About pages plus a one-page
  Audit & Opportunities document. Triggers when a qualified lead (Tier A or B) is ready
  for asset generation.
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

# Creative Agent

## Purpose

Generate all the copy and content needed for a preview website and audit PDF. The output is a complete copy package that the Builder Agent uses to deploy a live preview. Every asset is 80% templated, 20% personalized using three inputs from the lead record.

## When This Skill Runs

- **Auto-trigger:** When Qualifier Agent sets a Tier A lead to `qualified` (immediate)
- **Batch trigger:** Daily batch for Tier B leads in `qualified` status
- **Manual trigger:** `/creative-agent <lead_id>`

## The 3 Personalization Inputs

Everything this agent produces is customized using ONLY these three data points:

| Input | Source | Example |
|-------|--------|---------|
| **Trade type + top 5 services** | Lead category + service lookup table | Plumbing: drain cleaning, water heater install, leak repair, repiping, sewer line |
| **City / service area** | `lead.city` + `lead.service_area[]` | Denver, CO — serving Lakewood, Aurora, Arvada, Littleton, Centennial |
| **Top 3 review themes** | `lead.review_themes[]` from Qualifier Agent | "fast response times", "fair and transparent pricing", "thorough cleanup" |

## Service Lookup Table

Each trade category maps to a default set of 6–10 services. Use these unless the lead's GBP listing shows different specialties.

### Plumbing
Drain cleaning, Water heater install & repair, Leak detection & repair, Repiping, Sewer line repair & replacement, Fixture installation, Garbage disposal, Gas line services, Bathroom/kitchen plumbing, Emergency plumbing

### HVAC
AC installation, AC repair & maintenance, Furnace installation, Furnace repair, Ductwork, Mini-split systems, Thermostat installation, Indoor air quality, Maintenance plans, Emergency HVAC

### Electrical
Panel upgrades, Rewiring, EV charger installation, Lighting installation, Generator install & repair, Outlet & switch repair, Ceiling fan installation, Whole-home surge protection, Code compliance, Emergency electrical

### Roofing
Shingle roof install, Metal roof install, Roof repair, Roof inspection, Gutter installation, Storm damage repair, Flat roof systems, Skylight installation, Attic ventilation, Emergency tarping

### Landscaping
Lawn care & mowing, Hardscape (patios, walkways), Irrigation systems, Tree & shrub planting, Mulching & bed maintenance, Seasonal cleanup, Landscape design, Retaining walls, Outdoor lighting, Drainage solutions

### Arborists
Tree removal, Tree trimming & pruning, Stump grinding, Emergency storm cleanup, Tree health assessment, Cabling & bracing, Land clearing, Hedge trimming, Tree planting, Arborist consulting

### Carpentry
Framing, Trim & molding, Custom cabinetry, Deck building, Porch construction, Door & window installation, Shelving & built-ins, Wood repair & restoration, Pergolas & gazebos, Finish carpentry

### Fence/Deck
Wood fence install, Vinyl fence install, Chain link fence, Deck building, Deck staining & sealing, Fence repair, Gate installation, Pergola building, Railing install, Privacy screening

### Junk Removal
Residential junk removal, Commercial cleanout, Appliance removal, Furniture removal, Construction debris, Estate cleanout, Garage cleanout, Hot tub removal, E-waste disposal, Yard waste removal

## Output: Copy Package

The Creative Agent produces a structured copy package with content for every page:

### Page 1 — Home

```
hero_headline: "[Review theme]-driven [trade type] in [City]"
hero_subheadline: "Trusted by [City] homeowners for [review theme 1] and [review theme 2]"
hero_cta: "Get a Free Quote"
trust_badges: ["Licensed & Insured", "X+ Years Experience", "5-Star Rated"]
intro_paragraph: 2-3 sentences about the business using review themes as angles
services_preview: Top 4 services with icons and short descriptions
review_highlight: 1 paraphrased review quote
final_cta: "Ready to get started? Request your free quote today."
```

### Page 2 — Services

For each of the top 6–10 services:
```
service_name: ""
service_description: "2-3 sentences explaining the service"
service_cta: "Request a Quote for [Service Name]"
```

### Page 3 — Service Area

```
main_city: "[City]"
surrounding_areas: list from lead.service_area[]
area_description: "Proudly serving [City] and surrounding communities including [areas]."
map_embed: true
local_seo_paragraph: 1 paragraph with natural keyword placement for [trade] + [city]
```

### Page 4 — Reviews

```
reviews_intro: "See why [City] homeowners trust [Business Name]"
review_themes_summary: paragraph summarizing what customers love (paraphrased, never verbatim)
google_reviews_embed: true (widget or link to GBP)
cta: "Join hundreds of satisfied customers. Get your free quote."
```

### Page 5 — Quote Request

```
form_headline: "Get Your Free Quote"
form_subheadline: "Tell us about your project and we'll get back to you within [X hours]."
form_fields: ["Name", "Phone", "Email", "Address", "Service Needed (dropdown)", "Describe Your Project", "Upload Photos (optional)"]
confirmation_message: "Thanks! We've received your request and will be in touch shortly."
```

### Page 6 — About (optional placeholder)

```
about_headline: "About [Business Name]"
about_placeholder: "Family-owned [trade type] business serving [City] and surrounding areas."
team_photos: placeholder for client-uploaded images
values: ["Quality Workmanship", "Honest Pricing", "Customer-First Approach"]
```

## Output: Audit & Opportunities PDF Content

A one-page document with 4 sections:

```
section_1_current_state:
  title: "What's Missing"
  bullets:
    - "No website" OR "Outdated website (not mobile-friendly)"
    - "No online quote request form"
    - "No missed-call text-back system"
    - "No automated review collection"

section_2_customer_love:
  title: "What Your Customers Love"
  paragraph: "Based on your [X] Google reviews, customers consistently highlight your [theme 1], [theme 2], and [theme 3]. This is a strong foundation to build on."

section_3_opportunity:
  title: "The Opportunity"
  paragraph: "With a modern website and quote capture system, businesses like yours typically see [conservative range] additional monthly inquiries. Combined with your strong reviews, this positions [Business Name] to capture leads that currently go to competitors with better online presence."
  note: "Framed as potential, not a guarantee."

section_4_preview:
  title: "We Built You a Preview"
  cta: "See your preview site: [Preview Link]"
  subcta: "Want us to transfer it to you? Reply to this message."
```

## Guardrails

- **NEVER** copy Google reviews verbatim — only use paraphrased themes
- **NEVER** claim "24/7 emergency service" unless the business explicitly advertises it on their GBP
- **NEVER** fabricate credentials (years in business, license numbers, certifications)
- **NEVER** make specific ROI promises — always frame as "potential" or "typical range"
- **Keep copy concise** — trades don't read long paragraphs. Short sentences, clear value.
- **Tone:** professional but approachable. No marketing jargon. Write like a helpful neighbor, not an agency.

## Escalation Rules

Escalate to human when:
- Lead's GBP mentions licensing/certifications that can't be verified
- Business name contains legal terms that might need review (e.g., "Emergency", "Guaranteed")
- Review themes are negative or mixed — unclear how to position the business positively
- Trade category doesn't match any template (edge case business type)

## Example Usage

```
/creative-agent lead_12345
/creative-agent batch --tier B
```