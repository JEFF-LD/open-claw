"""
CLI dashboard. Prints funnel stats and economics.
"""

from openclaw.persistence.database import (
    count_leads_by_status, count_drafts_by_status,
    get_reply_count, get_positive_reply_count,
    get_conversion_stats, get_total_roi_pipeline,
    get_closed_revenue,
)


def print_dashboard():
    leads = count_leads_by_status()
    drafts = count_drafts_by_status()
    reply_count = get_reply_count()
    positive_count = get_positive_reply_count()
    conv = get_conversion_stats()
    roi_pipeline = get_total_roi_pipeline()
    closed_rev = get_closed_revenue()

    total_leads = sum(leads.values())
    new = leads.get("new", 0)
    qualified = leads.get("qualified", 0)
    draft_ready = leads.get("draft_ready", 0)
    approved = leads.get("approved", 0)
    sent = leads.get("sent", 0)
    replied = leads.get("replied", 0)
    won = leads.get("won", 0)
    lost = leads.get("lost", 0)
    paused = leads.get("paused", 0)

    # Drafts by status
    d_draft = drafts.get("draft", 0)
    d_approved = drafts.get("approved", 0)
    d_sent = drafts.get("sent", 0)
    d_failed = drafts.get("failed", 0)
    d_cancelled = drafts.get("cancelled", 0)

    # Rates
    reply_rate = f"{(reply_count / sent * 100):.1f}%" if sent > 0 else "-"
    positive_rate = f"{(positive_count / reply_count * 100):.1f}%" if reply_count > 0 else "-"

    print()
    print("=" * 52)
    print("  OPENCLAW PIPELINE DASHBOARD")
    print("=" * 52)
    print()
    print("  LEADS")
    print(f"  Total              {total_leads:>8}")
    print(f"  New                {new:>8}")
    print(f"  Qualified          {qualified:>8}")
    print(f"  Draft ready        {draft_ready:>8}")
    print(f"  Approved           {approved:>8}")
    print(f"  Sent               {sent:>8}")
    print(f"  Replied            {replied:>8}")
    print(f"  Won                {won:>8}")
    print(f"  Lost               {lost:>8}")
    print(f"  Paused             {paused:>8}")
    print()
    print("  RATES")
    print(f"  Reply rate         {reply_rate:>8}  ({reply_count} replies / {sent} sent)")
    print(f"  Positive rate      {positive_rate:>8}  ({positive_count} positive / {reply_count} replies)")
    print()
    print("  ECONOMICS")
    print(f"  Est pipeline ROI   ${roi_pipeline:>7,}/mo  (qualified+draft_ready+approved+sent)")
    print(f"  Closed revenue     ${closed_rev:>7,.0f}")
    print()
    print("  DRAFT QUEUE")
    print(f"    Pending approval {d_draft:>5}")
    print(f"    Approved         {d_approved:>5}")
    print(f"    Sent             {d_sent:>5}")
    print(f"    Failed           {d_failed:>5}")
    print(f"    Cancelled        {d_cancelled:>5}")
    print()
    print("=" * 52)
    print()
