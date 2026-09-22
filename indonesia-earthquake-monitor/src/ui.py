"""
ui.py
-----
Reusable Streamlit UI components for the Indonesia Earthquake Monitor.

Components
~~~~~~~~~~
- render_header()              - page title, timestamps, attribution
- render_kpi_cards()           - 4-column KPI metrics row
- render_sidebar_filters()     - sidebar filter controls
- render_latest_earthquakes()  - latest events table section
- render_data_table()          - full filterable data table
- render_no_data_message()     - graceful empty-state display
- render_error_message()       - BMKG fetch error display
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.analysis import compute_summary
from src.data_processing import COL_DATETIME, COL_MAG, get_display_df


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

def render_header(last_updated: str) -> None:
    """Render the dashboard title and metadata bar."""
    st.markdown(
        """
        <div style="
            border-bottom: 2px solid #E5E7EB;
            padding-bottom: 12px;
            margin-bottom: 8px;
        ">
            <h1 style="
                font-family: Inter, system-ui, sans-serif;
                font-size: 1.75rem;
                font-weight: 700;
                color: #111827;
                margin: 0;
                letter-spacing: -0.02em;
            ">Indonesia Earthquake Monitor</h1>
            <p style="
                font-family: Inter, system-ui, sans-serif;
                font-size: 0.82rem;
                color: #6B7280;
                margin: 4px 0 0 0;
            ">Data terbaru BMKG (Badan Meteorologi, Klimatologi, dan Geofisika)</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        st.caption(f"Terakhir diperbarui: {last_updated}")
    with col2:
        st.caption("Sumber: [BMKG](https://www.bmkg.go.id)")


# ---------------------------------------------------------------------------
# KPI Cards
# ---------------------------------------------------------------------------

def _kpi_card(label: str, value: str, sub: str = "", color: str = "#1D6FA4") -> str:
    """Return HTML string for a single KPI card."""
    return f"""
    <div style="
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-top: 3px solid {color};
        border-radius: 6px;
        padding: 16px 18px;
        font-family: Inter, system-ui, sans-serif;
    ">
        <div style="font-size: 0.75rem; font-weight: 600; color: #6B7280;
                    text-transform: uppercase; letter-spacing: 0.05em;">
            {label}
        </div>
        <div style="font-size: 2rem; font-weight: 700; color: #111827;
                    margin: 6px 0 2px; line-height: 1.1;">
            {value}
        </div>
        <div style="font-size: 0.78rem; color: #9CA3AF;">{sub}</div>
    </div>
    """


