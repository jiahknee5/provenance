#!/usr/bin/env python3
"""One-shot generator for demo-nav UI mockups. Run from repo root."""
from __future__ import annotations

from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "app" / "static" / "mockups" / "demo-nav"

THEMES = {
    "a": {
        "label": "Variant A",
        "name": "Campaign command center",
        "thesis": "Dark ops console — Clay × HubSpot density with monospace signal chips.",
        "fonts": "https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap",
        "font_sans": "'IBM Plex Sans',system-ui,sans-serif",
        "font_mono": "'IBM Plex Mono',monospace",
        "font_display": "'IBM Plex Sans',system-ui,sans-serif",
        "bg": "#0a0e14",
        "panel": "#121820",
        "panel2": "#1a2230",
        "ink": "#e8edf4",
        "muted": "#8b9cb3",
        "line": "#2a3548",
        "accent": "#ff7a59",
        "accent2": "#00d4aa",
        "chip_bg": "#1e2838",
        "chip_fg": "#a8c4e8",
        "hero_style": "flat",
        "radius": "8px",
        "shadow": "0 4px 24px rgba(0,0,0,.45)",
        "badge_bg": "#ff7a59",
        "badge_fg": "#0a0e14",
    },
    "b": {
        "label": "Variant B",
        "name": "Product tour",
        "thesis": "Light editorial tour — Stripe-docs whitespace with Fraunces serif accents.",
        "fonts": "https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,600;1,9..144,400&family=Source+Sans+3:wght@400;500;600;700&display=swap",
        "font_sans": "'Source Sans 3',Georgia,serif",
        "font_mono": "'Source Sans 3',Georgia,serif",
        "font_display": "'Fraunces',Georgia,serif",
        "bg": "#faf9f7",
        "panel": "#ffffff",
        "panel2": "#f6f4f0",
        "ink": "#1a1f36",
        "muted": "#697386",
        "line": "#e3e8ee",
        "accent": "#635bff",
        "accent2": "#0a2540",
        "chip_bg": "#f0f3f9",
        "chip_fg": "#3c4257",
        "hero_style": "minimal",
        "radius": "12px",
        "shadow": "0 1px 3px rgba(50,50,93,.08),0 4px 12px rgba(50,50,93,.06)",
        "badge_bg": "#635bff",
        "badge_fg": "#fff",
    },
    "c": {
        "label": "Variant C",
        "name": "Sales deck",
        "thesis": "Bold pitch deck — gradient heroes, Syne display type, motion-forward cards.",
        "fonts": "https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=DM+Sans:wght@400;500;600;700&display=swap",
        "font_sans": "'DM Sans',system-ui,sans-serif",
        "font_mono": "'DM Sans',system-ui,sans-serif",
        "font_display": "'Syne',system-ui,sans-serif",
        "bg": "#0f0a1a",
        "panel": "rgba(255,255,255,.06)",
        "panel2": "rgba(255,255,255,.1)",
        "ink": "#faf8ff",
        "muted": "#b8a8d4",
        "line": "rgba(255,255,255,.12)",
        "accent": "#f5c542",
        "accent2": "#a855f7",
        "chip_bg": "rgba(168,85,247,.2)",
        "chip_fg": "#e9d5ff",
        "hero_style": "gradient",
        "radius": "16px",
        "shadow": "0 20px 60px rgba(88,28,135,.35)",
        "badge_bg": "linear-gradient(135deg,#a855f7,#f5c542)",
        "badge_fg": "#0f0a1a",
    },
}

PAGES = ("sitemap", "hub", "direct", "email", "ads")
VARIANT_LINKS = {
    "sitemap": ("sitemap-a", "sitemap-b", "sitemap-c"),
    "hub": ("hub-a", "hub-b", "hub-c"),
    "direct": ("direct-a", "direct-b", "direct-c"),
    "email": ("email-a", "email-b", "email-c"),
    "ads": ("ads-a", "ads-b", "ads-c"),
}

GAUNTLET_CHANNELS = [
    ("Ads", "Paid social — UTM stack + variant message-match.", "3 scenarios", "/gauntletapt/ad-lp"),
    ("Direct", "Typed URL — IP tier and network type only.", "3 scenarios", "/gauntletapt/direct"),
    ("Email", "HubSpot cohort — magic token or logged-in CRM.", "2 scenarios", "/gauntletapt/email"),
    ("Search", "Organic referrer — intent-neutral entry.", "1 scenario", "/gauntletapt?ref=google"),
]
PLANET_CHANNELS = [
    ("Ads", "Paid social — UTM stack + variant message-match.", "2 scenarios", "/planetapt/ads"),
    ("Direct", "Typed URL — IP tier and network type only.", "2 scenarios", "/planetapt/direct"),
    ("Email", "HubSpot cohort — magic token or logged-in CRM.", "2 scenarios", "/planetapt/email"),
    ("Search", "Organic referrer — intent-neutral entry.", "1 scenario", "/planetapt?ref=google"),
]

DIRECT_CARDS = [
    ("g-direct-anon-tier0", "Cold visit — no signals", "Typed the URL. No UTMs, no login. IP layer is the only hint (tier 0 offline).",
     ["tier0", "anonymous", "anon"], True),
    ("g-direct-corp-tier2", "Corporate IP — Apple office", "Anonymous visitor from a resolved corporate netblock. Firmographic copy may allude; never recites employer.",
     ["corporate", "tier2", "apple", "ip=17.253.144.10"], True),
    ("g-direct-known-return", "Known return — Maya logged in", "Direct revisit with CRM cookie. Welcome-back say-level copy; Vector employer stays allude.",
     ["return-visitor", "crm", "login maya"], False),
]

EMAIL_CARDS = [
    ("g-email-liam-token", "HubSpot cohort — Liam (magic link)", "April cohort email with embedded token. Identified pre-login; abandoned-application objection may surface on console only.",
     "Liam — finish your Gauntlet application", "Your April cohort spot is still open. One click to resume.",
     "Continue application →", "liam.foster@gauntletai.com", ["hubspot", "magic-token", "utm_campaign=cohort-april"], True),
    ("g-email-maya-known", "Known exec — Maya (logged in + email UTMs)", "Email channel classification with active session. Say-level name + declared goals; Cedar Health employer never recited.",
     "Maya — catalyst track for engineering leaders", "Your declared goal: ship AI products faster. See the cohort fit.",
     "Review catalyst track →", "maya.chen@gauntletai.com", ["hubspot", "maya", "b2b"], False),
    ("p-email-kofi-token", "Crisis responders — Kofi (magic link)", "HubSpot crisis-responders campaign. Token identifies Kofi pre-login; relief-org context.",
     "Kofi — imagery for crisis response teams", "Daily coverage when minutes matter. Your trial link inside.",
     "Open crisis responder trial →", "kofi.adeyemi@reliefresponse.org", ["hubspot", "kofi", "utm_campaign=crisis-responders"], True),
    ("p-email-amara-known", "Enterprise agronomy — Amara (logged in)", "Email channel + CRM session. Enterprise track emphasis; location + archetype on console.",
     "Amara — enterprise imagery for agronomy teams", "Field-scale coverage + MRV workflows. See your enterprise path.",
     "View enterprise plan →", "amara.diallo@meridianagronomy.com", ["amara", "enterprise"], False),
]

