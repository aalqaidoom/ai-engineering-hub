import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from config import SECTORS, EV_MIN_USD, EV_MAX_USD, INVESTCORP_PRIMARY, INVESTCORP_GOLD
from data.fetcher import fetch_sector_data, fetch_price_history, fmt_currency, fmt_pct
from data.screener import compute_ai_score

st.set_page_config(page_title="Real Estate · Investcorp AI Portfolio", page_icon="🏢", layout="wide")

st.markdown(
    f"<h2 style='color:{INVESTCORP_PRIMARY};'>🏢 AI-Adjacent Real Estate</h2>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='color:#555;'>REITs and industrial real estate properties benefiting from AI infrastructure buildout — "
    "data centers, industrial logistics, and technology campuses.</p>",
    unsafe_allow_html=True,
)

RE_SECTORS = {"Real Estate (AI-Adjacent)": SECTORS["Real Estate (AI-Adjacent)"]}


@st.cache_data(ttl=3600, show_spinner=False)
def load_re_data():
    placeholder = st.empty()

    def on_progress(i, total, ticker):
        if total > 0:
            placeholder.progress(i / total, text=f"Fetching {ticker}…" if ticker else "Done")

    df = fetch_sector_data(RE_SECTORS, EV_MIN_USD, EV_MAX_USD, progress_callback=on_progress)
    placeholder.empty()
    if not df.empty:
        df = compute_ai_score(df)
    return df


with st.spinner("Loading real estate data…"):
    df = load_re_data()

if df.empty:
    st.warning(
        "No real estate companies matched the $50M–$500M EV filter right now. "
        "Market data may be delayed. Try again shortly."
    )
    st.stop()

# ── Sidebar filters ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔍 RE Filters")

    ev_range = st.slider(
        "Enterprise Value ($M)",
        min_value=50,
        max_value=500,
        value=(50, 500),
        step=10,
    )

    min_yield = st.slider(
        "Min Dividend Yield (%)",
        min_value=0,
        max_value=15,
        value=0,
        step=1,
    )

    st.markdown("---")
    st.caption(f"Universe: {len(df)} REITs/properties found")

# ── Filter ────────────────────────────────────────────────────────────────────
filtered = df[
    (df["enterprise_value"] >= ev_range[0] * 1e6)
    & (df["enterprise_value"] <= ev_range[1] * 1e6)
    & (df["dividend_yield"] * 100 >= min_yield)
].copy()

st.markdown(f"**{len(filtered)}** properties match your filters")

# ── KPI strip ─────────────────────────────────────────────────────────────────
if not filtered.empty:
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Properties", len(filtered))
    k2.metric("Avg Enterprise Value", fmt_currency(filtered["enterprise_value"].mean()))
    k3.metric("Avg Dividend Yield", fmt_pct(filtered["dividend_yield"].mean()))
    k4.metric("Avg AI Score", f"{filtered['ai_score'].mean():.1f} / 100")

    st.markdown("---")

    # ── EV vs Dividend Yield chart ─────────────────────────────────────────────
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("EV vs Dividend Yield")
        df_p = filtered.copy()
        df_p["ev_m"] = df_p["enterprise_value"] / 1e6
        df_p["dy_pct"] = df_p["dividend_yield"] * 100
        fig = px.scatter(
            df_p,
            x="ev_m",
            y="dy_pct",
            size="ai_score",
            hover_name="name",
            hover_data={"ticker": True, "ev_m": ":.0f", "dy_pct": ":.2f"},
            color="ai_score",
            color_continuous_scale=[[0, "#E8ECF0"], [1, INVESTCORP_GOLD]],
            labels={"ev_m": "Enterprise Value ($M)", "dy_pct": "Dividend Yield (%)", "ai_score": "AI Score"},
            size_max=30,
        )
        fig.update_layout(height=340, margin=dict(t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader("AI Score Distribution")
        fig2 = px.histogram(
            filtered,
            x="ai_score",
            nbins=12,
            color_discrete_sequence=[INVESTCORP_PRIMARY],
            labels={"ai_score": "AI Score", "count": "# Properties"},
        )
        fig2.update_layout(height=340, margin=dict(t=10, b=10), bargap=0.1)
        st.plotly_chart(fig2, use_container_width=True)

    # ── Properties table ───────────────────────────────────────────────────────
    st.subheader("Property Screener")

    disp_cols = [
        "ticker", "name", "enterprise_value", "market_cap",
        "dividend_yield", "revenue_growth", "gross_margin", "ai_score", "score_icon",
    ]
    disp = filtered[disp_cols].copy()
    disp["enterprise_value"] = disp["enterprise_value"].apply(fmt_currency)
    disp["market_cap"] = disp["market_cap"].apply(fmt_currency)
    disp["dividend_yield"] = disp["dividend_yield"].apply(fmt_pct)
    disp["revenue_growth"] = disp["revenue_growth"].apply(fmt_pct)
    disp["gross_margin"] = disp["gross_margin"].apply(fmt_pct)
    disp["ai_score"] = disp["score_icon"] + " " + disp["ai_score"].astype(str)
    disp = disp.drop(columns=["score_icon"])
    disp.columns = [
        "Ticker", "Property / REIT", "Enterprise Value", "Market Cap",
        "Dividend Yield", "Rev Growth", "Gross Margin", "AI Score",
    ]
    st.dataframe(disp, use_container_width=True, hide_index=True)

    csv = filtered.to_csv(index=False).encode()
    st.download_button(
        "⬇️ Export to CSV",
        data=csv,
        file_name="investcorp_real_estate.csv",
        mime="text/csv",
    )

    # ── Why AI-Adjacent? context box ───────────────────────────────────────────
    st.markdown("---")
    st.subheader("Why AI-Adjacent Real Estate?")

    ia1, ia2, ia3 = st.columns(3)
    with ia1:
        st.info(
            "**Data Center Demand**\n\n"
            "Hyperscalers and AI firms are signing long-term leases for data center space, "
            "driving occupancy and rental growth for specialist REITs."
        )
    with ia2:
        st.info(
            "**Industrial / Logistics**\n\n"
            "AI supply-chain optimization and last-mile delivery require dense warehouse networks, "
            "supporting industrial REIT valuations."
        )
    with ia3:
        st.info(
            "**Power Infrastructure**\n\n"
            "AI compute is power-hungry. Properties near renewable energy sources or "
            "with superior power capacity command premium valuations."
        )

    # ── Property deep-dive ─────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("Property Deep-Dive")

    ticker_options = filtered["ticker"].tolist()
    if ticker_options:
        selected = st.selectbox(
            "Select a property",
            options=ticker_options,
            format_func=lambda t: f"{t} — {filtered.loc[filtered['ticker']==t, 'name'].values[0]}",
        )
        row = filtered[filtered["ticker"] == selected].iloc[0]

        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Enterprise Value", fmt_currency(row["enterprise_value"]))
        d2.metric("Dividend Yield", fmt_pct(row["dividend_yield"]))
        d3.metric("Revenue Growth", fmt_pct(row["revenue_growth"]))
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