def render_kpi_cards(df: pd.DataFrame) -> None:
    """Render the 4-column KPI metric cards row."""
    summary = compute_summary(df)

    total = summary["total_events"]
    max_mag = summary["max_magnitude"]
    avg_depth = summary["avg_depth"]
    tsunami = summary["tsunami_events"]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            _kpi_card(
                "Total Kejadian",
                str(total) if total else "–",
                "gempa tercatat",
                "#1D6FA4",
            ),
            unsafe_allow_html=True,
        )

    with col2:
        mag_str = f"M {max_mag:.1f}" if max_mag is not None else "–"
        st.markdown(
            _kpi_card(
                "Magnitudo Terbesar",
                mag_str,
                f"rata-rata M {summary['avg_magnitude']:.1f}" if summary["avg_magnitude"] else "",
                "#B45309",
            ),
            unsafe_allow_html=True,
        )

    with col3:
        depth_str = f"{avg_depth:.0f} km" if avg_depth is not None else "–"
        depth_range = ""
        if summary["min_depth"] is not None and summary["max_depth"] is not None:
            depth_range = f"min {summary['min_depth']:.0f} – maks {summary['max_depth']:.0f} km"
        st.markdown(
            _kpi_card(
                "Rata-rata Kedalaman",
                depth_str,
                depth_range,
                "#0F766E",
            ),
            unsafe_allow_html=True,
        )

    with col4:
        tsunami_str = str(tsunami) if total else "–"
        pct = f"{tsunami / total * 100:.0f}% dari total" if total else ""
        card_color = "#DC2626" if tsunami > 0 else "#16A34A"
        st.markdown(
            _kpi_card(
                "Berpotensi Tsunami",
                tsunami_str,
                pct,
                card_color,
            ),
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Sidebar Filters
# ---------------------------------------------------------------------------

def render_sidebar_filters(df: pd.DataFrame) -> dict:
    """
    Render sidebar filter controls.

    Returns a dict of filter values:
      {
        'min_magnitude': float,
        'date_start': pd.Timestamp or None,
        'date_end': pd.Timestamp or None,
        'tsunami_filter': str,
      }
    """
    st.sidebar.markdown(
        "<h3 style='font-family: Inter, sans-serif; font-size: 0.95rem;"
        "font-weight: 600; color: #111827; margin-bottom: 4px;'>Filter Data</h3>",
        unsafe_allow_html=True,
    )

    # ---- Magnitude slider ----
    mag_min_global = 0.0
    mag_max_global = 10.0
    if not df.empty and not df[COL_MAG].dropna().empty:
        mag_min_global = float(df[COL_MAG].min())
        mag_max_global = float(df[COL_MAG].max())

    min_magnitude = st.sidebar.slider(
        "Magnitudo minimum",
        min_value=0.0,
        max_value=10.0,
        value=0.0,
        step=0.1,
        format="%.1f",
        help="Tampilkan hanya gempa dengan magnitudo >= nilai ini",
    )

    # ---- Date range ----
    st.sidebar.markdown("**Rentang tanggal**")

    if not df.empty and not df[COL_DATETIME].dropna().empty:
        dt_min = df[COL_DATETIME].min()
        dt_max = df[COL_DATETIME].max()
        try:
            dt_min_local = dt_min.tz_convert("Asia/Jakarta")
            dt_max_local = dt_max.tz_convert("Asia/Jakarta")
            d_min = dt_min_local.date()
            d_max = dt_max_local.date()
        except Exception:
            d_min = pd.Timestamp.now().date()
            d_max = pd.Timestamp.now().date()
    else:
        import datetime
        d_max = pd.Timestamp.now().date()
        d_min = d_max

    date_start = st.sidebar.date_input(
        "Dari",
        value=d_min,
        min_value=d_min,
        max_value=d_max,
        key="date_start",
    )
    date_end = st.sidebar.date_input(
        "Sampai",
        value=d_max,
        min_value=d_min,
        max_value=d_max,
        key="date_end",
    )

    # Convert date -> UTC Timestamp for apply_filters
    ts_start = pd.Timestamp(date_start, tz="Asia/Jakarta") if date_start else None
    ts_end = pd.Timestamp(date_end, tz="Asia/Jakarta") if date_end else None

    # ---- Tsunami status ----
    tsunami_options = ["Semua", "Berpotensi Tsunami", "Tidak Berpotensi", "Tidak diketahui"]
    tsunami_filter = st.sidebar.selectbox(
        "Status tsunami",
        options=tsunami_options,
        index=0,
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "<div style='font-size:0.75rem; color:#9CA3AF; font-family: Inter, sans-serif;'>"
        "Data diambil dari endpoint resmi BMKG:<br>"
        "<code>data.bmkg.go.id/DataMKG/TEWS/</code>"
        "</div>",
        unsafe_allow_html=True,
    )

    return {
        "min_magnitude": min_magnitude,
        "date_start": ts_start,
        "date_end": ts_end,
        "tsunami_filter": tsunami_filter,
    }


# ---------------------------------------------------------------------------
# Latest Earthquakes
# ---------------------------------------------------------------------------

def render_latest_earthquakes(df: pd.DataFrame, n: int = 10) -> None:
    """Render a clean table of the most recent n earthquakes."""
    st.markdown(
        "<h3 style='font-family: Inter, sans-serif; font-size: 1rem; "
        "font-weight: 600; color: #111827; margin-bottom: 4px;'>"
        "Gempa Terbaru</h3>",
        unsafe_allow_html=True,
    )

    if df.empty:
        st.info("Tidak ada data gempa untuk ditampilkan.")
        return

    recent = df.head(n).copy()
    display = get_display_df(recent)

    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
    )


# ---------------------------------------------------------------------------
# Full Data Table
# ---------------------------------------------------------------------------

def render_data_table(df: pd.DataFrame) -> None:
    """Render the full filtered data table."""
    st.markdown(
        "<h3 style='font-family: Inter, sans-serif; font-size: 1rem; "
        "font-weight: 600; color: #111827; margin-bottom: 4px;'>"
        "Tabel Data Lengkap</h3>",
        unsafe_allow_html=True,
    )

    if df.empty:
        st.info("Tidak ada data yang sesuai dengan filter yang dipilih.")
        return

    display = get_display_df(df)

    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
    )
    st.caption(f"Menampilkan {len(df)} kejadian gempa.")


# ---------------------------------------------------------------------------
# Error / No-data states
# ---------------------------------------------------------------------------

def render_no_data_message() -> None:
    """Display when the filtered result set is empty."""
    st.warning(
        "Tidak ada data gempa yang sesuai dengan filter yang dipilih. "
        "Coba perluas rentang tanggal atau kurangi magnitudo minimum."
    )


def render_error_message(error: str) -> None:
    """Display a friendly error when BMKG data cannot be fetched."""
    st.error(
        f"**Gagal mengambil data BMKG.**\n\n{error}\n\n"
        "Pastikan koneksi internet tersedia dan coba lagi dalam beberapa menit. "
        "Jika masalah berlanjut, periksa status layanan BMKG di "
        "[data.bmkg.go.id](https://data.bmkg.go.id)."
    )


def render_section_divider(title: str) -> None:
    """Render a labelled section divider."""
    st.markdown(
        f"""
        <div style="
            display: flex; align-items: center; gap: 12px;
            margin: 24px 0 12px;
        ">
            <div style="
                flex: 1; height: 1px;
                background: linear-gradient(to right, #E5E7EB, transparent);
            "></div>
            <span style="
                font-family: Inter, sans-serif;
                font-size: 0.75rem;
                font-weight: 600;
                color: #9CA3AF;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                white-space: nowrap;
            ">{title}</span>
            <div style="
                flex: 1; height: 1px;
                background: linear-gradient(to left, #E5E7EB, transparent);
            "></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