AD_VARIANTS = [
    ("demographic", "Location targeting", "SF Bay Area · Austin · Seattle", "v01", "x-location-tech-hubs", "CTO", "LD", "#3b82f6",
     "Bay Area and Austin CTOs tell us the same hiring story.", "See how they prove it →",
     "Tech Hubs Don't Have an AI Model Problem.", "They Have a Talent Proof Problem."),
    ("demographic", "Language targeting", "English (United States)", "v02", "x-language-en-us", "Cross-audience", "GA", "#64748b",
     "Most AI pilots stall — and it's rarely the model.", "Worth a look? →",
     "The Direct Path for US Engineering Teams", "to Go AI-First"),
    ("demographic", "Device targeting", "Desktop · Wi-Fi · Office hours", "v03", "x-device-wifi-office", "CTO", "LD", "#3b82f6",
     "B2B buyers research AI hiring solutions at their desk.", "Open to the breakdown? →",
     "Evaluate AI Talent Programs", "Like You Evaluate Vendors"),
    ("demographic", "Age targeting", "28–45", "v04", "x-age-senior-engineer", "Engineer", "EN", "#22c55e",
     "Senior engineers who made the AI leap tell us the same thing.", "Worth applying? →",
     "The Career Leap Experienced Engineers", "Regret Waiting On"),
    ("demographic", "Gender targeting", "All genders (broad reach)", "v05", "x-gender-all", "Cross-audience", "GA", "#64748b",
     "5,000+ engineers apply per Gauntlet cohort.", "See how selection works →",
     "Prove You're an", "AI-First Engineer"),
    ("audience", "Conversation targeting", "AI transformation threads", "v06", "x-conversation-ai-transform", "CTO", "LD", "#a855f7",
     "Your Q3 note mentioned doubling the engineering org.", "Worth a look? →",
     "Your Engineers Ship Features.", "Catalyst Teaches Them to Ship AI."),
    ("audience", "Event targeting", "HR Tech Conference attendees", "v07", "x-event-hrtech", "HR/L&D", "HR", "#a855f7",
     "Your L&D budget buys courses. Catalyst buys engineers who come back different.", "Worth sending the overview? →",
     "Your L&D Budget Buys Courses.", "Catalyst Buys AI Champions."),
    ("audience", "Post Engager", "Engaged with @GauntletAI (30d)", "v08", "x-engager-retarget", "Cross-audience", "GA", "#a855f7",
     "You liked our post about the Challenger selection rate.", "Pick up where you left off →",
     "You Saw the Selection Rate.", "Here's the Proof Model."),
    ("audience", "Keyword targeting", "AI engineer hiring · ML team build", "v09", "x-keyword-ai-hiring", "CTO", "LD", "#a855f7",
     "Saw your team posted three ML engineer roles last month.", "See how they prove it →",
     "Stop Interviewing for Skills You", "Can't Observe in 45 Minutes"),
    ("audience", "Movies & TV targeting", "Sci-fi · tech documentary fans", "v10", "x-movies-earth-docs", "Engineer", "EN", "#a855f7",
     "Engineers who binge tech docs apply at 3× the rate.", "Worth applying? →",
     "The Engineers Who Watch", "Ship Under Pressure"),
    ("audience", "Interest targeting", "Machine learning · DevOps", "v11", "x-interest-ml-devops", "Engineer", "EN", "#a855f7",
     "Your feed says you care about ML infra.", "Apply to Challenger →",
     "Your Feed Knows You're", "Ready for AI-Native"),
    ("audience", "Follower lookalike", "Similar to @GauntletAI followers", "v12", "x-lookalike-followers", "Cross-audience", "GA", "#a855f7",
     "People like you hire from Gauntlet cohorts.", "See the proof model →",
     "Hire Engineers Who've", "Already Proven It"),
]


def footer(page: str, var: str, t: dict) -> str:
    links = VARIANT_LINKS[page]
    nav = " · ".join(
        f'<a href="/apt/mockups/{lnk}"{" class=\"on\"" if lnk == f"{page}-{var}" else ""}>{lnk.split("-")[1].upper()}</a>'
        for lnk in links
    )
    return f"""<footer class="vfoot">
  <span class="vbadge">{t['label']} — {t['name']}</span>
  <nav class="vnav">{nav} · <a href="/apt/mockups">All mockups</a></nav>
</footer>"""


