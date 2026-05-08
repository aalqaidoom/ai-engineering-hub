import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from config import SECTORS, EV_MIN_USD, EV_MAX_USD, INVESTCORP_PRIMARY, INVESTCORP_GOLD
from data.fetcher import fetch_sector_data, fetch_price_history, fmt_currency, fmt_pct
from data.screener import compute_ai_score, rank_acquisition_targets

st.set_page_config(page_title="Acquisition Targets · Investcorp AI Portfolio", page_icon="🎯", layout="wide")

st.markdown(
    f"<h2 style='color:{INVESTCORP_PRIMARY};'>🎯 Acquisition Targets</h2>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='color:#555;'>Ranked shortlist of acquisition candidates scored on AI growth potential, "
    "valuation attractiveness, revenue quality, and balance-sheet health.</p>",
    unsafe_allow_html=True,
)


@st.cache_data(ttl=3600, show_spinner=False)
def load_all_data():
    placeholder = st.empty()

    def on_progress(i, total, ticker):
        if total > 0:
            placeholder.progress(i / total, text=f"Fetching {ticker}…" if ticker else "Done")

    df = fetch_sector_data(SECTORS, EV_MIN_USD, EV_MAX_USD, progress_callback=on_progress)
    placeholder.empty()
    if not df.empty:
        df = compute_ai_score(df)
        df = rank_acquisition_targets(df)
    return df


with st.spinner("Scoring acquisition targets…"):
    df = load_all_data()

if df.empty:
    st.warning("No targets available. Market data may be temporarily unavailable.")
    st.stop()

# ── Sidebar filters ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔍 Target Filters")

    selected_sectors = st.multiselect(
        "Sectors",
        options=list(SECTORS.keys()),
        default=list(SECTORS.keys()),
    )

    ev_range = st.slider("Enterprise Value ($M)", 50, 500, (50, 500), step=10)

    min_fit = st.slider("Min Investcorp Fit Score", 0, 100, 0, step=5)

    top_n = st.selectbox("Show top N targets", [10, 20, 30, 50], index=0)

    st.markdown("---")
    st.markdown(
        """
        **Fit Score components**
        - 40% AI Growth Score
        - 25% EV attractiveness
        - 20% Revenue growth
        - 10% Gross margin
        - 5%  Net cash position
        """
    )

# ── Apply filters ─────────────────────────────────────────────────────────────
filtered = df[
    df["sector"].isin(selected_sectors)
    & (df["enterprise_value"] >= ev_range[0] * 1e6)
    & (df["enterprise_value"] <= ev_range[1] * 1e6)
    & (df["fit_score"] >= min_fit)
].head(top_n).copy()

# ── KPI strip ─────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
k1.metric("Targets Shown", len(filtered))
k2.metric("Avg Fit Score", f"{filtered['fit_score'].mean():.1f}" if not filtered.empty else "—")
k3.metric("Avg AI Score", f"{filtered['ai_score'].mean():.1f}" if not filtered.empty else "—")
k4.metric("Total EV (combined)", fmt_currency(filtered["enterprise_value"].sum()) if not filtered.empty else "—")

st.markdown("---")

if filtered.empty:
    st.info("No targets match the current filters.")
    st.stop()

# ── Ranked target cards ───────────────────────────────────────────────────────
st.subheader(f"Top {len(filtered)} Acquisition Targets")

sector_colors = {s: info["color"] for s, info in SECTORS.items()}

for rank, (_, row) in enumerate(filtered.iterrows(), start=1):
    with st.expander(
        f"#{rank}  {row['score_icon']}  **{row['ticker']}** — {row['name']}  |  "
        f"Fit: **{row['fit_score']:.0f}**  |  AI: **{row['ai_score']:.0f}**  |  "
        f"EV: **{fmt_currency(row['enterprise_value'])}**",
        expanded=(rank <= 3),
    ):
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Fit Score", f"{row['fit_score']:.1f}")
        c2.metric("AI Score", f"{row['ai_score']:.1f}")
        c3.metric("Enterprise Value", fmt_currency(row["enterprise_value"]))
        c4.metric("Revenue Growth", fmt_pct(row["revenue_growth"]))
        c5.metric("Gross Margin", fmt_pct(row["gross_margin"]))

        r1, r2 = st.columns(2)
        with r1:
            st.markdown(f"**Sector:** {row['sector_icon']} {row['sector']}")
            st.markdown(f"**Market Cap:** {fmt_currency(row['market_cap'])}")
            st.markdown(f"**Employees:** {int(row['employees']):,}" if row["employees"] else "**Employees:** N/A")
            st.markdown(f"**Country:** {row['country']}")
            if row.get("website"):
                st.markdown(f"**Website:** {row['website']}")

        with r2:
            st.markdown(f"**R&D Intensity:** {fmt_pct(row['rd_intensity'])}")
            st.markdown(f"**Total Cash:** {fmt_currency(row['total_cash'])}")
            st.markdown(f"**Total Debt:** {fmt_currency(row['total_debt'])}")
            net_cash = row["total_cash"] - row["total_debt"]
            st.markdown(f"**Net Cash:** {fmt_currency(net_cash)}")
            if row.get("dividend_yield"):
                st.markdown(f"**Dividend Yield:** {fmt_pct(row['dividend_yield'])}")

        if row.get("description"):
            st.caption(row["description"])

