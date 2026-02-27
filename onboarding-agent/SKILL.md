---
name: onboarding-agent
description: >
  Manages the client onboarding process after a trade business says yes. Sends a single
  onboarding link covering plan selection, business info confirmation, domain connection,
  asset upload, and service selection. Tracks completion of each step, follows up on
  incomplete steps, collects missing assets, and triggers the Builder Agent for final
  site deployment when onboarding is complete.
version: 1.0.0
metadata:
  openclaw:
    requires:
      env:
        - CRM_API_KEY
        - PAYMENT_PROCESSOR_API_KEY
        - SENDGRID_API_KEY
        - TWILIO_ACCOUNT_SID
        - TWILIO_AUTH_TOKEN
        - TWILIO_PHONE_NUMBER
      bins:
        - curl
        - jq
    primaryEnv: CRM_API_KEY
---

# Onboarding Agent

## Purpose

Make "yes" turn into "live" with minimal friction. Send one onboarding link that handles everything — plan selection, business details, domain, assets, and services. Track progress, nudge on incomplete steps, and trigger final site build when ready.

## When This Skill Runs

- **Auto-trigger:** When human marks a lead as "won" after positive conversation
- **Auto-trigger:** When Scheduler Agent reports a positive call outcome
- **Auto-trigger:** When a prospect completes plan selection via async onboarding link
- **Manual trigger:** `/onboarding-agent <lead_id>`

## The Onboarding Form (5 Steps)

One link. One form. Five steps:

### Step 1: Choose Plan

| Plan | Price | Details |
|------|-------|---------|
| **Starter** | $497 setup + $149/month | Lower commitment, faster cash |
| **Growth** | $0 setup + $199/month (6-mo minimum) | Lower barrier, higher LTV |
| **Pro** | $0 setup + $179/month (12-mo minimum) | Best LTV, strongest commitment |

Add-ons displayed as checkboxes:
- [ ] Google Business Profile Tune-Up — $150 one-time
- [ ] Local SEO City Pages (5 pack) — $200 one-time
- [ ] Review Request Automation — $49/month
- [ ] Job Photo Gallery — $29/month
- [ ] Online Booking — $39/month
- [ ] Email/SMS Follow-Up Drip — $59/month
- [ ] Referral Engine — $39/month
- [ ] Monthly SEO Content — $99/month

### Step 2: Confirm Business Info

Pre-filled from lead record (client confirms or edits):
- Business name (legal/DBA)
- Phone number
- Email address
- Physical address
- Service area (cities/zip codes)
- Business hours
- Years in business
- License number (optional)
- Insurance info (optional)

### Step 3: Connect Domain

Options:
- **I have a domain** → enter domain name + instructions to update DNS
- **Buy one for me** → suggest 3 domain options based on business name + city, you handle registration
- **Use a subdomain for now** → deploy on `businessname.yourdomain.com`

### Step 4: Upload Assets (Optional)

- Logo (PNG, SVG, or JPG — minimum 500px wide)
- Team/owner photos
- Job photos (before/after)
- Any existing marketing materials

All optional — system uses professional stock imagery and placeholder if nothing uploaded.

### Step 5: Select Services + Service Area

- Display the category-specific service list from Creative Agent
- Client checks which services they offer
- Client confirms or adjusts service area cities
- Client can add custom services not on the list

## Process Steps

### Step 1: Send Onboarding Link

**Email template:**
```
Subject: Let's get [Business Name] live — one quick form

Hi [First Name],

Everything's ready to go! Just need a few details to launch your site.

Complete your setup here (takes about 5 minutes): [Onboarding Link]

Here's what we'll cover:
1. Pick your plan
2. Confirm your business details
3. Connect your domain
4. Upload your logo and photos (optional)
5. Choose your services and service areas

Once you're done, we'll have your site live within 48 hours.

[Your Name]
```

### Step 2: Track Completion

Monitor which steps the client has completed:

```
{
  "onboarding_status": {
    "step_1_plan": "completed",
    "step_2_info": "completed",
    "step_3_domain": "pending",
    "step_4_assets": "skipped",
    "step_5_services": "pending"
  },
  "completion_percentage": 40,
  "started_date": "2026-02-27",
  "last_activity": "2026-02-27"
}
```

### Step 3: Follow Up on Incomplete Steps

| Trigger | Action |
|---------|--------|
| Started but stopped at step 2+ | Wait 24h → send reminder with link to resume |
| Hasn't started after 48h | Send reminder email + SMS |
| Hasn't started after 96h | Escalate to human |
| Completed steps 1-2 but stuck on domain | Send simplified domain instructions or offer subdomain |
| All steps complete | Trigger final site build immediately |

**Reminder template:**
```
Hi [First Name], looks like you started setting up your site but didn't finish.
You can pick up where you left off here: [Onboarding Link]

You're [X]% done — just need [remaining steps]. — [Your Name]
```

### Step 4: Process Payment

On plan selection:
- Create customer in payment processor
- Set up recurring billing (monthly)
- If setup fee: charge immediately
- If no setup fee: first month charges immediately
- Send payment confirmation email

### Step 5: Trigger Final Build

When onboarding is complete (steps 1, 2, 3, 5 done — step 4 is optional):
- Pass all collected data to Builder Agent
- Builder Agent converts preview → production site
- Domain DNS configured
- All forms connected to client's email
- Tracking installed

### Step 6: Update CRM

```
{
  "status": "won",
  "plan": "growth",
  "monthly_revenue": 199,
  "add_ons": ["review_automation", "seo_content"],
  "add_on_revenue": 148,
  "total_monthly": 347,
  "domain": "smithplumbing.com",
  "onboarding_completed_date": "2026-03-01",
  "expected_launch_date": "2026-03-03"
}
```

## Guardrails

- **NEVER** charge a client without confirmed plan selection
- **NEVER** launch a site without confirmed business info (step 2) and services (step 5)
- **NEVER** send more than 3 onboarding reminders — escalate to human after that
- **Assets are optional** — never block a launch because photos weren't uploaded
- **Domain is flexible** — subdomain is always a fallback option
- **Payment failures:** retry once after 24h, then escalate to human

## Escalation Rules

Escalate to human when:
- Client hasn't started onboarding after 96 hours
- Payment fails on retry
- Client requests custom scope not in standard plans
- Client asks about contract terms or has legal questions
- Domain transfer is complex (registrar issues)

## Output

- Onboarding form sent with tracking link
- Client data collected and stored in CRM
- Payment processed and billing set up
- Builder Agent triggered for final site deployment
- Status updated to `won`

## Example Usage

```
/onboarding-agent lead_12345
/onboarding-agent status lead_12345
/onboarding-agent remind lead_12345
```