def base_css(t: dict, page: str) -> str:
    hero = ""
    if t["hero_style"] == "gradient":
        hero = """
  .hero{background:linear-gradient(135deg,#2d1b4e 0%,#0f0a1a 40%,#1a0f2e 100%);border:1px solid var(--line);border-radius:var(--radius);padding:48px 40px;margin-bottom:32px;position:relative;overflow:hidden}
  .hero::before{content:'';position:absolute;top:-40%;right:-10%;width:60%;height:140%;background:radial-gradient(circle,rgba(168,85,247,.35),transparent 65%);animation:pulse 6s ease-in-out infinite}
  @keyframes pulse{0%,100%{opacity:.6;transform:scale(1)}50%{opacity:1;transform:scale(1.05)}}
  .hero h1{font-family:var(--display);font-size:clamp(32px,5vw,52px);font-weight:800;line-height:1.05;letter-spacing:-.03em;position:relative}
  .hero .grad{background:linear-gradient(90deg,var(--accent2),var(--accent));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
  .hero p{font-size:17px;color:var(--muted);max-width:58ch;margin-top:14px;line-height:1.55;position:relative}
"""
    elif t["hero_style"] == "minimal":
        hero = """
  .hero{padding:56px 0 36px;border-bottom:1px solid var(--line);margin-bottom:36px}
  .hero .kicker{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);font-weight:600;margin-bottom:12px}
  .hero h1{font-family:var(--display);font-size:clamp(36px,4.5vw,48px);font-weight:600;line-height:1.12;letter-spacing:-.02em;max-width:18ch}
  .hero p{font-size:18px;color:var(--muted);max-width:52ch;margin-top:16px;line-height:1.65}
"""
    else:
        hero = """
  .hero{background:var(--panel2);border:1px solid var(--line);border-radius:var(--radius);padding:20px 24px;margin-bottom:20px;display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap}
  .hero h1{font-family:var(--display);font-size:22px;font-weight:700;margin:0}
  .hero p{font-size:13px;color:var(--muted);margin:4px 0 0;max-width:60ch}
  .hero .stat{font-family:var(--mono);font-size:11px;color:var(--accent2);background:var(--chip-bg);padding:4px 10px;border-radius:6px}
"""

    density = ""
    if page in ("ads",) and t["hero_style"] == "flat":
        density = "body{overflow:hidden;height:100vh}"
    elif page == "ads" and t["hero_style"] == "gradient":
        density = "body{overflow:hidden;height:100vh}"

    return f"""
  :root{{
    --bg:{t['bg']};--panel:{t['panel']};--panel2:{t['panel2']};--ink:{t['ink']};--muted:{t['muted']};
    --line:{t['line']};--accent:{t['accent']};--accent2:{t['accent2']};--chip-bg:{t['chip_bg']};--chip-fg:{t['chip_fg']};
    --radius:{t['radius']};--shadow:{t['shadow']};
    --sans:{t['font_sans']};--mono:{t['font_mono']};--display:{t['font_display']};
  }}
  *{{box-sizing:border-box;margin:0;padding:0}}
  html{{scroll-behavior:smooth}}
  body{{font-family:var(--sans);font-size:14px;line-height:1.5;color:var(--ink);background:var(--bg);-webkit-font-smoothing:antialiased;{density}}}
  a{{color:var(--accent);text-decoration:none}}
  a:hover{{text-decoration:underline}}
  .wrap{{max-width:1140px;margin:0 auto;padding:24px 28px 80px}}
  .topbar{{display:flex;align-items:center;justify-content:space-between;gap:12px;padding-bottom:16px;border-bottom:1px solid var(--line);margin-bottom:20px;font-size:12px;color:var(--muted)}}
  .topbar strong{{color:var(--ink)}}
  .chip{{display:inline-block;font-family:var(--mono);font-size:10.5px;font-weight:500;color:var(--chip-fg);background:var(--chip-bg);border-radius:6px;padding:3px 8px;border:1px solid var(--line)}}
  .chips{{display:flex;flex-wrap:wrap;gap:6px}}
  .btn{{display:inline-block;font-size:12px;font-weight:600;padding:7px 14px;border-radius:8px;border:1px solid var(--line);background:var(--panel);color:var(--ink)}}
  .btn.primary{{background:var(--accent);color:{'#0a0e14' if t['hero_style']=='flat' else '#fff'};border-color:var(--accent)}}
  .vfoot{{position:fixed;bottom:0;left:0;right:0;display:flex;align-items:center;justify-content:space-between;gap:12px;padding:10px 20px;background:var(--panel);border-top:1px solid var(--line);font-size:11px;z-index:99;flex-wrap:wrap}}
  .vbadge{{font-weight:700;padding:5px 12px;border-radius:999px;background:{t['badge_bg']};color:{t['badge_fg']}}}
  .vnav a{{color:var(--muted);margin:0 2px;font-weight:600}}
  .vnav a.on{{color:var(--accent)}}
  {hero}
"""


def wrap(page: str, var: str, title: str, body: str) -> str:
    t = THEMES[var]
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>{title} — {t['name']}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="{t['fonts']}" rel="stylesheet">
<style>{base_css(t, page)}</style>
</head>
<body>
<div class="wrap">
{body}
</div>
{footer(page, var, t)}
</body>
</html>"""


def sitemap(var: str) -> str:
    t = THEMES[var]
    if var == "a":
        tenant_style = """
  .tenant{background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);margin-bottom:16px;overflow:hidden}
  .tenant-hdr{display:flex;align-items:baseline;gap:10px;padding:14px 18px;border-bottom:1px solid var(--line);background:var(--panel2)}
  .tenant-hdr h2{font-size:15px;font-weight:700}
  .tenant-hdr .dom{font-family:var(--mono);font-size:11px;color:var(--muted)}
  .tenant-body{padding:14px 18px}
  .tenant-tag{font-size:12px;color:var(--muted);margin-bottom:12px;line-height:1.5}
  .ch-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
  @media(max-width:800px){.ch-grid{grid-template-columns:repeat(2,1fr)}}
  .ch-tile{display:block;padding:12px 14px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:inherit;text-decoration:none;transition:border-color .15s}
  .ch-tile:hover{border-color:var(--accent);text-decoration:none}
  .ch-tile .lbl{font-family:var(--mono);font-size:9px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}
  .ch-tile h3{font-size:13px;margin:4px 0 6px;font-weight:600}
  .ch-tile p{font-size:11px;color:var(--muted);line-height:1.4}
  .ch-tile .cnt{font-family:var(--mono);font-size:10px;color:var(--accent2);margin-top:8px}
"""
        hero = """<div class="hero">
  <div><h1>/apt/demo — visitor demo tour</h1><p>One sitemap for sales and product review: pick a tenant, then a channel.</p></div>
  <span class="stat">v1 · 14 scenarios · rules/demo_scenarios.yaml</span>
</div>
<a href="/apt/dev" class="chip" style="margin-bottom:16px;display:inline-block">Ops consoles → /apt/dev</a>"""
    elif var == "b":
        tenant_style = """
  .tenant{margin-bottom:48px}
  .tenant-hdr{margin-bottom:8px}
  .tenant-hdr h2{font-family:var(--display);font-size:28px;font-weight:600;letter-spacing:-.02em}
  .tenant-hdr .dom{font-size:14px;color:var(--muted);margin-left:8px}
  .tenant-tag{font-size:16px;color:var(--muted);line-height:1.65;margin-bottom:24px;max-width:58ch}
  .aud-note{font-size:13px;color:var(--muted);margin-bottom:20px}
  .ch-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:20px}
  @media(max-width:700px){.ch-grid{grid-template-columns:1fr}}
  .ch-tile{display:block;padding:28px 26px;border:1px solid var(--line);border-radius:var(--radius);background:var(--panel);color:inherit;text-decoration:none;box-shadow:var(--shadow);transition:transform .2s}
  .ch-tile:hover{transform:translateY(-2px);text-decoration:none;border-color:var(--accent)}
  .ch-tile .lbl{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.1em;color:var(--accent)}
  .ch-tile h3{font-family:var(--display);font-size:22px;margin:10px 0 8px;font-weight:600}
  .ch-tile p{font-size:14px;color:var(--muted);line-height:1.55}
  .ch-tile .cnt{font-size:12px;color:var(--accent2);margin-top:14px;font-weight:600}
"""
        hero = """<div class="hero">
  <div class="kicker">Visitor demo tour</div>
  <h1>Pick a tenant.<br>Pick a channel.</h1>
  <p>Curated galleries and landing URLs — same deterministic personalization engine as production.</p>
