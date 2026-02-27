"""
Prospector — finds local service businesses via Google Places API.
Writes leads to DB with lead_status=new.

# IMPORTANT:
# Only one short review excerpt is used for preview purposes.
# Do not bulk copy or store full review lists.
"""

import re
import time
import requests

from openclaw import config
from openclaw.schemas import _id, _now
from openclaw.agents.base import BaseAgent
from openclaw.persistence.database import insert_lead, lead_exists

SEARCH_TERMS = {
    "plumbing": "plumber",
    "hvac": "hvac contractor",
    "electrical": "electrician",
    "roofing": "roofing contractor",
    "landscaping": "landscaping company",
    "arborists": "arborist tree service",
    "carpentry": "carpenter",
    "fence_deck": "fence and deck contractor",
    "junk_removal": "junk removal service",
}

FRANCHISE_KEYWORDS = [
    "mr. rooter", "roto-rooter", "servpro", "stanley steemer",
    "1-800-got-junk", "college hunks", "trugreen", "servicemaster",
]


class ProspectorAgent(BaseAgent):
    name = "prospector"

    def execute(self, category: str = "", metro: str = "", **kw) -> dict:
        if not category or not metro:
            raise ValueError("category and metro required")

        config.require_places()

        self.log.info("Prospecting %s in %s", category, metro)
        raw = self._search_places(category, metro)

        created = 0
        skipped = 0
        errors = 0

        for place in raw:
            try:
                biz_name = place.get("name", "").strip()
                if not biz_name:
                    skipped += 1
                    continue
                if any(f in biz_name.lower() for f in FRANCHISE_KEYWORDS):
                    skipped += 1
                    continue

                phone = self._clean_phone(place.get("formatted_phone_number", ""))
                website = place.get("website", "")

                if lead_exists(business_name=biz_name, metro=metro):
                    skipped += 1
                    continue

                # Extract ONE short review excerpt if available
                excerpt_data = self._extract_single_excerpt(place)

                insert_lead({
                    "id": _id(),
                    "business_name": biz_name,
                    "phone": phone,
                    "category": category,
                    "metro": metro,
                    "rating": place.get("rating", 0.0),
                    "review_count": place.get("user_ratings_total", 0),
                    "has_website": int(bool(website)),
                    "website_url": website,
                    "gbp_link": place.get("url", ""),
                    "source": "google_places",
                    "lead_status": "new",
                    "last_review_date": excerpt_data.get("last_review_date", ""),
                    "review_excerpt": excerpt_data.get("review_excerpt", ""),
                    "review_excerpt_author": excerpt_data.get("review_excerpt_author", ""),
                    "review_excerpt_date": excerpt_data.get("review_excerpt_date", ""),
                    "created_at": _now(),
                    "updated_at": _now(),
                })
                created += 1
            except Exception as e:
                self.log.error("  Error processing place %s: %s", place.get("name", "?"), e)
                errors += 1

        return {"category": category, "metro": metro, "raw": len(raw),
                "created": created, "skipped": skipped, "errors": errors}

    @staticmethod
    def _extract_single_excerpt(place: dict) -> dict:
        """
        Extract at most ONE short review excerpt from Google Places API response.
        Only uses data the API already provides — no scraping.
        Excerpt is trimmed to 200 chars max. Only first name + last initial stored.
        """
        reviews = place.get("reviews", [])
        if not reviews:
            return {}

        # Take only the first review
        review = reviews[0]
        text = review.get("text", "").replace("\n", " ").replace("\r", " ").strip()
        if not text:
            return {}

        # Trim to 200 chars
        if len(text) > 200:
            text = text[:197].rsplit(" ", 1)[0] + "..."

        # Author: first name + last initial only
        author_full = review.get("author_name", "").strip()
        author_short = ""
        if author_full:
            parts = author_full.split()
            if len(parts) >= 2:
                author_short = f"{parts[0]} {parts[-1][0]}."
            else:
                author_short = parts[0]

        # Date: YYYY-MM from relative_time_description or time
        review_date = ""
        if review.get("time"):
            try:
                from datetime import datetime
                dt = datetime.fromtimestamp(review["time"])
                review_date = dt.strftime("%Y-%m")
            except Exception:
                pass

        # Last review date (most recent across all reviews — just check first)
        last_review_date = review_date

        return {
            "last_review_date": last_review_date,
            "review_excerpt": text,
            "review_excerpt_author": author_short,
            "review_excerpt_date": review_date,
        }

    def _search_places(self, category: str, metro: str) -> list[dict]:
        api_key = config.GOOGLE_PLACES_API_KEY

        query = f"{SEARCH_TERMS.get(category, category)} in {metro}"
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {"query": query, "key": api_key}
        all_places = []

        for _ in range(3):
            try:
                resp = requests.get(url, params=params, timeout=15)
                resp.raise_for_status()
                data = resp.json()
            except requests.RequestException as e:
                self.log.error("Places API request failed: %s", e)
                break

            for p in data.get("results", []):
                detail = self._get_details(p["place_id"], api_key)
                if detail:
                    p.update(detail)
                all_places.append(p)
            token = data.get("next_page_token")
            if not token or len(all_places) >= config.PROSPECT_BATCH_SIZE:
                break
            params = {"pagetoken": token, "key": api_key}
            time.sleep(2)

        return all_places[:config.PROSPECT_BATCH_SIZE]

    def _get_details(self, place_id: str, api_key: str) -> dict | None:
        # IMPORTANT: Request reviews field to get at most 1 short excerpt
        url = "https://maps.googleapis.com/maps/api/place/details/json"
        params = {
            "place_id": place_id,
            "fields": "formatted_phone_number,website,url,reviews",
            "key": api_key,
        }
        try:
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json().get("result", {})
        except Exception:
            return None

    @staticmethod
    def _clean_phone(phone: str) -> str:
        digits = re.sub(r"\D", "", phone)
        if len(digits) == 10:
            return f"+1{digits}"
        if len(digits) == 11 and digits.startswith("1"):
            return f"+{digits}"
        return phone
