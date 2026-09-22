"""
app.py
------
Indonesia Earthquake Monitor — main Streamlit application.

Run with:
    streamlit run app.py

Architecture:
  bmkg_api.py        -> fetch & cache raw BMKG JSON
  data_processing.py -> normalise to DataFrame, apply filters
  analysis.py        -> compute KPI metrics
  charts.py          -> Plotly chart figures
  map.py             -> PyDeck earthquake map
  ui.py              -> Streamlit UI components
"""

from __future__ import annotations

import time

import pandas as pd
import streamlit as st

from src.bmkg_api import (
    clear_cache,
    fetch_all_earthquakes,
    get_fetch_timestamp,
)
from src.charts import (
    chart_activity_over_time,
    chart_depth_distribution,
    chart_mag_vs_depth,
    chart_magnitude_distribution,
    chart_regional_activity,
    chart_tsunami_status,
)
from src.data_processing import apply_filters, build_master_dataframe
from src.map import build_earthquake_map, get_map_legend_html
from src.ui import (
    render_data_table,
    render_error_message,
    render_header,
    render_kpi_cards,
    render_latest_earthquakes,
    render_no_data_message,
    render_section_divider,
    render_sidebar_filters,
)

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Indonesia Earthquake Monitor",
    page_icon="🌏",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": (
            "**Indonesia Earthquake Monitor**\n\n"
            "Dashboard analitik gempa bumi Indonesia berbasis data resmi BMKG.\n\n"
            "Data source: [BMKG](https://www.bmkg.go.id)"
        )
    },
)

# ---------------------------------------------------------------------------
# Global CSS overrides
# ---------------------------------------------------------------------------

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Prevent horizontal overflow */
    html, body, .stApp {
        font-family: 'Inter', system-ui, sans-serif;
        overflow-x: hidden;
    }

    /* Clean sidebar */
    section[data-testid="stSidebar"] {
        background-color: #F9FAFB;
        border-right: 1px solid #E5E7EB;
    }

    /* Remove extra Streamlit top padding and set responsive container margins */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 100%;
    }

    /* Metric / card spacing */
    div[data-testid="column"] > div {
        height: 100%;
    }

    /* Tighten up tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        border-bottom: 2px solid #E5E7EB;
        overflow-x: auto;
        white-space: nowrap;
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        font-weight: 500;
        color: #6B7280;
        padding: 8px 16px;
        border-radius: 4px 4px 0 0;
        border: none;
        background: transparent;
    }
    .stTabs [aria-selected="true"] {
        color: #1D6FA4 !important;
        border-bottom: 2px solid #1D6FA4;
        background: transparent;
    }

    /* Dataframe responsiveness */
    .stDataFrame {
        border: 1px solid #E5E7EB;
        border-radius: 6px;
        width: 100%;
        overflow-x: auto;
    }

    /* Mobile media queries */
    @media (max-width: 768px) {
        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
            padding-top: 1rem;
        }

        /* Adjust KPI card margins when stacked */
        div[data-testid="column"] {
            margin-bottom: 8px;
        }

        /* Touch target sizing for interactive elements */
        button, input, select {
            min-height: 42px;
        }

        /* Ensure PyDeck container fits mobile width */
        .stPyDeckChart {
            width: 100% !important;
            overflow: hidden;
        }

        /* Tabs scrolling on mobile */
        .stTabs [data-baseweb="tab-list"] {
            display: flex;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
        }
    }

    /* Hide Streamlit hamburger and footer for cleaner look */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------

if "last_fetch_time" not in st.session_state:
    st.session_state["last_fetch_time"] = 0.0

if "fetch_timestamp" not in st.session_state:
    st.session_state["fetch_timestamp"] = ""

# Auto-refresh interval (seconds)
AUTO_REFRESH_INTERVAL = 300  # 5 minutes


# ---------------------------------------------------------------------------
# Sidebar – refresh controls
# ---------------------------------------------------------------------------

st.sidebar.markdown(
    "<h2 style='font-family: Inter, sans-serif; font-size: 1.05rem; "
    "font-weight: 700; color: #111827; margin-bottom: 0;'>"
    "🌏 Indonesia EQ Monitor</h2>",
    unsafe_allow_html=True,
)
st.sidebar.markdown("---")

manual_refresh = st.sidebar.button(
    "🔄 Perbarui Data",
    use_container_width=True,
    help="Ambil data terbaru dari BMKG",
)

if manual_refresh:
    clear_cache()
    st.session_state["last_fetch_time"] = 0.0

# Auto-refresh check
now = time.time()
if now - st.session_state["last_fetch_time"] >= AUTO_REFRESH_INTERVAL:
    # Cache has already been cleared by TTL; just update timestamp
    st.session_state["last_fetch_time"] = now
    st.session_state["fetch_timestamp"] = get_fetch_timestamp()

if not st.session_state["fetch_timestamp"]:
    st.session_state["fetch_timestamp"] = get_fetch_timestamp()


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

with st.spinner("Mengambil data gempa dari BMKG..."):
    raw_records, fetch_error = fetch_all_earthquakes()

master_df = pd.DataFrame()
if raw_records:
    master_df = build_master_dataframe(raw_records)

