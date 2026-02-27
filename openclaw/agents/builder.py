"""
Builder — generates premium static HTML preview sites.
Writes HTML to previews/ directory. Updates lead with preview_url + preview_path.

# IMPORTANT:
# Only one short review excerpt is used for preview purposes.
# Do not bulk copy or store full review lists.
"""

import html as html_mod
from pathlib import Path

from openclaw import config
from openclaw.agents.base import BaseAgent
from openclaw.agents.creative import CreativeAgent
from openclaw.persistence.database import get_leads_by_status, get_lead, update_lead

COLORS = {
    "plumbing": ("#1565C0", "#ffffff"),
    "hvac": ("#1565C0", "#FF6F00"),
    "electrical": ("#F9A825", "#212121"),
    "roofing": ("#B71C1C", "#ffffff"),
    "landscaping": ("#2E7D32", "#ffffff"),
    "arborists": ("#1B5E20", "#ffffff"),
    "carpentry": ("#6D4C41", "#ffffff"),
    "fence_deck": ("#5D4037", "#ffffff"),
    "junk_removal": ("#E65100", "#ffffff"),
}


class BuilderAgent(BaseAgent):
    name = "builder"

    def execute(self, lead_id: str = "", copy_package: dict = None, **kw) -> dict:
        if lead_id:
            leads = [l for l in [get_lead(lead_id)] if l]
        else:
            leads = get_leads_by_status("qualified")

        creative = CreativeAgent()
        built = 0
        errors = 0
        for lead in leads:
            try:
                if copy_package and lead_id:
                    pkg = copy_package
                else:
                    pkg = creative._generate(lead)

                html = self._render(lead, pkg)
                slug = self._make_slug(lead["business_name"])

                # Write to docs/preview/<slug>/index.html (GitHub Pages serves from /docs)
                slug_dir = Path(config.PREVIEW_DIR) / "preview" / slug
                slug_dir.mkdir(parents=True, exist_ok=True)
                path = slug_dir / "index.html"
                path.write_text(html, encoding="utf-8")

                preview_url = f"{config.PREVIEW_HOST}/preview/{slug}/"
                update_lead(lead["id"], preview_url=preview_url, preview_path=str(path))
                built += 1
                self.log.info("  Built: %s -> %s", lead["business_name"], path)
            except Exception as e:
                self.log.error("  Error building preview for %s: %s", lead.get("business_name", "?"), e)
                errors += 1

        return {"built": built, "errors": errors}

    def _render(self, lead: dict, pkg: dict) -> str:
        biz = html_mod.escape(lead["business_name"])
        phone = lead.get("phone", "")
        rating = pkg.get("rating", lead.get("rating", 0))
        review_count = pkg.get("review_count", lead.get("review_count", 0))
        primary, accent = COLORS.get(lead["category"], ("#1565C0", "#ffffff"))

        stars = self._stars(rating)
        svcs_html = ""
        for s in pkg.get("services", []):
            svcs_html += f'<div class="svc"><h3>{html_mod.escape(s["name"])}</h3><p>{html_mod.escape(s["desc"])}</p></div>\n'

        options_html = "".join(f'<option>{html_mod.escape(s["name"])}</option>' for s in pkg.get("services", []))

        # Review section — excerpt + themes
        review_section = self._build_review_section(lead, rating, review_count, primary)

        # Review themes as list items
        themes = lead.get("review_themes", [])
        themes_html = ""
        if themes:
            items = "".join(f"<li>{html_mod.escape(t)}</li>" for t in themes[:3])
            themes_html = f'<ul class="review-themes">{items}</ul>'

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{biz} | {html_mod.escape(pkg.get("service_area", ""))}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Inter',system-ui,sans-serif;color:#1a1a1a;line-height:1.6}}
.hero{{background:{primary};color:{accent};padding:80px 24px 72px;text-align:center}}
.hero h1{{font-size:2.2rem;font-weight:700;margin-bottom:12px;max-width:640px;margin-left:auto;margin-right:auto}}
.hero p{{font-size:1.15rem;opacity:.9;max-width:520px;margin:0 auto 28px}}
.stars{{font-size:1.1rem;margin-bottom:24px;letter-spacing:1px}}
.stars .num{{font-weight:700;font-size:1.3rem}}
.btn{{display:inline-block;padding:14px 36px;background:#fff;color:{primary};border-radius:8px;text-decoration:none;font-weight:600;font-size:1rem;transition:transform .15s}}
.btn:hover{{transform:translateY(-1px)}}
.btn-outline{{background:transparent;border:2px solid {accent};color:{accent}}}
section{{max-width:880px;margin:0 auto;padding:64px 24px}}
section h2{{font-size:1.6rem;font-weight:700;margin-bottom:32px;text-align:center}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:20px}}
.svc{{border:1px solid #e5e5e5;border-radius:10px;padding:24px;transition:box-shadow .2s}}
.svc:hover{{box-shadow:0 4px 16px rgba(0,0,0,.08)}}
.svc h3{{font-size:1.05rem;margin-bottom:6px;color:{primary}}}
.svc p{{color:#555;font-size:.95rem}}
.reviews{{background:#fafafa;text-align:center;padding:56px 24px}}
.reviews h2{{margin-bottom:20px}}
.reviews .rating{{font-size:1.3rem;margin-bottom:24px}}
.reviews .rating .stars-display{{letter-spacing:2px}}
.reviews blockquote{{max-width:560px;margin:0 auto 24px;font-style:italic;color:#444;font-size:1.05rem;line-height:1.7;padding:20px 28px;background:#fff;border-radius:10px;border-left:4px solid {primary}}}
.reviews blockquote footer{{font-style:normal;font-size:.85rem;color:#888;margin-top:10px}}
.review-themes{{list-style:none;display:flex;flex-wrap:wrap;justify-content:center;gap:12px;margin-top:20px;max-width:560px;margin-left:auto;margin-right:auto}}
.review-themes li{{background:#fff;border:1px solid #e0e0e0;border-radius:20px;padding:8px 18px;font-size:.9rem;color:#555}}
.trust{{background:#f8f8f8;text-align:center;padding:48px 24px}}
.trust h2{{margin-bottom:16px}}
.trust p{{color:#666;max-width:560px;margin:0 auto}}
#quote{{background:#f8f8f8}}
.form{{max-width:440px;margin:0 auto}}
.form input,.form select,.form textarea{{width:100%;padding:13px 16px;margin-bottom:14px;border:1px solid #d0d0d0;border-radius:8px;font-size:.95rem;font-family:inherit}}
.form button{{width:100%;padding:15px;background:{primary};color:#fff;border:none;border-radius:8px;font-size:1.05rem;font-weight:600;cursor:pointer;transition:opacity .15s}}
.form button:hover{{opacity:.9}}
footer{{background:#1a1a1a;color:#888;text-align:center;padding:40px 24px;font-size:.85rem}}
footer a{{color:#bbb}}
.sticky{{position:fixed;bottom:0;left:0;right:0;background:{primary};padding:14px;text-align:center;z-index:100;box-shadow:0 -2px 12px rgba(0,0,0,.15)}}
.sticky a{{color:{accent};margin:0 16px;text-decoration:none;font-weight:600;font-size:.95rem}}
@media(max-width:600px){{
  .hero{{padding:56px 16px 48px}}
  .hero h1{{font-size:1.5rem}}
  section{{padding:48px 16px}}
  .reviews blockquote{{padding:16px 20px}}
}}
</style>
</head>
<body>
<div class="hero">
  <div class="stars">{stars} <span class="num">{rating}</span> from {review_count} reviews</div>
  <h1>{pkg.get("hero_headline", biz)}</h1>
  <p>{html_mod.escape(pkg.get("hero_sub", ""))}</p>
  <a href="#quote" class="btn">Get a Free Quote</a>
</div>

<section>
  <h2>Our Services</h2>
  <div class="grid">{svcs_html}</div>
</section>

{review_section}

<div class="trust">
  <h2>Serving {html_mod.escape(pkg.get("service_area", "Your Area"))}</h2>
  <p>Trusted by homeowners across the area. Licensed, insured, and committed to quality work on every job.</p>
</div>

<section id="quote">
  <h2>{html_mod.escape(pkg.get("quote_headline", "Request a Free Quote"))}</h2>
  <div class="form">
    <input type="text" placeholder="Your Name" required>
    <input type="tel" placeholder="Phone Number" required>
    <input type="email" placeholder="Email Address">
    <select><option value="">Select a Service...</option>{options_html}</select>
    <textarea rows="3" placeholder="Describe your project..."></textarea>
    <button type="button">Request My Free Quote</button>
  </div>
</section>

<footer>
  <p>{biz} &mdash; {html_mod.escape(pkg.get("service_area", ""))}</p>
  <p style="margin-top:8px"><a href="tel:{phone}">{phone}</a></p>
  <p style="margin-top:16px;font-size:.75rem">Preview site built by OpenClaw</p>
</footer>

<div class="sticky">
  <a href="tel:{phone}">Call Now</a>
  <a href="#quote">Get Quote</a>
</div>
</body>
</html>"""

    def _build_review_section(self, lead: dict, rating: float, review_count: int, primary: str) -> str:
        """Build reviews section with dynamic stars, optional excerpt, and themes."""
        stars_display = self._stars(rating)

        # Excerpt block (only if we have one)
        excerpt = lead.get("review_excerpt", "")
        excerpt_html = ""
        if excerpt:
            author = html_mod.escape(lead.get("review_excerpt_author", ""))
            date = lead.get("review_excerpt_date", "")
            footer_parts = []
            if author:
                footer_parts.append(f"&mdash; {author}")
            if date:
                footer_parts.append(date)
            footer_parts.append("(Google Review)")
            footer_text = ", ".join(footer_parts)
            excerpt_html = f"""  <blockquote>
    &ldquo;{html_mod.escape(excerpt)}&rdquo;
    <footer>{footer_text}</footer>
  </blockquote>"""

        # Themes
        themes = lead.get("review_themes", [])
        themes_html = ""
        if themes:
            items = "".join(f"<li>{html_mod.escape(t)}</li>" for t in themes[:3])
            themes_html = f'  <ul class="review-themes">{items}</ul>'

        return f"""<div class="reviews">
  <h2>Trusted by {review_count} Local Customers</h2>
  <div class="rating">
    <span class="stars-display">{stars_display}</span>
    <span>{rating} from {review_count} reviews</span>
  </div>
{excerpt_html}
{themes_html}
</div>"""

    @staticmethod
    def _make_slug(name: str) -> str:
        """Lowercase, dash-separated, no special chars, max 40 chars."""
        import re
        slug = name.lower().strip()
        slug = re.sub(r"[^a-z0-9\s-]", "", slug)
        slug = re.sub(r"[\s]+", "-", slug)
        slug = re.sub(r"-+", "-", slug).strip("-")
        return slug[:40]

    @staticmethod
    def _stars(rating: float) -> str:
        """Render star count dynamically based on actual rating — never exaggerate."""
        rounded = round(rating)
        rounded = max(0, min(5, rounded))
        return "★" * rounded + "☆" * (5 - rounded)
