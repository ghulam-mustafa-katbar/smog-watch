"""UI Components and visualization helpers for Smog Watch.

Provides custom CSS, interactive Plotly time-series charts, national comparison
charts, geographic map plotting, and health advisory display panels.
"""
from typing import Dict, Any, List, Optional
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

from src.config import POLLUTANT_METADATA, PAKISTAN_CITIES


def inject_custom_css() -> None:
    """Inject responsive, high-contrast custom CSS for the dashboard."""
    st.markdown("""
    <style>
        /* Modern Clean Styling */
        .main-header {
            font-size: 2.2rem;
            font-weight: 700;
            color: #1A365D;
            margin-bottom: 0.2rem;
        }
        .sub-header {
            font-size: 1.1rem;
            color: #4A5568;
            margin-bottom: 1.5rem;
        }
        .metric-card {
            background-color: #FFFFFF;
            border-radius: 10px;
            padding: 1.2rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
            border-left: 6px solid #4A5568;
            margin-bottom: 1rem;
            transition: transform 0.2s;
        }
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.08);
        }
        .status-badge {
            display: inline-block;
            padding: 0.25rem 0.6rem;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            color: #FFFFFF;
        }
        .pollutant-chip {
            background-color: #EDF2F7;
            padding: 0.3rem 0.6rem;
            border-radius: 6px;
            font-size: 0.9rem;
            display: inline-block;
            margin-right: 0.4rem;
            margin-bottom: 0.4rem;
        }
        .advisory-box {
            background-color: #F7FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 1rem;
            margin-top: 1rem;
        }
        .timestamp-footer {
            font-size: 0.8rem;
            color: #718096;
            margin-top: 2rem;
            text-align: center;
        }
    </style>
    """, unsafe_allow_html=True)


def render_header() -> None:
    """Render application banner and title."""
    st.markdown('<div class="main-header">🌫️ Smog Watch Pakistan</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Live Atmospheric Telemetry & Air Quality Index Monitoring '
        'across Pakistan’s Major Urban Centers</div>',
        unsafe_allow_html=True
    )


def render_national_kpis(summary: Dict[str, Any]) -> None:
    """Render top summary metrics across reporting stations."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Active Stations",
            value=f"{summary.get('reporting_count', 0)} / {summary.get('total_stations', 0)}",
            delta=f"{summary.get('reporting_percentage', 0)}% Online"
        )
    with col2:
        avg_val = summary.get("average_aqi")
        st.metric(
            label="National Avg AQI",
            value=f"{avg_val}" if avg_val is not None else "N/A"
        )
    with col3:
        st.metric(
            label="Most Polluted City",
            value=summary.get("worst_city") or "N/A",
            delta=f"AQI {summary.get('worst_aqi')}" if summary.get("worst_aqi") is not None else None,
            delta_color="inverse"
        )
    with col4:
        st.metric(
            label="Cleanest Air Quality",
            value=summary.get("cleanest_city") or "N/A",
            delta=f"AQI {summary.get('cleanest_aqi')}" if summary.get("cleanest_aqi") is not None else None,
            delta_color="normal"
        )


def render_city_card(city_data: Dict[str, Any]) -> None:
    """Render detailed card for a single city's telemetry."""
    city_name = city_data.get("city", "Unknown")
    status = city_data.get("status")
    aqi = city_data.get("aqi")
    category = city_data.get("category", {})
    color = category.get("color", "#6C757D")
    badge = category.get("badge", "⚪ Unavailable")
    pollutants = city_data.get("pollutants", {})

    st.markdown(f"""
    <div class="metric-card" style="border-left-color: {color};">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h3 style="margin: 0; color: #1A202C;">{city_name}</h3>
            <span class="status-badge" style="background-color: {color};">{badge}</span>
        </div>
        <div style="margin-top: 0.8rem;">
            <span style="font-size: 2.2rem; font-weight: 700; color: {color};">
                {aqi if aqi is not None else 'N/A'}
            </span>
            <span style="font-size: 1rem; color: #718096; margin-left: 0.4rem;">US AQI</span>
        </div>
        <p style="font-size: 0.9rem; color: #4A5568; margin-top: 0.4rem;">
            {category.get('health_statement', '')}
        </p>
    </div>
    """, unsafe_allow_html=True)

    if status == "error":
        st.error(f"⚠️ {city_data.get('error_message', 'Telemetry offline')}")


