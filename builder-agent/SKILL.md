---
name: builder-agent
description: >
  Takes the copy package from the Creative Agent and deploys a live preview website
  on a preview subdomain. Pushes content to the site builder template system, configures
  forms, embeds maps and reviews widgets, generates a shareable preview link, and creates
  the audit PDF. Triggers when a copy package is ready for a qualified lead.
version: 1.0.0
metadata:
  openclaw:
    requires:
      env:
        - CRM_API_KEY
        - SITE_BUILDER_API_KEY
        - HOSTING_API_KEY
        - PDF_GENERATOR_API_KEY
      bins:
        - curl
        - jq
    primaryEnv: SITE_BUILDER_API_KEY
---

# Builder Agent

## Purpose

Turn the Creative Agent's copy package into a live, viewable preview website and a formatted audit PDF. The prospect should be able to click one link and see a real site with their business name, services, and city — ready to go live.

## When This Skill Runs

- **Auto-trigger:** When Creative Agent completes a copy package for a lead
- **Batch trigger:** Daily batch for Tier B leads with completed copy packages
- **Manual trigger:** `/builder-agent <lead_id>`

## Process Steps

### Step 1: Select Template Variant

Choose the correct template based on trade category:

| Category | Template ID | Color Scheme | Hero Image Style |
|----------|------------|-------------|-----------------|
| Plumbing | `tmpl_plumbing_01` | Blue/white | Pipe wrench, clean bathroom |
| HVAC | `tmpl_hvac_01` | Blue/orange | AC unit, comfortable family |
| Electrical | `tmpl_electrical_01` | Yellow/dark gray | Panel, well-lit home |
| Roofing | `tmpl_roofing_01` | Dark red/charcoal | Roof line, shingle closeup |
| Landscaping | `tmpl_landscape_01` | Green/earth tones | Manicured lawn, hardscape |
| Arborists | `tmpl_arborist_01` | Forest green/brown | Tall trees, crew at work |
| Carpentry | `tmpl_carpentry_01` | Warm wood/cream | Custom build, trim detail |
| Fence/Deck | `tmpl_fencedeck_01` | Cedar/slate | Backyard fence, deck view |
| Junk Removal | `tmpl_junk_01` | Orange/dark blue | Clean truck, empty space |

### Step 2: Populate Template with Copy Package

Map each section of the copy package to the template:

1. **Home page** — hero headline, subheadline, CTA button, trust badges, intro, services preview, review highlight, final CTA
2. **Services page** — render each service as a card/section with name, description, and individual CTA
3. **Service area page** — city name, surrounding areas list, description paragraph, Google Maps embed using business address
4. **Reviews page** — intro text, review themes summary, Google reviews embed widget (or link to GBP)
5. **Quote request page** — form with all specified fields, confirmation message on submit
6. **About page** — placeholder content, values list, image upload slots

### Step 3: Configure Interactive Elements

- **Quote form:** connect to form handler (email notification to business + CRM logging)
- **Click-to-call button:** link to `tel:+1XXXXXXXXXX` using lead phone number
- **SMS button:** link to `sms:+1XXXXXXXXXX` with pre-filled message
- **Maps embed:** use business address from lead record
- **Reviews widget:** embed Google reviews or link to GBP listing

### Step 4: Deploy to Preview Subdomain

- Deploy to: `preview-[lead_id].yourdomain.com` or `yourdomain.com/preview/[business-slug]`
- Enable SSL
- Set preview expiration: 30 days from deploy date
- Make the preview link clean and shareable (no query strings or tokens)

### Step 5: Generate Audit PDF

Using the audit content from the Creative Agent:

1. Apply the audit PDF template (branded, one page)
2. Populate all 4 sections (Current State, Customer Love, Opportunity, Preview Link)
3. Include the live preview URL as a clickable link
4. Generate and store the PDF
5. Link the PDF to the lead record in CRM

### Step 6: Update CRM

```
{
  "preview_url": "https://preview-12345.yourdomain.com",
  "audit_pdf_url": "https://assets.yourdomain.com/audits/lead_12345.pdf",
  "template_used": "tmpl_plumbing_01",
  "preview_deployed_date": "2026-02-27",
  "preview_expires_date": "2026-03-29",
  "status": "preview_built"
}
```

### Step 7: Trigger Outreach Agent

Notify the Outreach Agent that the preview is ready and provide:
- Preview URL
- Audit PDF URL
- Recommended outreach lane (Lane 1 if no website, Lane 2 if has website but no lead capture)

## Quality Checklist (Automated)

Before marking a preview as deployed, verify:

- [ ] All pages load without errors
- [ ] Business name appears correctly on every page
- [ ] Phone number is correct and click-to-call works
- [ ] City/service area names are spelled correctly
- [ ] Quote form submits successfully (test submission)
- [ ] Mobile responsive — check at 375px width
- [ ] SSL certificate is active
- [ ] Page load time under 3 seconds
- [ ] No placeholder text remaining (e.g., "[Business Name]" should be replaced)
- [ ] No "24/7 emergency" claims unless verified

## Guardrails

- **NEVER** deploy a preview with placeholder text still showing
- **NEVER** include real client data in test submissions
- **NEVER** deploy to a production domain — previews only go to preview subdomains
- **Preview lifespan:** auto-expire after 30 days if not converted
- **One preview per lead** — if regenerating, overwrite the existing preview
- **No tracking pixels** on preview sites — these are prospects, not clients yet

## Escalation Rules

Escalate to human when:
- Template deployment fails (API error, hosting issue)
- Quality checklist has any failures that can't be auto-fixed
- Preview URL returns a non-200 status code after deployment
- Audit PDF generation fails

## Output

Each run produces:
- Live preview website at a shareable URL
- Audit PDF stored and linked to lead record
- CRM record updated to status `preview_built`
- Outreach Agent triggered with preview assets

## Example Usage

```
/builder-agent lead_12345
/builder-agent batch --tier B
/builder-agent regenerate lead_12345
```