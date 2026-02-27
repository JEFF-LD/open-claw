"""
OpenClaw CLI — Phase 1.

Commands:
  init-db                          Initialize database
  prospect --category X --metro Y  Find leads
  qualify                          Score all new leads
  build                            Generate preview sites for qualified leads
  draft                            Generate outreach drafts for leads with previews
  queue                            List drafts awaiting approval
  approve <draft_id>               Approve a draft for sending
  send-approved [--limit N]        Send approved drafts (default limit: 25)
  check-replies                    Poll inbox for replies
  replies                          Show leads that replied (need human action)
  boost <lead_id>                  Re-generate a shorter draft for a lead
  pause <lead_id>                  Pause a lead (skip in pipeline)
  unpause <lead_id>                Unpause a lead
  dashboard                        Show funnel stats
  smoke-test                       Validate pipeline end-to-end (no real sends)
  serve [--port N]                 Start preview server (default: 8111)
  run-daily --category X --metro Y Full daily cycle
"""

import sys
import argparse

from openclaw.observability.logging_setup import setup_logging


def main():
    setup_logging()

    parser = argparse.ArgumentParser(description="OpenClaw Phase 1 CLI")
    sub = parser.add_subparsers(dest="command")

    # init-db
    sub.add_parser("init-db")

    # prospect
    p = sub.add_parser("prospect")
    p.add_argument("--category", required=True)
    p.add_argument("--metro", required=True)

    # qualify
    sub.add_parser("qualify")

    # build
    sub.add_parser("build")

    # draft
    sub.add_parser("draft")

    # queue
    sub.add_parser("queue")

    # approve
    p = sub.add_parser("approve")
    p.add_argument("draft_id")

    # send-approved
    p = sub.add_parser("send-approved")
    p.add_argument("--limit", type=int, default=25)

    # check-replies
    sub.add_parser("check-replies")

    # replies
    sub.add_parser("replies")

    # boost
    p = sub.add_parser("boost")
    p.add_argument("lead_id")

    # pause
    p = sub.add_parser("pause")
    p.add_argument("lead_id")

    # unpause
    p = sub.add_parser("unpause")
    p.add_argument("lead_id")

    # dashboard
    sub.add_parser("dashboard")

    # smoke-test
    sub.add_parser("smoke-test")

    # serve
    p = sub.add_parser("serve")
    p.add_argument("--port", type=int, default=None)

    # run-daily
    p = sub.add_parser("run-daily")
    p.add_argument("--category", required=True)
    p.add_argument("--metro", required=True)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # ---------------------------------------------------------------
    # Dispatch
    # ---------------------------------------------------------------

    if args.command == "init-db":
        from openclaw.persistence.database import init_db
        init_db()

    elif args.command == "prospect":
        from openclaw.agents.prospector import ProspectorAgent
        result = ProspectorAgent().run(category=args.category, metro=args.metro)
        _print_result("Prospector", result)

    elif args.command == "qualify":
        from openclaw.agents.qualifier import QualifierAgent
        result = QualifierAgent().run()
        _print_result("Qualifier", result)

    elif args.command == "build":
        from openclaw.agents.builder import BuilderAgent
        result = BuilderAgent().run()
        _print_result("Builder", result)

    elif args.command == "draft":
        from openclaw.agents.outreach import OutreachAgent
        result = OutreachAgent().run()
        _print_result("Outreach", result)

    elif args.command == "queue":
        from openclaw.persistence.database import get_drafts_by_status
        drafts = get_drafts_by_status("draft")
        if not drafts:
            print("No drafts in queue.")
            return
        print(f"\n{'ID':<14} {'Business':<30} {'Subject':<40} {'Follow-up'}")
        print("-" * 92)
        for d in drafts:
            print(f"{d['id']:<14} {d.get('business_name','')[:28]:<30} {d['subject'][:38]:<40} #{d['followup_number']}")
        print(f"\n{len(drafts)} drafts awaiting approval.")
        print("Use: python cli.py approve <draft_id>\n")

    elif args.command == "approve":
        _cmd_approve(args.draft_id)

    elif args.command == "send-approved":
        from openclaw.execution.email_sender import send_approved
        result = send_approved(limit=args.limit)
        if result.get("error"):
            print(f"Error: {result['error']}")
        else:
            print(f"Sent: {result['sent']}  Failed: {result['failed']}  Total: {result['total']}")

    elif args.command == "check-replies":
        from openclaw.execution.reply_checker import check_replies
        result = check_replies()
        if result.get("error"):
            print(f"Error: {result['error']}")
        else:
            print(f"Found {result['found']} new replies. (skipped {result.get('skipped', 0)} unmatched)")

    elif args.command == "replies":
        from openclaw.persistence.database import get_replies
        replies = get_replies()
        if not replies:
            print("No replies yet.")
            return
        print(f"\n{'Business':<30} {'Type':<12} {'From':<30} {'Date'}")
        print("-" * 85)
        for r in replies:
            print(f"{r.get('business_name','')[:28]:<30} {r['reply_type']:<12} {r['from_email'][:28]:<30} {r['created_at'][:10]}")
        print(f"\n{len(replies)} replies. Handle these manually.\n")

    elif args.command == "boost":
        from openclaw.agents.outreach import OutreachAgent
        from openclaw.persistence.database import get_lead
        lead = get_lead(args.lead_id)
        if not lead:
            print(f"Lead {args.lead_id} not found.")
            return
        result = OutreachAgent().run(lead_id=args.lead_id)
        _print_result("Boost", result)

    elif args.command == "pause":
        from openclaw.persistence.database import update_lead
        update_lead(args.lead_id, manual_override=True, lead_status="paused")
        print(f"Paused lead {args.lead_id}")

    elif args.command == "unpause":
        from openclaw.persistence.database import update_lead
        update_lead(args.lead_id, manual_override=False, lead_status="qualified")
        print(f"Unpaused lead {args.lead_id}")

    elif args.command == "dashboard":
        from openclaw.observability.dashboard import print_dashboard
        print_dashboard()

    elif args.command == "smoke-test":
        _cmd_smoke_test()

    elif args.command == "serve":
        from serve import main as serve_main
        # Override sys.argv so serve.py's argparse sees the right args
        serve_args = ["serve"]
        if args.port:
            serve_args += ["--port", str(args.port)]
        import sys as _sys
        _sys.argv = serve_args
        serve_main()

    elif args.command == "run-daily":
        _run_daily(args.category, args.metro)

    else:
        parser.print_help()


