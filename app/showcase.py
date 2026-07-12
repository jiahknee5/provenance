"""Showcase — the replica-entry gallery index.

  GET /showcase — the two personalized replica cards (GauntletAI + Planet) with their
                  entry links, consoles, and sample logins.

R38 exception (T-09): the /showcase index is KEPT because the locked deploy-gate suites
(test_gauntlet_site.py / test_planet_site.py :: test_showcase_card_publishes_the_entry_links)
pin its replica entry-link content. The per-use-case sister pages (/showcase/{slug},
/production, /observability) are retired — the tour narrative now lives on /apt/demo and
the per-decision observability lives on the per-section consoles (S4/T-04).
"""
from __future__ import annotations

from fastapi import Request
from fastapi.responses import HTMLResponse

from app.server import app, templates


@app.get("/showcase", response_class=HTMLResponse)
def showcase(request: Request):
    from app.gauntlet import MOUNTS as GAUNTLET_MOUNTS
    from app.gauntlet import entry_links as gauntlet_entry_links
    from app.planet import MOUNTS as PLANET_MOUNTS
    from app.planet import entry_links as planet_entry_links
    from pipeline.personalization import gauntlet_site as GS
    from pipeline.personalization import planet_site as PS
    gm = GAUNTLET_MOUNTS["portal"]
    pm = PLANET_MOUNTS["portal"]
    return templates.TemplateResponse(request, "showcase.html", {
        "gauntlet_entries": gauntlet_entry_links(gm),
        "gauntlet_login": GS.sample_login_email(),
        "gauntlet_page": gm["page"],
        "gauntlet_dev": gm["dev"],
        "gauntlet_dev_business": gm["dev_business"],
        "gauntlet_image_decisions": gm["image_decisions"],
        "gauntlet_ad_lp": gm["ad_lp"],
        "planet_entries": planet_entry_links(pm),
        "planet_login": PS.sample_login_email(),
        "planet_page": pm["page"],
        "planet_dev": pm["dev"],
        "planet_dev_business": pm["dev_business"],
        "planet_image_decisions": pm["image_decisions"],
    })
