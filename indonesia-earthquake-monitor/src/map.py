"""
map.py
------
PyDeck-based interactive earthquake map for the Indonesia Earthquake Monitor.
"""

from __future__ import annotations

import pandas as pd
import pydeck as pdk

from src.data_processing import (
    COL_DATETIME,
    COL_DEPTH,
    COL_LAT,
    COL_LON,
    COL_MAG,
    COL_REGION,
    COL_TSUNAMI,
)

# ---------------------------------------------------------------------------
# Map constants
# ---------------------------------------------------------------------------

# Indonesia geographic centre
INDONESIA_CENTRE = {"latitude": -2.5, "longitude": 118.0}
DEFAULT_ZOOM = 4

# Colour palette (RGBA)
COLOR_TSUNAMI = [220, 38, 38, 210]      # red
COLOR_NORMAL = [29, 111, 164, 180]      # blue
COLOR_UNKNOWN = [156, 163, 175, 160]    # grey

# Scale factor for circle radius: magnitude -> metres
MAG_RADIUS_SCALE = 25_000  # 1 magnitude unit = 25 km radius


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _color_for_row(status: str) -> list[int]:
    if status == "Berpotensi Tsunami":
        return COLOR_TSUNAMI
    if status == "Tidak Berpotensi":
        return COLOR_NORMAL
    return COLOR_UNKNOWN


def _radius_for_magnitude(mag: float) -> float:
    """Convert magnitude to visual circle radius in metres."""
    if pd.isna(mag):
        return MAG_RADIUS_SCALE
    # Exponential scaling feels natural for magnitude
    return max(MAG_RADIUS_SCALE * (2 ** (mag - 4)), 8_000)


def _prepare_map_data(df: pd.DataFrame) -> pd.DataFrame:
    """Add colour and radius columns needed by PyDeck."""
    if df.empty:
        return df

    map_df = df.dropna(subset=[COL_LAT, COL_LON]).copy()

    map_df["color"] = map_df[COL_TSUNAMI].apply(_color_for_row)
    map_df["radius"] = map_df[COL_MAG].apply(_radius_for_magnitude)

    # Tooltip-friendly strings
    try:
        map_df["waktu_wib"] = (
            map_df[COL_DATETIME]
            .dt.tz_convert("Asia/Jakarta")
            .dt.strftime("%d %b %Y %H:%M WIB")
        )
    except Exception:
        map_df["waktu_wib"] = map_df.get("date", "")

    map_df["mag_str"] = map_df[COL_MAG].apply(
        lambda m: f"{m:.1f}" if pd.notna(m) else "N/A"
    )
    map_df["depth_str"] = map_df[COL_DEPTH].apply(
        lambda d: f"{d:.0f} km" if pd.notna(d) else "N/A"
    )

    return map_df


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_earthquake_map(df: pd.DataFrame) -> pdk.Deck:
    """
    Build a PyDeck Deck object for the earthquake map.

    Parameters
    ----------
    df : filtered master DataFrame

    Returns
    -------
    pdk.Deck instance ready for st.pydeck_chart()
    """
    map_df = _prepare_map_data(df)

    if map_df.empty:
        # Return empty map centred on Indonesia
        return pdk.Deck(
            initial_view_state=pdk.ViewState(
                latitude=INDONESIA_CENTRE["latitude"],
                longitude=INDONESIA_CENTRE["longitude"],
                zoom=DEFAULT_ZOOM,
                pitch=0,
            ),
            map_provider="carto",
            map_style="light",
        )

    scatter_layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        get_position=[COL_LON, COL_LAT],
        get_radius="radius",
        get_fill_color="color",
        get_line_color=[255, 255, 255, 100],
        line_width_min_pixels=1,
        pickable=True,
        auto_highlight=True,
        opacity=0.8,
    )

    tooltip = {
        "html": (
            "<div style='font-family: Inter, sans-serif; font-size: 12px; "
            "background: rgba(255,255,255,0.95); padding: 10px; "
            "border-radius: 6px; border: 1px solid #e5e7eb; "
            "box-shadow: 0 2px 8px rgba(0,0,0,0.12);'>"
            "<b style='font-size: 14px; color: #111827;'>M{mag_str}</b>"
            "<br><span style='color:#6B7280;'>{waktu_wib}</span>"
            "<br><b>Kedalaman:</b> {depth_str}"
            f"<br><b>Wilayah:</b> {{{COL_REGION}}}"
            f"<br><b>Status:</b> {{{COL_TSUNAMI}}}"
            "</div>"
        ),
        "style": {"background": "none", "border": "none"},
    }

    view_state = pdk.ViewState(
        latitude=INDONESIA_CENTRE["latitude"],
        longitude=INDONESIA_CENTRE["longitude"],
        zoom=DEFAULT_ZOOM,
        pitch=0,
    )

    return pdk.Deck(
        layers=[scatter_layer],
        initial_view_state=view_state,
        map_provider="carto",
        map_style="light",
        tooltip=tooltip,
    )


def get_map_legend_html() -> str:
    """Return HTML for a simple map legend."""
    return """
    <div style="
        display: flex; gap: 16px; flex-wrap: wrap;
        font-family: Inter, sans-serif; font-size: 12px;
        color: #6B7280; margin-top: 4px;
    ">
        <span>
            <span style="display:inline-block; width:12px; height:12px;
                border-radius:50%; background:#1D6FA4; margin-right:5px;
                vertical-align:middle;"></span>
            Tidak Berpotensi
        </span>
        <span>
            <span style="display:inline-block; width:12px; height:12px;
                border-radius:50%; background:#DC2626; margin-right:5px;
                vertical-align:middle;"></span>
            Berpotensi Tsunami
        </span>
        <span>
            <span style="display:inline-block; width:12px; height:12px;
                border-radius:50%; background:#9CA3AF; margin-right:5px;
                vertical-align:middle;"></span>
            Status Tidak Diketahui
        </span>
        <span style="margin-left: 8px; color:#9CA3AF;">
            Ukuran lingkaran &prop; Magnitudo
        </span>
    </div>
    """
