---
name: outreach-agent
description: >
  Sends personalized email and SMS outreach to trade business leads with a preview site
  link. Manages two outreach lanes: "Preview Is Ready" for businesses without websites,
  and "Stop Losing After-Hours Leads" for businesses lacking lead capture. Runs automated
  4-touch follow-up sequences over 10 days. Stops immediately on any reply and escalates
  to human. Triggers when Builder Agent deploys a preview (status: preview_built).
version: 1.0.0
metadata:
  openclaw:
    requires:
      env:
        - CRM_API_KEY
        - SENDGRID_API_KEY
        - TWILIO_ACCOUNT_SID
        - TWILIO_AUTH_TOKEN
        - TWILIO_PHONE_NUMBER
      bins:
        - curl
        - jq
    primaryEnv: SENDGRID_API_KEY
---

# Outreach Agent

## Purpose

Deliver the preview site to prospects in a way that feels helpful, not spammy. Two outreach lanes target different pain points. Automated follow-ups handle timing. The agent stops the moment a prospect replies and hands off to you.

## When This Skill Runs

- **Auto-trigger:** When Builder Agent sets status to `preview_built`
- **Scheduled:** Follow-up sequence runs automatically at Day 2, 5, and 10
- **Manual trigger:** `/outreach-agent <lead_id>` or `/outreach-agent pause <lead_id>`

## Lane Selection Logic

| Condition | Lane | Hook |
|-----------|------|------|
| `lead.has_website == false` | Lane 1: "Preview Is Ready" | Your site is already built |
| `lead.has_website == true` AND no quote form detected | Lane 2: "After-Hours Leads" | You're losing leads |
| `lead.has_website == true` AND has quote form | Lane 2 (variant) | Missed-call text-back focus |

## Message Templates

### Lane 1: "Your Preview Is Ready"

**Day 0 — Initial (Email + SMS)**

Email subject: `I built something for [Business Name]`

Email body:
```
Hi [First Name],

I came across [Business Name] and noticed your customers love your [review theme 1].
I put together a preview of what a modern site could look like for you — takes
30 seconds to check out:

[Preview Link]

If you like it, I can transfer it to you. No pressure either way.

— [Your Name]
[Your Phone]
```

SMS:
```
Hi [First Name], I put together a website preview for [Business Name] based on
your great reviews. Take a look: [Preview Link] — [Your Name]
```

**Day 2 — Follow-up (Email or SMS, not both)**

```
Hi [First Name], just wanted to make sure you saw the preview I put together
for [Business Name]: [Preview Link]

Happy to walk you through it or make changes if anything's off. — [Your Name]
```

**Day 5 — Value add (Email)**

Subject: `Quick idea for [Business Name]`

```
Hi [First Name],

One thing I noticed — most [trade type] businesses lose 30-40% of leads that come
in after hours or when they're on a job.

I can add a missed-call text-back system to your site so callers get an instant
response even when you can't pick up. Combined with the quote capture form, you'd
catch a lot more jobs.

Here's the preview again if you want another look: [Preview Link]

— [Your Name]
```

**Day 10 — Close the loop (Email)**

Subject: `Closing the loop`

```
Hi [First Name],

Totally understand if the timing isn't right. I'll keep your preview live for
another 20 days in case you want to revisit: [Preview Link]

If you ever want to chat about getting more calls from online, just reply here.
No hard feelings either way.

— [Your Name]
```

### Lane 2: "Stop Losing After-Hours Leads"

**Day 0 — Initial (Email + SMS)**

Email subject: `Quick question about after-hours calls`

```
Hi [First Name],

Most [trade type] businesses lose 30-40% of leads that come in after hours or
when they're on a job.

I set up a system that instantly texts back missed callers and captures quote
requests 24/7. Would that be useful for [Business Name]?

Happy to show you how it works. — [Your Name]
```

SMS:
```
Hi [First Name], quick question — do you have a way to capture leads when you
can't answer the phone? I help [trade type] businesses with that. — [Your Name]
```

**Day 2, 5, 10:** Same cadence as Lane 1, adjusted to focus on lead capture pain point.

## Sending Rules

| Rule | Setting |
|------|---------|
| Max touches per lead | 4 (initial + 3 follow-ups) |
| Min gap between messages | 48 hours |
| Max messages per day (per lead) | 1 |
| Send window | Mon–Fri, 8am–6pm local time |
| No sending on | Weekends, major holidays |
| SMS opt-out | Honor "STOP" immediately, log and never SMS again |
| Email unsubscribe | Include unsubscribe link in every email, honor immediately |

## Process Steps

### Step 1: Determine Lane and Channel

- Check lane selection logic
- Check available channels: email (if `lead.email != null`), SMS (if `lead.phone != null`)
- If only phone available: SMS only
- If only email available: email only
- If both available: email + SMS on Day 0, alternate on follow-ups

### Step 2: Personalize Message

Replace all placeholders:
- `[First Name]` — from lead record (use business name if no first name)
- `[Business Name]` — from lead record
- `[trade type]` — from lead category (lowercase, e.g., "plumbing")
- `[review theme 1]` — from `lead.review_themes[0]`
- `[Preview Link]` — from `lead.preview_url`
- `[Your Name]` — from your sender profile config
- `[Your Phone]` — from your sender profile config

### Step 3: Send Initial Message

- Send via SendGrid (email) and/or Twilio (SMS)
- Log message in CRM: timestamp, channel, template used, message ID
- Update status to `contacted`

### Step 4: Schedule Follow-Ups

- Queue Day 2, Day 5, and Day 10 messages
- Each queued message checks for reply before sending (if replied → cancel remaining)

### Step 5: Monitor for Replies

- Check for email replies (via SendGrid inbound parse or IMAP)
- Check for SMS replies (via Twilio webhook)
- On ANY reply:
  1. Immediately cancel all remaining follow-ups
  2. Update status to `replied`
  3. Notify human (you) with the reply content
  4. Do NOT auto-respond — human handles from here

### Step 6: Sequence Complete (No Reply)

If all 4 touches sent and no reply:
- Update status to `lost` (reason: "no response after full sequence")
- Move to nurture list (monthly check-in, re-score in 90 days)

## Guardrails

- **NEVER** send more than 4 messages to a single lead
- **NEVER** send on weekends or outside 8am–6pm local time
- **NEVER** auto-respond to replies — human handles all conversations
- **NEVER** send to leads that are already clients (status: `won`, `live`, `retained`)
- **NEVER** ignore STOP/unsubscribe requests — process immediately
- **NEVER** use aggressive or misleading subject lines
- **Tone:** helpful neighbor, not aggressive salesperson
- **Compliance:** include physical address and unsubscribe link in all emails (CAN-SPAM)

## Escalation Rules

Escalate to human IMMEDIATELY when:
- Any reply received (positive, negative, or question)
- Email bounces (bad address — needs enrichment)
- SMS delivery failure (bad number)
- Prospect replies with legal threat or angry message
- Unsubscribe rate exceeds 5% in any batch

## Output

Each run produces:
- Messages sent with timestamps and delivery status
- CRM records updated (status: `contacted` or `replied`)
- Scheduled follow-ups queued
- Escalation notifications if triggered

## Example Usage

```
/outreach-agent lead_12345
/outreach-agent pause lead_12345
/outreach-agent batch --tier A
/outreach-agent stats --last 7d
```