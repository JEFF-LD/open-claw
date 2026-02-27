#!/usr/bin/env python3
"""
Cron-compatible daily run script.

Usage:
  python daily_run.py --category plumbing --metro "Denver CO"

Crontab example (run daily at 7am):
  0 7 * * 1-5 cd /path/to/openclaw-skills && python daily_run.py --category plumbing --metro "Denver CO" >> logs/cron.log 2>&1
"""

import sys
import argparse
import logging
from datetime import datetime

from openclaw.observability.logging_setup import setup_logging
from openclaw.persistence.database import init_db


def main():
    parser = argparse.ArgumentParser(description="OpenClaw daily pipeline run")
    parser.add_argument("--category", required=True)
    parser.add_argument("--metro", required=True)
    args = parser.parse_args()

    setup_logging()
    log = logging.getLogger("openclaw.daily")
    log.info("=== Daily run started: %s %s ===", args.category, args.metro)

    # Ensure DB exists
    init_db()

    # Step 1: Prospect
    from openclaw.agents.prospector import ProspectorAgent
    r = ProspectorAgent().run(category=args.category, metro=args.metro)
    log.info("Prospect: %s", r.get("result", r.get("error")))

    # Step 2: Qualify
    from openclaw.agents.qualifier import QualifierAgent
    r = QualifierAgent().run()
    log.info("Qualify: %s", r.get("result", r.get("error")))

    # Step 3: Build previews
    from openclaw.agents.builder import BuilderAgent
    r = BuilderAgent().run()
    log.info("Build: %s", r.get("result", r.get("error")))

    # Step 4: Generate outreach drafts
    from openclaw.agents.outreach import OutreachAgent
    r = OutreachAgent().run()
    log.info("Draft: %s", r.get("result", r.get("error")))

    log.info("=== Daily run complete. Review queue: python cli.py queue ===")


if __name__ == "__main__":
    main()
