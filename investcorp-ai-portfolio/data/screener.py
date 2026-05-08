import pandas as pd
import numpy as np
from config import AI_SCORE_WEIGHTS, score_label


def _normalize(series: pd.Series) -> pd.Series:
    mn, mx = series.min(), series.max()
    if mx == mn:
        return pd.Series(0.5, index=series.index)
    return (series - mn) / (mx - mn)


def compute_ai_score(df: pd.DataFrame) -> pd.DataFrame:
    """Add ai_score (0–100) and score_label/icon columns to dataframe."""
    if df.empty:
        return df

    df = df.copy()

    rev_growth = pd.to_numeric(df["revenue_growth"], errors="coerce").fillna(0)
    gross_margin = pd.to_numeric(df["gross_margin"], errors="coerce").fillna(0)
    rd_intensity = pd.to_numeric(df["rd_intensity"], errors="coerce").fillna(0).clip(0, 1)

    ev = pd.to_numeric(df["enterprise_value"], errors="coerce").replace(0, np.nan)
    revenue = pd.to_numeric(df["revenue"], errors="coerce").replace(0, np.nan)
    ev_rev = (ev / revenue).fillna(10).clip(0, 100)
    ev_efficiency = 1 / (ev_rev + 1)

    raw = (
        _normalize(rev_growth) * AI_SCORE_WEIGHTS["revenue_growth"]
        + _normalize(gross_margin) * AI_SCORE_WEIGHTS["gross_margin"]
        + _normalize(rd_intensity) * AI_SCORE_WEIGHTS["rd_intensity"]
        + _normalize(ev_efficiency) * AI_SCORE_WEIGHTS["ev_efficiency"]
    )

    df["ai_score"] = (raw * 100).round(1)
    df[["score_label", "score_icon"]] = df["ai_score"].apply(
        lambda s: pd.Series(score_label(s))
    )
    return df.sort_values("ai_score", ascending=False).reset_index(drop=True)


def rank_acquisition_targets(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add an investcorp_fit score combining AI score, EV attractiveness,
    revenue quality, and balance-sheet health.
    """
    if df.empty:
        return df

    df = df.copy()

    ev = pd.to_numeric(df["enterprise_value"], errors="coerce")
    ev_norm = 1 - _normalize(ev)  # smaller EV → higher fit for acquisition

    growth = pd.to_numeric(df["revenue_growth"], errors="coerce").fillna(0)
    margin = pd.to_numeric(df["gross_margin"], errors="coerce").fillna(0)
    cash = pd.to_numeric(df["total_cash"], errors="coerce").fillna(0)
    debt = pd.to_numeric(df["total_debt"], errors="coerce").fillna(0)
    net_cash_norm = _normalize(cash - debt)

    ai = pd.to_numeric(df["ai_score"], errors="coerce").fillna(0) / 100

    fit = (
        ai * 0.40
        + ev_norm * 0.25
        + _normalize(growth) * 0.20
        + _normalize(margin) * 0.10
        + net_cash_norm * 0.05
    )

    df["fit_score"] = (fit * 100).round(1)
    return df.sort_values("fit_score", ascending=False).reset_index(drop=True)


def sector_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate stats per sector."""
    if df.empty:
        return pd.DataFrame()

    return (
        df.groupby("sector")
        .agg(
            companies=("ticker", "count"),
            avg_ev=("enterprise_value", "mean"),
            avg_growth=("revenue_growth", "mean"),
            avg_margin=("gross_margin", "mean"),
            avg_ai_score=("ai_score", "mean"),
        )
        .round(3)
        .reset_index()
    )
