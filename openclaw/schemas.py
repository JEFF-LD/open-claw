"""
OpenClaw Phase 1 data models. Lean — only what's needed to close first 5 clients.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum


class LeadStatus(str, Enum):
    NEW = "new"
    QUALIFIED = "qualified"
    DRAFT_READY = "draft_ready"
    APPROVED = "approved"
    SENT = "sent"
    REPLIED = "replied"
    WON = "won"
    LOST = "lost"
    PAUSED = "paused"


def _id() -> str:
    return uuid.uuid4().hex[:12]


def _now() -> str:
    return datetime.utcnow().isoformat()
