"""
bmkg_api.py
-----------
Handles all communication with the official BMKG earthquake open-data API.

Endpoints used
~~~~~~~~~~~~~~
* autogempa.json       – single most-recent significant earthquake (Infogempa.gempa → dict)
* gempaterkini.json    – latest 15 M>=5.0 earthquakes (Infogempa.gempa → list)
* gempadirasakan.json  – latest 15 felt earthquakes   (Infogempa.gempa → list)

Real field names (verified from live responses)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Tanggal, Jam, DateTime, Coordinates, Lintang, Bujur,
Magnitude, Kedalaman, Wilayah, Potensi, Dirasakan, Shakemap
"""

from __future__ import annotations

import logging
import time
from typing import Any

import requests
import streamlit as st

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASE_URL = "https://data.bmkg.go.id/DataMKG/TEWS"

ENDPOINTS: dict[str, str] = {
    "autogempa": f"{BASE_URL}/autogempa.json",
    "gempaterkini": f"{BASE_URL}/gempaterkini.json",
    "gempadirasakan": f"{BASE_URL}/gempadirasakan.json",
}

REQUEST_TIMEOUT: int = 15   # seconds
CACHE_TTL: int = 300        # 5 minutes


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _fetch_json(url: str, timeout: int = REQUEST_TIMEOUT) -> dict[str, Any] | None:
    """
    Fetch JSON from *url*.

    Returns the parsed dict on success, or None on any failure.
    All exceptions are logged; callers should treat None as an error signal.
    """
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        logger.error("Timeout fetching %s (limit=%ds)", url, timeout)
    except requests.exceptions.HTTPError as exc:
        logger.error("HTTP error fetching %s: %s", url, exc)
    except requests.exceptions.ConnectionError as exc:
        logger.error("Connection error fetching %s: %s", url, exc)
    except requests.exceptions.RequestException as exc:
        logger.error("Request error fetching %s: %s", url, exc)
    except ValueError as exc:
        logger.error("JSON parse error from %s: %s", url, exc)
    return None


def _extract_gempa_list(raw: dict[str, Any] | None, endpoint_name: str) -> list[dict]:
    """
    Safely navigate the nested BMKG structure:
      raw -> Infogempa -> gempa  (list or dict)

    Always returns a flat list of earthquake dicts.
    """
    if raw is None:
        return []
    try:
        gempa = raw["Infogempa"]["gempa"]
        if isinstance(gempa, dict):
            return [gempa]
        if isinstance(gempa, list):
            return gempa
        logger.warning("Unexpected 'gempa' type (%s) in %s", type(gempa), endpoint_name)
        return []
    except (KeyError, TypeError) as exc:
        logger.error("Schema error in %s response: %s", endpoint_name, exc)
        return []


# ---------------------------------------------------------------------------
# Public cached fetchers
# ---------------------------------------------------------------------------

@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def fetch_gempaterkini() -> list[dict]:
    """
    Return up to 15 latest M>=5.0 earthquakes from BMKG gempaterkini endpoint.
    Result is cached for CACHE_TTL seconds.
    """
    raw = _fetch_json(ENDPOINTS["gempaterkini"])
    return _extract_gempa_list(raw, "gempaterkini")


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def fetch_gempadirasakan() -> list[dict]:
    """
    Return up to 15 latest felt earthquakes from BMKG gempadirasakan endpoint.
    Result is cached for CACHE_TTL seconds.
    """
    raw = _fetch_json(ENDPOINTS["gempadirasakan"])
    return _extract_gempa_list(raw, "gempadirasakan")


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def fetch_autogempa() -> dict | None:
    """
    Return the single most-recent significant earthquake dict, or None.
    Result is cached for CACHE_TTL seconds.
    """
    raw = _fetch_json(ENDPOINTS["autogempa"])
    result = _extract_gempa_list(raw, "autogempa")
    return result[0] if result else None


def fetch_all_earthquakes() -> tuple[list[dict], str | None]:
    """
    Merge gempaterkini + gempadirasakan into one deduplicated list.

    Returns
    -------
    (records, error_message)
        records       : list of raw BMKG earthquake dicts
        error_message : non-None string if data could not be fetched
    """
    terkini = fetch_gempaterkini()
    dirasakan = fetch_gempadirasakan()

    if not terkini and not dirasakan:
        return [], "Tidak dapat mengambil data dari BMKG. Periksa koneksi internet Anda."

    # Deduplicate by DateTime field
    seen: set[str] = set()
    merged: list[dict] = []

    for record in (dirasakan + terkini):
        key = record.get("DateTime", "")
        if key and key not in seen:
            seen.add(key)
            merged.append(record)
        elif not key:
            # No DateTime - use Tanggal+Jam as fallback key
            fallback = record.get("Tanggal", "") + record.get("Jam", "")
            if fallback not in seen:
                seen.add(fallback)
                merged.append(record)

    return merged, None


def clear_cache() -> None:
    """Force-clear the Streamlit data cache for all BMKG fetchers."""
    fetch_gempaterkini.clear()
    fetch_gempadirasakan.clear()
    fetch_autogempa.clear()


def get_fetch_timestamp() -> str:
    """Return current local time as a human-readable string."""
    return time.strftime("%d %b %Y, %H:%M:%S WIB")