st.markdown("---")

# ── Fit Score vs AI Score quadrant chart ──────────────────────────────────────
st.subheader("Investcorp Fit Score vs AI Growth Score")

df_q = filtered.copy()
df_q["ev_m"] = df_q["enterprise_value"] / 1e6

fig_quad = px.scatter(
    df_q,
    x="ai_score",
    y="fit_score",
    color="sector",
    size="ev_m",
    hover_name="name",
    text="ticker",
    color_discrete_map=sector_colors,
    labels={
        "ai_score": "AI Growth Score",
        "fit_score": "Investcorp Fit Score",
        "ev_m": "EV ($M)",
    },
    size_max=45,
)

# Quadrant lines
mid_ai = 50
mid_fit = 50
fig_quad.add_vline(x=mid_ai, line_dash="dot", line_color="#CCCCCC")
fig_quad.add_hline(y=mid_fit, line_dash="dot", line_color="#CCCCCC")

fig_quad.add_annotation(x=75, y=85, text="🟢 Prime Targets", showarrow=False, font=dict(color=INVESTCORP_PRIMARY, size=11))
fig_quad.add_annotation(x=25, y=85, text="🟡 Value Plays", showarrow=False, font=dict(color="#888", size=11))
fig_quad.add_annotation(x=75, y=15, text="🟠 Growth Watch", showarrow=False, font=dict(color="#888", size=11))
fig_quad.add_annotation(x=25, y=15, text="🔴 Monitor", showarrow=False, font=dict(color="#CCC", size=11))

fig_quad.update_traces(textposition="top center", textfont_size=9)
fig_quad.update_layout(height=480, margin=dict(t=10, b=10))
st.plotly_chart(fig_quad, use_container_width=True)

# ── EV breakdown by sector ─────────────────────────────────────────────────────
c1, c2 = st.columns(2)

with c1:
    st.subheader("Combined EV by Sector")
    ev_by_sector = (
        filtered.groupby("sector")["enterprise_value"]
        .sum()
        .reset_index()
        .sort_values("enterprise_value", ascending=False)
    )
    ev_by_sector["ev_m"] = ev_by_sector["enterprise_value"] / 1e6
    fig_bar = px.bar(
        ev_by_sector,
        x="sector",
        y="ev_m",
        color="sector",
        color_discrete_map=sector_colors,
        labels={"ev_m": "Total EV ($M)", "sector": ""},
        text_auto=".0f",
    )
    fig_bar.update_layout(showlegend=False, height=320, margin=dict(t=10, b=10))
    st.plotly_chart(fig_bar, use_container_width=True)

with c2:
    st.subheader("Avg Fit Score by Sector")
    fit_by_sector = (
        filtered.groupby("sector")["fit_score"]
        .mean()
        .reset_index()
        .sort_values("fit_score", ascending=False)
    )
    fig_fit = px.bar(
        fit_by_sector,
        x="fit_score",
        y="sector",
        orientation="h",
        color="sector",
        color_discrete_map=sector_colors,
        labels={"fit_score": "Avg Fit Score", "sector": ""},
        text_auto=".1f",
    )
    fig_fit.update_layout(showlegend=False, height=320, margin=dict(t=10, b=10))
    st.plotly_chart(fig_fit, use_container_width=True)

# ── Export ─────────────────────────────────────────────────────────────────────
st.markdown("---")

export_cols = [
    "ticker", "name", "sector", "enterprise_value", "market_cap",
    "revenue_growth", "gross_margin", "rd_intensity", "ai_score",
    "fit_score", "total_cash", "total_debt", "employees", "country",
]
export_df = filtered[export_cols].copy()
export_df["enterprise_value"] = export_df["enterprise_value"].apply(fmt_currency)
export_df["market_cap"] = export_df["market_cap"].apply(fmt_currency)
export_df["total_cash"] = export_df["total_cash"].apply(fmt_currency)
export_df["total_debt"] = export_df["total_debt"].apply(fmt_currency)
export_df["revenue_growth"] = export_df["revenue_growth"].apply(fmt_pct)
export_df["gross_margin"] = export_df["gross_margin"].apply(fmt_pct)
export_df["rd_intensity"] = export_df["rd_intensity"].apply(fmt_pct)

csv = export_df.to_csv(index=False).encode()
st.download_button(
    "⬇️ Export Acquisition Shortlist (CSV)",
    data=csv,
    file_name="investcorp_acquisition_targets.csv",
    mime="text/csv",
)

st.caption("Fit Score is a composite internal ranking metric. All data from Yahoo Finance. Not financial advice.")
