"""
charts.py
---------
Plotly chart components for the Indonesia Earthquake Monitor dashboard.
All functions accept a pre-filtered pd.DataFrame and return a Plotly Figure.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.analysis import events_per_day, regional_frequency, tsunami_breakdown
from src.data_processing import COL_DEPTH, COL_MAG, COL_REGION, COL_TSUNAMI

# ---------------------------------------------------------------------------
# Design tokens (restrained, data-analyst palette)
# ---------------------------------------------------------------------------

PRIMARY = "#1D6FA4"
ACCENT = "#E05C2D"
MUTED = "#6B7280"
GRID = "rgba(200,200,200,0.2)"
BG = "rgba(0,0,0,0)"         # transparent – inherits from Streamlit theme

FONT_FAMILY = "Inter, system-ui, sans-serif"

BASE_LAYOUT = dict(
    paper_bgcolor=BG,
    plot_bgcolor=BG,
    font=dict(family=FONT_FAMILY, size=12, color="#374151"),
    margin=dict(l=20, r=20, t=40, b=20),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
        bgcolor="rgba(255,255,255,0.6)",
        bordercolor="rgba(0,0,0,0.1)",
        borderwidth=1,
    ),
)

AXIS_STYLE = dict(
    gridcolor=GRID,
    showline=True,
    linecolor="rgba(200,200,200,0.4)",
    zeroline=False,
)


def _apply_base(fig: go.Figure, title: str = "") -> go.Figure:
    """Apply shared layout settings to a figure."""
    fig.update_layout(**BASE_LAYOUT, title=dict(text=title, font=dict(size=14, color="#111827")))
    fig.update_xaxes(**AXIS_STYLE)
    fig.update_yaxes(**AXIS_STYLE)
    return fig


# ---------------------------------------------------------------------------
# Chart 1 – Activity over time
# ---------------------------------------------------------------------------

def chart_activity_over_time(df: pd.DataFrame) -> go.Figure:
    """Bar chart of earthquake events per day."""
    daily = events_per_day(df)

    if daily.empty:
        fig = go.Figure()
        fig.add_annotation(text="Tidak ada data", showarrow=False,
                           xref="paper", yref="paper", x=0.5, y=0.5)
        return _apply_base(fig, "Aktivitas Gempa per Hari")

    fig = go.Figure(
        go.Bar(
            x=daily["date"],
            y=daily["count"],
            marker_color=PRIMARY,
            hovertemplate="<b>%{x|%d %b %Y}</b><br>Jumlah: %{y}<extra></extra>",
        )
    )
    fig.update_xaxes(tickformat="%d %b")
    fig.update_yaxes(title_text="Jumlah Kejadian")
    return _apply_base(fig, "Aktivitas Gempa per Hari")


# ---------------------------------------------------------------------------
# Chart 2 – Magnitude distribution
# ---------------------------------------------------------------------------

def chart_magnitude_distribution(df: pd.DataFrame) -> go.Figure:
    """Histogram of earthquake magnitudes."""
    if df.empty or df[COL_MAG].dropna().empty:
        fig = go.Figure()
        fig.add_annotation(text="Tidak ada data", showarrow=False,
                           xref="paper", yref="paper", x=0.5, y=0.5)
        return _apply_base(fig, "Distribusi Magnitudo")

    fig = px.histogram(
        df,
        x=COL_MAG,
        nbins=20,
        color_discrete_sequence=[PRIMARY],
        labels={COL_MAG: "Magnitudo"},
        opacity=0.85,
    )
    fig.update_traces(
        hovertemplate="Magnitudo: %{x}<br>Jumlah: %{y}<extra></extra>"
    )
    fig.update_yaxes(title_text="Jumlah Kejadian")
    fig.update_xaxes(title_text="Magnitudo")
    return _apply_base(fig, "Distribusi Magnitudo")


# ---------------------------------------------------------------------------
# Chart 3 – Regional activity (top 10)
# ---------------------------------------------------------------------------

def chart_regional_activity(df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """Horizontal bar chart of top N most active regions."""
    regional = regional_frequency(df, top_n=top_n)

    if regional.empty:
        fig = go.Figure()
        fig.add_annotation(text="Tidak ada data", showarrow=False,
                           xref="paper", yref="paper", x=0.5, y=0.5)
        return _apply_base(fig, f"Top {top_n} Wilayah Paling Aktif")

    # Truncate long region strings for readability
    regional["region_short"] = regional["region"].str[:55]

    fig = go.Figure(
        go.Bar(
            x=regional["count"],
            y=regional["region_short"],
            orientation="h",
            marker_color=PRIMARY,
            hovertext=regional["region"],
            hovertemplate="<b>%{hovertext}</b><br>Jumlah: %{x}<extra></extra>",
        )
    )
    fig.update_layout(yaxis=dict(autorange="reversed"))
    fig.update_xaxes(title_text="Jumlah Kejadian")
    return _apply_base(fig, f"Top {top_n} Wilayah Paling Aktif")


# ---------------------------------------------------------------------------
# Chart 4 – Depth distribution
# ---------------------------------------------------------------------------

def chart_depth_distribution(df: pd.DataFrame) -> go.Figure:
    """Histogram of earthquake depths."""
    if df.empty or df[COL_DEPTH].dropna().empty:
        fig = go.Figure()
        fig.add_annotation(text="Tidak ada data", showarrow=False,
                           xref="paper", yref="paper", x=0.5, y=0.5)
        return _apply_base(fig, "Distribusi Kedalaman")

    fig = px.histogram(
        df,
        x=COL_DEPTH,
        nbins=20,
        color_discrete_sequence=[ACCENT],
        labels={COL_DEPTH: "Kedalaman (km)"},
        opacity=0.85,
    )
    fig.update_traces(
        hovertemplate="Kedalaman: %{x} km<br>Jumlah: %{y}<extra></extra>"
    )
    fig.update_yaxes(title_text="Jumlah Kejadian")
    fig.update_xaxes(title_text="Kedalaman (km)")
    return _apply_base(fig, "Distribusi Kedalaman Gempa")


# ---------------------------------------------------------------------------
# Chart 5 – Tsunami status breakdown (pie/donut)
# ---------------------------------------------------------------------------

def chart_tsunami_status(df: pd.DataFrame) -> go.Figure:
    """Donut chart showing tsunami status breakdown."""
    breakdown = tsunami_breakdown(df)

    if breakdown.empty:
        fig = go.Figure()
        fig.add_annotation(text="Tidak ada data", showarrow=False,
                           xref="paper", yref="paper", x=0.5, y=0.5)
        return _apply_base(fig, "Status Potensi Tsunami")

    color_map = {
        "Berpotensi Tsunami": "#DC2626",
        "Tidak Berpotensi": "#16A34A",
        "Tidak diketahui": "#9CA3AF",
    }
    colors = [color_map.get(s, MUTED) for s in breakdown["status"]]

    fig = go.Figure(
        go.Pie(
            labels=breakdown["status"],
            values=breakdown["count"],
            hole=0.50,
            marker_colors=colors,
            hovertemplate="<b>%{label}</b><br>Jumlah: %{value} (%{percent})<extra></extra>",
        )
    )
    return _apply_base(fig, "Status Potensi Tsunami")


# ---------------------------------------------------------------------------
# Chart 6 – Magnitude vs Depth scatter
# ---------------------------------------------------------------------------

def chart_mag_vs_depth(df: pd.DataFrame) -> go.Figure:
    """Scatter plot of Magnitude vs Depth."""
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Tidak ada data", showarrow=False,
                           xref="paper", yref="paper", x=0.5, y=0.5)
        return _apply_base(fig, "Magnitudo vs Kedalaman")

    color_map = {
        "Berpotensi Tsunami": "#DC2626",
        "Tidak Berpotensi": "#1D6FA4",
        "Tidak diketahui": "#9CA3AF",
    }

    fig = px.scatter(
        df.dropna(subset=[COL_MAG, COL_DEPTH]),
        x=COL_MAG,
        y=COL_DEPTH,
        color=COL_TSUNAMI,
        color_discrete_map=color_map,
        opacity=0.75,
        labels={
            COL_MAG: "Magnitudo",
            COL_DEPTH: "Kedalaman (km)",
            COL_TSUNAMI: "Status Tsunami",
        },
        hover_data={COL_REGION: True},
    )
    fig.update_yaxes(autorange="reversed", title_text="Kedalaman (km)")
    fig.update_xaxes(title_text="Magnitudo")
    return _apply_base(fig, "Magnitudo vs Kedalaman")
