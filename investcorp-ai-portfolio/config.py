EV_MIN_USD = 50_000_000
EV_MAX_USD = 500_000_000

# Reference stocks that define each theme (large-caps used as thematic anchors only)
REFERENCE_STOCKS = {
    "AI Semiconductor Ecosystem": ["NVDA", "AMD", "ARM", "TSM", "ASML", "MU", "SNDK", "KLAC", "AVGO"],
    "Data Center & Networking": ["ANET", "CSCO", "CLS", "GLW", "VRT"],
    "Cloud & AI Applications": ["AMZN", "MSFT", "GOOG", "META", "ORCL", "CRWV"],
    "AI Power & Energy": ["ETN", "GEV", "PWR", "BE", "OKLO"],
}

# Small-cap screening universe — same industries as reference stocks, EV $50M–$500M
SECTORS = {
    "AI Semiconductor Ecosystem": {
        "color": "#7B2FBE",
        "icon": "💾",
        "description": (
            "Chip IP licensing, semiconductor fab equipment, memory, "
            "advanced packaging, and process-control — the supply chain "
            "behind NVDA, AMD, TSM, ASML, MU, and KLAC."
        ),
        "tickers": [
            "CEVA",   # chip IP licensing (like ARM, but smaller)
            "ACLS",   # ion implant equipment (KLAC ecosystem)
            "COHU",   # semiconductor test handlers
            "AEHR",   # wafer-level burn-in testing
            "FORM",   # probe cards for wafer testing
            "ICHR",   # gas/chemical delivery for fabs
            "UCTT",   # ultra-clean components for fabs
            "ONTO",   # optical process-control inspection
            "NVTS",   # GaN power ICs (next-gen power semis)
            "SITM",   # MEMS timing ICs for data centers
            "ALGM",   # magnetic sensors & power ICs for AI servers
            "AOSL",   # power management discrete semis
            "DIOD",   # discrete & analog semiconductors
            "MRAM",   # embedded MRAM (persistent memory)
            "SMTC",   # IoT & data-center analog chips
            "PRSO",   # mmWave chips for high-speed connectivity
        ],
    },
    "Data Center & Networking": {
        "color": "#1A6FBF",
        "icon": "🌐",
        "description": (
            "Ethernet switches, optical fiber, EMS/ODM manufacturing, "
            "cooling, and network test equipment — the physical layer "
            "behind ANET, CSCO, CLS, GLW, and VRT."
        ),
        "tickers": [
            "CLFD",   # fiber connectivity (GLW ecosystem, smaller)
            "ADTN",   # broadband networking equipment
            "CALX",   # cloud-based broadband networking
            "AVNW",   # microwave/IP backhaul networking
            "RBBN",   # edge cloud & enterprise networking
            "VIAV",   # network test & measurement
            "NTCT",   # network management & security analytics
            "DGII",   # IoT/edge connectivity hardware
            "CRNT",   # microwave backhaul (emerging-market data centers)
            "CASA",   # cable/broadband access equipment
            "SIFY",   # data center & cloud services (India)
            "GILT",   # satellite networking equipment
        ],
    },
    "Cloud & AI Applications": {
        "color": "#0F9D58",
        "icon": "☁️",
        "description": (
            "AI cloud platforms, GPU-as-a-service, enterprise AI software, "
            "and AI-native SaaS — the application layer built on "
            "AMZN, MSFT, GOOG, ORCL, and CRWV."
        ),
        "tickers": [
            "AI",     # C3.ai — enterprise AI applications
            "BBAI",   # BigBear.ai — AI analytics & decision intelligence
            "SOUN",   # SoundHound AI — voice & audio AI
            "MGNI",   # Magnite — programmatic advertising AI
            "PERI",   # Perion Network — AI-driven digital advertising
            "MITK",   # Mitek Systems — AI identity verification
            "DTST",   # Data Storage Corp — cloud & colocation
            "INPX",   # Inpixon — enterprise AI & indoor intelligence
            "RCAT",   # Red Cat Holdings — AI drone platforms
            "ARQQ",   # Arqit Quantum — quantum-safe encryption SaaS
            "QBTS",   # D-Wave Quantum — quantum cloud computing
            "PCYG",   # Park City Group — supply-chain AI SaaS
        ],
    },
    "AI Power & Energy": {
        "color": "#E8A020",
        "icon": "⚡",
        "description": (
            "Power management, electrical infrastructure, clean energy, "
            "and next-gen nuclear for AI data centers — the energy layer "
            "behind ETN, GEV, PWR, BE, and OKLO."
        ),
        "tickers": [
            "STEM",   # Stem Inc — AI-optimized battery energy storage
            "AMRC",   # Ameresco — clean energy project development
            "SHLS",   # Shoals Technologies — solar electrical BOS
            "FTCI",   # FTC Solar — utility-scale solar trackers
            "ARRY",   # Array Technologies — solar tracking systems
            "FLUX",   # Flux Power — lithium battery packs for industrial
            "MVST",   # Microvast — fast-charge batteries for heavy industry
            "BEEM",   # Beam Global — off-grid EV & power infrastructure
            "SPWR",   # SunPower — residential & commercial solar
            "NOVA",   # Sunnova Energy — solar-as-a-service
            "AMPS",   # Altus Power — distributed solar & storage
            "MNTK",   # Montauk Renewables — renewable natural gas
        ],
    },
}

ALL_TICKERS = list({t for s in SECTORS.values() for t in s["tickers"]})

INVESTCORP_PRIMARY = "#003366"
INVESTCORP_GOLD = "#C5A028"
INVESTCORP_LIGHT = "#F5F7FA"

AI_SCORE_WEIGHTS = {
    "revenue_growth": 0.35,
    "gross_margin": 0.25,
    "rd_intensity": 0.20,
    "ev_efficiency": 0.20,
}

SCORE_LABELS = {
    (75, 100): ("Very High", "🟢"),
    (55, 75):  ("High",      "🟡"),
    (30, 55):  ("Medium",    "🟠"),
    (0,  30):  ("Low",       "🔴"),
}


def score_label(score: float) -> tuple[str, str]:
    for (lo, hi), (label, icon) in SCORE_LABELS.items():
        if lo <= score <= hi:
            return label, icon
    return "Low", "🔴"
