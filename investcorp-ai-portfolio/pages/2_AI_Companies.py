import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.express as px
import pandas as pd

from config import SECTORS, EV_MIN_USD, EV_MAX_USD, INVESTCORP_PRIMARY, INVESTCORP_GOLD
from data.fetcher import fetch_sector_data, fetch_price_history, fmt_currency, fmt_pct
from data.screener import compute_ai_score

st.set_page_config(page_title="AI Companies · Investcorp AI Portfolio", page_icon="💻", layout="wide")

st.markdown(
    f"<h2 style='color:{INVESTCORP_PRIMARY};'>💻 AI Growth Companies Screener</h2>",
    unsafe_allow_html=True,
)

# Exclude Real Estate sector — handled on its own page
COMPANY_SECTORS = {k: v for k, v in SECTORS.items() if k != "Real Estate (AI-Adjacent)"}


@st.cache_data(ttl=3600, show_spinner=False)
def load_data():
    placeholder = st.empty()

    def on_progress(i, total, ticker):
        if total > 0:
            placeholder.progress(i / total, text=f"Fetching {ticker}…" if ticker else "Done")

    df = fetch_sector_data(COMPANY_SECTORS, EV_MIN_USD, EV_MAX_USD, progress_callback=on_progress)
    placeholder.empty()
    if not df.empty:
        df = compute_ai_score(df)
    return df


with st.spinner("Fetching live data…"):
    df = load_data()

if df.empty:
    st.warning("No data available. Check your network connection and try again.")
    st.stop()

# ── Sidebar filters ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"### 🔍 Filters")

    selected_sectors = st.multiselect(
        "Sectors",
        options=list(COMPANY_SECTORS.keys()),
        default=list(COMPANY_SECTORS.keys()),
    )

    ev_range = st.slider(
        "Enterprise Value ($M)",
        min_value=50,
        max_value=500,
        value=(50, 500),
        step=10,
    )

    min_growth = st.slider(
        "Min Revenue Growth (%)",
        min_value=-50,
        max_value=200,
        value=-50,
        step=5,
    )

    min_score = st.slider(
        "Min AI Score",
        min_value=0,
        max_value=100,
        value=0,
        step=5,
    )

    st.markdown("---")
    st.caption(f"Universe: {len(df)} companies found in EV range")

# ── Apply filters ─────────────────────────────────────────────────────────────
filtered = df[
    df["sector"].isin(selected_sectors)
    & (df["enterprise_value"] >= ev_range[0] * 1e6)
    & (df["enterprise_value"] <= ev_range[1] * 1e6)
    & (df["revenue_growth"] * 100 >= min_growth)
    & (df["ai_score"] >= min_score)
].copy()

st.markdown(f"**{len(filtered)}** companies match your filters")

# ── Results table ─────────────────────────────────────────────────────────────
if filtered.empty:
    st.info("No companies match the current filters. Try relaxing the criteria.")
else:
    display_cols = [
        "ticker", "name", "sector", "enterprise_value", "market_cap",
        "revenue_growth", "gross_margin", "rd_intensity", "ai_score", "score_icon",
    ]
    disp = filtered[display_cols].copy()
    disp["enterprise_value"] = disp["enterprise_value"].apply(fmt_currency)
    disp["market_cap"] = disp["market_cap"].apply(fmt_currency)
    disp["revenue_growth"] = disp["revenue_growth"].apply(fmt_pct)
    disp["gross_margin"] = disp["gross_margin"].apply(fmt_pct)
    disp["rd_intensity"] = disp["rd_intensity"].apply(fmt_pct)
    disp["ai_score"] = disp["score_icon"] + " " + disp["ai_score"].astype(str)
    disp = disp.drop(columns=["score_icon"])
    disp.columns = [
        "Ticker", "Company", "Sector", "Enterprise Value", "Market Cap",
        "Rev Growth", "Gross Margin", "R&D Intensity", "AI Score",
    ]
    st.dataframe(disp, use_container_width=True, hide_index=True)

    # CSV download
    csv = filtered.to_csv(index=False).encode()
    st.download_button(
        "⬇️ Export to CSV",
        data=csv,
        file_name="investcorp_ai_companies.csv",
        mime="text/csv",
    )

st.markdown("---")

# ── Metric charts ──────────────────────────────────────────────────────────────
if not filtered.empty:
    c1, c2 = st.columns(2)

    sector_colors = {s: info["color"] for s, info in SECTORS.items()}

    with c1:
        st.subheader("AI Score by Sector")
        fig = px.box(
            filtered,
            x="sector",
            y="ai_score",
            color="sector",
            color_discrete_map=sector_colors,
            labels={"ai_score": "AI Score", "sector": ""},
            points="all",
        )
        fig.update_layout(showlegend=False, height=320, margin=dict(t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader("Gross Margin vs R&D Intensity")
        df_p = filtered.copy()
        df_p["gross_pct"] = df_p["gross_margin"] * 100
        df_p["rd_pct"] = df_p["rd_intensity"] * 100
        df_p["ev_m"] = df_p["enterprise_value"] / 1e6
        fig2 = px.scatter(
            df_p,
            x="rd_pct",
            y="gross_pct",
            color="sector",
            size="ev_m",
            hover_name="name",
            hover_data={"ticker": True, "ev_m": ":.0f"},
            color_discrete_map=sector_colors,
            labels={"rd_pct": "R&D Intensity (%)", "gross_pct": "Gross Margin (%)", "ev_m": "EV ($M)"},
            size_max=35,
        )
        fig2.update_layout(height=320, margin=dict(t=10, b=10))
        st.plotly_chart(fig2, use_container_width=True)

# ── Company detail expander ────────────────────────────────────────────────────
st.markdown("---")
st.subheader("Company Deep-Dive")

if not filtered.empty:
    ticker_options = filtered["ticker"].tolist()
    selected = st.selectbox("Select a company", options=ticker_options, format_func=lambda t: f"{t} — {filtered.loc[filtered['ticker']==t, 'name'].values[0]}")

    row = filtered[filtered["ticker"] == selected].iloc[0]

    dc1, dc2, dc3, dc4 = st.columns(4)
    dc1.metric("Enterprise Value", fmt_currency(row["enterprise_value"]))
    dc2.metric("Revenue Growth", fmt_pct(row["revenue_growth"]))
    dc3.metric("Gross Margin", fmt_pct(row["gross_margin"]))
    dc4.metric("AI Score", f"{row['score_icon']} {row['ai_score']:.1f}")

    if row.get("description"):
        st.caption(row["description"])

    hist = fetch_price_history(selected, period="1y")
    if not hist.empty:
        fig_hist = px.area(
            hist,
            x=hist.index,
            y="Close",
            title=f"{selected} — 1-Year Price History",
            labels={"Close": "Price ($)", "index": "Date"},
            color_discrete_sequence=[INVESTCORP_GOLD],
        )
        fig_hist.update_layout(height=280, margin=dict(t=30, b=10))
        st.plotly_chart(fig_hist, use_container_width=True)
