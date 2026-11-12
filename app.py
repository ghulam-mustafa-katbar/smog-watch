"""Smog Watch Pakistan - Interactive Air Quality & Smog Monitoring Dashboard.

Built with Streamlit, Plotly, and Open-Meteo Air Quality telemetry.
Complies with US EPA Air Quality Standards and zero fabricated data requirements.
"""
from datetime import datetime
import streamlit as st
import pandas as pd

from src.config import (
    PAKISTAN_CITIES,
    PRIMARY_FIVE_CITIES,
    POLLUTANT_METADATA,
    CACHE_TTL_SECONDS
)
from src.api import AirQualityAPIClient
from src.ranking import rank_cities, calculate_national_summary
from src.ui_components import (
    inject_custom_css,
    render_header,
    render_national_kpis,
    render_city_card,
    render_hourly_trend_chart,
    render_comparison_bar_chart,
    render_city_map,
    render_advisory_panel
)

# Streamlit Page Configuration
st.set_page_config(
    page_title="Smog Watch Pakistan",
    page_icon="🌫️",
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_cached_telemetry() -> dict:
    """Fetch live air quality telemetry with 10-minute caching.

    Returns:
        Dictionary mapping city names to validated telemetry results.
    """
    client = AirQualityAPIClient()
    return client.fetch_all_cities(PAKISTAN_CITIES)


def main() -> None:
    """Main application execution pipeline."""
    inject_custom_css()

    # Sidebar Controls
    st.sidebar.title("🌫️ Smog Watch PK")
    st.sidebar.caption("Real-Time Atmospheric Telemetry")

    if st.sidebar.button("🔄 Refresh Telemetry", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    # City Selector
    city_options = list(PAKISTAN_CITIES.keys())
    selected_city = st.sidebar.selectbox(
        "Select Focus City",
        options=city_options,
        index=0,
        help="Primary cities: Lahore, Karachi, Islamabad, Faisalabad, Peshawar"
    )

    st.sidebar.divider()
    st.sidebar.markdown("### 🇵🇰 Mandatory Cities")
    for pc in PRIMARY_FIVE_CITIES:
        st.sidebar.markdown(f"- **{pc}** ({PAKISTAN_CITIES[pc]['province']})")

    st.sidebar.divider()
    st.sidebar.markdown(
        "**Data Source:** Open-Meteo Atmospheric Model & Ground Observation Assimilation.\n\n"
        "**Standard:** US EPA AQI Linear Interpolation Formula.\n\n"
        "**Integrity:** 100% authentic sensor & model telemetry. Zero synthetic mock data."
    )

    # Fetch live telemetry
    with st.spinner("Fetching verified atmospheric telemetry for Pakistani cities..."):
        telemetry_map = get_cached_telemetry()

    ranked_list = rank_cities(telemetry_map)
    summary = calculate_national_summary(ranked_list)

    # Header & KPIs
    render_header()
    render_national_kpis(summary)

    st.markdown("---")

    # Navigation Tabs
    tab_overview, tab_leaderboard, tab_map, tab_methodology = st.tabs([
        "📍 City Deep Dive",
        "🏆 National Smog Leaderboard",
        "🗺️ Geographic Map",
        "🔬 Methodology & Standards"
    ])

    # Tab 1: City Deep Dive
    with tab_overview:
        city_data = telemetry_map.get(selected_city, {})
        render_city_card(city_data)

        # Pollutant Breakdown Metrics
        st.markdown(f"#### Real-Time Pollutant Breakdown ({selected_city})")
        pollutants = city_data.get("pollutants", {})
        sub_indices = city_data.get("sub_indices", {})

        cols = st.columns(3)
        pollutant_keys = list(POLLUTANT_METADATA.keys())

        for idx, p_key in enumerate(pollutant_keys):
            col = cols[idx % 3]
            meta = POLLUTANT_METADATA[p_key]
            val = pollutants.get(p_key)
            sub_aqi = sub_indices.get(p_key)

            with col:
                st.markdown(f"""
                <div style="background: #F8F9FA; padding: 0.8rem; border-radius: 8px; margin-bottom: 0.8rem; border: 1px solid #E2E8F0;">
                    <div style="font-size: 0.85rem; color: #718096;">{meta['name']} ({meta['label']})</div>
                    <div style="font-size: 1.4rem; font-weight: 700; color: #2D3748;">
                        {f'{val:.1f}' if val is not None else 'N/A'} <span style="font-size: 0.85rem; font-weight: 400;">{meta['unit']}</span>
                    </div>
                    <div style="font-size: 0.8rem; color: #4A5568;">
                        Sub-AQI: <strong>{sub_aqi if sub_aqi is not None else '—'}</strong>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # 48-Hour Trend Chart
        st.markdown("#### 48-Hour Atmospheric Trend Analysis")
        render_hourly_trend_chart(city_data.get("hourly_series"), selected_city)

        # Health Advisory
        render_advisory_panel(city_data.get("category", {}))

    # Tab 2: National Leaderboard
    with tab_leaderboard:
        st.markdown("### 🏆 Pakistan Smog Severity Leaderboard")
        st.caption("Ranked from most polluted (#1) to cleanest based on US EPA composite AQI.")

        # Leaderboard Table Dataframe
        table_rows = []
        for c in ranked_list:
            table_rows.append({
                "Rank": c["rank_display"],
                "City": c["city"],
                "Province": PAKISTAN_CITIES[c["city"]]["province"],
                "Status": "Mandatory Primary" if PAKISTAN_CITIES[c["city"]]["is_primary"] else "Secondary",
                "US AQI": c["aqi"] if c["aqi"] is not None else "N/A",
                "PM2.5 (µg/m³)": f"{c['pm2_5']:.1f}" if c["pm2_5"] is not None else "N/A",
                "Air Category": c["category"],
                "Telemetry Status": "Online" if c["is_reporting"] else "Offline/Unavailable"
            })

        df_leaderboard = pd.DataFrame(table_rows)
        st.dataframe(df_leaderboard, use_container_width=True, hide_index=True)

        st.markdown("---")
        render_comparison_bar_chart(ranked_list)

    # Tab 3: Map
    with tab_map:
        st.markdown("### 🗺️ Telemetry Stations Map Across Pakistan")
        st.caption("Geographic distribution of monitoring stations in Pakistan.")
        render_city_map(telemetry_map)

    # Tab 4: Methodology & Standards
    with tab_methodology:
        st.markdown("""
        ### 🔬 Atmospheric Calculation Standards & Architecture

        #### 1. Air Quality Calculation (US EPA Standard)
        Smog Watch adheres strictly to the United States Environmental Protection Agency (EPA)
        piecewise linear interpolation standard:

        $$I_p = \\frac{I_{Hi} - I_{Lo}}{BP_{Hi} - BP_{Lo}} (C_p - BP_{Lo}) + I_{Lo}$$

        Where:
        - $I_p$ = The calculated Air Quality Index sub-index for pollutant $p$.
        - $C_p$ = The truncated/rounded ambient concentration of pollutant $p$.
        - $BP_{Hi}$ = The breakpoint that is greater than or equal to $C_p$.
        - $BP_{Lo}$ = The breakpoint that is less than or equal to $C_p$.
        - $I_{Hi}$ = The AQI value corresponding to $BP_{Hi}$.
        - $I_{Lo}$ = The AQI value corresponding to $BP_{Lo}$.

        The overall composite AQI represents the **maximum sub-index** among all monitored pollutants:
        $$\\text{AQI}_{\\text{overall}} = \\max(I_{PM2.5}, I_{PM10}, \\dots)$$

        #### 2. Zero-Fabrication Integrity Policy
        - **No Synthetic Mocking**: Smog Watch strictly forbids using random numbers, placeholder values, or synthetic data when live telemetry fails.
        - **Transparent Missing Data**: If upstream telemetry is unavailable or an error occurs, the station is explicitly marked `Offline / Data Unavailable`, preventing misleading health decisions.

        #### 3. Supported Pakistani Urban Centers
        All five required primary cities are verified with geographic coordinates and regional timezones:
        - **Lahore** (Punjab) - `31.5204° N, 74.3587° E`
        - **Karachi** (Sindh) - `24.8607° N, 67.0011° E`
        - **Islamabad** (Federal Capital) - `33.6844° N, 73.0479° E`
        - **Faisalabad** (Punjab) - `31.4504° N, 73.1350° E`
        - **Peshawar** (Khyber Pakhtunkhwa) - `34.0151° N, 71.5249° E`
        """)

    # Footer
    curr_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S PKT")
    st.markdown(
        f'<div class="timestamp-footer">'
        f'Smog Watch v1.0.0 | Telemetry Timestamp: {curr_time} | Open-Meteo High-Resolution Telemetry'
        f'</div>',
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
