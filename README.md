# Trades Growth System — OpenClaw Skills

## 8 Agent Skills for Autonomous Local Trades Business Growth

### Installation

1. Copy all 8 skill folders into your OpenClaw skills directory:
   ```
   cp -r *-agent ~/.openclaw/workspace/skills/
   ```

2. Set your environment variables (see each SKILL.md for required keys):
   ```
   # Core
   export CRM_API_KEY="your-crm-key"
   export GOOGLE_PLACES_API_KEY="your-places-key"

   # Email & SMS
   export SENDGRID_API_KEY="your-sendgrid-key"
   export TWILIO_ACCOUNT_SID="your-twilio-sid"
   export TWILIO_AUTH_TOKEN="your-twilio-auth"
   export TWILIO_PHONE_NUMBER="+1XXXXXXXXXX"

   # Site Building
   export SITE_BUILDER_API_KEY="your-builder-key"
   export HOSTING_API_KEY="your-hosting-key"

   # Payments
   export PAYMENT_PROCESSOR_API_KEY="your-stripe-key"

   # Analytics & GBP
   export ANALYTICS_API_KEY="your-ga4-key"
   export GBP_API_KEY="your-gbp-key"
   export CALL_TRACKING_API_KEY="your-tracking-key"

   # Optional
   export DATA_PROVIDER_API_KEY="your-data-provider-key"
   export PDF_GENERATOR_API_KEY="your-pdf-key"
   export CALENDAR_API_KEY="your-calendar-key"
   ```

3. Restart OpenClaw or wait for hot-reload.

### Agent Pipeline

```
Prospector → Qualifier → Creative → Builder → Outreach → Scheduler → Onboarding → Fulfillment
```

### Quick Reference

| Agent | Trigger Command | Purpose |
|-------|----------------|---------|
| Prospector | `/prospector-agent plumbing "Denver, CO"` | Source leads |
| Qualifier | `/qualifier-agent batch` | Score leads 0-100 |
| Creative | `/creative-agent lead_12345` | Generate site copy |
| Builder | `/builder-agent lead_12345` | Deploy preview site |
| Outreach | `/outreach-agent lead_12345` | Send email/SMS |
| Scheduler | `/scheduler-agent lead_12345` | Book calls |
| Onboarding | `/onboarding-agent lead_12345` | Collect info + payment |
| Fulfillment | `/fulfillment-agent report-all` | Monthly reports + upsells |

### CRM States

```
new → qualified → preview_built → contacted → replied → won / lost → live → retained
```

### Start Here

1. Set up your CRM (Airtable, Notion, or database)
2. Get API keys for SendGrid + Twilio
3. Build your first site template
4. Run: `/prospector-agent plumbing "YourCity, ST"`
5. Review leads, then: `/qualifier-agent batch`
6. Build previews for top leads and start outreach