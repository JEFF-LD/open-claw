"""
IMAP reply checker. Polls inbox for replies, matches to leads, classifies intent.

Matching priority:
  1. In-Reply-To / References headers → message_id stored on outreach_drafts
  2. Sender email address → leads.email
"""

import email
import imaplib
import logging
import re
from email.header import decode_header

from openclaw import config
from openclaw.schemas import _id, _now
from openclaw.persistence.database import (
    insert_reply, get_lead_id_by_email, get_lead_id_by_message_thread,
    update_lead,
)

log = logging.getLogger("openclaw.replies")

# Simple keyword-based reply classification
POSITIVE_KEYWORDS = ["yes", "interested", "sounds good", "let's do it", "tell me more",
                      "love it", "looks great", "set it up", "go ahead", "call me",
                      "i'm in", "let's talk", "when can we"]
NEGATIVE_KEYWORDS = ["not interested", "no thanks", "remove me", "unsubscribe",
                      "stop", "don't contact", "not for me", "take me off",
                      "do not contact", "not right now"]
QUESTION_KEYWORDS = ["how much", "price", "cost", "what's included", "how does",
                      "can you", "do you", "what do you charge", "what are your rates"]
OOO_KEYWORDS = ["out of office", "auto-reply", "away from", "on vacation",
                 "limited access", "currently unavailable", "automatic reply",
                 "i am currently out"]


def check_replies() -> dict:
    """Poll IMAP inbox for replies. Returns summary."""
    try:
        config.require_imap()
    except config.ConfigError as e:
        return {"error": str(e), "found": 0}

    try:
        mail = imaplib.IMAP4_SSL(config.IMAP_HOST)
        mail.login(config.IMAP_USER, config.IMAP_PASS)
        mail.select("INBOX")
    except imaplib.IMAP4.error as e:
        log.error("IMAP auth failed — check IMAP_USER/IMAP_PASS: %s", e)
        return {"error": f"IMAP auth failed: {e}", "found": 0}
    except Exception as e:
        log.error("IMAP connection failed: %s", e)
        return {"error": str(e), "found": 0}

    # Search for recent unseen messages
    try:
        _, message_ids = mail.search(None, "UNSEEN")
        ids = message_ids[0].split() if message_ids[0] else []
    except Exception as e:
        log.error("IMAP search failed: %s", e)
        _safe_logout(mail)
        return {"error": str(e), "found": 0}

    found = 0
    skipped = 0
    for msg_id in ids:
        try:
            _, data = mail.fetch(msg_id, "(RFC822)")
            if not data or not data[0] or not isinstance(data[0], tuple):
                skipped += 1
                continue
            msg = email.message_from_bytes(data[0][1])

            from_email = _extract_email(msg.get("From", ""))
            subject = _safe_decode_header(msg.get("Subject", ""))
            body = _extract_body(msg)
            in_reply_to = msg.get("In-Reply-To", "").strip()
            references = msg.get("References", "").strip()

            # Match to a lead: try message threading first, then email
            lead_id = get_lead_id_by_message_thread(in_reply_to, references)
            if not lead_id:
                lead_id = get_lead_id_by_email(from_email)
            if not lead_id:
                skipped += 1
                continue

            # Classify
            reply_type = _classify(subject + " " + body)

            insert_reply({
                "id": _id(),
                "lead_id": lead_id,
                "from_email": from_email,
                "subject": subject[:200],
                "in_reply_to": in_reply_to[:200],
                "raw_body": body[:2000],
                "reply_type": reply_type,
                "created_at": _now(),
            })

            # Update lead status + cancel pending drafts
            update_lead(lead_id, lead_status="replied")
            _cancel_pending_drafts(lead_id)

            found += 1
            log.info("Reply from %s: type=%s subj=%s", from_email, reply_type, subject[:60])

        except Exception as e:
            log.error("Error processing message %s: %s", msg_id, e)
            skipped += 1

    _safe_logout(mail)
    return {"found": found, "skipped": skipped}


def _classify(text: str) -> str:
    lower = text.lower()
    if any(kw in lower for kw in OOO_KEYWORDS):
        return "ooo"
    if any(kw in lower for kw in NEGATIVE_KEYWORDS):
        return "negative"
    if any(kw in lower for kw in POSITIVE_KEYWORDS):
        return "positive"
    if any(kw in lower for kw in QUESTION_KEYWORDS):
        return "question"
    return "other"


def _extract_email(from_str: str) -> str:
    if not from_str:
        return ""
    match = re.search(r"<(.+?)>", from_str)
    if match:
        return match.group(1).lower().strip()
    return from_str.strip().lower()


def _safe_decode_header(header) -> str:
    """Decode email header, never crash."""
    if not header:
        return ""
    try:
        parts = decode_header(header)
        decoded = []
        for part, charset in parts:
            if isinstance(part, bytes):
                decoded.append(part.decode(charset or "utf-8", errors="replace"))
            else:
                decoded.append(str(part))
        return " ".join(decoded)
    except Exception:
        return str(header)


def _extract_body(msg) -> str:
    """Extract plain text body from email, never crash."""
    try:
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or "utf-8"
                        return payload.decode(charset, errors="replace")
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or "utf-8"
                return payload.decode(charset, errors="replace")
    except Exception as e:
        log.warning("Could not extract email body: %s", e)
    return ""


def _cancel_pending_drafts(lead_id: str):
    """Cancel any unsent drafts for this lead."""
    from openclaw.persistence.database import get_db
    with get_db() as db:
        db.execute(
            "UPDATE outreach_drafts SET status='cancelled' "
            "WHERE lead_id=? AND status IN ('draft', 'approved')",
            (lead_id,),
        )


def _safe_logout(mail):
    """Logout from IMAP, never crash."""
    try:
        mail.logout()
    except Exception:
        pass