</div>
<p style="margin-bottom:32px"><a href="/apt/dev">Ops consoles → /apt/dev</a></p>"""
    else:
        tenant_style = """
  .tenant{margin-bottom:28px}
  .tenant-hdr h2{font-family:var(--display);font-size:20px;font-weight:800}
  .tenant-hdr .dom{font-size:12px;color:var(--muted)}
  .tenant-tag{font-size:13px;color:var(--muted);margin:8px 0 16px}
  .ch-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
  @media(max-width:900px){.ch-grid{grid-template-columns:repeat(2,1fr)}}
  .ch-tile{display:block;padding:18px 16px;border-radius:var(--radius);background:var(--panel);border:1px solid var(--line);backdrop-filter:blur(8px);color:inherit;text-decoration:none;transition:transform .2s,box-shadow .2s}
  .ch-tile:hover{transform:translateY(-4px);box-shadow:var(--shadow);text-decoration:none}
  .ch-tile h3{font-family:var(--display);font-size:15px;font-weight:700;margin:6px 0}
  .ch-tile p{font-size:11px;color:var(--muted);line-height:1.4}
  .ch-tile .cnt{font-size:10px;color:var(--accent);margin-top:10px;font-weight:700}
  .ch-tile .lbl{font-size:9px;text-transform:uppercase;letter-spacing:.1em;color:var(--accent2)}
"""
        hero = """<div class="hero">
  <h1>/apt/demo<br><span class="grad">Visitor demo tour</span></h1>
  <p>One sitemap for sales — tenant × channel × scenario. Deterministic rebuild from query params.</p>
</div>
<a href="/apt/dev" class="btn primary" style="margin-bottom:24px">Ops consoles →</a>"""

    def tenant_block(name, domain, tagline, biz, con, channels):
        tiles = ""
        for lbl, desc, cnt, href in channels:
            tiles += f"""<a class="ch-tile" href="{href}">
      <div class="lbl">{name}</div>
      <h3>{lbl}</h3>
      <p>{desc}</p>
      <div class="cnt">{cnt}</div>
    </a>"""
        return f"""<section class="tenant">
  <div class="tenant-hdr"><h2>{name}</h2><span class="dom">{domain}</span></div>
  <div class="tenant-body">
    <p class="tenant-tag">{tagline}</p>
    <p class="aud-note">Audience tabs: <strong>{biz}</strong> · <strong>{con}</strong></p>
    <div class="ch-grid">{tiles}</div>
  </div>
</section>"""

    extra = tenant_style
    body = f"""<style>{extra}</style>
<div class="topbar"><span>Mockup · <strong>Demo sitemap</strong></span><span>/apt/demo</span></div>
{hero}
{tenant_block("GauntletAI", "gauntletai.com", "AI hiring fellowship — entry channel × IP tier × CRM identity.", "Companies", "Individuals", GAUNTLET_CHANNELS)}
{tenant_block("Planet", "planet.com", "Earth observation — location signal on channel, IP, and identity.", "Enterprise", "Self-serve", PLANET_CHANNELS)}
<p style="font-size:12px;color:var(--muted);margin-top:20px">Catalog: <code>rules/demo_scenarios.yaml</code> · Prompt ref: <code>rules/design_prompts.yaml</code></p>"""
    return wrap("sitemap", var, "/apt/demo — sitemap", body)


def hub(var: str) -> str:
    cards = [
        ("Marketer console", "Campaign-ops view — workflow, copy slots, image guardrails, staged YAML diffs.", "/gauntletapt/dev/business"),
        ("Engineer console", "Full decision trace, 11-stage process map, plain-English story, audit ledger.", "/gauntletapt/dev"),
        ("Image decisions", "Pipeline guide — intents, guardrails, pre-cached vs live inventory.", "/gauntletapt/image-decisions"),
        ("Live replica", "The personalized page a visitor sees — same query params, no console chrome.", "/gauntletapt"),
        ("X ads grid", "All 12 paid-social mockups with per-variant landing links.", "/gauntletapt/ad-lp"),
    ]
    entries = [
        ("Direct", "/gauntletapt"),
        ("Email UTMs", "/gauntletapt?utm_source=hubspot&utm_medium=email"),
        ("X ad v09", "/gauntletapt?utm_source=x&utm_medium=paid&utm_campaign=x-keyword-ai-hiring&utm_content=v09"),
        ("Search", "/gauntletapt?ref=google"),
    ]

    if var == "a":
        style = """
  .site-tog{display:inline-flex;gap:2px;background:var(--panel2);border:1px solid var(--line);border-radius:8px;padding:3px;margin-bottom:16px}
  .site-tog a{font-size:12px;font-weight:600;padding:7px 16px;border-radius:6px;color:var(--muted);text-decoration:none}
  .site-tog a.on{background:var(--accent);color:#0a0e14}
  .id-tog{display:inline-flex;gap:2px;margin-left:auto}
  .id-tog a{font-family:var(--mono);font-size:11px;padding:5px 12px;border:1px solid var(--line);border-radius:6px;color:var(--muted);text-decoration:none}
  .id-tog a.on{border-color:var(--accent2);color:var(--accent2)}
  .hub-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin:20px 0}
  .hub-card{display:block;padding:14px 16px;border:1px solid var(--line);border-radius:8px;background:var(--panel);color:inherit;text-decoration:none}
  .hub-card:hover{border-color:var(--accent);text-decoration:none}
  .hub-card h2{font-size:14px;margin-bottom:6px}
  .hub-card p{font-size:11px;color:var(--muted);line-height:1.45}
  .hub-card .go{font-family:var(--mono);font-size:10px;color:var(--accent);margin-top:10px}
  .entries{padding:14px 16px;border:1px solid var(--line);border-radius:8px;background:var(--panel2)}
"""
        hero = """<div class="hero"><div><h1>/apt/dev — personalization consoles</h1><p>Site picker + identity preview → engineer or marketer console.</p></div></div>"""
        site = """<nav class="site-tog"><a href="#" class="on">GauntletAI</a><a href="#">Planet</a></nav>
<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:8px">
  <span style="font-size:12px;color:var(--muted)">GauntletAI · gauntletai.com</span>
  <nav class="id-tog"><a href="#" class="on">anon</a><a href="#">known · maya.chen@gauntletai.com</a></nav>
