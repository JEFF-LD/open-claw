"""
SMTP email sender. Only sends approved drafts. Plain text only.
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.utils import make_msgid

from openclaw import config
from openclaw.schemas import _now
from openclaw.persistence.database import get_draft, update_draft, get_lead, update_lead

log = logging.getLogger("openclaw.email")


def send_draft(draft_id: str) -> dict:
    """Send a single approved draft. Returns {ok, message_id, error}."""
    draft = get_draft(draft_id)
    if not draft:
        return {"ok": False, "error": f"Draft {draft_id} not found"}

    # Hard guard: only approved drafts can be sent
    if draft["status"] != "approved":
        return {"ok": False, "error": f"Draft {draft_id} is not approved (status={draft['status']})"}

    to_email = draft.get("email", "")
    if not to_email:
        update_draft(draft_id, status="failed", error="No email address")
        return {"ok": False, "error": "No email address for lead"}

    # Validate SMTP config with clear error
    try:
        config.require_smtp()
    except config.ConfigError as e:
        error_msg = str(e)
        update_draft(draft_id, status="failed", error=error_msg)
        return {"ok": False, "error": error_msg}

    # Build message with explicit Message-ID for reply threading
    message_id = make_msgid(domain=config.FROM_EMAIL.split("@")[-1] if "@" in config.FROM_EMAIL else "openclaw.local")

    msg = MIMEText(draft["body"], "plain", "utf-8")
    msg["Subject"] = draft["subject"]
    msg["From"] = f"{config.FROM_NAME} <{config.FROM_EMAIL}>"
    msg["To"] = to_email
    msg["Reply-To"] = config.FROM_EMAIL
    msg["Message-ID"] = message_id

    try:
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=30) as server:
            server.starttls()
            server.login(config.SMTP_USER, config.SMTP_PASS)
            server.send_message(msg)

        update_draft(draft_id, status="sent", sent_at=_now(), message_id=message_id, error="")
        update_lead(draft["lead_id"], lead_status="sent")
        log.info("Sent: %s -> %s [%s]", draft["subject"], to_email, message_id)
        return {"ok": True, "message_id": message_id}

    except smtplib.SMTPAuthenticationError as e:
        error_msg = f"SMTP auth failed — check SMTP_USER/SMTP_PASS: {e}"
        update_draft(draft_id, status="failed", error=error_msg)
        log.error("Auth failed for %s: %s", draft_id, error_msg)
        return {"ok": False, "error": error_msg}

    except Exception as e:
        error_msg = str(e)
        update_draft(draft_id, status="failed", error=error_msg)
        log.error("Send failed for %s: %s", draft_id, error_msg)
        return {"ok": False, "error": error_msg}


def send_approved(limit: int = 25) -> dict:
    """Send all approved drafts up to limit. Returns summary."""
    # Pre-check SMTP config before starting the batch
    try:
        config.require_smtp()
    except config.ConfigError as e:
        log.error("Cannot send: %s", e)
        return {"sent": 0, "failed": 0, "total": 0, "error": str(e)}

    from openclaw.persistence.database import get_drafts_by_status

    drafts = get_drafts_by_status("approved", limit=limit)
    sent = 0
    failed = 0

    for draft in drafts:
        result = send_draft(draft["id"])
        if result["ok"]:
            sent += 1
        else:
            failed += 1
            log.warning("  Failed: %s — %s", draft.get("subject", ""), result.get("error", ""))

    return {"sent": sent, "failed": failed, "total": len(drafts)}
