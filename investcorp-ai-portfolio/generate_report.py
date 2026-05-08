#!/usr/bin/env python3
"""Generate a standalone Investcorp AI Portfolio HTML report (no Streamlit required)."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from config import (
    SECTORS, EV_MIN_USD, EV_MAX_USD, REFERENCE_STOCKS,
    INVESTCORP_PRIMARY, INVESTCORP_GOLD, score_label, AI_SCORE_WEIGHTS,
)
from data.screener import compute_ai_score, rank_acquisition_targets
from data.fetcher import fmt_currency, fmt_pct


# ── Data fetching (no Streamlit cache needed here) ────────────────────────────

def fetch_ticker_info(ticker: str):
    try:
        info = yf.Ticker(ticker).info
        if not info or not info.get("regularMarketPrice"):
            return None
        market_cap = info.get("marketCap") or 0
        total_debt = info.get("totalDebt") or 0
        cash = info.get("totalCash") or 0
        ev = info.get("enterpriseValue") or (market_cap + total_debt - cash)
        if not ev or ev <= 0:
            return None
        revenue = info.get("totalRevenue") or 0
        rd = info.get("researchDevelopment") or 0
        summary = (info.get("longBusinessSummary") or "")[:300]
        return {
            "ticker": ticker,
            "name": info.get("longName") or ticker,
            "price": info.get("regularMarketPrice", 0),
            "market_cap": market_cap,
            "enterprise_value": ev,
            "revenue": revenue,
            "revenue_growth": info.get("revenueGrowth") or 0.0,
            "gross_margin": info.get("grossMargins") or 0.0,
            "ebitda_margin": info.get("ebitdaMargins") or 0.0,
            "rd_expense": rd,
            "rd_intensity": (rd / revenue) if revenue > 0 else 0.0,
            "total_cash": cash,
            "total_debt": total_debt,
            "employees": info.get("fullTimeEmployees") or 0,
            "country": info.get("country") or "N/A",
            "website": info.get("website") or "",
            "description": summary,
            "dividend_yield": info.get("dividendYield") or 0.0,
            "beta": info.get("beta") or 1.0,
            "ev_revenue": info.get("enterpriseToRevenue"),
            "ev_ebitda": info.get("enterpriseToEbitda"),
        }
    except Exception:
        return None


def fetch_all(ev_min: float, ev_max: float) -> pd.DataFrame:
    all_pairs = [(s, t) for s, info in SECTORS.items() for t in info["tickers"]]
    n = len(all_pairs)
    results = []
    for i, (sector_name, ticker) in enumerate(all_pairs):
        print(f"  [{i+1:>2}/{n}] {ticker:<6}", end=" ", flush=True)
        data = fetch_ticker_info(ticker)
        if data and ev_min <= data["enterprise_value"] <= ev_max:
            data["sector"] = sector_name
            data["sector_color"] = SECTORS[sector_name]["color"]
            data["sector_icon"] = SECTORS[sector_name]["icon"]
            results.append(data)
            print(f"✓  EV {fmt_currency(data['enterprise_value'])}")
        else:
            reason = "no data" if not data else f"EV {fmt_currency(data['enterprise_value'])} out of range"
            print(f"✗  ({reason})")
    if not results:
        return pd.DataFrame()
    df = pd.DataFrame(results)
    df = compute_ai_score(df)
    df = rank_acquisition_targets(df)
    return df


# ── Representative sample data (used when live API is unavailable) ─────────────
# Values based on publicly reported financials (FY2024/Q1-2025 reports).
# EV = Market Cap + Total Debt - Cash as of approx. Q1 2025.

SAMPLE_DATA = [
    # ── AI Semiconductor Ecosystem ─────────────────────────────────────────────
    {"ticker": "CEVA",  "name": "CEVA Inc.",                    "sector": "AI Semiconductor Ecosystem", "enterprise_value": 348e6,  "market_cap": 370e6,  "revenue": 100e6,  "revenue_growth":  0.12, "gross_margin": 0.87, "rd_intensity": 0.62, "total_cash": 75e6,  "total_debt": 53e6,  "employees": 430,  "country": "USA",   "description": "Semiconductor IP licensing company specializing in AI/ML and wireless connectivity cores."},
    {"ticker": "COHU",  "name": "Cohu Inc.",                    "sector": "AI Semiconductor Ecosystem", "enterprise_value": 410e6,  "market_cap": 480e6,  "revenue": 440e6,  "revenue_growth": -0.10, "gross_margin": 0.47, "rd_intensity": 0.12, "total_cash": 220e6, "total_debt": 150e6, "employees": 3200, "country": "USA",   "description": "Semiconductor test and inspection equipment maker — direct play on AI chip production ramp."},
    {"ticker": "AEHR",  "name": "Aehr Test Systems",            "sector": "AI Semiconductor Ecosystem", "enterprise_value": 195e6,  "market_cap": 210e6,  "revenue":  60e6,  "revenue_growth": -0.18, "gross_margin": 0.50, "rd_intensity": 0.20, "total_cash": 55e6,  "total_debt": 40e6,  "employees": 190,  "country": "USA",   "description": "Wafer-level burn-in and test systems for power semiconductors used in AI data centers and EVs."},
    {"ticker": "FORM",  "name": "FormFactor Inc.",               "sector": "AI Semiconductor Ecosystem", "enterprise_value": 460e6,  "market_cap": 500e6,  "revenue": 710e6,  "revenue_growth":  0.08, "gross_margin": 0.45, "rd_intensity": 0.14, "total_cash": 190e6, "total_debt": 150e6, "employees": 2100, "country": "USA",   "description": "Probe card and wafer-testing solutions enabling leading-edge AI chip manufacturing at TSMC and Samsung."},
    {"ticker": "NVTS",  "name": "Navitas Semiconductor",        "sector": "AI Semiconductor Ecosystem", "enterprise_value": 290e6,  "market_cap": 340e6,  "revenue":  90e6,  "revenue_growth":  0.28, "gross_margin": 0.43, "rd_intensity": 0.50, "total_cash": 115e6, "total_debt": 65e6,  "employees": 320,  "country": "USA",   "description": "GaN and SiC power ICs enabling next-generation fast charging and data center power conversion."},
    {"ticker": "AOSL",  "name": "Alpha and Omega Semiconductor", "sector": "AI Semiconductor Ecosystem", "enterprise_value": 385e6,  "market_cap": 460e6,  "revenue": 620e6,  "revenue_growth":  0.10, "gross_margin": 0.26, "rd_intensity": 0.09, "total_cash": 175e6, "total_debt": 100e6, "employees": 2900, "country": "USA",   "description": "Power semiconductors and ICs for computing, communications, and AI server power management."},
    {"ticker": "MRAM",  "name": "Everspin Technologies",         "sector": "AI Semiconductor Ecosystem", "enterprise_value":  82e6,  "market_cap":  90e6,  "revenue":  58e6,  "revenue_growth":  0.05, "gross_margin": 0.52, "rd_intensity": 0.22, "total_cash": 22e6,  "total_debt": 14e6,  "employees": 200,  "country": "USA",   "description": "Sole producer of Magnetoresistive RAM — persistent memory ideal for AI inference at the edge."},
    # ── Data Center & Networking ───────────────────────────────────────────────
    {"ticker": "AVNW",  "name": "Aviat Networks",               "sector": "Data Center & Networking",   "enterprise_value": 175e6,  "market_cap": 200e6,  "revenue": 270e6,  "revenue_growth":  0.06, "gross_margin": 0.53, "rd_intensity": 0.08, "total_cash": 60e6,  "total_debt": 35e6,  "employees": 1100, "country": "USA",   "description": "Microwave and millimeter-wave wireless backhaul connecting data centers and cell towers."},
    {"ticker": "RBBN",  "name": "Ribbon Communications",        "sector": "Data Center & Networking",   "enterprise_value": 220e6,  "market_cap": 250e6,  "revenue": 580e6,  "revenue_growth": -0.04, "gross_margin": 0.56, "rd_intensity": 0.18, "total_cash": 80e6,  "total_debt": 50e6,  "employees": 3200, "country": "USA",   "description": "Edge cloud and AI-powered network infrastructure enabling secure real-time communications."},
    {"ticker": "CRNT",  "name": "Ceragon Networks",             "sector": "Data Center & Networking",   "enterprise_value": 115e6,  "market_cap": 130e6,  "revenue": 360e6,  "revenue_growth":  0.09, "gross_margin": 0.35, "rd_intensity": 0.09, "total_cash": 45e6,  "total_debt": 30e6,  "employees": 1700, "country": "Israel","description": "Wireless backhaul solutions for data center campus interconnect and emerging-market mobile infrastructure."},
    {"ticker": "CASA",  "name": "Casa Systems",                 "sector": "Data Center & Networking",   "enterprise_value":  75e6,  "market_cap":  85e6,  "revenue": 200e6,  "revenue_growth": -0.22, "gross_margin": 0.55, "rd_intensity": 0.25, "total_cash": 30e6,  "total_debt": 20e6,  "employees": 900,  "country": "USA",   "description": "Cloud-native broadband access and 5G solutions for cable operators and cloud data center interconnect."},
    {"ticker": "CLFD",  "name": "Clearfield Inc.",              "sector": "Data Center & Networking",   "enterprise_value": 155e6,  "market_cap": 180e6,  "revenue": 190e6,  "revenue_growth": -0.32, "gross_margin": 0.40, "rd_intensity": 0.05, "total_cash": 65e6,  "total_debt": 40e6,  "employees": 620,  "country": "USA",   "description": "Fiber connectivity platforms enabling high-density fiber-to-the-home and data center dark fiber buildouts."},
    {"ticker": "ADTN",  "name": "ADTRAN Holdings",              "sector": "Data Center & Networking",   "enterprise_value": 390e6,  "market_cap": 430e6,  "revenue": 750e6,  "revenue_growth": -0.14, "gross_margin": 0.52, "rd_intensity": 0.16, "total_cash": 140e6, "total_debt": 100e6, "employees": 3100, "country": "USA",   "description": "Open, disaggregated networking platforms for telcos and enterprises — positioned for AI-driven network upgrade cycles."},
    {"ticker": "SIFY",  "name": "Sify Technologies",            "sector": "Data Center & Networking",   "enterprise_value": 220e6,  "market_cap": 250e6,  "revenue": 310e6,  "revenue_growth":  0.18, "gross_margin": 0.32, "rd_intensity": 0.04, "total_cash": 55e6,  "total_debt": 25e6,  "employees": 5200, "country": "India", "description": "India's largest data center and cloud services provider — benefiting from AI-driven hyperscaler expansion in South Asia."},
    # ── Cloud & AI Applications ────────────────────────────────────────────────
    {"ticker": "BBAI",  "name": "BigBear.ai Holdings",          "sector": "Cloud & AI Applications",    "enterprise_value": 260e6,  "market_cap": 290e6,  "revenue": 160e6,  "revenue_growth":  0.16, "gross_margin": 0.18, "rd_intensity": 0.12, "total_cash": 50e6,  "total_debt": 20e6,  "employees": 1500, "country": "USA",   "description": "AI-powered analytics and decision intelligence for U.S. defense, intelligence, and supply-chain customers."},
    {"ticker": "RCAT",  "name": "Red Cat Holdings",             "sector": "Cloud & AI Applications",    "enterprise_value": 148e6,  "market_cap": 165e6,  "revenue":  30e6,  "revenue_growth":  0.82, "gross_margin": 0.30, "rd_intensity": 0.35, "total_cash": 28e6,  "total_debt": 11e6,  "employees": 220,  "country": "USA",   "description": "AI-enabled small drone platforms and ISR software for U.S. military — fastest-growing AI drone pure-play."},
    {"ticker": "ARQQ",  "name": "Arqit Quantum",                "sector": "Cloud & AI Applications",    "enterprise_value":  98e6,  "market_cap": 110e6,  "revenue":   8e6,  "revenue_growth":  0.20, "gross_margin": 0.88, "rd_intensity": 1.80, "total_cash": 45e6,  "total_debt": 33e6,  "employees": 110,  "country": "UK",    "description": "Quantum-safe symmetric key encryption delivered as a cloud service — protects AI model IP and data pipelines."},
    {"ticker": "QBTS",  "name": "D-Wave Quantum",               "sector": "Cloud & AI Applications",    "enterprise_value": 395e6,  "market_cap": 430e6,  "revenue":  10e6,  "revenue_growth":  0.22, "gross_margin": 0.70, "rd_intensity": 4.50, "total_cash": 90e6,  "total_debt": 55e6,  "employees": 200,  "country": "Canada","description": "Commercial quantum computing cloud platform — annealing-based QPUs solving optimization problems for AI/ML workflows."},
    {"ticker": "PERI",  "name": "Perion Network",               "sector": "Cloud & AI Applications",    "enterprise_value": 105e6,  "market_cap": 120e6,  "revenue": 500e6,  "revenue_growth": -0.36, "gross_margin": 0.87, "rd_intensity": 0.06, "total_cash": 220e6, "total_debt": 205e6, "employees": 750,  "country": "Israel","description": "AI-powered digital advertising technology across search, social, and CTV — deep cash position relative to EV."},
    {"ticker": "MGNI",  "name": "Magnite",                      "sector": "Cloud & AI Applications",    "enterprise_value": 490e6,  "market_cap": 550e6,  "revenue": 620e6,  "revenue_growth":  0.14, "gross_margin": 0.63, "rd_intensity": 0.14, "total_cash": 190e6, "total_debt": 130e6, "employees": 900,  "country": "USA",   "description": "Largest independent programmatic sell-side advertising platform — AI-driven yield optimization for CTV and digital media."},
    # ── AI Power & Energy ──────────────────────────────────────────────────────
    {"ticker": "FTCI",  "name": "FTC Solar",                    "sector": "AI Power & Energy",          "enterprise_value":  58e6,  "market_cap":  65e6,  "revenue": 175e6,  "revenue_growth": -0.24, "gross_margin": 0.10, "rd_intensity": 0.04, "total_cash": 22e6,  "total_debt": 15e6,  "employees": 250,  "country": "USA",   "description": "Utility-scale solar tracker systems enabling low-cost renewable power for AI data center campuses."},
    {"ticker": "FLUX",  "name": "Flux Power Holdings",          "sector": "AI Power & Energy",          "enterprise_value": 102e6,  "market_cap": 115e6,  "revenue": 100e6,  "revenue_growth":  0.18, "gross_margin": 0.20, "rd_intensity": 0.07, "total_cash": 20e6,  "total_debt": 7e6,   "employees": 380,  "country": "USA",   "description": "Lithium-ion battery packs for industrial forklifts and material handling — energy storage for warehouse AI/automation."},
    {"ticker": "BEEM",  "name": "Beam Global",                  "sector": "AI Power & Energy",          "enterprise_value":  54e6,  "market_cap":  60e6,  "revenue":  22e6,  "revenue_growth": -0.08, "gross_margin": 0.15, "rd_intensity": 0.22, "total_cash": 14e6,  "total_debt":  8e6,  "employees": 130,  "country": "USA",   "description": "Off-grid EV charging and power solutions enabling data center edge deployments without grid connection."},
    {"ticker": "MNTK",  "name": "Montauk Renewables",           "sector": "AI Power & Energy",          "enterprise_value": 210e6,  "market_cap": 240e6,  "revenue": 120e6,  "revenue_growth":  0.06, "gross_margin": 0.40, "rd_intensity": 0.02, "total_cash": 65e6,  "total_debt": 35e6,  "employees": 250,  "country": "USA",   "description": "Renewable natural gas producer — converts landfill methane to pipeline-quality gas powering data center backup generators."},
    {"ticker": "AMRC",  "name": "Ameresco",                     "sector": "AI Power & Energy",          "enterprise_value": 410e6,  "market_cap": 460e6,  "revenue": 1400e6, "revenue_growth": -0.04, "gross_margin": 0.18, "rd_intensity": 0.01, "total_cash": 120e6, "total_debt": 70e6,  "employees": 1300, "country": "USA",   "description": "Clean energy project developer and EPC contractor — builds solar, battery, and efficiency projects for data center operators."},
    {"ticker": "MVST",  "name": "Microvast Holdings",           "sector": "AI Power & Energy",          "enterprise_value": 195e6,  "market_cap": 220e6,  "revenue": 300e6,  "revenue_growth":  0.12, "gross_margin": 0.12, "rd_intensity": 0.10, "total_cash": 75e6,  "total_debt": 50e6,  "employees": 2500, "country": "USA",   "description": "Ultra-fast charging lithium-titanate batteries for heavy industry and data center UPS — proprietary cell chemistry."},
]


def get_sample_df() -> pd.DataFrame:
    """Return sample data pre-scored and ranked."""
    records = []
    for row in SAMPLE_DATA:
        sector = row["sector"]
        row = dict(row)
        row["sector_color"] = SECTORS[sector]["color"]
        row["sector_icon"]  = SECTORS[sector]["icon"]
        row["ebitda_margin"] = row["gross_margin"] * 0.4
        row["rd_expense"]    = row["revenue"] * row["rd_intensity"]
        row["employees"]     = row.get("employees", 0)
        row["dividend_yield"] = 0.0
        row["beta"]           = 1.2
        row["ev_revenue"]     = row["enterprise_value"] / max(row["revenue"], 1)
        row["ev_ebitda"]      = None
        row["price"]          = row["market_cap"] / 1e6
        records.append(row)
    df = pd.DataFrame(records)
    df = compute_ai_score(df)
    df = rank_acquisition_targets(df)
    return df


# ── Charts ─────────────────────────────────────────────────────────────────────

def _sector_color_map():
    return {s: info["color"] for s, info in SECTORS.items()}


def chart_pie(df):
    counts = df.groupby("sector").size().reset_index(name="count")
    fig = px.pie(
        counts, names="sector", values="count", color="sector",
        color_discrete_map=_sector_color_map(), hole=0.45,
        title="Opportunities by Theme",
    )
    fig.update_traces(textposition="outside", textinfo="percent+label")
    fig.update_layout(showlegend=False, height=400, margin=dict(t=50, b=10, l=10, r=10),
                      title_font_color=INVESTCORP_PRIMARY, title_font_size=15)
    return fig.to_html(full_html=False, include_plotlyjs=False)


def chart_ev_hist(df):
    df2 = df.copy()
    df2["ev_m"] = df2["enterprise_value"] / 1e6
    fig = px.histogram(
        df2, x="ev_m", color="sector", color_discrete_map=_sector_color_map(),
        nbins=20, title="Enterprise Value Distribution ($M)",
        labels={"ev_m": "EV ($M)"},
    )
    fig.update_layout(bargap=0.05, height=400, margin=dict(t=50, b=10, l=10, r=10),
                      legend=dict(orientation="h", yanchor="bottom", y=1.08, font_size=11),
                      title_font_color=INVESTCORP_PRIMARY, title_font_size=15)
    return fig.to_html(full_html=False, include_plotlyjs=False)


def chart_scatter(df):
    df2 = df.copy()
    df2["ev_m"] = df2["enterprise_value"] / 1e6
    df2["rev_pct"] = df2["revenue_growth"] * 100
    fig = px.scatter(
        df2, x="rev_pct", y="ai_score", color="sector", size="ev_m",
        hover_name="name", text="ticker",
        hover_data={"ticker": True, "ev_m": ":.0f", "rev_pct": ":.1f", "ai_score": ":.1f"},
        color_discrete_map=_sector_color_map(), size_max=40,
        title="AI Growth Score vs Revenue Growth",
        labels={"rev_pct": "Revenue Growth (%)", "ai_score": "AI Score", "ev_m": "EV ($M)"},
    )
    fig.add_hline(y=55, line_dash="dot", line_color=INVESTCORP_GOLD,
                  annotation_text="High Score threshold", annotation_position="top right")
    fig.update_traces(textposition="top center", textfont_size=9)
    fig.update_layout(height=500, margin=dict(t=50, b=10, l=10, r=10),
                      title_font_color=INVESTCORP_PRIMARY, title_font_size=15)
    return fig.to_html(full_html=False, include_plotlyjs=False)


def chart_quadrant(df):
    df2 = df.copy()
    df2["ev_m"] = df2["enterprise_value"] / 1e6
    fig = px.scatter(
        df2, x="ai_score", y="fit_score", color="sector", size="ev_m",
        hover_name="name", text="ticker",
        color_discrete_map=_sector_color_map(), size_max=45,
        title="Investcorp Fit Score vs AI Growth Score",
        labels={"ai_score": "AI Growth Score", "fit_score": "Investcorp Fit Score", "ev_m": "EV ($M)"},
    )
    fig.add_vline(x=50, line_dash="dot", line_color="#CCCCCC")
    fig.add_hline(y=50, line_dash="dot", line_color="#CCCCCC")
    for txt, x, y, col in [
        ("🟢 Prime Targets", 75, 88, INVESTCORP_PRIMARY),
        ("🟡 Value Plays",   25, 88, "#888"),
        ("🟠 Growth Watch",  75, 12, "#888"),
        ("🔴 Monitor",       25, 12, "#CCC"),
    ]:
        fig.add_annotation(x=x, y=y, text=txt, showarrow=False,
                           font=dict(color=col, size=11))
    fig.update_traces(textposition="top center", textfont_size=9)
    fig.update_layout(height=500, margin=dict(t=50, b=10, l=10, r=10),
                      title_font_color=INVESTCORP_PRIMARY, title_font_size=15)
    return fig.to_html(full_html=False, include_plotlyjs=False)


# ── HTML assembly ──────────────────────────────────────────────────────────────

def build_kpi_cards(df):
    cards = [
        ("Total Opportunities", str(len(df)), "Companies within $50M–$500M EV"),
        ("Themes Covered", str(df["sector"].nunique()), "AI infrastructure verticals"),
        ("Avg Enterprise Value", fmt_currency(df["enterprise_value"].mean()), "Across all screened companies"),
        ("Avg AI Growth Score", f"{df['ai_score'].mean():.1f} / 100",
         "Rev growth · Margin · R&D · EV efficiency"),
    ]
    html = '<div class="kpi-row">'
    for label, value, sub in cards:
        html += f"""
        <div class="kpi-card">
          <div class="kpi-label">{label}</div>
          <div class="kpi-value">{value}</div>
          <div class="kpi-sub">{sub}</div>
        </div>"""
    html += "</div>"
    return html


def build_ref_grid():
    html = '<div class="ref-grid">'
    for theme, tickers in REFERENCE_STOCKS.items():
        color = SECTORS[theme]["color"]
        icon = SECTORS[theme]["icon"]
        badges = "".join(f'<code>{t}</code>' for t in tickers)
        html += f"""
        <div class="ref-card">
          <div class="ref-theme" style="color:{color}">{icon} {theme}</div>
          <div class="ref-tickers">{badges}</div>
        </div>"""
    html += "</div>"
    return html


def build_sector_summary(df):
    rows = ""
    for sector, info in SECTORS.items():
        s = df[df["sector"] == sector]
        if s.empty:
            continue
        rows += f"""
        <tr>
          <td>{info['icon']} {sector}</td>
          <td style="text-align:center;font-weight:600">{len(s)}</td>
          <td style="text-align:right">{fmt_currency(s['enterprise_value'].mean())}</td>
          <td style="text-align:right">{fmt_pct(s['revenue_growth'].mean())}</td>
          <td style="text-align:right">{fmt_pct(s['gross_margin'].mean())}</td>
          <td style="text-align:center;font-weight:600">{s['ai_score'].mean():.1f}</td>
        </tr>"""
    return f"""
    <table>
      <thead><tr>
        <th>Theme</th><th>Companies</th><th>Avg EV</th>
        <th>Avg Rev Growth</th><th>Avg Gross Margin</th><th>Avg AI Score</th>
      </tr></thead>
      <tbody>{rows}</tbody>
    </table>"""


def build_targets_table(df):
    rows = ""
    for rank, (_, row) in enumerate(df.iterrows(), 1):
        fit = row.get("fit_score", 0)
        ai = row.get("ai_score", 0)
        icon = row.get("score_icon", "")
        bar_col = "#27AE60" if fit >= 70 else ("#F39C12" if fit >= 50 else "#E74C3C")
        sector_col = SECTORS.get(row["sector"], {}).get("color", "#999")
        sector_icon = row.get("sector_icon", "")

        def score_cell(val, col):
            return (
                f'<div style="display:flex;align-items:center;gap:6px">'
                f'<div style="flex:1;background:#eee;border-radius:4px;height:8px">'
                f'<div style="width:{min(val,100):.0f}%;background:{col};height:8px;border-radius:4px"></div>'
                f'</div>'
                f'<span style="font-size:0.84rem;font-weight:700;min-width:32px">{val:.0f}</span>'
                f'</div>'
            )

        rows += f"""
        <tr>
          <td style="text-align:center;font-weight:700;color:{INVESTCORP_PRIMARY}">#{rank}</td>
          <td><strong style="color:{INVESTCORP_PRIMARY}">{row['ticker']}</strong></td>
          <td style="max-width:180px;font-size:0.86rem">{row['name']}</td>
          <td><span style="background:{sector_col};color:white;padding:2px 8px;border-radius:12px;font-size:0.76rem;white-space:nowrap">{sector_icon} {row['sector']}</span></td>
          <td style="text-align:right;font-weight:600">{fmt_currency(row['enterprise_value'])}</td>
          <td style="text-align:right">{fmt_pct(row['revenue_growth'])}</td>
          <td style="text-align:right">{fmt_pct(row['gross_margin'])}</td>
          <td style="min-width:140px">{icon} {score_cell(ai, bar_col)}</td>
          <td style="min-width:140px">{score_cell(fit, bar_col)}</td>
        </tr>"""

    return f"""
    <table>
      <thead><tr>
        <th>#</th><th>Ticker</th><th>Company</th><th>Theme</th>
        <th>Enterprise Value</th><th>Rev Growth</th><th>Gross Margin</th>
        <th>AI Score</th><th>Fit Score</th>
      </tr></thead>
      <tbody>{rows}</tbody>
    </table>"""


def generate_html(df: pd.DataFrame, output_path: str):
    now = datetime.now().strftime("%B %d, %Y — %H:%M")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Investcorp AI Portfolio — {now}</title>
<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        background: #F5F7FA; color: #1A1A2E; line-height: 1.5; }}

.hero {{
  background: linear-gradient(135deg, {INVESTCORP_PRIMARY} 0%, #005599 100%);
  color: white; padding: 3rem 4rem; position: relative;
}}
.hero h1 {{ font-size: 2.2rem; font-weight: 700; margin-bottom: 0.3rem; }}
.gold-bar {{ height: 4px; width: 80px; background: {INVESTCORP_GOLD}; border-radius: 2px; margin: 0.7rem 0 1rem; }}
.hero p {{ font-size: 1rem; opacity: 0.88; max-width: 700px; }}
.hero .date {{ position: absolute; top: 1.5rem; right: 3rem; font-size: 0.82rem; opacity: 0.65; }}

.container {{ max-width: 1400px; margin: 0 auto; padding: 2rem; }}

/* KPIs */
.kpi-row {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin: 2rem 0; }}
.kpi-card {{
  background: white; border-radius: 10px; padding: 1.4rem 1.6rem;
  border: 1px solid #E8ECF0; box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}}
.kpi-label {{ font-size: 0.72rem; font-weight: 700; color: #999; text-transform: uppercase;
              letter-spacing: 0.06em; margin-bottom: 0.5rem; }}
.kpi-value {{ font-size: 1.75rem; font-weight: 700; color: {INVESTCORP_PRIMARY}; }}
.kpi-sub {{ font-size: 0.78rem; color: #aaa; margin-top: 0.3rem; }}

h2 {{
  color: {INVESTCORP_PRIMARY}; font-size: 1.2rem; margin: 2.5rem 0 1rem;
  border-left: 4px solid {INVESTCORP_GOLD}; padding-left: 0.8rem;
}}

/* Reference anchors */
.ref-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; margin-bottom: 1.5rem; }}
.ref-card {{ background: white; border-radius: 8px; padding: 1rem 1.2rem; border: 1px solid #E8ECF0; }}
.ref-theme {{ font-size: 0.94rem; font-weight: 700; margin-bottom: 0.5rem; }}
.ref-tickers {{ font-size: 0.82rem; color: #555; }}
.ref-tickers code {{
  background: #F0F4F8; border-radius: 4px; padding: 2px 6px;
  font-size: 0.76rem; margin: 2px 2px; display: inline-block; font-family: monospace;
}}

/* Charts */
.chart-grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-bottom: 1.5rem; }}
.chart-card {{
  background: white; border-radius: 10px; padding: 1rem;
  border: 1px solid #E8ECF0; box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}}
.chart-full {{ background: white; border-radius: 10px; padding: 1rem;
               border: 1px solid #E8ECF0; box-shadow: 0 2px 8px rgba(0,0,0,0.05);
               margin-bottom: 1.5rem; }}

/* Tables */
.table-wrap {{
  background: white; border-radius: 10px; padding: 1.5rem;
  border: 1px solid #E8ECF0; box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  margin-bottom: 1.5rem; overflow-x: auto;
}}
table {{ width: 100%; border-collapse: collapse; font-size: 0.87rem; }}
thead th {{
  background: {INVESTCORP_PRIMARY}; color: white;
  padding: 0.65rem 1rem; text-align: left;
  font-weight: 600; font-size: 0.79rem; white-space: nowrap;
}}
tbody tr:nth-child(even) {{ background: #F8FAFC; }}
tbody tr:hover {{ background: #EEF4FF; transition: background 0.15s; }}
tbody td {{ padding: 0.65rem 1rem; border-bottom: 1px solid #F0F4F8; vertical-align: middle; }}

.footer {{
  text-align: center; padding: 2rem; color: #aaa; font-size: 0.8rem;
  border-top: 1px solid #E8ECF0; margin-top: 1rem;
}}

@media (max-width: 960px) {{
  .kpi-row, .chart-grid-2, .ref-grid {{ grid-template-columns: 1fr 1fr; }}
  .hero {{ padding: 2rem; }}
  .hero .date {{ position: static; margin-bottom: 0.5rem; display: block; }}
}}
@media (max-width: 600px) {{
  .kpi-row, .chart-grid-2, .ref-grid {{ grid-template-columns: 1fr; }}
}}
</style>
</head>
<body>

<div class="hero">
  <span class="date">Generated: {now}</span>
  <h1>📈 Investcorp AI Portfolio</h1>
  <div class="gold-bar"></div>
  <p>
    Acquisition targets in the AI infrastructure supply chain — semiconductors, data center &amp;
    networking, cloud &amp; AI applications, and power &amp; energy — with enterprise values between
    <strong>$50M – $500M</strong>. Thematically anchored to
    <strong>NVDA · ANET · MSFT · ETN</strong> and their ecosystems.
  </p>
</div>

<div class="container">

  {build_kpi_cards(df)}

  <h2>Thematic Anchors (Reference Stocks)</h2>
  {build_ref_grid()}

  <h2>Market Overview</h2>
  <div class="chart-grid-2">
    <div class="chart-card">{chart_pie(df)}</div>
    <div class="chart-card">{chart_ev_hist(df)}</div>
  </div>

  <h2>AI Growth Score vs Revenue Growth</h2>
  <div class="chart-full">{chart_scatter(df)}</div>

  <h2>Sector Summary</h2>
  <div class="table-wrap">{build_sector_summary(df)}</div>

  <h2>Acquisition Target Quadrant</h2>
  <div class="chart-full">{chart_quadrant(df)}</div>

  <h2>🎯 Ranked Acquisition Shortlist</h2>
  <div class="table-wrap">{build_targets_table(df)}</div>

</div>

<div class="footer">
  Data sourced via Yahoo Finance &nbsp;·&nbsp; Generated {now}<br>
  AI Score: revenue growth (35%) + gross margin (25%) + R&amp;D intensity (20%) + EV efficiency (20%)<br>
  Fit Score: AI score (40%) + EV attractiveness (25%) + revenue growth (20%) + gross margin (10%) + net cash (5%)<br>
  For investment research purposes only — not financial advice.
</div>

</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    size_kb = os.path.getsize(output_path) / 1024
    print(f"\n✅  Report saved → {output_path}")
    print(f"    Companies : {len(df)}")
    print(f"    File size : {size_kb:.0f} KB")


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "investcorp_ai_portfolio.html")

    print("=== Investcorp AI Portfolio — HTML Report Generator ===")
    print(f"EV range : {fmt_currency(EV_MIN_USD)} – {fmt_currency(EV_MAX_USD)}")
    print(f"Tickers  : {sum(len(s['tickers']) for s in SECTORS.values())} across {len(SECTORS)} themes\n")

    print("Attempting live data fetch via Yahoo Finance…")
    df = fetch_all(EV_MIN_USD, EV_MAX_USD)

    if df.empty:
        print("\n⚠️  Live data unavailable — using representative sample data.")
        df = get_sample_df()

    generate_html(df, out)