</div>"""
    elif var == "b":
        style = """
  .site-tog{display:flex;gap:24px;border-bottom:1px solid var(--line);padding-bottom:12px;margin-bottom:32px}
  .site-tog a{font-family:var(--display);font-size:20px;color:var(--muted);text-decoration:none;padding-bottom:12px;border-bottom:2px solid transparent;margin-bottom:-13px}
  .site-tog a.on{color:var(--ink);border-color:var(--accent)}
  .meta-row{display:flex;gap:16px;align-items:center;margin-bottom:28px;flex-wrap:wrap}
  .meta-row p{font-size:15px;color:var(--muted);max-width:50ch;line-height:1.6}
  .id-tog a{font-size:13px;font-weight:600;margin-right:12px;color:var(--muted);text-decoration:none;padding:6px 0;border-bottom:2px solid transparent}
  .id-tog a.on{color:var(--accent);border-color:var(--accent)}
  .hub-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:24px;margin:32px 0}
  .hub-card{display:block;padding:32px 28px;border:1px solid var(--line);border-radius:var(--radius);background:var(--panel);box-shadow:var(--shadow);color:inherit;text-decoration:none}
  .hub-card h2{font-family:var(--display);font-size:22px;margin-bottom:10px}
  .hub-card p{font-size:14px;color:var(--muted);line-height:1.6}
  .hub-card .go{font-size:13px;font-weight:600;color:var(--accent);margin-top:16px}
  .entries{padding:24px;border:1px solid var(--line);border-radius:var(--radius);background:var(--panel2)}
"""
        hero = """<div class="hero">
  <div class="kicker">Personalization consoles</div>
  <h1>One hub for both live replicas.</h1>
  <p>Pick a site, preview identity, open the engineer or marketer console.</p>
</div>"""
        site = """<nav class="site-tog"><a href="#" class="on">GauntletAI</a><a href="#">Planet</a></nav>
<div class="meta-row">
  <p>AI hiring fellowship — entry channel × IP tier × CRM identity.</p>
  <nav class="id-tog"><a href="#">Anonymous</a><a href="#" class="on">Known (maya.chen@gauntletai.com)</a></nav>
</div>"""
    else:
        style = """
  .site-tog{display:flex;gap:10px;margin-bottom:20px}
  .site-tog a{padding:10px 20px;border-radius:999px;border:1px solid var(--line);font-weight:700;font-size:13px;color:var(--muted);text-decoration:none}
  .site-tog a.on{background:linear-gradient(135deg,var(--accent2),var(--accent));color:var(--badge_fg);border:none}
  .id-tog{display:flex;gap:8px;margin-bottom:24px}
  .id-tog a{padding:8px 16px;border-radius:8px;font-size:12px;font-weight:600;border:1px solid var(--line);color:var(--muted);text-decoration:none}
  .id-tog a.on{border-color:var(--accent);color:var(--accent)}
  .hub-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;margin:20px 0}
  .hub-card{display:block;padding:22px 20px;border-radius:var(--radius);background:var(--panel);border:1px solid var(--line);color:inherit;text-decoration:none;transition:transform .2s}
  .hub-card:hover{transform:scale(1.02);text-decoration:none}
  .hub-card h2{font-family:var(--display);font-size:17px;font-weight:800;margin-bottom:8px}
  .hub-card p{font-size:12px;color:var(--muted);line-height:1.45}
  .hub-card .go{font-size:11px;font-weight:700;color:var(--accent);margin-top:12px;text-transform:uppercase;letter-spacing:.06em}
  .entries{padding:18px;border-radius:var(--radius);border:1px solid var(--line);background:var(--panel2)}
"""
        hero = """<div class="hero">
  <h1>/apt/dev<br><span class="grad">Console command</span></h1>
  <p>Route into engineer or marketer consoles with the right site + identity preview.</p>
</div>"""
        site = """<nav class="site-tog"><a href="#" class="on">GauntletAI</a><a href="#">Planet</a></nav>
<nav class="id-tog"><a href="#" class="on">Anonymous</a><a href="#">Known · maya.chen@gauntletai.com</a></nav>"""

    card_html = "".join(
        f'<a class="hub-card" href="{href}"><h2>{title}</h2><p>{desc}</p><span class="go">Open →</span></a>'
        for title, desc, href in cards
    )
    entry_html = " ".join(f'<a class="chip" href="{href}">{lbl} →</a>' for lbl, href in entries)

    body = f"""<style>{style}</style>
<div class="topbar"><span>Mockup · <strong>Ops hub</strong></span><a href="/apt/demo">Demo sitemap →</a></div>
{hero}
{site}
<div class="hub-grid">{card_html}</div>
<div class="entries">
  <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin-bottom:10px">Simulate an entry for GauntletAI</div>
  <div class="chips">{entry_html} <span class="chip">then log in as maya.chen@gauntletai.com</span></div>
</div>"""
    return wrap("hub", var, "/apt/dev — ops hub", body)


def direct(var: str) -> str:
    if var == "a":
        style = """
  .gal-back{font-size:12px;font-weight:600;margin-bottom:12px;display:inline-block}
  .aud-tog{display:inline-flex;gap:2px;background:var(--panel2);border:1px solid var(--line);border-radius:8px;padding:3px;margin-bottom:16px}
  .aud-tog a{font-size:11px;font-weight:600;padding:6px 12px;border-radius:6px;color:var(--muted);text-decoration:none}
  .aud-tog a.on{background:var(--accent);color:#0a0e14}
  .card-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}
  .sc-card{border:1px solid var(--line);border-radius:8px;background:var(--panel);padding:14px 16px}
  .sc-card.featured{border-color:var(--accent2)}
  .sc-card h2{font-size:14px;margin-bottom:6px}
  .sc-card .story{font-size:11px;color:var(--muted);line-height:1.45;margin-bottom:10px}
  .links{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
"""
        hero = """<a class="gal-back" href="/apt/demo">← Demo sitemap</a>
<div class="hero"><div><h1>/gauntletapt/direct — Direct entry gallery</h1><p>Typed URL — IP tier and network type are the only arrival signals.</p></div></div>"""
    elif var == "b":
        style = """
  .gal-back{font-size:14px;margin-bottom:20px;display:inline-block}
  .aud-tog{display:flex;gap:20px;margin-bottom:28px;border-bottom:1px solid var(--line);padding-bottom:12px}
  .aud-tog a{font-size:14px;font-weight:600;color:var(--muted);text-decoration:none;padding-bottom:12px;margin-bottom:-13px;border-bottom:2px solid transparent}
  .aud-tog a.on{color:var(--ink);border-color:var(--accent)}
  .card-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:24px}
  .sc-card{border:1px solid var(--line);border-radius:var(--radius);background:var(--panel);padding:28px;box-shadow:var(--shadow)}
  .sc-card.featured{border-color:var(--accent)}
  .sc-card h2{font-family:var(--display);font-size:22px;margin-bottom:10px}
  .sc-card .story{font-size:14px;color:var(--muted);line-height:1.6;margin-bottom:14px}
  .links{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}
"""
        hero = """<a class="gal-back" href="/apt/demo">← Demo sitemap</a>
<div class="hero">
  <div class="kicker">GauntletAI · Direct</div>
  <h1>Direct entry gallery</h1>
  <p>Typed URL — IP tier and network type are the only arrival signals.</p>