# -------------------------------------------------------------------
# approve — only drafts with status "draft"
# -------------------------------------------------------------------

def _cmd_approve(draft_id: str):
    from openclaw.persistence.database import get_draft, update_draft, update_lead
    draft = get_draft(draft_id)
    if not draft:
        print(f"Draft {draft_id} not found.")
        return
    if draft["status"] != "draft":
        print(f"Cannot approve: draft {draft_id} has status '{draft['status']}' (must be 'draft').")
        return
    update_draft(draft_id, status="approved", error="")
    update_lead(draft["lead_id"], lead_status="approved")
    print(f"Approved: {draft['subject']} -> {draft.get('email', 'N/A')}")


# -------------------------------------------------------------------
# smoke-test — validate pipeline end-to-end without real sends
# -------------------------------------------------------------------

def _cmd_smoke_test():
    from openclaw import config
    from openclaw.schemas import _id, _now
    from openclaw.persistence.database import (
        db_exists, init_db, insert_lead, get_lead,
        get_drafts_by_status,
    )

    print()
    print("=" * 52)
    print("  OPENCLAW SMOKE TEST")
    print("=" * 52)
    print()

    # 1. Ensure DB
    if not db_exists():
        print("[1/6] Creating database...")
        init_db()
    else:
        print("[1/6] Database exists.")
        # Still run init_db to apply any migrations
        from openclaw.persistence.database import _ensure_columns
        _ensure_columns()

    # 2. Create fake lead
    print("[2/6] Creating test lead...")
    lead_id = "smoke_" + _id()[:6]
    insert_lead({
        "id": lead_id,
        "business_name": "Ace Plumbing & Drain",
        "owner_name": "Mike Johnson",
        "email": "test@example.com",
        "phone": "+13035551234",
        "category": "plumbing",
        "metro": "Denver CO",
        "rating": 4.7,
        "review_count": 42,
        "has_website": 0,
        "website_url": "",
        "gbp_link": "https://maps.google.com/?cid=fake",
        "source": "smoke_test",
        "lead_status": "new",
        "created_at": _now(),
        "updated_at": _now(),
    })
    print(f"  Lead ID: {lead_id}")
    print(f"  Business: Ace Plumbing & Drain")
    print(f"  Metro: Denver CO | Rating: 4.7 | Reviews: 42 | No website")

    # 3. Qualify
    print("[3/6] Qualifying...")
    from openclaw.agents.qualifier import QualifierAgent
    r = QualifierAgent().run(lead_id=lead_id)
    if r["ok"]:
        lead = get_lead(lead_id)
        print(f"  Score: {lead['qualification_score']} | Tier: {lead['tier']} | ROI: ${lead['roi_estimate_monthly']}/mo")
    else:
        print(f"  ERROR: {r['error']}")
        return

    # 4. Build preview
    print("[4/6] Building preview...")
    from openclaw.agents.builder import BuilderAgent
    r = BuilderAgent().run(lead_id=lead_id)
    if r["ok"]:
        lead = get_lead(lead_id)
        print(f"  Preview URL:  {lead['preview_url']}")
        print(f"  Preview file: {lead['preview_path']}")
    else:
        print(f"  ERROR: {r['error']}")
        return

    # 5. Generate draft
    print("[5/6] Generating outreach draft...")
    from openclaw.agents.outreach import OutreachAgent
    r = OutreachAgent().run(lead_id=lead_id)
    if r["ok"]:
        drafts = get_drafts_by_status("draft")
        smoke_drafts = [d for d in drafts if d["lead_id"] == lead_id]
        if smoke_drafts:
            draft = smoke_drafts[0]
            print(f"  Draft ID: {draft['id']}")
            print(f"  Subject:  {draft['subject']}")
            print(f"  To:       {draft.get('email', 'N/A')}")
            print()
            print("  --- DRAFT BODY ---")
            for line in draft["body"].split("\n"):
                print(f"  {line}")
            print("  --- END DRAFT ---")
        else:
            print("  Draft created but not found in queue (may be deduped).")
    else:
        print(f"  ERROR: {r['error']}")
        return

    # 6. SMTP/IMAP status
    print()
    print("[6/6] Environment check...")
    if config.has_smtp():
        print("  SMTP: configured (ready to send)")
    else:
        print("  SMTP: NOT configured — set SMTP_USER, SMTP_PASS, FROM_EMAIL in .env")

    if config.has_imap():
        print("  IMAP: configured (ready to check replies)")
        from openclaw.execution.reply_checker import check_replies
        result = check_replies()
        if result.get("error"):
            print(f"  IMAP test: {result['error']}")
        else:
            print(f"  IMAP test: OK — {result['found']} new replies found")
    else:
        print("  IMAP: NOT configured — set IMAP_USER, IMAP_PASS in .env")

    print()
    print("=" * 52)
    print("  SMOKE TEST COMPLETE")
    print("=" * 52)
    print()
    if smoke_drafts:
        print("  To send this test email:")
        print(f"    1. python cli.py approve {smoke_drafts[0]['id']}")
        print(f"    2. python cli.py send-approved --limit 1")
        print()
        print("  To clean up without sending:")
        print(f"    - The test lead '{lead_id}' uses email test@example.com")
        print(f"    - It will not match real prospects or interfere with real pipeline")
    print()


