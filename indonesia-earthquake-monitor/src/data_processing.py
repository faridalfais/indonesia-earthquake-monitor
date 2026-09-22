"""
data_processing.py
------------------
Normalises raw BMKG JSON records into a clean Pandas DataFrame.

BMKG field names (actual, verified):
  Tanggal    - date string, e.g. "23 Sep 2026"
  Jam        - local time string, e.g. "00:20:14 WIB"
  DateTime   - ISO-8601 UTC string, e.g. "2026-09-22T17:20:14+00:00"
  Coordinates- "lat,lon" string, e.g. "-8.21,120.28"
  Lintang    - latitude label string, e.g. "8.21 LS"
  Bujur      - longitude label string, e.g. "120.28 BT"
  Magnitude  - string, e.g. "4.2"
  Kedalaman  - depth string, e.g. "7 km"
  Wilayah    - region description string
  Potensi    - tsunami potential string (gempaterkini, autogempa)
  Dirasakan  - felt intensity string (gempadirasakan, autogempa)
  Shakemap   - image filename (autogempa only)
"""

from __future__ import annotations

import logging
import re

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Column name constants (output DataFrame)
# ---------------------------------------------------------------------------

COL_DATE = "date"
COL_TIME = "time"
COL_DATETIME = "datetime"
COL_LAT = "latitude"
COL_LON = "longitude"
COL_MAG = "magnitude"
COL_DEPTH = "depth_km"
COL_REGION = "region"
COL_TSUNAMI = "tsunami_status"
COL_FELT = "felt_intensity"
COL_SOURCE = "source"

OUTPUT_COLS = [
    COL_DATE, COL_TIME, COL_DATETIME,
    COL_LAT, COL_LON,
    COL_MAG, COL_DEPTH,
    COL_REGION, COL_TSUNAMI, COL_FELT, COL_SOURCE,
]


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _parse_depth(raw: str | None) -> float:
    """Extract numeric depth from strings like '7 km' or '10km'."""
    if not raw:
        return np.nan
    match = re.search(r"[\d.]+", str(raw))
    return float(match.group()) if match else np.nan


def _parse_coordinates(raw: str | None) -> tuple[float, float]:
    """
    Parse "lat,lon" string into (lat, lon) floats.
    Returns (nan, nan) on failure.
    """
    if not raw:
        return np.nan, np.nan
    parts = str(raw).split(",")
    if len(parts) != 2:
        return np.nan, np.nan
    try:
        lat = float(parts[0].strip())
        lon = float(parts[1].strip())
        return lat, lon
    except ValueError:
        return np.nan, np.nan


def _parse_datetime(raw: str | None) -> pd.Timestamp | pd.NaT:
    """Parse ISO-8601 DateTime string to UTC-aware Timestamp."""
    if not raw:
        return pd.NaT
    try:
        return pd.to_datetime(raw, utc=True)
    except Exception:
        return pd.NaT


def _infer_tsunami(potensi: str | None) -> str:
    """
    Map BMKG Potensi text to a clean tsunami status label.

    Typical values observed:
      "Tidak berpotensi tsunami"
      "Gempa ini dirasakan untuk diteruskan pada masyarakat"
      (empty / missing when not reported)
    """
    if not potensi:
        return "Tidak diketahui"
    p = str(potensi).lower()
    if "berpotensi tsunami" in p and "tidak" not in p:
        return "Berpotensi Tsunami"
    if "tidak berpotensi" in p:
        return "Tidak Berpotensi"
    return "Tidak diketahui"


