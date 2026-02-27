---
name: scheduler-agent
description: >
  Books kickoff meetings and sends calendar reminders when a trade business prospect
  replies positively. Manages calendar availability, sends booking links, confirms
  appointments, and sends reminders at 24h and 1h before the call. Only triggers
  on positive replies that need a call — async onboarding bypasses this agent.
version: 1.0.0
metadata:
  openclaw:
    requires:
      env:
        - CRM_API_KEY
        - CALENDAR_API_KEY
        - SENDGRID_API_KEY
        - TWILIO_ACCOUNT_SID
        - TWILIO_AUTH_TOKEN
        - TWILIO_PHONE_NUMBER
      bins:
        - curl
        - jq
    primaryEnv: CALENDAR_API_KEY
---

# Scheduler Agent

## Purpose

When a prospect says "yes" or asks questions, make booking a call effortless. Send a single calendar link, confirm the booking, and handle reminders. Most clients should onboard async — this agent only activates when a call is actually needed.

## When This Skill Runs

- **Auto-trigger:** When human marks a reply as "needs call" after handling the conversation
- **Manual trigger:** `/scheduler-agent <lead_id>`

## When a Call IS Needed vs. Async Onboarding

| Situation | Path |
|-----------|------|
| Prospect says "yes, let's do it" with no questions | Skip Scheduler → send Onboarding link directly |
| Prospect says "yes" but has questions about pricing/scope | Scheduler → book 15-min call |
| Prospect wants multiple add-ons or custom work | Scheduler → book 15-min call |
| Prospect is interested but hesitant | Scheduler → book 15-min call |
| Prospect asks a simple question answerable by text | Human answers via text → then Onboarding link |

## Process Steps

### Step 1: Send Booking Link

Send a personalized booking message with a single calendar link:

**Email template:**
```
Subject: Let's get [Business Name] set up — pick a time

Hi [First Name],

Great to hear from you! Let's jump on a quick 15-minute call to get everything
sorted for [Business Name].

Pick a time that works for you: [Calendar Link]

Talk soon,
[Your Name]
```

**SMS template:**
```
Hi [First Name]! Here's a link to book a quick 15-min call about your new site:
[Calendar Link] — [Your Name]
```

### Step 2: Monitor for Booking

- Check calendar for new booking from this lead (match by email or phone)
- If booked within 48 hours → proceed to Step 3
- If not booked after 48 hours → send one reminder:

```
Hi [First Name], just bumping this in case it got buried. Here's the link
again to grab a quick time: [Calendar Link] — [Your Name]
```

- If not booked after 96 hours → notify human for manual follow-up

### Step 3: Confirm Booking

On booking confirmation:

```
Subject: Confirmed: [Date] at [Time] — [Business Name] kickoff

Hi [First Name],

You're all set for [Date] at [Time]. I'll call you at [lead.phone].

We'll cover:
- Your top services and service area
- How the site and quote capture system works
- Choosing your plan
- Next steps to go live

Talk then!
[Your Name]
```

Update CRM: log booking date/time, set `call_scheduled = true`

### Step 4: Send Reminders

- **24 hours before:** Email reminder with call details
- **1 hour before:** SMS reminder

```
Quick reminder: we're chatting at [Time] today about [Business Name]'s new site.
I'll call you at [lead.phone]. — [Your Name]
```

### Step 5: Post-Call

After the call (human marks call as completed):
- If moving forward → trigger Onboarding Agent
- If needs time to decide → schedule a follow-up reminder in 3 days
- If declined → update status to `lost` (reason: "declined after call")

## Calendar Configuration

| Setting | Value |
|---------|-------|
| Meeting duration | 15 minutes |
| Buffer between meetings | 15 minutes |
| Available hours | Mon–Fri, 9am–5pm your local time |
| Max meetings per day | 6 |
| Booking window | Next 14 days |
| No-show follow-up | Auto-send reschedule link after 15 min past start time |

## Guardrails

- **NEVER** book calls on weekends unless prospect specifically requests it
- **NEVER** send more than 2 booking reminders (initial link + 1 bump)
- **NEVER** auto-reschedule without prospect confirmation
- **Max 1 reminder SMS and 1 reminder email per scheduled call**
- **No-show:** send one reschedule link, then escalate to human if no response

## Escalation Rules

Escalate to human when:
- Prospect doesn't book after 96 hours and 2 attempts
- Prospect no-shows and doesn't respond to reschedule link
- Prospect requests a time outside available hours
- Calendar API errors prevent booking

## Output

- Calendar event created with prospect details
- Confirmation and reminder messages sent
- CRM updated with call status and outcome
- Onboarding Agent triggered on positive call outcome

## Example Usage

```
/scheduler-agent lead_12345
/scheduler-agent reschedule lead_12345
```