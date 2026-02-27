---
name: fulfillment-agent
description: >
  Manages post-launch operations for live trade business clients. Handles site launch
  deployment, sets up tracking and forms, generates monthly performance reports (traffic,
  leads, calls, reviews), publishes monthly SEO content, manages before/after photo posts
  to Google Business Profile, detects upsell opportunities based on client data, and
  monitors retention signals. Triggers on client status change to "live" and runs monthly
  reporting cycle on the 1st of each month.
version: 1.0.0
metadata:
  openclaw:
    requires:
      env:
        - CRM_API_KEY
        - ANALYTICS_API_KEY
        - GBP_API_KEY
        - SENDGRID_API_KEY
        - TWILIO_ACCOUNT_SID
        - TWILIO_AUTH_TOKEN
        - TWILIO_PHONE_NUMBER
        - CALL_TRACKING_API_KEY
      bins:
        - curl
        - jq
    primaryEnv: CRM_API_KEY
---

# Fulfillment Agent

## Purpose

This is where profit compounds. Launch client sites, deliver measurable value every month, detect upsell opportunities, and monitor retention. The goal: clients stay for 12+ months because they see real results.

## When This Skill Runs

- **Auto-trigger:** When Onboarding Agent completes and Builder Agent deploys final site (status → `live`)
- **Scheduled:** Monthly reporting cycle on 1st of each month for all `live` and `retained` clients
- **Scheduled:** Weekly check for upsell triggers and retention signals
- **Manual trigger:** `/fulfillment-agent <client_id>` or `/fulfillment-agent report <client_id>`

## Phase 1: Site Launch

When a client moves to `live` status, execute this checklist:

### Launch Checklist

1. **Deploy production site**
   - Move from preview subdomain to client's domain
   - Verify all pages, forms, and CTAs work on production URL
   - Verify SSL is active

2. **Install tracking**
   - Google Analytics (GA4) property created and connected
   - Call tracking number provisioned and forwarded to client's real number
   - Form submission logging active (each submission → email to client + CRM log)

3. **Configure automations**
   - Missed-call text-back: when call goes unanswered → auto-SMS to caller within 60 seconds
   - Quote form auto-confirmation: SMS + email to the person who submitted
   - New lead notification: email + SMS to client when a form is submitted or call comes in

4. **Set up review automation** (if purchased as add-on)
   - Post-job SMS trigger: client marks job complete → system sends review request to customer
   - Review request template: "Thanks for choosing [Business Name]! Would you mind leaving a quick review? [Google Review Link]"

5. **First Google Business Profile post**
   - Create and publish a post about the new website launch
   - Include a link to the site

6. **Send "You're Live!" notification to client**

```
Subject: [Business Name] is live!

Hi [First Name],

Your new site is live at [Domain]! Here's what's set up and working:

- Your website with [X] service pages
- Quote request form (you'll get email + text notifications for every submission)
- Missed-call text-back (callers get an instant response when you can't pick up)
- Click-to-call and SMS buttons
[If review automation] - Automated review requests after each job

You'll get your first monthly performance report on [1st of next month].

If you need anything, just reply here. Welcome aboard!

[Your Name]
```

## Phase 2: Monthly Value Delivery

Run on the 1st of every month for every `live` and `retained` client.

### Monthly Report Contents

```
MONTHLY PERFORMANCE REPORT — [Month Year]
[Business Name] | [Domain]

WEBSITE TRAFFIC
- Total visitors: [X]
- Unique visitors: [X]
- Top traffic sources: [organic, direct, referral]
- Mobile vs desktop split: [X]% / [X]%

LEADS CAPTURED
- Form submissions: [X]
- Phone calls received: [X]
- Missed-call text-backs sent: [X]
- Total leads: [X]

GOOGLE REVIEWS
- New reviews this month: [X]
- Current rating: [X.X] ([Total] reviews)
- Rating trend: [up/stable/down]

CONTENT PUBLISHED
- Blog post: "[Title]" — published [Date]
- GBP post: "[Title]" — published [Date]

NEXT MONTH
- Planned content: [Topic]
- Recommendations: [based on data]
```

### Monthly Content Production

For each client, generate and publish:

1. **1 blog post or service page** (Creative Agent generates, Builder Agent publishes)
   - Rotate between: seasonal tips, service deep-dives, local area content, FAQ answers
   - Include local SEO keywords naturally
   - 400–600 words

2. **1 Google Business Profile post**
   - Highlight a recent job, seasonal offer, or tip
   - Include a photo if available
   - Link back to the website

3. **Before/after photo posts** (if client submits photos)
   - Client uploads via a simple link
   - Agent formats and posts to GBP with description

### Report Delivery

- Generate PDF report
- Email to client on 1st of month
- Store report in CRM for historical tracking
- If client hasn't opened last 2 reports → flag for retention check

## Phase 3: Upsell Detection

Run weekly scans on all client data to identify upsell opportunities:

| Trigger | Upsell Opportunity | Action |
|---------|-------------------|--------|
| High traffic (500+/mo) but low form submissions (<5) | Quote form optimization, live chat | Flag for human to pitch |
| 50+ reviews but no review automation | Review request add-on ($49/mo) | Auto-send pitch email |
| Only 1 service area page | Service area expansion pack ($200) | Auto-send pitch email |
| No social media presence detected | GBP management add-on | Flag for human to pitch |
| 6+ months active, high engagement | PPC / local service ads | Flag for human to pitch |
| Client submits job photos regularly | Job photo gallery add-on ($29/mo) | Auto-send pitch email |
| High call volume, no booking system | Online booking add-on ($39/mo) | Auto-send pitch email |

### Upsell Email Template (automated)

```
Subject: Quick idea to get more from your site

Hi [First Name],

Looking at your [Month] numbers, I noticed [specific observation].

[Specific recommendation — 2-3 sentences explaining the value].

Want me to add this to your plan? It's [price] and I can have it live this week.

Just reply "yes" or let me know if you have questions.

[Your Name]
```

**Rules:** max 1 upsell pitch per client per month. Never pitch in the same email as the monthly report. Only pitch add-ons the client doesn't already have.

## Phase 4: Retention Monitoring

### Healthy Client Signals
- Opens monthly reports
- Submits job photos
- Refers other businesses
- Responds to messages within 48 hours
- Steady or growing traffic/leads

### At-Risk Client Signals
- Hasn't opened last 2 monthly reports
- No form submissions in 30+ days
- Payment failed (even once)
- Sent a complaint or negative message
- Traffic declining for 2+ consecutive months

### Retention Actions

| Signal | Action |
|--------|--------|
| 2 unopened reports | Send a personal check-in email (not automated) |
| No leads in 30 days | Investigate — is the form working? Is traffic dropping? Fix and report to client |
| Payment failed | Auto-retry in 24h, then escalate to human |
| Complaint received | Escalate to human immediately |
| Traffic declining 2+ months | Review SEO, check for technical issues, report findings to client |
| 3 months active, no issues | Update status to `retained`, send a thank-you message |

### Client Status Progression

- `live` → `retained` (after 3 months of active service, no issues)
- `live` or `retained` → `churned` (cancelled or payment failed permanently)

## Guardrails

- **NEVER** send a report with fabricated data — if tracking is broken, report "data unavailable" and fix
- **NEVER** publish content without running through the Creative Agent's guardrails (no false claims, no copied reviews)
- **NEVER** pitch more than 1 upsell per client per month
- **NEVER** auto-respond to client complaints — escalate to human
- **Report accuracy:** verify all numbers against source data before sending
- **Content quality:** every blog post must be unique per client (no duplicate content across clients)

## Escalation Rules

Escalate to human when:
- Client replies to a report or upsell pitch (any reply)
- Payment fails on retry
- Client requests cancellation
- Tracking/analytics broken and can't auto-fix
- Client receives 3+ negative reviews in 30 days
- Client complains about anything
- Upsell accepted (human confirms scope and activates)

## Output

- Monthly reports generated and emailed
- Content published (blog + GBP post)
- Upsell opportunities flagged or pitched
- Retention status monitored and updated
- CRM records updated with all activity

## Example Usage

```
/fulfillment-agent launch client_12345
/fulfillment-agent report client_12345
/fulfillment-agent report-all
/fulfillment-agent upsell-scan
/fulfillment-agent retention-check
```