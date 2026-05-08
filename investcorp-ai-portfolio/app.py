import streamlit as st
from config import INVESTCORP_PRIMARY, INVESTCORP_GOLD, SECTORS, EV_MIN_USD, EV_MAX_USD

st.set_page_config(
    page_title="Investcorp AI Portfolio",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    f"""
    <style>
        .hero-banner {{
            background: linear-gradient(135deg, {INVESTCORP_PRIMARY} 0%, #005599 100%);
            padding: 3rem 2.5rem;
            border-radius: 12px;
            color: white;
            margin-bottom: 2rem;
        }}
        .hero-banner h1 {{
            font-size: 2.6rem;
            font-weight: 700;
            margin: 0 0 0.4rem 0;
            color: white;
        }}
        .hero-banner p {{
            font-size: 1.1rem;
            opacity: 0.88;
            margin: 0;
        }}
        .gold-line {{
            height: 4px;
            background: {INVESTCORP_GOLD};
            border-radius: 2px;
            margin: 0.5rem 0 1.5rem 0;
            width: 80px;
        }}
        .card {{
            background: white;
            border-radius: 10px;
            padding: 1.5rem;
            border: 1px solid #E8ECF0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            height: 100%;
        }}
        .card h3 {{
            color: {INVESTCORP_PRIMARY};
            margin: 0.3rem 0 0.6rem 0;
        }}
        .card p {{
            color: #555;
            font-size: 0.92rem;
            margin: 0;
        }}
        .badge {{
            display: inline-block;
            background: {INVESTCORP_GOLD};
            color: white;
            border-radius: 20px;
            padding: 0.15rem 0.7rem;
            font-size: 0.78rem;
            font-weight: 600;
            margin-bottom: 0.6rem;
        }}
        section[data-testid="stSidebar"] {{
            background-color: {INVESTCORP_PRIMARY};
        }}
        section[data-testid="stSidebar"] * {{
            color: white !important;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero-banner">
        <h1>📈 Investcorp AI Portfolio</h1>
        <div class="gold-line"></div>
        <p>
            Identifying high-growth AI companies and real estate assets with enterprise values
            between <strong>$50M – $500M</strong> for strategic acquisition by Investcorp.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(
        f"""
        <div class="card">
            <div class="badge">EV Range</div>
            <h3>$50M – $500M</h3>
            <p>Target enterprise value window for actionable acquisitions</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        f"""
        <div class="card">
            <div class="badge">Sectors</div>
            <h3>{len(SECTORS)} Focus Areas</h3>
            <p>Tech / Software · Data Centers · Real Estate · Healthcare AI</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    total_tickers = sum(len(s["tickers"]) for s in SECTORS.values())
    st.markdown(
        f"""
        <div class="card">
            <div class="badge">Universe</div>
            <h3>{total_tickers}+ Companies</h3>
            <p>Screened live from public markets using AI growth metrics</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col4:
    st.markdown(
        f"""
        <div class="card">
            <div class="badge">Scoring</div>
            <h3>AI Growth Score</h3>
            <p>Composite: revenue growth, margins, R&D intensity, EV efficiency</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("---")

st.subheader("How to use this dashboard")

nav_col1, nav_col2 = st.columns(2)

with nav_col1:
    for label, icon, desc in [
        ("Overview", "📊", "Sector breakdown, EV distribution, and key market metrics at a glance."),
        ("AI Companies", "💻", "Live screener for AI software, SaaS, and infrastructure companies within the target EV range."),
    ]:
        st.markdown(
            f"""
            <div class="card" style="margin-bottom:1rem;">
                <div class="badge">{icon} {label}</div>
                <p>{desc}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

with nav_col2:
    for label, icon, desc in [
        ("Real Estate", "🏢", "AI-adjacent REITs and industrial properties benefiting from the AI buildout."),
        ("Acquisition Targets", "🎯", "Ranked acquisition shortlist with Investcorp Fit Score and exportable CSV report."),
    ]:
        st.markdown(
            f"""
            <div class="card" style="margin-bottom:1rem;">
                <div class="badge">{icon} {label}</div>
                <p>{desc}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("---")
st.caption(
    "Data sourced via Yahoo Finance (yfinance). Refreshed every hour. "
    "For investment research purposes only — not financial advice."
)
