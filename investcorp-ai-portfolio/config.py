EV_MIN_USD = 50_000_000
EV_MAX_USD = 500_000_000

SECTORS = {
    "Tech / Software": {
        "color": "#4A90E2",
        "icon": "💻",
        "description": "AI software, SaaS, and cloud infrastructure companies",
        "tickers": [
            "BBAI", "SOUN", "AEYE", "GFAI", "QBTS", "ARQQ", "DTST",
            "VERB", "MITK", "INPX", "RCAT", "PRSO", "CEVA", "PCYG",
            "MIND", "PERI", "OTIC", "AIXI", "FWRG", "AEAC",
        ],
    },
    "Data Centers / Infrastructure": {
        "color": "#27AE60",
        "icon": "🏗️",
        "description": "Hardware, networking, and power infrastructure enabling AI",
        "tickers": [
            "CLFD", "PCTI", "DGII", "AVNW", "INFN", "CASA",
            "VIAV", "NTCT", "SPOK", "LIQT", "BAND", "CRNT",
            "WAVD", "SIFY", "UTSI", "GILT", "CODA",
        ],
    },
    "Real Estate (AI-Adjacent)": {
        "color": "#F39C12",
        "icon": "🏢",
        "description": "Data center REITs and industrial real estate benefiting from AI buildout",
        "tickers": [
            "GIPR", "ILPT", "NLOP", "PLYM", "GOOD", "NXRT",
            "BRSP", "FBRT", "NREF", "ALEX", "CLDT",
            "STHO", "GMRE", "MDRR", "NREF",
        ],
    },
    "Healthcare AI": {
        "color": "#E74C3C",
        "icon": "🏥",
        "description": "AI-driven diagnostics, biotech, and medical technology",
        "tickers": [
            "MDAI", "SANG", "ACCD", "TALK", "OTRK", "MTLS",
            "MDRX", "RXRX", "ABSI", "SDGR", "EXAI",
            "NARI", "HIMS", "HROW", "AORT", "LFMD",
        ],
    },
}

ALL_TICKERS = list({t for s in SECTORS.values() for t in s["tickers"]})

AI_SCORE_WEIGHTS = {
    "revenue_growth": 0.35,
    "gross_margin": 0.25,
    "rd_intensity": 0.20,
    "ev_efficiency": 0.20,
}

INVESTCORP_PRIMARY = "#003366"
INVESTCORP_GOLD = "#C5A028"
INVESTCORP_LIGHT = "#F5F7FA"

SCORE_LABELS = {
    (75, 100): ("Very High", "🟢"),
    (55, 75): ("High", "🟡"),
    (30, 55): ("Medium", "🟠"),
    (0, 30): ("Low", "🔴"),
}


def score_label(score: float) -> tuple[str, str]:
    for (lo, hi), (label, icon) in SCORE_LABELS.items():
        if lo <= score <= hi:
            return label, icon
    return "Low", "🔴"
