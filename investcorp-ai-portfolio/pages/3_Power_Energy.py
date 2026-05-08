import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.express as px
import pandas as pd

from config import SECTORS, EV_MIN_USD, EV_MAX_USD, INVESTCORP_PRIMARY, INVESTCORP_GOLD, REFERENCE_STOCKS
from data.fetcher import fetch_sector_data, fetch_price_history, fmt_currency, fmt_pct
from data.screener import compute_ai_score

st.set_page_config(page_title="Power & Energy · Investcorp AI Portfolio", page_icon="⚡", layout="wide")

st.markdown(
    f"<h2 style='color:{INVESTCORP_PRIMARY};'>⚡ AI Power & Energy Infrastructure</h2>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='color:#555;'>Small-cap companies in the same power and energy infrastructure "
    "space as <strong>ETN · GEV · PWR · BE · OKLO</strong> — enabling AI data center "
    "power at scale through grid modernization, clean energy, and energy storage.</p>",
    unsafe_allow_html=True,
)

POWER_SECTORS = {"AI Power & Energy": SECTORS["AI Power & Energy"]}


@st.cache_data(ttl=3600, show_spinner=False)
def load_power_data():
    placeholder = st.empty()

    def on_progress(i, total, ticker):
        if total > 0:
            placeholder.progress(i / total, text=f"Fetching {ticker}…" if ticker else "Done")

    df = fetch_sector_data(POWER_SECTORS, EV_MIN_USD, EV_MAX_USD, progress_callback=on_progress)
    placeholder.empty()
    if not df.empty:
        df = compute_ai_score(df)
    return df


with st.spinner("Loading power & energy data…"):
    df = load_power_data()

# ── Reference anchors ─────────────────────────────────────────────────────────
with st.expander("📌 Reference anchors for this theme", expanded=False):
    ref_cols = st.columns(5)
    anchors = [
        ("ETN", "Eaton", "Power management, UPS, electrical components for data centers"),
        ("GEV", "GE Vernova", "Power generation turbines & grid equipment"),
        ("PWR", "Quanta Services", "Electrical infrastructure construction & grid modernization"),
        ("BE",  "Bloom Energy",   "Fuel cell systems powering data centers with clean energy"),
        ("OKLO","Oklo",           "Small modular nuclear reactors for always-on clean power"),
    ]
    for col, (ticker, name, desc) in zip(ref_cols, anchors):
        col.markdown(
            f"**{ticker}**\n\n_{name}_\n\n<span style='font-size:0.82rem;color:#666'>{desc}</span>",
            unsafe_allow_html=True,
        )

if df.empty:
    st.warning(
        "No power & energy companies matched the $50M–$500M EV filter right now. "
        "Market data may be delayed — try again shortly."
    )
    st.stop()

# ── Sidebar filters ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔍 Power & Energy Filters")

    ev_range = st.slider("Enterprise Value ($M)", 50, 500, (50, 500), step=10)
    min_growth = st.slider("Min Revenue Growth (%)", -50, 200, -50, step=5)
    min_score = st.slider("Min AI Score", 0, 100, 0, step=5)

    st.markdown("---")
    st.caption(f"Universe: {len(df)} companies found in EV range")

# ── Apply filters ─────────────────────────────────────────────────────────────
filtered = df[
    (df["enterprise_value"] >= ev_range[0] * 1e6)
    & (df["enterprise_value"] <= ev_range[1] * 1e6)
    & (df["revenue_growth"] * 100 >= min_growth)
    & (df["ai_score"] >= min_score)
].copy()

st.markdown(f"**{len(filtered)}** companies match your filters")

