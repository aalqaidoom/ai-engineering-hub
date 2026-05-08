import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
from typing import Optional


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_ticker_info(ticker: str) -> Optional[dict]:
    """Return key financial fields for a single ticker, or None if unavailable."""
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
        rd_intensity = (rd / revenue) if revenue > 0 else 0.0

        summary = info.get("longBusinessSummary", "") or ""

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
            "rd_intensity": rd_intensity,
            "total_cash": cash,
            "total_debt": total_debt,
            "employees": info.get("fullTimeEmployees") or 0,
            "country": info.get("country") or "N/A",
            "website": info.get("website") or "",
            "description": summary[:300] if summary else "",
            "week52_high": info.get("fiftyTwoWeekHigh") or 0,
            "week52_low": info.get("fiftyTwoWeekLow") or 0,
            "pe_ratio": info.get("trailingPE"),
            "ev_revenue": info.get("enterpriseToRevenue"),
            "ev_ebitda": info.get("enterpriseToEbitda"),
            "dividend_yield": info.get("dividendYield") or 0.0,
            "beta": info.get("beta") or 1.0,
            "short_ratio": info.get("shortRatio") or 0.0,
            "recommendation": info.get("recommendationKey") or "N/A",
        }
    except Exception:
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_price_history(ticker: str, period: str = "1y") -> pd.DataFrame:
    """Return OHLCV price history for a ticker."""
    try:
        return yf.Ticker(ticker).history(period=period)
    except Exception:
        return pd.DataFrame()


def fetch_sector_data(
    sectors: dict,
    ev_min: float,
    ev_max: float,
    progress_callback=None,
) -> pd.DataFrame:
    """
    Fetch live data for all tickers across sectors, filter by EV range.
    progress_callback(i, total, ticker) is called for each fetch if provided.
    """
    all_tickers = [(sector, ticker) for sector, info in sectors.items() for ticker in info["tickers"]]
    total = len(all_tickers)
    results = []

    for i, (sector_name, ticker) in enumerate(all_tickers):
        if progress_callback:
            progress_callback(i, total, ticker)

        data = fetch_ticker_info(ticker)
        if data and ev_min <= data["enterprise_value"] <= ev_max:
            data["sector"] = sector_name
            data["sector_color"] = sectors[sector_name]["color"]
            data["sector_icon"] = sectors[sector_name]["icon"]
            results.append(data)

    if progress_callback:
        progress_callback(total, total, "")

    return pd.DataFrame(results) if results else pd.DataFrame()


def fmt_currency(value: float) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "N/A"
    if value >= 1e9:
        return f"${value/1e9:.1f}B"
    if value >= 1e6:
        return f"${value/1e6:.0f}M"
    if value >= 1e3:
        return f"${value/1e3:.0f}K"
    return f"${value:.0f}"


def fmt_pct(value: float) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "N/A"
    return f"{value * 100:.1f}%"
