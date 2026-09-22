"""
analysis.py
-----------
Reusable statistical and analytical functions for earthquake data.
All functions accept a pd.DataFrame produced by data_processing.build_master_dataframe().
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.data_processing import (
    COL_DATE,
    COL_DATETIME,
    COL_DEPTH,
    COL_MAG,
    COL_REGION,
    COL_TSUNAMI,
)


# ---------------------------------------------------------------------------
# Basic KPI metrics
# ---------------------------------------------------------------------------

def total_events(df: pd.DataFrame) -> int:
    """Total number of earthquake records in the DataFrame."""
    return len(df)


def max_magnitude(df: pd.DataFrame) -> float | None:
    """Largest recorded magnitude, or None if no data."""
    if df.empty or df[COL_MAG].isna().all():
        return None
    return float(df[COL_MAG].max())


def average_magnitude(df: pd.DataFrame) -> float | None:
    """Mean magnitude, or None if no data."""
    if df.empty or df[COL_MAG].isna().all():
        return None
    return float(df[COL_MAG].mean())


def average_depth(df: pd.DataFrame) -> float | None:
    """Mean depth in km, or None if no data."""
    if df.empty or df[COL_DEPTH].isna().all():
        return None
    return float(df[COL_DEPTH].mean())


def min_depth(df: pd.DataFrame) -> float | None:
    """Minimum depth in km, or None if no data."""
    if df.empty or df[COL_DEPTH].isna().all():
        return None
    return float(df[COL_DEPTH].min())


def max_depth(df: pd.DataFrame) -> float | None:
    """Maximum depth in km, or None if no data."""
    if df.empty or df[COL_DEPTH].isna().all():
        return None
    return float(df[COL_DEPTH].max())


def tsunami_event_count(df: pd.DataFrame) -> int:
    """Count of events flagged as 'Berpotensi Tsunami'."""
    if df.empty:
        return 0
    return int((df[COL_TSUNAMI] == "Berpotensi Tsunami").sum())


def unknown_tsunami_count(df: pd.DataFrame) -> int:
    """Count of events with unknown tsunami status."""
    if df.empty:
        return 0
    return int((df[COL_TSUNAMI] == "Tidak diketahui").sum())


# ---------------------------------------------------------------------------
# Time-based analysis
# ---------------------------------------------------------------------------

def events_per_day(df: pd.DataFrame) -> pd.DataFrame:
    """
    Count earthquake events grouped by calendar date (WIB).

    Returns a DataFrame with columns: ['date', 'count'].
    """
    if df.empty or df[COL_DATETIME].isna().all():
        return pd.DataFrame(columns=["date", "count"])

    try:
        dates = df[COL_DATETIME].dt.tz_convert("Asia/Jakarta").dt.date
    except Exception:
        dates = pd.to_datetime(df[COL_DATE], dayfirst=False, errors="coerce").dt.date

    counts = dates.value_counts().sort_index().reset_index()
    counts.columns = ["date", "count"]
    counts["date"] = pd.to_datetime(counts["date"])
    return counts


def cumulative_events(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cumulative earthquake count over time.

    Returns DataFrame with columns: ['date', 'cumulative'].
    """
    daily = events_per_day(df)
    if daily.empty:
        return pd.DataFrame(columns=["date", "cumulative"])
    daily["cumulative"] = daily["count"].cumsum()
    return daily[["date", "cumulative"]]


def magnitude_bins(df: pd.DataFrame, bin_size: float = 0.5) -> pd.DataFrame:
    """
    Group earthquakes into magnitude bins.

    Returns DataFrame with columns: ['magnitude_bin', 'count'].
    """
    if df.empty or df[COL_MAG].isna().all():
        return pd.DataFrame(columns=["magnitude_bin", "count"])

    mag_min = np.floor(df[COL_MAG].min())
    mag_max = np.ceil(df[COL_MAG].max()) + bin_size
    bins = np.arange(mag_min, mag_max, bin_size)
    labels = [f"{b:.1f}–{b+bin_size:.1f}" for b in bins[:-1]]

    cut = pd.cut(df[COL_MAG].dropna(), bins=bins, labels=labels, right=False)
    counts = cut.value_counts().sort_index().reset_index()
    counts.columns = ["magnitude_bin", "count"]
    return counts


# ---------------------------------------------------------------------------
# Regional analysis
# ---------------------------------------------------------------------------

def regional_frequency(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """
    Count earthquakes per region, return top_n most frequent.

    Returns DataFrame with columns: ['region', 'count'].
    """
    if df.empty:
        return pd.DataFrame(columns=["region", "count"])

    counts = (
        df[COL_REGION]
        .value_counts()
        .head(top_n)
        .reset_index()
    )
    counts.columns = ["region", "count"]
    return counts


def tsunami_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return count of events by tsunami status.

    Returns DataFrame with columns: ['status', 'count'].
    """
    if df.empty:
        return pd.DataFrame(columns=["status", "count"])

    counts = df[COL_TSUNAMI].value_counts().reset_index()
    counts.columns = ["status", "count"]
    return counts


# ---------------------------------------------------------------------------
# Summary dictionary
# ---------------------------------------------------------------------------

def compute_summary(df: pd.DataFrame) -> dict:
    """
    Compute a full summary dict of all key metrics for use in KPI cards.
    """
    return {
        "total_events": total_events(df),
        "max_magnitude": max_magnitude(df),
        "avg_magnitude": average_magnitude(df),
        "avg_depth": average_depth(df),
        "min_depth": min_depth(df),
        "max_depth": max_depth(df),
        "tsunami_events": tsunami_event_count(df),
        "unknown_tsunami": unknown_tsunami_count(df),
    }