# ── KPI strip ─────────────────────────────────────────────────────────────────
if not filtered.empty:
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Companies", len(filtered))
    k2.metric("Avg Enterprise Value", fmt_currency(filtered["enterprise_value"].mean()))
    k3.metric("Avg Revenue Growth", fmt_pct(filtered["revenue_growth"].mean()))
    k4.metric("Avg AI Score", f"{filtered['ai_score'].mean():.1f} / 100")

    st.markdown("---")

    # ── Charts ────────────────────────────────────────────────────────────────
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("EV vs Revenue Growth")
        df_p = filtered.copy()
        df_p["ev_m"] = df_p["enterprise_value"] / 1e6
        df_p["rev_pct"] = df_p["revenue_growth"] * 100
        fig = px.scatter(
            df_p,
            x="rev_pct",
            y="ev_m",
            size="ai_score",
            hover_name="name",
            hover_data={"ticker": True, "ev_m": ":.0f", "rev_pct": ":.1f", "ai_score": ":.1f"},
            color="ai_score",
            color_continuous_scale=[[0, "#E8ECF0"], [0.5, INVESTCORP_GOLD], [1, "#003366"]],
            labels={"rev_pct": "Revenue Growth (%)", "ev_m": "Enterprise Value ($M)", "ai_score": "AI Score"},
            size_max=35,
        )
        fig.update_layout(height=340, margin=dict(t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader("AI Score Ranking")
        df_bar = filtered.sort_values("ai_score", ascending=True).copy()
        fig2 = px.bar(
            df_bar,
            x="ai_score",
            y="ticker",
            orientation="h",
            color="ai_score",
            color_continuous_scale=[[0, "#E8ECF0"], [0.5, INVESTCORP_GOLD], [1, "#003366"]],
            labels={"ai_score": "AI Score", "ticker": ""},
            text_auto=".1f",
        )
        fig2.update_layout(height=340, margin=dict(t=10, b=10), showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig2, use_container_width=True)

    # ── Screener table ────────────────────────────────────────────────────────
    st.subheader("Power & Energy Screener")
    disp = filtered[[
        "ticker", "name", "enterprise_value", "market_cap",
        "revenue_growth", "gross_margin", "rd_intensity",
        "total_cash", "total_debt", "ai_score", "score_icon",
    ]].copy()
    disp["enterprise_value"] = disp["enterprise_value"].apply(fmt_currency)
    disp["market_cap"] = disp["market_cap"].apply(fmt_currency)
    disp["revenue_growth"] = disp["revenue_growth"].apply(fmt_pct)
    disp["gross_margin"] = disp["gross_margin"].apply(fmt_pct)
    disp["rd_intensity"] = disp["rd_intensity"].apply(fmt_pct)
    disp["total_cash"] = disp["total_cash"].apply(fmt_currency)
    disp["total_debt"] = disp["total_debt"].apply(fmt_currency)
    disp["ai_score"] = disp["score_icon"] + " " + disp["ai_score"].astype(str)
    disp = disp.drop(columns=["score_icon"])
    disp.columns = [
        "Ticker", "Company", "Enterprise Value", "Market Cap",
        "Rev Growth", "Gross Margin", "R&D Intensity",
        "Cash", "Debt", "AI Score",
    ]
    st.dataframe(disp, use_container_width=True, hide_index=True)

    csv = filtered.to_csv(index=False).encode()
    st.download_button("⬇️ Export to CSV", data=csv, file_name="investcorp_power_energy.csv", mime="text/csv")

    # ── Why AI needs power ─────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("The AI Power Thesis")

    t1, t2, t3 = st.columns(3)
    with t1:
        st.info(
            "**Explosive Power Demand**\n\n"
            "A single AI training run can consume as much electricity as hundreds of homes use annually. "
            "Hyperscalers are signing 20-year power purchase agreements to secure capacity."
        )
    with t2:
        st.info(
            "**Grid Modernization**\n\n"
            "Aging grid infrastructure must be upgraded to deliver the gigawatts demanded by "
            "new data center campuses — creating multi-decade opportunity for electrical contractors "
            "and equipment makers."
        )
    with t3:
        st.info(
            "**Clean Power Premium**\n\n"
            "Hyperscalers have net-zero commitments. Data centers powered by renewables, "
            "fuel cells, or nuclear SMRs command premium contracts and avoid carbon pricing risk."
        )

    # ── Company deep-dive ──────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("Company Deep-Dive")
    ticker_options = filtered["ticker"].tolist()
    if ticker_options:
        selected = st.selectbox(
            "Select a company",
            options=ticker_options,
            format_func=lambda t: f"{t} — {filtered.loc[filtered['ticker']==t, 'name'].values[0]}",
        )
        row = filtered[filtered["ticker"] == selected].iloc[0]

        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Enterprise Value", fmt_currency(row["enterprise_value"]))
        d2.metric("Revenue Growth", fmt_pct(row["revenue_growth"]))
        d3.metric("Gross Margin", fmt_pct(row["gross_margin"]))
        d4.metric("AI Score", f"{row['score_icon']} {row['ai_score']:.1f}")

        if row.get("description"):
            st.caption(row["description"])

        hist = fetch_price_history(selected, period="1y")
        if not hist.empty:
            fig_price = px.area(
                hist,
                x=hist.index,
                y="Close",
                title=f"{selected} — 1-Year Price History",
                labels={"Close": "Price ($)", "index": "Date"},
                color_discrete_sequence=[INVESTCORP_GOLD],
            )
            fig_price.update_layout(height=280, margin=dict(t=30, b=10))
            st.plotly_chart(fig_price, use_container_width=True)