def _clean_region(wilayah: str | None) -> str:
    """Return a cleaned region string, stripping verbose prefixes where safe."""
    if not wilayah:
        return "Tidak diketahui"
    # BMKG sometimes uses long descriptions; keep them as-is but strip whitespace
    return str(wilayah).strip()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def normalize_records(records: list[dict], source_label: str = "BMKG") -> pd.DataFrame:
    """
    Convert a list of raw BMKG earthquake dicts into a normalised DataFrame.

    Parameters
    ----------
    records     : raw list from bmkg_api fetch functions
    source_label: label appended to the 'source' column

    Returns
    -------
    pd.DataFrame with columns defined in OUTPUT_COLS
    """
    if not records:
        return pd.DataFrame(columns=OUTPUT_COLS)

    rows: list[dict] = []

    for rec in records:
        lat, lon = _parse_coordinates(rec.get("Coordinates"))
        datetime_utc = _parse_datetime(rec.get("DateTime"))

        row = {
            COL_DATE: rec.get("Tanggal", ""),
            COL_TIME: rec.get("Jam", ""),
            COL_DATETIME: datetime_utc,
            COL_LAT: lat,
            COL_LON: lon,
            COL_MAG: pd.to_numeric(rec.get("Magnitude"), errors="coerce"),
            COL_DEPTH: _parse_depth(rec.get("Kedalaman")),
            COL_REGION: _clean_region(rec.get("Wilayah")),
            COL_TSUNAMI: _infer_tsunami(rec.get("Potensi")),
            COL_FELT: rec.get("Dirasakan", ""),
            COL_SOURCE: source_label,
        }
        rows.append(row)

    df = pd.DataFrame(rows, columns=OUTPUT_COLS)

    # Sort newest first
    df.sort_values(COL_DATETIME, ascending=False, inplace=True, na_position="last")
    df.reset_index(drop=True, inplace=True)

    return df


def build_master_dataframe(records: list[dict]) -> pd.DataFrame:
    """
    Full pipeline: raw records -> clean, deduplicated, typed DataFrame.
    """
    df = normalize_records(records)

    if df.empty:
        return df

    # Drop rows with both lat and lon as NaN (cannot map)
    df.dropna(subset=[COL_LAT, COL_LON], how="all", inplace=True)

    # Drop exact duplicates on datetime+magnitude+region
    df.drop_duplicates(subset=[COL_DATETIME, COL_MAG, COL_REGION], inplace=True)

    df.reset_index(drop=True, inplace=True)
    return df


def apply_filters(
    df: pd.DataFrame,
    min_magnitude: float = 0.0,
    date_start: pd.Timestamp | None = None,
    date_end: pd.Timestamp | None = None,
    tsunami_filter: str | None = None,
) -> pd.DataFrame:
    """
    Apply user-selected filters to the master DataFrame.

    Parameters
    ----------
    df            : master DataFrame
    min_magnitude : minimum magnitude threshold
    date_start    : filter rows on or after this UTC timestamp
    date_end      : filter rows on or before this UTC timestamp
    tsunami_filter: one of the COL_TSUNAMI values, or None for all

    Returns
    -------
    Filtered DataFrame (copy)
    """
    filtered = df.copy()

    # Magnitude filter
    filtered = filtered[filtered[COL_MAG] >= min_magnitude]

    # Date filters – compare against COL_DATETIME (UTC-aware)
    if date_start is not None and not filtered.empty:
        if date_start.tzinfo is None:
            date_start = date_start.tz_localize("UTC")
        filtered = filtered[filtered[COL_DATETIME] >= date_start]

    if date_end is not None and not filtered.empty:
        if date_end.tzinfo is None:
            date_end = date_end.tz_localize("UTC")
        # Include the full end day
        date_end_eod = date_end + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        filtered = filtered[filtered[COL_DATETIME] <= date_end_eod]

    # Tsunami filter
    if tsunami_filter and tsunami_filter != "Semua":
        filtered = filtered[filtered[COL_TSUNAMI] == tsunami_filter]

    filtered.reset_index(drop=True, inplace=True)
    return filtered


def get_display_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return a human-readable version of the DataFrame for display in tables.
    Converts UTC datetime to WIB (UTC+7) and formats columns.
    """
    if df.empty:
        return df

    display = df.copy()

    # Convert datetime to WIB for display
    try:
        display["Waktu (WIB)"] = display[COL_DATETIME].dt.tz_convert("Asia/Jakarta").dt.strftime("%d %b %Y %H:%M")
    except Exception:
        display["Waktu (WIB)"] = display[COL_DATE] + " " + display[COL_TIME]

    cols = {
        "Waktu (WIB)": "Waktu (WIB)",
        COL_MAG: "Magnitudo",
        COL_DEPTH: "Kedalaman (km)",
        COL_REGION: "Wilayah",
        COL_TSUNAMI: "Status Tsunami",
        COL_FELT: "Dirasakan",
    }

    available = [c for c in cols if c in display.columns]
    display = display[available].rename(columns=cols)
    return display
