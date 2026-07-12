# Planet (planet.com) — Market Segments & Location-Personalization Research

> Deep web research run 2026-07-09 for the Planet personalized-marketing demo (`/planetapt`, `/ads`,
> `/ads-lp` equivalents). Companion to `copy-personalization-research.md` (copy playbook) and
> `docs/04-workflow/ACTION-IMAGE-PERSONALIZATION.md` (image intent framework).
> All company facts verified against planet.com, SEC filings, and press coverage as of July 2026;
> URLs cited inline. The summary table in §5 is the build-ready artifact.

---

## 1. The company — verified facts

**Planet Labs PBC** (NYSE: **PL**), San Francisco. Public benefit corporation. Founded **2010 by
three NASA scientists** (Will Marshall, Robbie Schingler, Chris Boshuizen). Mission language used
verbatim in every press release: *"driven by a mission to image the world every day, and make
change visible, accessible and actionable."*
([FY26 Q4 press release](https://www.sec.gov/Archives/edgar/data/1836833/000119312526115951/pl-ex99_1.htm))

**Scale (FY2026, ended Jan 31 2026):**
- Record revenue **$307.7M, +26% YoY**; Q4 revenue **+41% YoY**; **$900M backlog, +79% YoY**;
  first full fiscal year of non-GAAP profitability (adj. EBITDA $15.5M, FCF $53M).
  ([Nasdaq press release](https://www.nasdaq.com/press-release/planet-reports-financial-results-fourth-quarter-and-full-fiscal-year-2026-2026-03-19),
  [Q4 FY26 earnings call](https://www.stockinsights.ai/us/PL/earnings-transcript/fy26-q4-5f2a))
- **897 direct customers** at FY26 end (metric de-emphasized as long tail moves to self-serve);
  marketing materials say "over 1,000 customers" including platform users.
- Launched **40 satellites in FY26**, including 4 high-resolution Pelicans; R&D partnership with
  **Google** on data centers in space.
- Largest commercial EO fleet by count: **~200 SuperDoves + ~21 SkySats + Pelicans**, third-largest
  satellite operator after SpaceX and OneWeb.
  ([Orbital Radar fleet page](https://orbitalradar.com/satellites/operator/planet-labs))

**Product lineup** ([planet.com/products](https://www.planet.com/products/),
[constellations](https://www.planet.com/constellations/)):

| Product | What it is | Key spec |
|---|---|---|
| **PlanetScope** (SuperDove fleet) | Daily monitoring of Earth's entire landmass | 3 m, 8 spectral bands, daily revisit |
| **SkySat** | High-res tasking | 50 cm, sub-daily revisit, ~21 sats |
| **Pelican** | Next-gen high-res tasking, on-orbit edge compute | 30–50 cm; Gen-1 commercial ops 2025, Gen-2 from 2026 ([docs](https://docs.planet.com/data/imagery/pelican/)) |
| **Owl** | Forthcoming next-gen monitoring constellation | near-daily **1 m-class** imagery |
| **Tanager** | Hyperspectral | **400+ spectral bands**; methane/CO2 detection, vegetation species, water quality |
| **Planet SuperRes** | Proprietary generative-AI enhancement | 3 m PlanetScope → sharp 2 m visual |
| **Planet Mosaics** | Formerly "Basemaps" — cloud-free composites | visual + analytic time series |
| **Planetary Variables** | Analysis-ready measurement feeds | Soil Water Content (100 m/1 km, 20+ yr archive, cloud-proof — [docs](https://docs.planet.com/data/planetary-variables/soil-water-content/techspec/)); Land Surface Temperature (100 m/1 km, 24 h latency); Crop Biomass (3 m/10 m); Forest Carbon Diligence (30 m, global, 2013–present); Forest Carbon Monitoring (**3 m, tree-scale**); Field Boundaries ([index](https://docs.planet.com/data/planetary-variables/)) |
| **Planet Insights Platform** | Cloud platform (Sentinel Hub tech) for querying/visualizing/streaming Planet + public data | APIs, ArcGIS/QGIS integrations |

**Pricing motion** ([planet.com/pricing](https://www.planet.com/pricing/),
[self-serve announcement](https://www.planet.com/pulse/planet-enables-self-service-purchasing-for-small-customers-on-planet-insights-platform/)):
- **Two-track GTM**: direct enterprise sales for large accounts (incl. nine-figure "satellite
  services" deals) + **self-serve** for the long tail.
- Self-serve today: **Area Under Management (AUM)** subscriptions for PlanetScope over fixed AOIs
  (public tiers listed from ~$2,700 to ~$9,650+/yr by area), **Single Order Tasking** for SkySat,
  and platform processing units. AUM is explicitly *"not permitted for defense and intelligence
  use cases."*
- **30-day free trial** of Planet Insights Platform, no credit card, sandbox data + public imagery
  (Sentinel, Landsat), 30,000 processing units
  ([trial page](https://www.planet.com/sign-up/agriculture/)).
- **Satellite services / dedicated capacity** model: customers get dedicated Pelican capacity +
  direct downlink without building their own constellation (Germany/Ukraine, Sweden, Japan).

**Brand voice** (from planet.com and releases): plain, mission-forward, change-oriented. Recurring
phrases: *"image the world every day"* · *"make change visible, accessible and actionable"* ·
*"the daily pace of change"* · *"broad area management"* · *"look broader… closer… deeper"* ·
*"AI-Powered Earth Intelligence"* · *"use space to help life on Earth"* (founding intent, quoted
in the [Crisis Response terms](https://planet.widen.net/s/w7qb85sdnn/crisis-response-program_tos_2023.1)).
Segment page taglines are imperative-verb triplets: *"Understand events, anticipate impacts,
respond immediately"* (D&I); *"Survey waters, detect vessels, track activity"* (maritime);
*"Oversee assets, monitor competition, mitigate disaster"* (energy).

**The core marketing asset for this demo:** Planet is the only commercial operator that images
**every place on Earth's landmass every day**. Any visitor's geography — their county, their
coastline, their forest, their port — is already in the archive, going back years. That makes
**location the message-match signal**: the ad/page can truthfully say "we already image *your*
ground daily," and the hero image can *show* it. (Guardrail from the image pipeline still applies:
allude at region/landscape scale, never the visitor's street or house — daily-planet-scale
confidence, not surveillance.)

---

## 2. Segments

Nine segments, matching planet.com's own industry nav
([planet.com/industries](https://www.planet.com/industries/)) plus two adjacent programs
(disaster response, education & research) that planet.com markets separately.

### 2.1 Agriculture

- **Buyer/persona:** VP/Director of Agronomy or Digital Agriculture at input majors and co-ops;
  Head of Data Science / product lead at agtech platforms; supply-chain and seed-production leads.
  Org types: seed & crop-protection majors, digital-ag platforms, co-ops, precision-ag SaaS.
- **Jobs-to-be-done / pains:** in-season crop-health visibility across millions of dispersed acres;
  yield forecasting; irrigation and variable-rate decisions; seed-production supply-chain
  reliability; cloud cover killing revisit from other sources; scaling agronomists' attention.
- **Planet positioning:** *"Maximize Yield, Minimize Risk with Earth Intelligence"* — daily 3 m
  imagery "even in regions with frequent cloud cover," field-level detail preseason to harvest,
  simple cloud APIs ([industry page](https://www.planet.com/industries/agriculture/)).
- **Named customers:** **Bayer Crop Science** (multi-year enterprise license expansion 2025;
  monitors seed-production fields across four continents, powers Climate FieldView —
  [BusinessWire](https://www.businesswire.com/news/home/20250225042074/en/Planet-and-Bayer-Accelerate-Digital-Innovation-in-Agriculture-with-Major-Enterprise-License-Expansion),
  [Planet Pulse](https://www.planet.com/pulse/planet-bayer-partnership/)); **Corteva** (customer
  since 2017, powers Granular/LandVisor); **Syngenta** (Cropwise: 40,000+ users, 230M+ acres);
  **BASF Digital Farming**, **Organic Valley** (1,600 member farms), **AMAGGI**, **Disagro**,
  **Taranis**, **Abelio**
  ([customer roundup](https://www.unconventionalvalue.com/p/how-people-use-planets-data-agriculture)).
- **KPIs that resonate:** revisit rate (daily vs 5-day Sentinel), % of season with usable imagery,
  yield-forecast accuracy, acres monitored per agronomist, days-to-detection of crop stress.
- **Location angle (strong):** agriculture IS geography. The visitor's region maps to a crop
  system — Iowa → corn/soy; Central Valley → almonds/irrigation; Kansas → winter wheat;
  Mato Grosso → soy frontier. Copy can name the crop belt and season stage ("mid-season in the
  corn belt"); the claim "we imaged every field in {region} today" is literally true.
- **Hero-image concept:** satellite-view quilt of center-pivot circles and field polygons in the
  visitor's regional palette (Midwest greens vs Central Valley ochre), with an NDVI-style
  false-color gradient sweeping across fields — healthy emerald to stressed amber — implying
  daily change detection. No text, no farms identifiable at building scale.
- **Ad copy angles (X/Twitter):**
  - *"Every field in {region}, imaged today."* / "Daily 3 m imagery catches crop stress while you can still act on it."
  - *"Your agronomists can't drive 2 million acres. Satellites already did."* / "Field-level insight from preseason to harvest, delivered by API."
  - *"Cloud cover broke your revisit. Daily imaging fixes it."* / "200+ satellites mean today's miss is tomorrow's capture."

### 2.2 Defense & Intelligence

- **Buyer/persona:** national space/defense procurement (MoDs, NRO/NGA-equivalents), intelligence
  agency GEOINT leads, defense primes and analytics integrators, allied-government mission owners.
- **Jobs-to-be-done / pains:** strategic indications & warnings over denied areas; maritime domain
  awareness; monitoring military installations and critical infrastructure at scale; sovereign
  access to space capability without building a constellation; analyst overload → need AI triage.
- **Planet positioning:** *"Understand events, anticipate impacts, respond immediately"* — "move
  from data to decision faster, with insight delivered at planetary scale… we pull back the
  curtain and shed light on what's happening around the world"
  ([D&I page](https://www.planet.com/industries/defense-and-intelligence/)).
- **Named customers/contracts:** **NATO** (intelligence deal, 2025); **Germany-funded €240M
  ($283M) multi-year agreement** — dedicated Pelican capacity + direct downlink, later confirmed
  signed by **Ukraine** with Germany as financier
  ([BusinessWire](https://www.businesswire.com/news/home/20250701149801/en/Planet-Awarded-%E2%82%AC240-Million-Satellite-Services-Deal),
  [Via Satellite](https://www.satellitetoday.com/government-military/2025/07/01/planet-highlights-defense-momentum-with-280m-german-government-deal/),
  [GAU](https://deaidua.org/news/2026/06/09/germany-funds-240-million-satellite-deal-ukraine/));
  **Swedish Armed Forces** (multi-year, low nine-figure satellite services deal, FY26 Q4);
  **US NRO** (EOCL program, alongside Maxar/BlackSky); **DIU** Hybrid Space Architecture;
  **US Navy** (seven-figure MDA expansion).
- **KPIs that resonate:** revisit rate over AOI, tip-to-cue latency, direct-downlink latency,
  % of theater under daily coverage, dark-target detection rate.
- **Location angle (strong but must be handled carefully):** the theater of interest, not the
  visitor's location per se. For a visitor from an allied capital, reference their *regional
  security context* (Baltic, Black Sea, Indo-Pacific) — "daily coverage over the regions your
  mission watches." Never imply we're watching the visitor.
- **Hero-image concept:** dusk-lit satellite view of a strategic littoral/border region with
  abstract vessel wakes and port geometry, subtle grid/telemetry overlay suggesting automated
  detection — cinematic, not surveillance-creepy (pipeline guardrail: no surveillance aesthetics —
  keep it map-room, not spy-cam).
- **Ad copy angles:**
  - *"The theater doesn't pause. Neither does the constellation."* / "Daily global coverage plus 30 cm tasking, downlinked direct to your ground segment."
  - *"Sweden signed. NATO signed. The map is being watched — by whom?"* / "Sovereign access to dedicated satellite capacity, without building satellites."
  - *"Indications and warnings, at the daily pace of change."* / "AI-triaged monitoring of installations and coastlines at planetary scale."

### 2.3 Civil Government

- **Buyer/persona:** state/provincial forestry and natural-resources divisions, emergency-management
  agencies, environmental regulators, county planning/permitting offices, national mapping agencies.
- **Jobs-to-be-done / pains:** wildfire risk assessment and active-incident response; permit
  compliance and code enforcement over jurisdictions too big to drive; disaster damage assessment;
  regulatory reporting (transparency/traceability mandates); shrinking field-staff budgets.
- **Planet positioning:** *"AI-Powered Change Detection for Government"*; "broad area management —
  monitoring, measuring, and reporting on changes to natural and human-made assets over vast areas"
  ([gov risk post](https://www.planet.com/pulse/how-governments-use-near-daily-earth-data-to-reduce-risk-in-key-policy-areas/)).
- **Named examples:** a **US State Division of Forestry** replaced helicopter recon — digitizes
  wildfire perimeters "in minutes," cut investigation time/cost by **$160,000** (same post);
  **California Forest Observatory** (tree-scale fuel mapping; 10x spatial detail with Planet
  Mosaics — [wildfire post](https://www.planet.com/pulse/how-governments-can-reduce-wildfire-risk-before-ignition/));
  permit-compliance enforcement for mining/construction/cannabis
  ([e-book](https://learn.planet.com/planet-for-permit-compliance-and-enforcement-ebook.html)).
  Planet.com has a dedicated "US State and Local" nav item.
- **KPIs that resonate:** time to digitize a fire perimeter, $ saved vs aerial survey, violations
  detected per analyst, % of jurisdiction monitored monthly, disaster damage-assessment turnaround.
- **Location angle (very strong):** the visitor's *jurisdiction* is the product surface. A
  California visitor → wildfire fuel and defensible space; Gulf Coast → hurricane damage
  assessment; Mountain West → drought and water compliance; a county official anywhere → "your
  whole county, every day."
- **Hero-image concept:** oblique satellite view of the visitor's regional landscape type (chaparral
  foothills / river floodplain / pine forest) with a translucent change-detection wipe: one half
  "before," one half "after" with burn scar or floodwater extent rendered in analytic color — the
  authority of evidence, not disaster porn.
- **Ad copy angles:**
  - *"Your whole {state/county}, imaged daily."* / "Fire perimeters in minutes, not helicopter hours."
  - *"One agency cut wildfire investigation costs $160K."* / "Near-daily imagery replaced aerial recon. Yours can too."
  - *"You can't field-inspect every parcel. You can watch all of them."* / "AI change detection flags unpermitted activity across the jurisdiction."

### 2.4 Forestry, Land Use & Carbon

- **Buyer/persona:** carbon project developers and registries, forest-carbon MRV leads, NGO forest
  monitors, ministries of environment/climate, sustainable-timber and commodity supply-chain
  compliance teams (EUDR), Indigenous-rights organizations.
- **Jobs-to-be-done / pains:** credible MRV for carbon credits (buyers distrust self-reported
  baselines); detecting deforestation/degradation early enough to intervene; **EUDR** due
  diligence (deforestation-free proof after the 2020-12-31 cutoff, geolocation per plot;
  enforcement Dec 2026 / Jun 2027 — [npj Climate Action](https://www.nature.com/articles/s44168-025-00276-9));
  REDD+ reporting; monitoring vast remote areas with no roads.
- **Planet positioning:** *"Monitor forests, detect land use changes, improve REDD+ MRV"*
  (industry nav); Forest Carbon products: Diligence at 30 m (global, 2013–present) and Monitoring
  at **3 m tree scale** — "the world's first tree-scale global forest monitoring system" (product
  lead David Marvin, ex-Salo Sciences, acquired 2023 —
  [GovExec event bio](https://events.govexec.com/planet-labs-using-earth-observation-data-to-monitor-wildfire-risk/),
  [Forest Carbon Diligence techspec](https://docs.planet.com/data/planetary-variables/forest-carbon-diligence/techspec/)).
- **Named examples:** **NICFI Satellite Data Program** (Norway's International Climate & Forests
  Initiative — free high-res tropical monitoring with KSAT/Airbus; used by Global Forest Watch,
  MapBiomas, IPAM, Forests of the World —
  [Pulse](https://www.planet.com/pulse/planets-high-resolution-satellite-monitoring-helps-nicfi-general-partners-reduce-and-reverse-tropical-forest-loss/));
  **Permian Global / Katingan Mentaya Project** (157,000 ha Indonesian peatland carbon project
  monitored with PlanetScope —
  [Pulse](https://www.planet.com/pulse/planetscope-and-planet-basemaps-utilized-for-carbon-credits-monitoring-in-indonesian-tropical-forest/)).
- **KPIs that resonate:** deforestation-alert latency, hectares under verified monitoring, carbon
  baseline accuracy (canopy height/cover/AGC density), EUDR plots cleared per week, credit-buyer
  diligence pass rate.
- **Location angle (strong):** the visitor's forest biome or supply-shed — Pacific Northwest
  timber, Amazon/Cerrado frontier, Southeast Asian peatland, European managed forest. For EUDR
  buyers: "the supply sheds you source from" (cocoa/West Africa, coffee/Brazil–Vietnam).
- **Hero-image concept:** top-down 3 m-style canopy texture in deep greens with a time-slider
  motif: a thin seam where the same forest is shown one year apart, a small clearing appearing —
  change made visible at tree scale. Regional biome palette (peat swamp vs boreal vs temperate).
- **Ad copy angles:**
  - *"Every tree, every year. Baselines buyers believe."* / "Tree-scale canopy height, cover, and carbon — global, 2013 to now."
  - *"EUDR enforcement lands December 2026. Is your supply shed clean?"* / "Plot-level deforestation checks against daily imagery, audit-ready."
  - *"Deforestation alerts are only useful before the clearing finishes."* / "Daily revisit catches degradation while it's still small."

### 2.5 Insurance & Financial Services

- **Buyer/persona:** heads of underwriting/claims innovation at P&C and agro insurers and
  reinsurers; cat-modeling and exposure-management leads; parametric-product designers; also
  hedge-fund/commodity analysts (financial services adjacency named in Planet's boilerplate).
- **Jobs-to-be-done / pains:** loss adjustment at scale after weather events (adjuster shortage);
  fraud detection; underwriting accuracy for wildfire/flood exposure; parametric triggers needing
  trusted, continuous, sensor-free data; "prevented planting" claim verification.
- **Planet positioning:** *"Global data, continuous insight"*; *"Minimize Risk With Broad Area
  Management — improve underwriting and streamline loss adjustment… monitor, measure, and report
  on assets across space and time"* ([insurance page](https://www.planet.com/industries/insurance/)).
- **Named examples:** **AXA Climate** — parametric drought insurance built on Planet **Soil Water
  Content** (payouts auto-trigger days after a risk period; launched southern/central Brazil —
  [Pulse](https://www.planet.com/pulse/axa-climate-leverages-planetary-variables-for-drought-insurance-through-extended-strategic-partnership/));
  **Swiss Re**, **NCIS**, **AIAG**, **GreenTriangle**, **Suyana**, **PlanetWatchers** (agro-insurance
  webinar circuit — [Pulse](https://www.planet.com/pulse/satellite-data-and-ai-the-shift-to-data-driven-agriculture-insurance/));
  PlanetWatchers/ProAg cut wind-damage field-validation time an estimated **40%**
  ([case study](https://live-planet-watchers.pantheonsite.io/proag-case-study/)).
- **KPIs that resonate:** claim-triage time, adjuster field-days saved, loss-ratio improvement,
  parametric payout latency (days not months), fraud catch rate, % of book with pre-event imagery.
- **Location angle (very strong):** the visitor's *book of business* is geographic — Gulf/Atlantic
  coast hurricane exposure, California WUI wildfire, Midwest hail/wind, Plains drought. Copy can
  name the peril that dominates their region; the archive claim is powerful: "we have a
  before-picture of every insured property in {region}."
- **Hero-image concept:** split-frame satellite view of a regional coastline or plains township:
  left, intact; right, post-event with analytic damage-grading tint (total/moderate/low bins as
  color fields, echoing Planet's own claims workflow). Peril matches region (storm surge on
  coasts, hail swath in plains).
- **Ad copy angles:**
  - *"The 'before' picture of every property in {region} already exists."* / "Daily archive imagery turns claims triage from weeks into days."
  - *"Your adjusters see one field a time. Satellites graded 90,000 acres."* / "AI damage bins from 50 cm tasking, hours after the event."
  - *"Parametric triggers need data nobody can argue with."* / "20 years of satellite soil-moisture, no ground sensors to maintain."

### 2.6 Energy & Infrastructure

- **Buyer/persona:** pipeline-integrity and ROW managers, utility vegetation-management leads,
  mining HSE/geotech and water-resource engineers, renewables developers, ESG/methane-compliance
  officers.
- **Jobs-to-be-done / pains:** encroachment detection on thousands of linear miles; tailings-dam
  and water monitoring; construction progress across dispersed sites; methane LDAR obligations;
  reducing dangerous, costly aerial/manual inspection.
- **Planet positioning:** *"Oversee assets, monitor competition, mitigate disaster"* — "reduce the
  need for human inspections… monitor encroachment, predict market fluctuations"
  ([industry page](https://www.planet.com/industries/energy-and-infrastructure/),
  [pipeline datasheet](https://learn.planet.com/rs/997-CHH-265/images/Pipeline%20Use%20Cases%20Datasheet_A4_Screen.pdf)).
  Tanager hyperspectral adds direct **methane plume detection**.
- **Named examples:** **Freeport-McMoRan** — daily PlanetScope monitoring of tailings storage
  facilities; engineers derive pond outlines via ML instead of walking miles-long dam crests;
  also dust-control prioritization ([Pulse](https://www.planet.com/pulse/planets-data-supports-safe-and-sustainable-mining-management/)).
  Planet's own site shows competitive mine-activity monitoring (Coyote Creek vs Beulah dragline
  activity).
- **KPIs that resonate:** encroachments detected per survey, inspection cost per mile vs aerial,
  incident-response time, methane events detected/quantified, % of assets with weekly imagery.
- **Location angle (strong):** the visitor's asset geography — Permian Basin operators, Gulf
  refining corridor, Appalachian pipelines, Western utility fire zones, Atacama/Nevada mines.
  Regional terrain instantly signals "we know your operating environment."
- **Hero-image concept:** high-oblique satellite view of a pipeline/transmission corridor cutting
  through the visitor's regional terrain (desert basin, forested ridge), with faint analytic
  highlights on ROW buffer zones and one flagged change — order and control, machine-precise.
- **Ad copy angles:**
  - *"Every mile of right-of-way, checked from orbit."* / "Daily imagery flags encroachment before the dig crew shows up."
  - *"Freeport monitors tailings dams without walking the crest."* / "Daily satellite monitoring keeps engineers safe and models calibrated."
  - *"Your methane obligations just became visible from space."* / "400-band hyperspectral detects and quantifies plumes at the source."

### 2.7 Maritime

- **Buyer/persona:** navies/coast guards and fisheries-enforcement agencies, port authorities,
  marine insurers (fraud), commodity-flow analysts, ocean-conservation NGOs.
- **Jobs-to-be-done / pains:** dark vessels (AIS off) invisible to conventional tracking; IUU
  fishing enforcement over EEZs of millions of sq km; sanctions evasion via ship-to-ship
  transfers; port congestion and activity intelligence.
- **Planet positioning:** *"Survey waters, detect vessels, track activity"* — "near-daily 3.7 m
  imagery over **20 million sq km of open water**, covering strategic regions like the South China
  Sea, the Persian Gulf"; **Automated Vessel Detection** deep-learning feeds classify vessels
  (cargo, tanker, military) and detect ship-to-ship transfers; integrates with AIS and partner
  platform Theia (SynMax) for dark-vessel analytics
  ([maritime page](https://www.planet.com/industries/maritime/)).
- **Named examples:** **Global Fishing Watch / "Illuminating dark fishing fleets in North Korea"**
  (Science Advances) — CNN on PlanetScope + tasked SkySat verified **~800 pair trawlers** fishing
  illegally in North Korean waters; the dark fleet caught an estimated **$700M of squid**
  ([paper](https://www.science.org/doi/10.1126/sciadv.abb1197),
  [GFW analysis](https://globalfishingwatch.org/article/2020-analysis-dark-fleets/)). US Navy MDA
  expansion (see §2.2).
- **KPIs that resonate:** dark-vessel detection rate, sq km of water surveyed daily, detection-to-
  interdiction latency, AIS-gap correlation rate, insured-voyage verification rate.
- **Location angle (strong for coastal/port visitors):** the visitor's nearest strategic waterway —
  Gulf Coast ports, Singapore Strait, North Sea wind corridors, Mediterranean routes. "The waters
  off {region}, surveyed daily."
- **Hero-image concept:** top-down deep-blue satellite seascape of a recognizable regional
  coastline/port geometry, scattered vessel wakes as white commas, two or three highlighted with
  clean analytic reticles — one isolated wake with no marker implying a dark vessel.
- **Ad copy angles:**
  - *"AIS off doesn't mean invisible."* / "Deep-learning vessel detection across 20 million sq km of ocean, near-daily."
  - *"~800 dark trawlers, found from orbit."* / "The methodology behind the North Korea dark-fleet exposé is a product."
  - *"Every port call in {region}, on the record."* / "Daily imaging plus AIS fusion turns anecdotes into evidence."

### 2.8 Disaster Response & Humanitarian

- **Buyer/persona:** emergency-management agencies, humanitarian NGOs (UN agencies, Red Cross
  network), international response coordinators, GIS leads at relief organizations. (Often a
  brand/PR-halo segment more than a revenue segment — Planet gives this data away.)
- **Jobs-to-be-done / pains:** situational awareness in the first 24–72 hours; damage assessment
  when roads/comms are down; prioritizing scarce relief resources; documenting impacts for funding
  appeals.
- **Planet positioning:** **Crisis Response Program / Disaster Data** — "Accelerate humanitarian
  response with Planet imagery"; select imagery at no cost to qualified responders for major
  earthquakes, floods, storms, wildfires, human-made disasters; grounded in Planet's founding
  intent "to use space to help life on Earth"
  ([disaster data page](https://www.planet.com/disasterdata/)).
- **Named examples:** **Los Angeles County wildfires** (Jan 2025) and **Brazil/Bolivia floods**
  (Rio Acre, 12,000+ displaced) crisis-data releases
  ([LA post](https://community.planet.com/community-blasts-88/planet-crisis-response-los-angeles-county-wildfires-6088),
  [Brazil post](https://community.planet.com/community-blasts-88/planet-crisis-response-brazil-and-bolivia-flooding-713)).
- **KPIs that resonate:** hours from event to first usable image, area assessed per day, % of
  affected settlements with before/after pairs, responder time saved vs ground survey.
- **Location angle (strong, empathetic register):** the visitor's regional hazard — hurricanes on
  the Gulf, floods on major river basins, quakes on the Ring of Fire. Tone must be readiness and
  service, never fear-mongering their home.
- **Hero-image concept:** dawn-lit satellite view of a river valley or coastal town region with
  flood extent rendered as a calm, analytic blue overlay and clear high-ground routes visible —
  legible, humane, "the map responders needed by sunrise."
- **Ad copy angles:**
  - *"When {region} floods, the first map matters most."* / "Before/after imagery of any place on Earth, within hours."
  - *"Roads close. Comms drop. Orbits don't."* / "Daily global imaging gives responders the picture on day one."
  - *"We imaged it yesterday, too."* / "The before-picture that makes damage assessment instant."

### 2.9 Education & Research

- **Buyer/persona:** university faculty/PIs in remote sensing, ecology, hydrology, economics;
  grad students; campus GIS librarians and research-computing offices (Campus License buyers).
- **Jobs-to-be-done / pains:** commercial-grade data on academic budgets; temporal density for
  time-series science; teaching datasets; publication-grade licensing.
- **Planet positioning:** **Education & Research Program** — free/low-cost non-commercial access
  (Basic: up to **3,000 sq km/month**); **10,000+ users, 1,000+ universities, 100+ countries**
  (MIT, Rutgers, Utrecht, Toronto, Yamaguchi); SkySat added — "a first for a university program";
  Campus Licenses for whole institutions; Planet data has contributed to **thousands of academic
  publications (~2 papers/day)** ([program page](https://www.planet.com/industries/education-and-research/),
  [science page](https://www.planet.com/science/),
  [program update](https://www.planet.com/pulse/education-and-research-program-enhances-global-accessibility-and-user-capabilities/)).
- **KPIs that resonate:** publications enabled, temporal resolution vs Landsat/Sentinel, sq km
  quota, time-to-approval (≤3 weeks), citation impact.
- **Location angle (moderate):** the visitor's study region or campus region — "daily imagery of
  your field sites"; researchers think in AOIs, so "your study area, every day since 2016" lands.
- **Hero-image concept:** aesthetic time-lapse strip of one natural feature near the visitor's
  region (a meandering river, a retreating glacier, an urban edge) as four/five sequential
  satellite tiles showing change — science-poster beauty, the archive as instrument.
- **Ad copy angles:**
  - *"Your study area, imaged daily since 2016."* / "Free academic access to the world's densest EO time series."
  - *"Two papers a day are published on this data."* / "Join 10,000+ researchers at 1,000+ universities."
  - *"Landsat gives you 16 days. We give you 1."* / "Daily 3 m imagery for time-series science, free for university research."

---

## 3. Competitive landscape (for differentiation claims)

| Competitor | Their strength | Planet's counter |
|---|---|---|
| **Maxar Intelligence** (private, Advent) | Best-in-class native 30 cm optical; deep NGA/NRO relationships (EnhancedView) | Small fleet, tasked — can't see everywhere every day. Planet: daily full-landmass coverage + its own 30–50 cm Pelican tasking. ([SpaceNexus comparison](https://spacenexus.us/compare/planet-labs-vs-maxar)) |
| **Airbus** (Pléiades Neo) | 30 cm optical + SAR portfolio, mature OneAtlas catalog, European incumbency | Same tasked-archive model; no daily global monitoring layer. |
| **BlackSky** | High revisit over chosen AOIs (up to ~7/day), <90 min tip-to-alert latency | Revisit only where tasked; ~83 cm class. Planet monitors *everywhere* daily so nothing needs pre-tasking to be in the archive. ([New Space Economy 2026](https://newspaceeconomy.ca/2026/04/05/earth-observation-satellites-in-2026-free-data-commercial-operators-and-the-race-to-differentiate/)) |
| **ICEYE** (SAR, 60+ sats) | All-weather/night radar; strong defense momentum (Ukraine via Rheinmetall) | Complementary, not substitutable: SAR lacks optical interpretability, spectral bands, hyperspectral gas detection. |
| **Sentinel-2 / Landsat (free)** | Free, scientific-grade, drives the analytics ecosystem | 10 m / 5-day (S2) vs 3 m / daily; Planet Insights Platform *hosts* the free data, upselling density. The trial itself leads with Sentinel/Landsat sandbox. |

**Differentiation spine for all ad copy:** (1) only daily coverage of the entire landmass —
"your geography is already in the archive"; (2) largest EO fleet, vertically integrated, fast
iteration ("agile aerospace"); (3) one platform from daily 3 m to 30 cm tasking to hyperspectral
to measurement feeds — "broader, closer, deeper"; (4) a time machine: years of daily history of
any AOI, which no tasked competitor can backfill.

---

## 4. Location personalization — cross-segment mechanics for the demo

- **The truthful superpower claim:** "Planet imaged {visitor's region} today — and every day for
  the last decade." True for any land location on Earth. This is *message-match* (the demo's
  strongest intent) keyed on geography instead of ad keyword.
- **Tier gating (per the image pipeline):** region at coarse granularity (state/metro/biome) is a
  tier-1 signal; industry+region compound (e.g., "Gulf Coast insurer") is tier-2 delta. Never
  street/property scale — the pipeline's anti-surveillance guardrail maps exactly to Planet's
  brand risk here.
- **Geography → segment inference:** region alone suggests segment priors (Des Moines → ag;
  DC/Arlington → defense; Houston → energy; Hartford/Zurich → insurance; college towns →
  research), usable as a fallback route when no industry signal exists.
- **Hero-image grammar (shared across segments):** true-color or analytic-false-color *satellite
  aesthetic*, regional landform recognizable at landscape scale, one "change made visible" motif
  (before/after seam, alert highlight, time-lapse strip), brand-clean (no text, no logos — matches
  existing guardrails).

---

## 5. Summary table — segment → persona → pain → location angle → image concept → ad hook

Copy-ready for `/ads`, `/ads-lp`, `/planetapt` builds. `{region}` = coarse visitor geography.

| Segment | Persona | Core pain | Location angle | Hero-image concept | Ad hook (headline / subhead) |
|---|---|---|---|---|---|
| **Agriculture** | VP Digital Ag / agronomy lead at input major, co-op, agtech | Can't see crop stress across millions of acres in time to act; clouds break revisit | Visitor's crop belt + season stage ("mid-season in the corn belt") | Satellite quilt of the region's field patterns with NDVI-style health gradient sweeping across | "Every field in {region}, imaged today." / "Daily 3 m imagery catches crop stress while you can still act on it." |
| **Defense & Intel** | MoD/agency GEOINT procurement, defense integrator | Denied-area I&W; analyst overload; sovereign capability gap | Their *regional security theater* (Baltic, Indo-Pacific), never the visitor | Dusk littoral/border region, vessel wakes + subtle telemetry grid; map-room not spy-cam | "The theater doesn't pause. Neither does the constellation." / "Daily coverage plus 30 cm tasking, downlinked direct." |
| **Civil Government** | State forestry / emergency mgmt / permitting director | Jurisdiction too big for field staff; fire and disaster response speed | "Your whole {state/county}, every day" — regional hazard (fire/flood/drought) | Regional landscape with before/after change-detection wipe (burn scar or flood extent in analytic color) | "Fire perimeters in minutes, not helicopter hours." / "One state agency cut investigation costs $160K with daily imagery." |
| **Forestry & Carbon** | Carbon project developer, MRV lead, EUDR compliance officer | Distrusted baselines; late deforestation alerts; EUDR proof burden | Visitor's forest biome or sourcing supply shed (cocoa/coffee/soy origin regions) | Tree-scale canopy texture with one-year time seam revealing a small new clearing | "EUDR enforcement lands December 2026. Is your supply shed clean?" / "Plot-level checks against daily imagery, audit-ready." |
| **Insurance & FinServ** | Head of claims/underwriting innovation, cat modeler, parametric designer | Adjuster shortage post-event; fraud; payout latency | Their regional book's peril: coast → hurricane, plains → hail, West → wildfire | Split-frame regional coastline/township, pre/post event with damage-grade color bins | "The 'before' picture of every property in {region} already exists." / "Daily archive turns claims triage from weeks into days." |
| **Energy & Infra** | Pipeline ROW/integrity manager, mining HSE, utility veg-mgmt lead | Encroachment across thousands of miles; dangerous manual inspection; methane compliance | Their operating basin/corridor (Permian, Gulf corridor, Western fire zones) | Pipeline/transmission corridor through regional terrain, ROW buffer highlighted, one flagged change | "Every mile of right-of-way, checked from orbit." / "Daily imagery flags encroachment before the dig crew shows up." |
| **Maritime** | Coast guard / fisheries enforcement, port authority, marine insurer | Dark vessels; IUU fishing; sanctions evasion at EEZ scale | Nearest strategic waterway: "the waters off {region}, surveyed daily" | Deep-blue regional coastline, vessel wakes as white commas, one unmarked wake = dark vessel | "AIS off doesn't mean invisible." / "Deep-learning vessel detection across 20 million sq km of ocean, near-daily." |
| **Disaster Response** | Emergency mgmt agency, humanitarian NGO GIS lead | First-72-hours situational awareness with roads/comms down | Regional hazard, readiness register ("when {region} floods…") — never fear-monger | Dawn river-valley/coastal region, calm analytic flood overlay, visible high-ground routes | "Roads close. Comms drop. Orbits don't." / "Before/after imagery of any place on Earth, within hours." |
| **Education & Research** | University PI, grad researcher, campus GIS librarian | Commercial-grade temporal density on academic budget | "Your study area, every day since 2016" — field-site region | Time-lapse strip of a regional natural feature (river meander, urban edge) across 4–5 tiles | "Landsat gives you 16 days. We give you 1." / "Daily 3 m imagery for time-series science, free for university research." |

---

## 6. Source index

Company/products: [planet.com](https://www.planet.com/) · [products](https://www.planet.com/products/) · [constellations](https://www.planet.com/constellations/) · [Pelican docs](https://docs.planet.com/data/imagery/pelican/) · [Planetary Variables docs](https://docs.planet.com/data/planetary-variables/) · [pricing](https://www.planet.com/pricing/) · [FY26 Q4 8-K ex-99.1](https://www.sec.gov/Archives/edgar/data/1836833/000119312526115951/pl-ex99_1.htm) · [FY26 Q4 earnings transcript](https://www.stockinsights.ai/us/PL/earnings-transcript/fy26-q4-5f2a).
Segments: industry pages under [planet.com/industries](https://www.planet.com/industries/) (agriculture, defense-and-intelligence, civil-government, forestry, insurance, energy-and-infrastructure, maritime, education-and-research) · Planet Pulse posts and case studies linked inline per segment.
Competitors: [SpaceNexus Planet-vs-Maxar](https://spacenexus.us/compare/planet-labs-vs-maxar) · [New Space Economy EO 2026](https://newspaceeconomy.ca/2026/04/05/earth-observation-satellites-in-2026-free-data-commercial-operators-and-the-race-to-differentiate/) · [EO operator directory](https://newspaceeconomy.ca/2026/04/16/global-directory-of-earth-observation-satellite-operators-and-their-products-and-services/).
