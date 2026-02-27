"""
Outreach — generates email DRAFTS only. Never sends.
Writes to outreach_drafts table with status=draft.
Human approves via CLI before anything is sent.
"""

from openclaw import config
from openclaw.schemas import _id, _now
from openclaw.agents.base import BaseAgent
from openclaw.persistence.database import (
    get_leads_by_status, get_lead, update_lead,
    insert_draft, get_lead_draft_count, draft_exists,
)


class OutreachAgent(BaseAgent):
    name = "outreach"

    def execute(self, lead_id: str = "", **kw) -> dict:
        if lead_id:
            leads = [l for l in [get_lead(lead_id)] if l]
        else:
            # Get qualified leads that have a preview built (have preview_url)
            qualified = get_leads_by_status("qualified")
            leads = [l for l in qualified if l.get("preview_url")]

        drafted = 0
        skipped = 0
        errors = 0
        for lead in leads:
            try:
                # Skip paused leads
                if lead.get("manual_override") or lead.get("lead_status") == "paused":
                    skipped += 1
                    continue

                existing = get_lead_draft_count(lead["id"])
                if existing >= 3:
                    skipped += 1
                    continue

                followup = existing  # 0 = initial, 1 = bump, 2 = close-the-loop

                # Dedup: don't create duplicate for same lead + followup_number
                if draft_exists(lead["id"], followup):
                    skipped += 1
                    continue

                draft = self._generate_draft(lead, followup)
                insert_draft(draft)
                update_lead(lead["id"], lead_status="draft_ready")
                drafted += 1
                self.log.info("  Drafted: %s (followup #%d)", lead["business_name"], followup)
            except Exception as e:
                self.log.error("  Error drafting for %s: %s", lead.get("business_name", "?"), e)
                errors += 1

        return {"drafted": drafted, "skipped": skipped, "errors": errors}

    def _generate_draft(self, lead: dict, followup: int) -> dict:
        biz = lead["business_name"]
        name = lead.get("owner_name") or biz.split()[0]
        metro = lead.get("metro", "")
        preview = lead.get("preview_url", "")
        sender = config.FROM_NAME or "Your Name"

        if followup == 0:
            subject = f"Quick website preview for {biz}"
            body = (
                f"Hi {name},\n\n"
                f"I noticed you don't currently have a modern quote-ready website, "
                f"so I built a quick preview based on your services in {metro}.\n\n"
                f"You can view it here:\n{preview}\n\n"
                f"It includes:\n"
                f"  - Service pages\n"
                f"  - Review highlights\n"
                f"  - Free quote capture\n"
                f"  - Mobile-first layout\n\n"
                f"If you'd like, I can transfer this to you and get it live this week.\n\n"
                f"Would you be open to that?\n\n"
                f"-- {sender}"
            )
        elif followup == 1:
            subject = f"Following up — {biz}"
            body = (
                f"Hi {name},\n\n"
                f"Just wanted to make sure you saw the preview I put together "
                f"for {biz}:\n\n{preview}\n\n"
                f"Happy to walk you through it or make changes.\n\n"
                f"-- {sender}"
            )
        else:
            subject = "Closing the loop"
            body = (
                f"Hi {name},\n\n"
                f"Totally understand if the timing isn't right. "
                f"I'll keep your preview live for another few weeks:\n\n{preview}\n\n"
                f"If you ever want to chat about getting more calls online, just reply.\n\n"
                f"-- {sender}"
            )

        return {
            "id": _id(),
            "lead_id": lead["id"],
            "subject": subject,
            "body": body,
            "followup_number": followup,
            "status": "draft",
            "created_at": _now(),
        }