# ---------------------------------------------------------------------------
# Sidebar Filters (requires master_df to know date bounds)
# ---------------------------------------------------------------------------

filters = render_sidebar_filters(master_df)

# Apply filters
filtered_df = apply_filters(
    master_df,
    min_magnitude=filters["min_magnitude"],
    date_start=filters["date_start"],
    date_end=filters["date_end"],
    tsunami_filter=filters["tsunami_filter"],
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

render_header(st.session_state["fetch_timestamp"])

# ---------------------------------------------------------------------------
# Error state
# ---------------------------------------------------------------------------

if fetch_error:
    render_error_message(fetch_error)
    st.stop()

if master_df.empty:
    render_error_message("Data BMKG berhasil diambil tetapi tidak mengandung rekaman gempa yang dapat diproses.")
    st.stop()

# ---------------------------------------------------------------------------
# KPI Cards
# ---------------------------------------------------------------------------

render_kpi_cards(filtered_df)

# ---------------------------------------------------------------------------
# Map section
# ---------------------------------------------------------------------------

render_section_divider("PETA GEMPA INTERAKTIF")

map_deck = build_earthquake_map(filtered_df)
st.pydeck_chart(map_deck, use_container_width=True)
st.markdown(get_map_legend_html(), unsafe_allow_html=True)

# Empty state below map
if filtered_df.empty:
    render_no_data_message()
    st.stop()

# ---------------------------------------------------------------------------
# Charts – tabbed layout
# ---------------------------------------------------------------------------

render_section_divider("ANALISIS DATA")

tab_time, tab_mag, tab_region, tab_depth, tab_scatter, tab_tsunami = st.tabs([
    "Aktivitas Waktu",
    "Distribusi Magnitudo",
    "Aktivitas Wilayah",
    "Distribusi Kedalaman",
    "Magnitudo vs Kedalaman",
    "Status Tsunami",
])

with tab_time:
    st.plotly_chart(
        chart_activity_over_time(filtered_df),
        use_container_width=True,
        config={"displayModeBar": False},
    )

with tab_mag:
    st.plotly_chart(
        chart_magnitude_distribution(filtered_df),
        use_container_width=True,
        config={"displayModeBar": False},
    )

with tab_region:
    st.plotly_chart(
        chart_regional_activity(filtered_df),
        use_container_width=True,
        config={"displayModeBar": False},
    )

with tab_depth:
    st.plotly_chart(
        chart_depth_distribution(filtered_df),
        use_container_width=True,
        config={"displayModeBar": False},
    )

with tab_scatter:
    st.plotly_chart(
        chart_mag_vs_depth(filtered_df),
        use_container_width=True,
        config={"displayModeBar": False},
    )

with tab_tsunami:
    col_pie, col_info = st.columns([1, 1])
    with col_pie:
        st.plotly_chart(
            chart_tsunami_status(filtered_df),
            use_container_width=True,
            config={"displayModeBar": False},
        )
    with col_info:
        st.markdown(
            """
            <div style="
                font-family: Inter, sans-serif;
                font-size: 0.85rem;
                color: #374151;
                padding: 16px;
                background: #F9FAFB;
                border: 1px solid #E5E7EB;
                border-radius: 6px;
                margin-top: 20px;
            ">
            <b>Catatan tentang status tsunami:</b><br><br>
            BMKG melaporkan potensi tsunami pada gempa-gempa tertentu melalui field
            <code>Potensi</code> di endpoint <em>gempaterkini</em>.
            Gempa yang dilaporkan melalui endpoint <em>gempadirasakan</em> (gempa dirasakan)
            umumnya tidak menyertakan informasi potensi tsunami.<br><br>
            Status <b>"Tidak diketahui"</b> bukan berarti berpotensi tsunami —
            melainkan informasi tersebut tidak tersedia dalam data yang dilaporkan BMKG
            untuk kejadian tersebut.
            </div>
            """,
            unsafe_allow_html=True,
        )

# ---------------------------------------------------------------------------
# Latest earthquakes
# ---------------------------------------------------------------------------

render_section_divider("GEMPA TERBARU")
render_latest_earthquakes(filtered_df, n=15)

# ---------------------------------------------------------------------------
# Full data table
# ---------------------------------------------------------------------------

render_section_divider("DATA LENGKAP")

with st.expander("Tampilkan tabel data lengkap", expanded=False):
    render_data_table(filtered_df)

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

st.markdown(
    """
    <div style="
        margin-top: 40px;
        padding-top: 16px;
        border-top: 1px solid #E5E7EB;
        font-family: Inter, sans-serif;
        font-size: 0.75rem;
        color: #9CA3AF;
        text-align: center;
    ">
        Data bersumber dari
        <a href="https://data.bmkg.go.id" target="_blank"
           style="color: #1D6FA4; text-decoration: none;">BMKG Open Data</a>
        &mdash; Badan Meteorologi, Klimatologi, dan Geofisika Republik Indonesia.
        Dashboard ini dibuat untuk tujuan analisis data dan portofolio.
        Data diperbarui setiap ±5 menit. Tidak disarankan untuk keputusan darurat.
    </div>
    """,
    unsafe_allow_html=True,
)
