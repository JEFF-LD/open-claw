"""
Creative — generates homepage copy for preview sites.
Minimal personalization: category, metro, rating, review_count, services, 1 theme.
"""

from openclaw.agents.base import BaseAgent
from openclaw.persistence.database import get_leads_by_status, get_lead

SERVICES = {
    "plumbing": [
        ("Drain Cleaning", "Professional drain clearing for sinks, tubs, and main lines."),
        ("Water Heater Service", "Tank and tankless water heater installation and repair."),
        ("Leak Repair", "Fast detection and repair of hidden and visible leaks."),
        ("Repiping", "Full and partial repiping for aging plumbing systems."),
        ("Sewer Line Service", "Sewer inspection, cleaning, and trenchless repair."),
        ("Fixture Installation", "Faucets, toilets, garbage disposals, and more."),
    ],
    "hvac": [
        ("AC Installation & Repair", "Central air systems installed and serviced."),
        ("Furnace Service", "Installation, repair, and seasonal tune-ups."),
        ("Ductwork", "Duct cleaning, repair, and new installations."),
        ("Mini-Split Systems", "Ductless heating and cooling solutions."),
        ("Thermostat Installation", "Smart and programmable thermostats."),
        ("Maintenance Plans", "Preventative HVAC maintenance programs."),
    ],
    "electrical": [
        ("Panel Upgrades", "Electrical panel upgrades for safety and capacity."),
        ("Rewiring", "Whole-home rewiring for older properties."),
        ("EV Charger Installation", "Level 2 electric vehicle charger setup."),
        ("Lighting", "Interior, exterior, and landscape lighting."),
        ("Generator Installation", "Standby and portable generator hookups."),
        ("Code Compliance", "Inspections and code violation corrections."),
    ],
    "roofing": [
        ("Roof Installation", "New shingle, metal, and flat roof installations."),
        ("Roof Repair", "Leak repair, shingle replacement, storm damage."),
        ("Roof Inspection", "Comprehensive assessments with detailed reports."),
        ("Gutter Service", "Installation, repair, and cleaning."),
        ("Storm Damage Repair", "Emergency tarping and insurance assistance."),
        ("Skylight Installation", "New skylights and leak repair."),
    ],
    "landscaping": [
        ("Lawn Care", "Mowing, fertilization, and weed control."),
        ("Hardscaping", "Patios, walkways, and retaining walls."),
        ("Irrigation Systems", "Sprinkler installation and repair."),
        ("Landscape Design", "Custom design and installation."),
        ("Seasonal Cleanup", "Spring and fall cleanups."),
        ("Outdoor Lighting", "Low-voltage landscape lighting."),
    ],
    "arborists": [
        ("Tree Removal", "Safe removal of trees of any size."),
        ("Trimming & Pruning", "Professional pruning for health and aesthetics."),
        ("Stump Grinding", "Complete stump removal below grade."),
        ("Emergency Service", "Storm damage response and cleanup."),
        ("Tree Health Assessment", "Disease diagnosis and treatment."),
        ("Land Clearing", "Lot clearing for construction."),
    ],
    "carpentry": [
        ("Custom Cabinetry", "Built-to-order cabinets and built-ins."),
        ("Deck Building", "Custom wood and composite decks."),
        ("Trim & Molding", "Crown molding, baseboards, finish work."),
        ("Door & Window Install", "Interior and exterior installation."),
        ("Pergolas & Gazebos", "Custom outdoor structures."),
        ("Wood Repair", "Structural and cosmetic restoration."),
    ],
    "fence_deck": [
        ("Wood Fence", "Cedar, pine, and redwood privacy fencing."),
        ("Vinyl Fence", "Low-maintenance vinyl in multiple styles."),
        ("Deck Building", "Custom decks in wood and composite."),
        ("Deck Staining", "Professional staining and sealing."),
        ("Fence Repair", "Quick repair for damaged fences and gates."),
        ("Privacy Screening", "Custom privacy solutions for yards."),
    ],
    "junk_removal": [
        ("Residential Removal", "Full-service home and apartment cleanout."),
        ("Commercial Cleanout", "Office and warehouse clearing."),
        ("Appliance Removal", "Old appliances hauled away."),
        ("Construction Debris", "Renovation site cleanup."),
        ("Estate Cleanout", "Compassionate estate clearing."),
        ("Yard Waste Removal", "Branches, stumps, debris hauled away."),
    ],
}


class CreativeAgent(BaseAgent):
    name = "creative"

    def execute(self, lead_id: str = "", **kw) -> dict:
        if lead_id:
            leads = [l for l in [get_lead(lead_id)] if l]
        else:
            leads = get_leads_by_status("qualified")

        packages = []
        for lead in leads:
            packages.append(self._generate(lead))
        return {"generated": len(packages), "packages": packages}

    def _generate(self, lead: dict) -> dict:
        cat = lead["category"]
        metro = lead["metro"]
        biz = lead["business_name"]
        themes = lead.get("review_themes", [])
        theme1 = themes[0] if themes else "quality work"
        cat_label = cat.replace("_", " ").title()
        svcs = SERVICES.get(cat, SERVICES["plumbing"])

        return {
            "lead_id": lead["id"],
            "biz_name": biz,
            "hero_headline": f"{cat_label} Services in {metro}",
            "hero_sub": f"Trusted by local homeowners for {theme1}.",
            "rating": lead["rating"],
            "review_count": lead["review_count"],
            "services": [{"name": s[0], "desc": s[1]} for s in svcs],
            "service_area": metro,
            "quote_headline": f"Get a Free {cat_label} Estimate",
        }