</div>"""
    else:
        style = """
  .gal-back{font-size:12px;margin-bottom:16px;display:inline-block}
  .aud-tog{display:flex;gap:8px;margin-bottom:20px}
  .aud-tog a{padding:8px 16px;border-radius:999px;border:1px solid var(--line);font-size:12px;font-weight:700;color:var(--muted);text-decoration:none}
  .aud-tog a.on{background:var(--accent2);color:#fff;border-color:var(--accent2)}
  .card-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
  .sc-card{border-radius:var(--radius);background:var(--panel);border:1px solid var(--line);padding:20px;transition:transform .2s}
  .sc-card:hover{transform:translateY(-3px)}
  .sc-card.featured{border-color:var(--accent)}
  .sc-card h2{font-family:var(--display);font-size:16px;font-weight:800;margin-bottom:8px}
  .sc-card .story{font-size:12px;color:var(--muted);line-height:1.45;margin-bottom:10px}
  .links{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}
"""
        hero = """<a class="gal-back" href="/apt/demo">← Demo sitemap</a>
<div class="hero">
  <h1>Direct entry<br><span class="grad">GauntletAI</span></h1>
  <p>3 scenarios · audience segment filter below</p>
</div>"""

    cards = ""
    for sid, title, story, chips, featured in DIRECT_CARDS:
        chip_html = "".join(f'<span class="chip">{c}</span>' for c in chips)
        cards += f"""<article class="sc-card{' featured' if featured else ''}" id="{sid}">
  <h2>{title}</h2>
  <p class="story">{story}</p>
  <div class="chips">{chip_html}</div>
  <div class="links">
    <a class="btn primary" href="/gauntletapt">Open landing →</a>
    <a class="btn" href="/gauntletapt/dev">Engineer console</a>
    <a class="btn" href="/gauntletapt/dev/business">Marketer console</a>
  </div>
</article>"""

    body = f"""<style>{style}</style>
<div class="topbar"><span>Mockup · <strong>Direct gallery</strong></span><span>GauntletAI</span></div>
{hero}
<nav class="aud-tog"><a href="#" class="on">All</a><a href="#">Companies</a><a href="#">Individuals</a></nav>
<div class="card-grid">{cards}</div>"""
    return wrap("direct", var, "Direct entry gallery", body)


def email(var: str) -> str:
    if var == "a":
        email_style = """
  .email-wrap{border:1px solid var(--line);border-radius:8px;overflow:hidden;margin-bottom:10px;background:var(--panel2)}
  .email-hdr{padding:8px 12px;font-family:var(--mono);font-size:10px;color:var(--muted);border-bottom:1px solid var(--line)}
  .email-in{padding:12px 14px}
  .email-subj{font-size:14px;font-weight:700;margin-bottom:4px}
  .email-pre{font-size:11px;color:var(--muted);margin-bottom:10px}
  .email-cta{display:inline-block;font-size:11px;font-weight:700;background:var(--accent);color:#0a0e14;padding:6px 12px;border-radius:6px;margin-top:8px}
  .card-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}
  .sc-card{border:1px solid var(--line);border-radius:8px;background:var(--panel);padding:14px}
"""
        hero = """<div class="hero"><div><h1>/gauntletapt/email — Email entry gallery</h1><p>HubSpot cohort sends — magic token or logged-in CRM before landing.</p></div></div>"""
    elif var == "b":
        email_style = """
  .email-wrap{border:1px solid var(--line);border-radius:var(--radius);overflow:hidden;margin-bottom:14px;background:#f5f8fa}
  .email-hdr{padding:10px 14px;font-size:12px;font-weight:600;color:#33475b;background:#eaf0f6;border-bottom:1px solid #dfe3eb}
  .email-in{padding:16px 18px;background:#fff}
  .email-subj{font-size:16px;font-weight:700;color:#33475b;margin-bottom:6px}
  .email-pre{font-size:13px;color:#7c98b6;margin-bottom:12px}
  .email-cta{display:inline-block;font-size:12px;font-weight:700;background:#ff7a59;color:#fff;padding:8px 14px;border-radius:6px;margin-top:10px}
  .card-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:28px}
  .sc-card{border:1px solid var(--line);border-radius:var(--radius);background:var(--panel);padding:24px;box-shadow:var(--shadow)}
  .sc-card h2{font-family:var(--display);font-size:20px;margin-top:12px}
"""
        hero = """<div class="hero">
  <div class="kicker">Email channel</div>
  <h1>HubSpot-style entry gallery</h1>
  <p>Magic token or logged-in CRM — preview the inbox moment before landing.</p>
</div>"""
    else:
        email_style = """
  .email-wrap{border-radius:12px;overflow:hidden;margin-bottom:12px;border:1px solid var(--line);background:linear-gradient(180deg,rgba(168,85,247,.15),transparent)}
  .email-hdr{padding:8px 12px;font-size:10px;color:var(--muted)}
  .email-in{padding:14px}
  .email-subj{font-family:var(--display);font-size:15px;font-weight:700;margin-bottom:6px}
  .email-pre{font-size:11px;color:var(--muted);margin-bottom:10px}
  .email-cta{display:inline-block;font-size:11px;font-weight:800;background:linear-gradient(90deg,var(--accent2),var(--accent));color:var(--badge_fg);padding:8px 16px;border-radius:999px;margin-top:8px}
  .card-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
  .sc-card{border-radius:var(--radius);background:var(--panel);border:1px solid var(--line);padding:18px}
  .sc-card h2{font-family:var(--display);font-size:15px;font-weight:800;margin-top:10px}
"""
        hero = """<div class="hero">
  <h1>Email gallery<br><span class="grad">HubSpot previews</span></h1>
  <p>Gauntlet + Planet cohort sends with magic tokens and CRM sessions.</p>
</div>"""

    cards = ""
    for sid, title, story, subj, pre, cta, recip, chips, featured in EMAIL_CARDS:
        chip_html = "".join(f'<span class="chip">{c}</span>' for c in chips)
        cards += f"""<article class="sc-card{' featured' if featured else ''}" id="{sid}">
  <div class="email-wrap">
    <div class="email-hdr">HubSpot · {recip}</div>
    <div class="email-in">
      <div class="email-subj">{subj}</div>
      <div class="email-pre">{pre}</div>
      <p style="font-size:12px;color:var(--muted);line-height:1.45;margin-top:8px">{story}</p>
      <span class="email-cta">{cta}</span>
    </div>
  </div>
  <h2>{title}</h2>
  <div class="chips">{chip_html}</div>
  <div class="links" style="display:flex;gap:6px;flex-wrap:wrap;margin-top:10px">
    <a class="btn primary" href="#">Open landing →</a>
    <a class="btn" href="#">Engineer console</a>
    <a class="btn" href="#">Marketer console</a>
  </div>
</article>"""

    body = f"""<style>{email_style}</style>
<div class="topbar"><span>Mockup · <strong>Email gallery</strong></span><a href="/apt/demo">← Sitemap</a></div>
<a class="gal-back" href="/apt/demo" style="font-size:12px;margin-bottom:12px;display:inline-block">← Demo sitemap</a>
{hero}
<nav class="aud-tog" style="display:flex;gap:8px;margin-bottom:16px">
  <a href="#" class="btn" style="{'background:var(--accent);color:#0a0e14' if var=='a' else ''}">All</a>
  <a href="#" class="btn">Companies / Enterprise</a>
  <a href="#" class="btn">Individuals / Self-serve</a>
</nav>
<div class="card-grid">{cards}</div>"""
    return wrap("email", var, "Email entry gallery", body)


def ads(var: str) -> str:
    cards = ""
    for cat, typ, cfg, vid, camp, fit, av, accent, trig, cta, h1a, h1b in AD_VARIANTS:
        border = "#3b82f6" if cat == "demographic" else "#a855f7"
        cards += f"""<a class="ad-card cat-{cat}" href="/gauntletapt?utm_source=x&utm_medium=paid&utm_campaign={camp}&utm_content={vid}">
  <div class="ad-meta">
    <span class="cat-tag" style="background:{border}">{cat}</span>
    <div class="ad-type">{typ}</div>
    <div class="ad-cfg">{cfg}</div>
    <div class="ad-fit">Best for <b>{fit}</b></div>
  </div>
  <div class="x-post">
    <div class="x-top"><span class="av" style="background:{accent}">{av}</span><div><b>Gauntlet AI</b><span>@GauntletAI · Promoted</span></div></div>
    <p class="x-text"><span class="trig">{trig}</span></p>
    <div class="x-foot"><span class="x-cta">{cta}</span><span class="utm">utm_content={vid}</span></div>
    <div class="hero-shift"><span class="lbl">Hero shift</span><span class="gen">Generic hero headline</span><span class="per">{h1a} {h1b}</span></div>
  </div>
</a>"""

    if var == "a":
        style = """
  html,body{height:100%;overflow:hidden}
  .wrap{max-width:none;padding:8px 12px 60px;height:100vh;display:flex;flex-direction:column}
  .ad-grid{flex:1;display:grid;grid-template-columns:repeat(6,1fr);grid-template-rows:repeat(2,1fr);gap:8px;min-height:0}
  @media(max-width:1200px){.ad-grid{grid-template-columns:repeat(4,1fr);grid-template-rows:repeat(3,1fr)}}
  .ad-card{display:flex;flex-direction:column;border:1px solid #cfd9de;border-radius:8px;overflow:hidden;background:#fff;color:#0f1419;text-decoration:none;min-height:0}
  .ad-card:hover{border-color:var(--accent);text-decoration:none}
  .ad-card.cat-demographic{border-left:3px solid #3b82f6}
  .ad-card.cat-audience{border-left:3px solid #a855f7}
  .ad-meta{padding:6px 8px;border-bottom:1px solid #eff3f4;font-size:10px}
  .cat-tag{display:inline-block;font-size:7px;font-weight:700;text-transform:uppercase;color:#fff;border-radius:3px;padding:1px 5px;margin-bottom:3px}
  .ad-type{font-weight:700;font-size:11px}
  .ad-cfg{font-family:var(--mono);font-size:9px;color:#536471;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .ad-fit{font-size:9px;color:#536471}
  .x-post{flex:1;background:#15202b;display:flex;flex-direction:column;min-height:0}
  .x-top{display:flex;gap:6px;padding:5px 7px;border-bottom:1px solid #38444d;align-items:center}
  .av{width:20px;height:20px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:8px;font-weight:700;color:#fff}
  .x-top b{display:block;font-size:10px;color:#fff}
  .x-top span{font-size:9px;color:#8899a6}
  .x-text{padding:5px 7px;font-size:10px;color:#e7e9ea;line-height:1.3;flex:1}
  .trig{color:#c9a24b;font-weight:500}
  .x-foot{padding:0 7px 4px;display:flex;gap:6px;font-size:9px}
  .x-cta{color:#c9a24b;font-weight:700}
  .utm{font-family:var(--mono);color:#8899a6;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .hero-shift{padding:4px 7px;border-top:1px solid #38444d;font-size:9px}
  .hero-shift .lbl{font-family:var(--mono);font-size:7px;text-transform:uppercase;color:#8899a6}
  .hero-shift .gen{color:#6d6960;text-decoration:line-through;display:block}
  .hero-shift .per{color:#c9a24b;font-weight:600;display:block}
"""
        hero = """<div class="hero" style="margin-bottom:8px;padding:10px 14px"><div><h1 style="font-size:14px">X Ads Manager — 12 Variants</h1><p style="font-size:10px">GauntletAI paid-social catalog</p></div><a href="/apt/demo" class="chip">← Sitemap</a></div>"""
    elif var == "b":
        style = """
  .ad-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:24px;margin-top:24px}
  @media(max-width:900px){.ad-grid{grid-template-columns:1fr}}
  .ad-card{display:block;border:1px solid var(--line);border-radius:var(--radius);overflow:hidden;background:var(--panel);color:inherit;text-decoration:none;box-shadow:var(--shadow)}
  .ad-card:hover{transform:translateY(-2px);text-decoration:none}
  .ad-meta{padding:16px 18px;border-bottom:1px solid var(--line)}
  .cat-tag{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--accent)}
  .ad-type{font-family:var(--display);font-size:18px;font-weight:600;margin:6px 0}
  .ad-cfg{font-size:12px;color:var(--muted)}
  .ad-fit{font-size:12px;color:var(--muted);margin-top:6px}
  .x-post{padding:18px;background:#f8fafc}
  .x-top{display:flex;gap:10px;align-items:center;margin-bottom:10px}
  .av{width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;color:#fff}
  .x-top b{display:block;font-size:14px}
  .x-top span{font-size:12px;color:var(--muted)}
  .x-text{font-size:14px;line-height:1.5;color:var(--ink);margin-bottom:12px}
  .trig{font-weight:600;color:var(--accent2)}
  .x-foot{font-size:12px;color:var(--muted)}
  .x-cta{color:var(--accent);font-weight:700}
  .hero-shift{margin-top:12px;padding-top:12px;border-top:1px solid var(--line);font-size:12px}
  .hero-shift .gen{color:var(--muted);text-decoration:line-through}
  .hero-shift .per{color:var(--ink);font-weight:600}
"""
        hero = """<div class="hero">
  <div class="kicker">GauntletAI · Paid social</div>
  <h1>12 X ad variants</h1>
  <p>One per X Ads Manager targeting type — message-match landing URLs.</p>
</div>"""
    else:
        style = """
  .ad-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:20px}
  @media(max-width:1100px){.ad-grid{grid-template-columns:repeat(3,1fr)}}
  @media(max-width:700px){.ad-grid{grid-template-columns:repeat(2,1fr)}}
  .ad-card{display:block;border-radius:var(--radius);overflow:hidden;background:var(--panel);border:1px solid var(--line);color:inherit;text-decoration:none;transition:transform .2s,box-shadow .2s}
  .ad-card:hover{transform:translateY(-4px) scale(1.01);box-shadow:var(--shadow);text-decoration:none}
  .ad-meta{padding:12px 14px;background:linear-gradient(135deg,rgba(168,85,247,.2),transparent)}
  .cat-tag{font-size:8px;font-weight:800;text-transform:uppercase;color:var(--accent2)}
  .ad-type{font-family:var(--display);font-size:13px;font-weight:800}
  .ad-cfg{font-size:10px;color:var(--muted);margin-top:4px}
  .x-post{padding:12px;background:#15202b}
  .x-top{display:flex;gap:8px;align-items:center;margin-bottom:8px}
  .av{width:24px;height:24px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:9px;font-weight:700;color:#fff}
  .x-top b{font-size:11px;color:#fff;display:block}
  .x-top span{font-size:9px;color:#8899a6}
  .x-text{font-size:10px;color:#e7e9ea;line-height:1.35}
  .trig{color:var(--accent)}
  .x-cta{font-size:10px;font-weight:800;color:var(--accent)}
  .hero-shift{padding:8px 14px;font-size:9px;border-top:1px solid var(--line)}
  .hero-shift .per{font-weight:700;color:var(--accent)}
"""
        hero = """<div class="hero">
  <h1>12 variants.<br><span class="grad">One proof model.</span></h1>
  <p>X Ads Manager targeting types → personalized hero shift on landing.</p>
</div>"""

    body = f"""<style>{style}</style>
<div class="topbar"><span>Mockup · <strong>Ads grid</strong></span><span>GauntletAI</span></div>
{hero}
<div class="ad-grid">{cards}</div>"""
    return wrap("ads", var, "X ads grid", body)


def index_html() -> str:
    cards = ""
    page_labels = dict(_PAGES)
    for page, plabel in _PAGES:
        for var, vname in _VARIANTS:
            t = THEMES[var]
            cards += f"""<a class="card" href="/apt/mockups/{page}-{var}">
  <div class="thumb" style="background:{'#0a0e14' if var=='a' else '#faf9f7' if var=='b' else '#0f0a1a'}"></div>
  <div class="body">
    <div class="tag">{t['label']} · {vname}</div>
    <div class="name">{plabel}</div>
    <div class="desc">{t['thesis']}</div>
  </div>
</a>"""

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Demo nav UI mockups</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@500&family=Source+Serif+4:wght@600&display=swap" rel="stylesheet">
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:system-ui,sans-serif;background:#f4f2ef;color:#1a1f36;padding:32px 24px 80px}}
  h1{{font-family:'Source Serif 4',serif;font-size:36px;margin-bottom:8px}}
  .sub{{color:#697386;margin-bottom:32px;max-width:60ch;line-height:1.6}}
  .grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;max-width:1200px}}
  @media(max-width:900px){{.grid{{grid-template-columns:repeat(2,1fr)}}}}
  @media(max-width:560px){{.grid{{grid-template-columns:1fr}}}}
  .card{{display:block;border:1px solid #e3e8ee;border-radius:12px;overflow:hidden;background:#fff;text-decoration:none;color:inherit;transition:transform .2s}}
  .card:hover{{transform:translateY(-3px);box-shadow:0 12px 32px rgba(50,50,93,.12)}}
  .thumb{{height:100px}}
  .body{{padding:16px 18px}}
  .tag{{font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:#635bff}}
  .name{{font-family:'Source Serif 4',serif;font-size:18px;margin-top:6px;font-weight:600}}
  .desc{{font-size:13px;color:#697386;margin-top:6px;line-height:1.45}}
</style>
</head>
<body>
<h1>Demo navigation — 15 UI mockups</h1>
<p class="sub">Three design directions per page type. Mockups only — production templates unchanged. Preview at <code>/apt/mockups/{{name}}</code>.</p>
<div class="grid">{cards}</div>
</body>
</html>"""


_PAGES = (
    ("sitemap", "Demo sitemap"),
    ("hub", "Ops hub"),
    ("direct", "Direct gallery"),
    ("email", "Email gallery"),
    ("ads", "Ads grid"),
)
_VARIANTS = (
    ("a", "Campaign command center"),
    ("b", "Product tour"),
    ("c", "Sales deck"),
)


def readme() -> str:
    lines = ["# Demo navigation UI mockups\n",
             "Three genuinely distinct design directions per demo-nav page type.\n",
             "## Preview\n",
             "- Index: [`/apt/mockups`](/apt/mockups)\n",
             "- Individual: `/apt/mockups/{page}-{variant}` (e.g. `/apt/mockups/sitemap-a`)\n",
             "\n## Variant families\n",
             "| Family | Thesis | Aesthetic |\n",
             "|--------|--------|----------|\n"]
    for var, vname in _VARIANTS:
        lines.append(f"| **{var.upper()}** — {vname} | {THEMES[var]['thesis']} | "
                     f"{'Dark ops' if var=='a' else 'Light editorial' if var=='b' else 'Bold pitch'} |\n")
    lines.append("\n## Files\n\n| Page | A | B | C |\n|------|---|---|---|\n")
    for page, plabel in _PAGES:
        lines.append(f"| {plabel} | `{page}-a.html` | `{page}-b.html` | `{page}-c.html` |\n")
    lines.append("\n## Production templates (unchanged)\n\n")
    lines.append("| Mockup | Current template |\n|--------|------------------|\n")
    lines.append("| sitemap | `apt_demo_sitemap.html` |\n")
    lines.append("| hub | `apt_dev_hub.html` |\n")
    lines.append("| direct | `demo_channel_gallery.html` |\n")
    lines.append("| email | `demo_email_card.html` + gallery |\n")
    lines.append("| ads | `gauntlet_ad_lp.html` |\n")
    return "".join(lines)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    builders = {"sitemap": sitemap, "hub": hub, "direct": direct, "email": email, "ads": ads}
    for page in PAGES:
        for var in ("a", "b", "c"):
            path = OUT / f"{page}-{var}.html"
            path.write_text(builders[page](var))
            print("wrote", path.name)
    (OUT / "index.html").write_text(index_html())
    (OUT / "README.md").write_text(readme())
    print("done — 15 mockups + index + README")


if __name__ == "__main__":
    main()
