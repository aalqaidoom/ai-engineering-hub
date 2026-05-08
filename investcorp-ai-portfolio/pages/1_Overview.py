import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from config import SECTORS, EV_MIN_USD, EV_MAX_USD, INVESTCORP_PRIMARY, INVESTCORP_GOLD
from data.fetcher import fetch_sector_data, fmt_currency, fmt_pct
from data.screener import compute_ai_score, sector_summary

st.set_page_config(page_title="Overview · Investcorp AI Portfolio", page_icon="📊", layout="wide")

st.markdown(
    f"<h2 style='color:{INVESTCORP_PRIMARY};'>📊 Portfolio Overview</h2>",
    unsafe_allow_html=True,
)
st.markdown(
    f"<p style='color:#555;'>All companies with enterprise value between "
    f"<strong>{fmt_currency(EV_MIN_USD)} – {fmt_currency(EV_MAX_USD)}</strong> "
    f"across {len(SECTORS)} AI growth sectors.</p>",
    unsafe_allow_html=True,
)

@st.cache_data(ttl=3600, show_spinner=False)
def load_data():
    placeholder = st.empty()
    results = []

    def on_progress(i, total, ticker):
        if total > 0:
            placeholder.progress(i / total, text=f"Fetching {ticker}…" if ticker else "Done")

    df = fetch_sector_data(SECTORS, EV_MIN_USD, EV_MAX_USD, progress_callback=on_progress)
    placeholder.empty()
    if not df.empty:
        df = compute_ai_score(df)
    return df


with st.spinner("Loading live market data…"):
    df = load_data()

if df.empty:
    st.warning("No companies matched the EV filter right now. Market data may be unavailable. Try again shortly.")
    st.stop()

summary = sector_summary(df)

# ── KPI row ──────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("Total Opportunities", len(df))
k2.metric("Sectors Covered", df["sector"].nunique())
k3.metric("Avg Enterprise Value", fmt_currency(df["enterprise_value"].mean()))
k4.metric("Avg Revenue Growth", fmt_pct(df["revenue_growth"].mean()))
k5.metric("Avg AI Score", f"{df['ai_score'].mean():.1f} / 100")

st.markdown("---")

# ── Charts row ────────────────────────────────────────────────────────────────
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("Opportunities by Sector")
    sector_counts = df.groupby("sector").size().reset_index(name="count")
    sector_colors = {s: info["color"] for s, info in SECTORS.items()}
    fig_pie = px.pie(
        sector_counts,
        names="sector",
        values="count",
        color="sector",
        color_discrete_map=sector_colors,
        hole=0.45,
    )
    fig_pie.update_traces(textposition="outside", textinfo="percent+label")
    fig_pie.update_layout(
        showlegend=False,
        margin=dict(t=10, b=10, l=10, r=10),
        height=320,
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with chart_col2:
    st.subheader("Enterprise Value Distribution ($M)")
    df_ev = df.copy()
    df_ev["ev_m"] = df_ev["enterprise_value"] / 1e6
    fig_hist = px.histogram(
        df_ev,
        x="ev_m",
        color="sector",
        color_discrete_map=sector_colors,
        nbins=20,
        labels={"ev_m": "Enterprise Value ($M)", "count": "# Companies"},
    )
    fig_hist.update_layout(
        bargap=0.05,
        margin=dict(t=10, b=10, l=10, r=10),
        height=320,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig_hist, use_container_width=True)

# ── AI Score vs Revenue Growth scatter ───────────────────────────────────────
st.subheader("AI Growth Score vs Revenue Growth")
df_plot = df.copy()
df_plot["ev_m"] = df_plot["enterprise_value"] / 1e6
df_plot["rev_growth_pct"] = df_plot["revenue_growth"] * 100

fig_scatter = px.scatter(
    df_plot,
    x="rev_growth_pct",
    y="ai_score",
    color="sector",
    size="ev_m",
    hover_name="name",
    hover_data={"ticker": True, "ev_m": ":.0f", "rev_growth_pct": ":.1f", "ai_score": ":.1f"},
    color_discrete_map=sector_colors,
    labels={
        "rev_growth_pct": "Revenue Growth (%)",
        "ai_score": "AI Score",
        "ev_m": "EV ($M)",
    },
    size_max=40,
)
fig_scatter.add_hline(y=55, line_dash="dot", line_color=INVESTCORP_GOLD, annotation_text="High Score threshold")
fig_scatter.update_layout(height=420, margin=dict(t=10, b=10, l=10, r=10))
st.plotly_chart(fig_scatter, use_container_width=True)

# ── Sector summary table ──────────────────────────────────────────────────────
st.subheader("Sector Summary")
display_summary = summary.copy()
display_summary["avg_ev"] = display_summary["avg_ev"].apply(fmt_currency)
display_summary["avg_growth"] = display_summary["avg_growth"].apply(fmt_pct)
display_summary["avg_margin"] = display_summary["avg_margin"].apply(fmt_pct)
display_summary["avg_ai_score"] = display_summary["avg_ai_score"].round(1)
display_summary.columns = ["Sector", "Companies", "Avg EV", "Avg Revenue Growth", "Avg Gross Margin", "Avg AI Score"]
st.dataframe(display_summary, use_container_width=True, hide_index=True)

# ── Top 5 companies ───────────────────────────────────────────────────────────
st.subheader("Top 5 by AI Growth Score")
top5 = df.head(5)[["ticker", "name", "sector", "enterprise_value", "revenue_growth", "gross_margin", "ai_score", "score_icon"]]
top5_disp = top5.copy()
top5_disp["enterprise_value"] = top5_disp["enterprise_value"].apply(fmt_currency)
top5_disp["revenue_growth"] = top5_disp["revenue_growth"].apply(fmt_pct)
top5_disp["gross_margin"] = top5_disp["gross_margin"].apply(fmt_pct)
top5_disp["ai_score"] = top5_disp["score_icon"] + " " + top5_disp["ai_score"].astype(str)
top5_disp = top5_disp.drop(columns=["score_icon"])
top5_disp.columns = ["Ticker", "Company", "Sector", "Enterprise Value", "Rev Growth", "Gross Margin", "AI Score"]
st.dataframe(top5_disp, use_container_width=True, hide_index=True)
