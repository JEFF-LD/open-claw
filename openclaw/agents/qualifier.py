"""
Qualifier — scores leads 0-100, assigns tier, estimates ROI.
Updates leads table in-place. No separate qualifications table.

Disqualification filters:
  - rating < 4.4
  - review_count < 15
  - no review in last 120 days (if last_review_date available)
"""

import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

from openclaw.agents.base import BaseAgent
from openclaw.persistence.database import get_leads_by_status, update_lead, get_lead

AVG_TICKET = {
    "plumbing": 450, "hvac": 800, "electrical": 400, "roofing": 3500,
    "landscaping": 1200, "arborists": 1100, "carpentry": 900,
    "fence_deck": 2500, "junk_removal": 350,
}

CATEGORY_THEMES = {
    "plumbing": ["responsive service", "fair pricing", "clean work"],
    "hvac": ["reliable technicians", "on-time service", "thorough work"],
    "electrical": ["professional crew", "safety-focused", "fair estimates"],
    "roofing": ["quality materials", "clean job site", "great communication"],
    "landscaping": ["beautiful results", "reliable crew", "attention to detail"],
    "arborists": ["safe tree work", "knowledgeable team", "prompt service"],
    "carpentry": ["craftsmanship", "on-budget", "excellent finish"],
    "fence_deck": ["solid construction", "timely completion", "fair pricing"],
    "junk_removal": ["fast service", "reasonable rates", "friendly crew"],
}

# Keywords for extracting review themes from excerpt
THEME_KEYWORDS = {
    "fast": "Fast response times",
    "quick": "Fast response times",
    "responsive": "Fast response times",
    "professional": "Professional service",
    "honest": "Honest and transparent",
    "fair": "Fair pricing",
    "clean": "Clean job sites",
    "reliable": "Reliable and dependable",
    "emergency": "Emergency service available",
    "friendly": "Friendly team",
    "quality": "Quality workmanship",
    "on time": "Always on time",
    "recommend": "Highly recommended",
    "great": "Great customer experience",
}


class QualifierAgent(BaseAgent):
    name = "qualifier"

    def execute(self, lead_id: str = "", **kw) -> dict:
        if lead_id:
            leads = [l for l in [get_lead(lead_id)] if l]
        else:
            leads = get_leads_by_status("new")

        qualified = 0
        disqualified = 0
        errors = 0
        for lead in leads:
            try:
                # Disqualification filters
                reason = self._check_disqualify(lead)
                if reason:
                    update_lead(lead["id"], lead_status="lost", human_notes=f"Disqualified: {reason}")
                    self.log.info("  DQ: %s — %s", lead["business_name"], reason)
                    disqualified += 1
                    continue

                score, tier = self._score(lead)
                roi = self._estimate_roi(lead)
                themes = self._extract_themes(lead)

                update_lead(lead["id"],
                    qualification_score=score, tier=tier,
                    roi_estimate_monthly=roi, review_themes=themes,
                    lead_status="qualified",
                )
                qualified += 1
                self.log.info("  %s | score=%d tier=%s roi=$%d/mo", lead["business_name"], score, tier, roi)
            except Exception as e:
                self.log.error("  Error qualifying %s: %s", lead.get("business_name", "?"), e)
                errors += 1

        return {"qualified": qualified, "disqualified": disqualified, "errors": errors}

    def _check_disqualify(self, lead: dict) -> str | None:
        """Return disqualification reason or None if OK."""
        if lead["rating"] < 4.4:
            return f"rating {lead['rating']} < 4.4"
        if lead["review_count"] < 15:
            return f"review_count {lead['review_count']} < 15"
        # Check review recency if we have a date
        last_date = lead.get("last_review_date", "")
        if last_date:
            try:
                dt = datetime.strptime(last_date[:7], "%Y-%m")
                cutoff = datetime.utcnow() - timedelta(days=120)
                if dt < cutoff:
                    return f"last review {last_date} > 120 days ago"
            except ValueError:
                pass  # can't parse date, skip this check
        return None

    def _extract_themes(self, lead: dict) -> list[str]:
        """Extract 2-3 review themes from excerpt, or use category fallback."""
        excerpt = lead.get("review_excerpt", "")
        if excerpt:
            lower = excerpt.lower()
            matched = []
            seen = set()
            for keyword, theme in THEME_KEYWORDS.items():
                if keyword in lower and theme not in seen:
                    matched.append(theme)
                    seen.add(theme)
                if len(matched) >= 3:
                    break
            if matched:
                return matched
        # Fallback: generic themes for category
        return CATEGORY_THEMES.get(lead["category"], ["Quality workmanship", "Reliable service", "Professional team"])

    def _score(self, lead: dict) -> tuple[int, str]:
        s = 0
        if lead["rating"] >= 4.6: s += 20
        elif lead["rating"] >= 4.0: s += 10
        if lead["review_count"] >= 40: s += 20
        elif lead["review_count"] >= 20: s += 12
        elif lead["review_count"] >= 10: s += 5
        if not lead["has_website"]: s += 25
        elif lead.get("website_url"):
            ws = self._check_website(lead["website_url"])
            if ws == "weak": s += 15
            elif ws == "modern": s -= 15
        if lead.get("email"): s += 10
        if lead.get("phone"): s += 5
        if lead["review_count"] < 10: s -= 10
        s = max(0, min(100, s))
        if s >= 80: return s, "A"
        if s >= 55: return s, "B"
        if s >= 30: return s, "C"
        return s, "D"

    def _estimate_roi(self, lead: dict) -> int:
        avg = AVG_TICKET.get(lead["category"], 600)
        missed = 6 if not lead["has_website"] else 3
        return missed * avg

    def _check_website(self, url: str) -> str:
        try:
            resp = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code != 200:
                return "weak"
            html = resp.text.lower()
            soup = BeautifulSoup(html, "html.parser")
            has_form = bool(soup.find("form"))
            has_viewport = bool(soup.find("meta", {"name": "viewport"}))
            if has_form and has_viewport and len(html) > 40000:
                return "modern"
            return "weak"
        except Exception:
            return "weak"