# -------------------------------------------------------------------
# run-daily
# -------------------------------------------------------------------

def _run_daily(category: str, metro: str):
    """Full daily cycle: prospect -> qualify -> build -> draft."""
    print("\n=== OPENCLAW DAILY RUN ===\n")

    print("[1/4] Prospecting...")
    from openclaw.agents.prospector import ProspectorAgent
    r = ProspectorAgent().run(category=category, metro=metro)
    _print_result("Prospector", r)

    print("[2/4] Qualifying...")
    from openclaw.agents.qualifier import QualifierAgent
    r = QualifierAgent().run()
    _print_result("Qualifier", r)

    print("[3/4] Building previews...")
    from openclaw.agents.builder import BuilderAgent
    r = BuilderAgent().run()
    _print_result("Builder", r)

    print("[4/4] Generating outreach drafts...")
    from openclaw.agents.outreach import OutreachAgent
    r = OutreachAgent().run()
    _print_result("Outreach", r)

    print("\n=== DAILY RUN COMPLETE ===")
    print("Next: python cli.py queue")
    print("Then: python cli.py approve <id>")
    print("Then: python cli.py send-approved\n")


def _print_result(agent: str, result: dict):
    if result.get("ok"):
        r = result["result"]
        print(f"  {agent}: {r}")
    else:
        print(f"  {agent} ERROR: {result.get('error', 'unknown')}")


if __name__ == "__main__":
    main()