def render_hourly_trend_chart(hourly_series: Optional[Dict[str, list]], city_name: str) -> None:
    """Render interactive Plotly line chart of past 24h and next 24h AQI and PM2.5."""
    if not hourly_series or not hourly_series.get("time"):
        st.info("No historical or forecast trend series available for this location.")
        return

    df = pd.DataFrame({
        "time": pd.to_datetime(hourly_series["time"]),
        "pm2_5": hourly_series.get("pm2_5", []),
        "us_aqi": hourly_series.get("us_aqi", [])
    })

    fig = go.Figure()

    # AQI trace
    fig.add_trace(go.Scatter(
        x=df["time"],
        y=df["us_aqi"],
        mode="lines+markers",
        name="US AQI",
        line=dict(color="#D97706", width=2.5),
        marker=dict(size=4)
    ))

    # PM2.5 trace
    fig.add_trace(go.Scatter(
        x=df["time"],
        y=df["pm2_5"],
        mode="lines",
        name="PM2.5 (µg/m³)",
        line=dict(color="#DC2626", width=1.8, dash="dot"),
        yaxis="y2"
    ))

    # Threshold horizontal reference lines
    fig.add_hline(y=50, line_dash="dash", line_color="#00E400", annotation_text="Good (50)")
    fig.add_hline(y=100, line_dash="dash", line_color="#EAB308", annotation_text="Moderate (100)")
    fig.add_hline(y=150, line_dash="dash", line_color="#F97316", annotation_text="Unhealthy for Sensitive (150)")
    fig.add_hline(y=200, line_dash="dash", line_color="#EF4444", annotation_text="Unhealthy (200)")
    fig.add_hline(y=300, line_dash="dash", line_color="#8B5CF6", annotation_text="Hazardous (300)")

    fig.update_layout(
        title=f"48-Hour AQI & PM2.5 Telemetry Trend ({city_name})",
        xaxis_title="Time (Asia/Karachi)",
        yaxis=dict(title="US AQI Index"),
        yaxis2=dict(
            title="PM2.5 Concentration (µg/m³)",
            overlaying="y",
            side="right"
        ),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=50, b=40),
        height=380
    )

    st.plotly_chart(fig, use_container_width=True)


def render_comparison_bar_chart(ranked_cities: List[Dict[str, Any]]) -> None:
    """Render horizontal bar chart comparing Pakistani cities ranked by AQI."""
    valid = [c for c in ranked_cities if c.get("is_reporting") and c.get("aqi") is not None]
    if not valid:
        st.warning("No reporting cities available for comparison.")
        return

    df = pd.DataFrame(valid)
    df = df.sort_values(by="aqi", ascending=True)

    fig = px.bar(
        df,
        x="aqi",
        y="city",
        orientation="h",
        color="category",
        color_discrete_map={
            "Good": "#00E400",
            "Moderate": "#FFFF00",
            "Unhealthy for Sensitive Groups": "#FF7E00",
            "Unhealthy": "#FF0000",
            "Very Unhealthy": "#8F3F97",
            "Hazardous": "#7E0023",
            "Beyond Index / Severe Hazard": "#4A0012"
        },
        text="aqi",
        title="Live AQI Comparison Across Pakistani Urban Centers"
    )

    fig.update_layout(
        xaxis_title="Air Quality Index (US EPA Standard)",
        yaxis_title="City",
        height=320,
        margin=dict(l=20, r=20, t=40, b=20)
    )

    st.plotly_chart(fig, use_container_width=True)


def render_city_map(city_data_map: Dict[str, Dict[str, Any]]) -> None:
    """Render geographic map with color-coded AQI pins across Pakistan."""
    map_data = []
    for name, data in city_data_map.items():
        meta = PAKISTAN_CITIES.get(name)
        if not meta:
            continue

        aqi = data.get("aqi")
        status = data.get("status")
        color = data.get("category", {}).get("color", "#6C757D")

        map_data.append({
            "city": name,
            "latitude": meta["latitude"],
            "longitude": meta["longitude"],
            "aqi": aqi if aqi is not None else 0,
            "status": "Online" if status == "success" else "Offline",
            "color": color
        })

    if not map_data:
        return

    df_map = pd.DataFrame(map_data)
    st.map(df_map, latitude="latitude", longitude="longitude", size=20)


def render_advisory_panel(category: Dict[str, Any]) -> None:
    """Render structured public health advisory for the selected smog level."""
    adv = category.get("advisory", {})
    color = category.get("color", "#4A5568")

    st.markdown(f"""
    <div class="advisory-box" style="border-left: 5px solid {color};">
        <h4 style="margin-top: 0; color: #2D3748;">📋 Public Health & Smog Advisory</h4>
        <p><strong>General Population:</strong> {adv.get('general', 'No advisory available.')}</p>
        <p><strong>Sensitive Groups (Elderly, Children, Asthmatics):</strong> {adv.get('sensitive', 'No advisory available.')}</p>
        <div style="margin-top: 0.6rem;">
            <span class="pollutant-chip">😷 <strong>N95 Mask:</strong> {'Required Outdoors' if adv.get('mask_recommended') else 'Optional'}</span>
            <span class="pollutant-chip">🏠 <strong>HEPA Air Purifier:</strong> {'Recommended' if adv.get('air_purifier_recommended') else 'Not critical'}</span>
            <span class="pollutant-chip">🏃 <strong>Outdoor Exertion:</strong> {adv.get('outdoor_exercise', 'Safe')}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
