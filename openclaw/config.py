"""
Central configuration. Reads from .env.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env")

# Database
DB_PATH = os.getenv("OPENCLAW_DB_PATH", str(_ROOT / "openclaw.db"))

# Google Places
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "")

# SMTP (outbound email)
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")

# IMAP (reply checking)
IMAP_HOST = os.getenv("IMAP_HOST", "imap.gmail.com")
IMAP_USER = os.getenv("IMAP_USER", "")
IMAP_PASS = os.getenv("IMAP_PASS", "")

# Identity
FROM_EMAIL = os.getenv("FROM_EMAIL", "")
FROM_NAME = os.getenv("FROM_NAME", "")
CALENDAR_LINK = os.getenv("CALENDAR_LINK", "")

# Preview hosting (GitHub Pages serves from /docs)
PREVIEW_HOST = os.getenv("PREVIEW_HOST", "").rstrip("/")
PREVIEW_DIR = os.getenv("PREVIEW_DIR", str(_ROOT / "docs"))
PREVIEW_PORT = int(os.getenv("PREVIEW_PORT", "8111"))

# Pipeline
PROSPECT_BATCH_SIZE = int(os.getenv("PROSPECT_BATCH_SIZE", "50"))
OUTREACH_DAILY_LIMIT = int(os.getenv("OUTREACH_DAILY_LIMIT", "25"))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR = os.getenv("LOG_DIR", str(_ROOT / "logs"))


# ---------------------------------------------------------------------------
# Operator guards — validate env vars are set before they're needed
# ---------------------------------------------------------------------------

class ConfigError(RuntimeError):
    """Raised when required configuration is missing."""


def require_smtp():
    """Call before any SMTP operation. Raises ConfigError with clear message."""
    missing = []
    if not SMTP_USER:
        missing.append("SMTP_USER  (e.g. your-outreach@gmail.com)")
    if not SMTP_PASS:
        missing.append("SMTP_PASS  (Gmail App Password — https://myaccount.google.com/apppasswords)")
    if not FROM_EMAIL:
        missing.append("FROM_EMAIL (e.g. your-outreach@gmail.com)")
    if not FROM_NAME:
        missing.append("FROM_NAME  (e.g. John Smith)")
    if missing:
        raise ConfigError(
            "SMTP is not configured. Set these in .env:\n  " + "\n  ".join(missing)
        )


def require_imap():
    """Call before any IMAP operation. Raises ConfigError with clear message."""
    missing = []
    if not IMAP_USER:
        missing.append("IMAP_USER  (e.g. your-outreach@gmail.com)")
    if not IMAP_PASS:
        missing.append("IMAP_PASS  (Gmail App Password)")
    if missing:
        raise ConfigError(
            "IMAP is not configured. Set these in .env:\n  " + "\n  ".join(missing)
        )


def require_places():
    """Call before any Google Places operation. Raises ConfigError with clear message."""
    if not GOOGLE_PLACES_API_KEY:
        raise ConfigError(
            "GOOGLE_PLACES_API_KEY is not set.\n"
            "  Get one at: https://console.cloud.google.com/apis/credentials\n"
            "  Then add to .env:  GOOGLE_PLACES_API_KEY=AIza..."
        )


def has_smtp() -> bool:
    """Non-throwing check for SMTP readiness."""
    return bool(SMTP_USER and SMTP_PASS and FROM_EMAIL)


def has_imap() -> bool:
    """Non-throwing check for IMAP readiness."""
    return bool(IMAP_USER and IMAP_PASS)
