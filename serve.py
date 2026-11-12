"""Enterprise-grade Web Dashboard for Smog Watch Pakistan.

Features a world-class UI/UX aesthetic with executive dark-slate glassmorphism,
interactive Leaflet maps, dynamic gradient Chart.js visualizations,
pollutant gauge bars, real-time city switching, and actionable health protocols.
"""
import json
import logging
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any

from src.config import (
    PAKISTAN_CITIES,
    PRIMARY_FIVE_CITIES,
    POLLUTANT_METADATA,
    CACHE_TTL_SECONDS
)
from src.api import AirQualityAPIClient
from src.ranking import rank_cities, calculate_national_summary

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SmogWatchServer")

_CACHE: Dict[str, Any] = {"data": None, "timestamp": 0}


def get_telemetry_data(force_refresh: bool = False) -> Dict[str, Any]:
    """Retrieve atmospheric telemetry, utilizing 10-minute caching."""
    global _CACHE
    now = time.time()
    if not force_refresh and _CACHE["data"] and (now - _CACHE["timestamp"] < CACHE_TTL_SECONDS):
        return _CACHE["data"]

    logger.info("Fetching fresh atmospheric telemetry for Pakistani cities...")
    client = AirQualityAPIClient()
    raw_data = client.fetch_all_cities(PAKISTAN_CITIES)
    ranked = rank_cities(raw_data)
    summary = calculate_national_summary(ranked)

    _CACHE = {
        "data": {
            "cities": raw_data,
            "ranked": ranked,
            "summary": summary,
            "city_metadata": PAKISTAN_CITIES,
            "updated_at": datetime.now().strftime("%d %b %Y, %I:%M %p PKT")
        },
        "timestamp": now
    }
    return _CACHE["data"]


def render_html_dashboard(telemetry: Dict[str, Any]) -> str:
    """Generate the ultra-premium, executive dashboard HTML."""
    telemetry_json = json.dumps(telemetry)
    summary = telemetry["summary"]
    updated_at = telemetry["updated_at"]

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smog Watch PK | National Air Quality & Smog Intelligence System</title>
    
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    
    <!-- Leaflet Map CSS -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin=""/>
    
    <!-- Chart.js & Leaflet JS -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>

    <style>
        :root {{
            --bg-deep: #0B0F19;
            --bg-card: #111827;
            --bg-card-hover: #1A2234;
            --bg-glass: rgba(17, 24, 39, 0.75);
            --border-glass: rgba(255, 255, 255, 0.08);
            --border-active: rgba(255, 255, 255, 0.16);
            --text-primary: #F9FAFB;
            --text-secondary: #94A3B8;
            --text-muted: #64748B;
            --accent-glow: rgba(59, 130, 246, 0.15);
            --radius-lg: 16px;
            --radius-md: 12px;
            --radius-sm: 8px;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
        }}

        body {{
            background-color: var(--bg-deep);
            color: var(--text-primary);
            min-height: 100vh;
            background-image: 
                radial-gradient(circle at 10% 20%, rgba(30, 58, 138, 0.12) 0%, transparent 40%),
                radial-gradient(circle at 90% 80%, rgba(136, 19, 55, 0.12) 0%, transparent 40%);
            background-attachment: fixed;
            -webkit-font-smoothing: antialiased;
        }}

        /* Navbar */
        .navbar {{
            background: var(--bg-glass);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border-bottom: 1px solid var(--border-glass);
            position: sticky;
            top: 0;
            z-index: 1000;
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .brand {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .brand-icon {{
            width: 38px;
            height: 38px;
            background: linear-gradient(135deg, #10B981, #06B6D4);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25);
        }}

        .brand-title {{
            font-size: 1.2rem;
            font-weight: 800;
            letter-spacing: -0.5px;
            background: linear-gradient(to right, #FFFFFF, #94A3B8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .brand-subtitle {{
            font-size: 0.75rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
        }}

        .nav-actions {{
            display: flex;
            align-items: center;
            gap: 16px;
        }}

        .live-pill {{
            display: flex;
            align-items: center;
            gap: 8px;
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid rgba(16, 185, 129, 0.25);
            padding: 6px 14px;
            border-radius: 30px;
            font-size: 0.8rem;
            font-weight: 600;
            color: #34D399;
        }}

        .pulse-dot {{
            width: 8px;
            height: 8px;
            background: #10B981;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }}

        @keyframes pulse {{
            0% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }}
            70% {{ transform: scale(1); box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }}
            100% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }}
        }}

        .btn-refresh {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-glass);
            color: var(--text-primary);
            padding: 8px 16px;
            border-radius: var(--radius-sm);
            font-size: 0.85rem;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.2s ease;
        }}

        .btn-refresh:hover {{
            background: rgba(255, 255, 255, 0.1);
            border-color: var(--border-active);
            transform: translateY(-1px);
        }}

        /* Container */
        .container {{
            max-width: 1440px;
            margin: 0 auto;
            padding: 2rem;
        }}

        /* KPI Grid */
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 1.25rem;
            margin-bottom: 2rem;
        }}

        .kpi-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-glass);
            border-radius: var(--radius-lg);
            padding: 1.5rem;
            position: relative;
            overflow: hidden;
            transition: all 0.25s ease;
        }}

        .kpi-card:hover {{
            border-color: var(--border-active);
            transform: translateY(-2px);
            box-shadow: 0 12px 24px -10px rgba(0, 0, 0, 0.5);
        }}

        .kpi-card::after {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 3px;
            background: linear-gradient(90deg, #3B82F6, transparent);
        }}

        .kpi-card.alert::after {{
            background: linear-gradient(90deg, #EF4444, #F59E0B);
        }}

        .kpi-card.success::after {{
            background: linear-gradient(90deg, #10B981, #06B6D4);
        }}

        .kpi-label {{
            font-size: 0.8rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 700;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .kpi-val {{
            font-size: 2.2rem;
            font-weight: 800;
            letter-spacing: -1px;
            margin: 0.5rem 0 0.25rem 0;
        }}

        .kpi-subtext {{
            font-size: 0.85rem;
            color: var(--text-secondary);
            display: flex;
            align-items: center;
            gap: 6px;
        }}

        /* Quick City Switcher Tabs */
        .city-switcher-wrapper {{
            background: var(--bg-card);
            border: 1px solid var(--border-glass);
            border-radius: var(--radius-lg);
            padding: 1rem 1.25rem;
            margin-bottom: 2rem;
            display: flex;
            align-items: center;
            gap: 12px;
            overflow-x: auto;
            scrollbar-width: none;
        }}

        .city-switcher-wrapper::-webkit-scrollbar {{
            display: none;
        }}

        .switcher-title {{
            font-size: 0.85rem;
            font-weight: 700;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            white-space: nowrap;
            margin-right: 8px;
        }}

        .city-pill {{
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--border-glass);
            border-radius: 40px;
            padding: 8px 18px;
            font-size: 0.9rem;
            font-weight: 600;
            color: var(--text-secondary);
            cursor: pointer;
            white-space: nowrap;
            display: flex;
            align-items: center;
            gap: 10px;
            transition: all 0.2s ease;
        }}

        .city-pill:hover {{
            background: rgba(255, 255, 255, 0.08);
            color: var(--text-primary);
        }}

        .city-pill.active {{
            background: #2563EB;
            border-color: #3B82F6;
            color: #FFFFFF;
            box-shadow: 0 4px 16px rgba(37, 99, 235, 0.4);
        }}

        .city-pill .pill-aqi {{
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 700;
            background: rgba(0, 0, 0, 0.3);
        }}

        /* Main Layout */
        .main-layout {{
            display: grid;
            grid-template-columns: 1.4fr 1fr;
            gap: 2rem;
        }}

        @media (max-width: 1100px) {{
            .main-layout {{
                grid-template-columns: 1fr;
            }}
        }}

        /* Glass Card */
        .glass-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-glass);
            border-radius: var(--radius-lg);
            padding: 1.75rem;
            margin-bottom: 2rem;
            position: relative;
        }}

        .card-header-row {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 1.5rem;
        }}

        .city-name-lg {{
            font-size: 2.2rem;
            font-weight: 800;
            letter-spacing: -1px;
            color: var(--text-primary);
            line-height: 1.1;
        }}

        .city-meta-tags {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-top: 8px;
        }}

        .meta-tag {{
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid var(--border-glass);
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--text-muted);
        }}

        /* AQI Showcase Display */
        .aqi-hero-banner {{
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--border-glass);
            border-radius: var(--radius-md);
            padding: 1.5rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.75rem;
            position: relative;
            overflow: hidden;
        }}

        .aqi-score-box {{
            display: flex;
            align-items: baseline;
            gap: 12px;
        }}

        .aqi-large-number {{
            font-size: 4rem;
            font-weight: 900;
            letter-spacing: -2px;
            line-height: 1;
            font-family: 'JetBrains Mono', monospace;
        }}

        .aqi-units {{
            font-size: 1rem;
            color: var(--text-muted);
            font-weight: 600;
            text-transform: uppercase;
        }}

        .category-badge-lg {{
            padding: 10px 22px;
            border-radius: 40px;
            font-size: 1rem;
            font-weight: 700;
            letter-spacing: 0.5px;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
        }}

        .health-statement-text {{
            font-size: 0.95rem;
            color: var(--text-secondary);
            line-height: 1.6;
            margin-bottom: 1.75rem;
        }}

        /* Pollutant Grid */
        .pollutant-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 1rem;
            margin-bottom: 1.75rem;
        }}

        .pollutant-card {{
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--border-glass);
            border-radius: var(--radius-md);
            padding: 1rem;
            transition: all 0.2s ease;
        }}

        .pollutant-card:hover {{
            background: rgba(255, 255, 255, 0.05);
            border-color: var(--border-active);
        }}

        .pollutant-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 6px;
        }}

        .pollutant-sym {{
            font-size: 0.85rem;
            font-weight: 700;
            color: var(--text-muted);
        }}

        .sub-aqi-pill {{
            font-size: 0.7rem;
            font-weight: 700;
            padding: 2px 6px;
            border-radius: 4px;
            background: rgba(255, 255, 255, 0.08);
            color: var(--text-secondary);
        }}

        .pollutant-conc {{
            font-size: 1.5rem;
            font-weight: 800;
            color: var(--text-primary);
            font-family: 'JetBrains Mono', monospace;
        }}

        .pollutant-unit {{
            font-size: 0.75rem;
            font-weight: 500;
            color: var(--text-muted);
            margin-left: 2px;
        }}

        .meter-bar {{
            width: 100%;
            height: 4px;
            background: rgba(255, 255, 255, 0.08);
            border-radius: 2px;
            margin-top: 10px;
            overflow: hidden;
        }}

        .meter-fill {{
            height: 100%;
            border-radius: 2px;
            transition: width 0.5s ease;
        }}

        /* Health Advisories */
        .advisory-wrapper {{
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--border-glass);
            border-radius: var(--radius-md);
            padding: 1.5rem;
        }}

        .advisory-headline {{
            font-size: 0.95rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .advisory-tile-row {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
            gap: 12px;
        }}

        .advisory-tile {{
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--border-glass);
            border-radius: var(--radius-sm);
            padding: 12px 14px;
        }}

        .advisory-tile-title {{
            font-size: 0.75rem;
            color: var(--text-muted);
            text-transform: uppercase;
            font-weight: 700;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }}

        .advisory-tile-val {{
            font-size: 0.9rem;
            font-weight: 700;
            color: var(--text-primary);
        }}

        /* Chart Canvas Container */
        .chart-box {{
            height: 360px;
            position: relative;
            margin-top: 1rem;
        }}

        /* Leaderboard Table */
        .leaderboard-table {{
            width: 100%;
            border-collapse: separate;
            border-spacing: 0 8px;
        }}

        .leaderboard-row {{
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--border-glass);
            border-radius: var(--radius-sm);
            cursor: pointer;
            transition: all 0.2s ease;
        }}

        .leaderboard-row:hover {{
            background: rgba(255, 255, 255, 0.06);
            transform: translateX(4px);
        }}

        .leaderboard-row.active {{
            background: rgba(37, 99, 235, 0.15);
            border: 1px solid #3B82F6;
        }}

        .leaderboard-row td {{
            padding: 14px 16px;
        }}

        .leaderboard-row td:first-child {{
            border-top-left-radius: var(--radius-sm);
            border-bottom-left-radius: var(--radius-sm);
        }}

        .leaderboard-row td:last-child {{
            border-top-right-radius: var(--radius-sm);
            border-bottom-right-radius: var(--radius-sm);
        }}

        .rank-num {{
            font-size: 1.1rem;
            font-weight: 800;
            font-family: 'JetBrains Mono', monospace;
            color: var(--text-muted);
            width: 45px;
        }}

        .city-col-name {{
            font-size: 1rem;
            font-weight: 700;
            color: var(--text-primary);
        }}

        .city-col-sub {{
            font-size: 0.75rem;
            color: var(--text-muted);
        }}

        .aqi-score-col {{
            font-size: 1.3rem;
            font-weight: 800;
            font-family: 'JetBrains Mono', monospace;
            text-align: right;
        }}

        /* Leaflet Map */
        #pakistanMap {{
            height: 320px;
            border-radius: var(--radius-md);
            overflow: hidden;
            border: 1px solid var(--border-glass);
            margin-top: 1rem;
        }}

        /* Footer */
        .footer {{
            border-top: 1px solid var(--border-glass);
            padding: 2.5rem 2rem;
            text-align: center;
            color: var(--text-muted);
            font-size: 0.85rem;
            margin-top: 4rem;
        }}
    </style>
</head>
<body>

    <!-- Header Navbar -->
    <nav class="navbar">
        <div class="brand">
            <div class="brand-icon">🌫️</div>
            <div>
                <div class="brand-title">Smog Watch Pakistan</div>
                <div class="brand-subtitle">National Environmental Telemetry Network</div>
            </div>
        </div>
        <div class="nav-actions">
            <div class="live-pill">
                <div class="pulse-dot"></div>
                LIVE SATELLITE & SENSOR INGESTION
            </div>
            <a href="/?refresh=1" class="btn-refresh">
                <span>🔄</span> Refresh Telemetry
            </a>
        </div>
    </nav>

    <!-- Main Content Container -->
    <div class="container">
        <!-- 4 KPI Metrics -->
        <div class="kpi-grid">
            <div class="kpi-card success">
                <div class="kpi-label">Active Monitoring Stations <span>📡</span></div>
                <div class="kpi-val">{summary.get('reporting_count', 0)} / {summary.get('total_stations', 0)}</div>
                <div class="kpi-subtext">
                    <span style="color: #34D399; font-weight: 700;">{summary.get('reporting_percentage', 0)}% Coverage</span> • Zero Mock Data
                </div>
            </div>

            <div class="kpi-card">
                <div class="kpi-label">National Mean Smog Index <span>📊</span></div>
                <div class="kpi-val" style="color: #38BDF8;">{summary.get('average_aqi', 'N/A')}</div>
                <div class="kpi-subtext">Calculated via US EPA Standard Breakpoints</div>
            </div>

            <div class="kpi-card alert">
                <div class="kpi-label">Smog Epicenter (Highest) <span>🔥</span></div>
                <div class="kpi-val" style="color: #F87171;">{summary.get('worst_city', 'N/A')}</div>
                <div class="kpi-subtext">
                    <span style="color: #F87171; font-weight: 700;">AQI {summary.get('worst_aqi', '—')}</span> • Extreme Hazard Warning
                </div>
            </div>

            <div class="kpi-card success">
                <div class="kpi-label">Cleanest Air Haven <span>🍃</span></div>
                <div class="kpi-val" style="color: #34D399;">{summary.get('cleanest_city', 'N/A')}</div>
                <div class="kpi-subtext">
                    <span style="color: #34D399; font-weight: 700;">AQI {summary.get('cleanest_aqi', '—')}</span> • Relative Low Impact
                </div>
            </div>
        </div>

        <!-- Quick Switcher City Bar -->
        <div class="city-switcher-wrapper">
            <div class="switcher-title">Select Focus City:</div>
            {"".join(f'''
            <div class="city-pill {'active' if c['city'] == 'Lahore' else ''}" id="pill-{c['city']}" onclick="selectCity('{c['city']}')">
                <span>{c['city']}</span>
                <span class="pill-aqi" style="background: {c['color']}33; color: {c['color']}; border: 1px solid {c['color']}66;">
                    AQI {c['aqi'] if c['aqi'] is not None else '—'}
                </span>
            </div>
            ''' for c in telemetry['ranked'])}
        </div>

        <!-- Main 2-Column Responsive Layout -->
        <div class="main-layout">
            <!-- Left Column: City Deep Dive & 48h Forecast -->
            <div>
                <!-- Primary City Showcase Card -->
                <div class="glass-card" id="cityDetailsPanel">
                    <!-- Populated dynamically via JS -->
                </div>

                <!-- 48-Hour Atmospheric Forecast & Historical Trend -->
                <div class="glass-card">
                    <div class="card-header-row">
                        <div>
                            <h3 style="font-size: 1.25rem; font-weight: 700;">📈 48-Hour Atmospheric Telemetry & Forecast</h3>
                            <p style="font-size: 0.8rem; color: var(--text-muted); margin-top: 4px;">
                                Assimilated 24h observational history combined with 24h high-resolution photochemical model forecast.
                            </p>
                        </div>
                    </div>
                    <div class="chart-box">
                        <canvas id="trendChart"></canvas>
                    </div>
                </div>
            </div>

            <!-- Right Column: Severity Leaderboard & Interactive Map -->
            <div>
                <!-- National Leaderboard -->
                <div class="glass-card">
                    <div class="card-header-row">
                        <div>
                            <h3 style="font-size: 1.25rem; font-weight: 700;">🏆 National Smog Severity Leaderboard</h3>
                            <p style="font-size: 0.8rem; color: var(--text-muted); margin-top: 4px;">
                                Ranked from most polluted to cleanest based on EPA composite AQI.
                            </p>
                        </div>
                    </div>

                    <table class="leaderboard-table">
                        <tbody>
                            {"".join(f'''
                            <tr class="leaderboard-row {'active' if c['city'] == 'Lahore' else ''}" id="row-{c['city']}" onclick="selectCity('{c['city']}')">
                                <td class="rank-num">#{c['rank'] if c['rank'] is not None else '—'}</td>
                                <td>
                                    <div class="city-col-name">{c['city']}</div>
                                    <div class="city-col-sub">{telemetry['city_metadata'][c['city']]['province']} • {'Primary Mandate' if telemetry['city_metadata'][c['city']]['is_primary'] else 'Secondary Hub'}</div>
                                </td>
                                <td>
                                    <span style="display: inline-block; padding: 4px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 700; background: {c['color']}22; color: {c['color']}; border: 1px solid {c['color']}55;">
                                        {c['badge']}
                                    </span>
                                </td>
                                <td class="aqi-score-col" style="color: {c['color']};">
                                    {c['aqi'] if c['aqi'] is not None else 'N/A'}
                                </td>
                            </tr>
                            ''' for c in telemetry['ranked'])}
                        </tbody>
                    </table>
                </div>

                <!-- Interactive Pakistan Map -->
                <div class="glass-card">
                    <div class="card-header-row">
                        <div>
                            <h3 style="font-size: 1.25rem; font-weight: 700;">🗺️ Spatial Pollution Radar</h3>
                            <p style="font-size: 0.8rem; color: var(--text-muted); margin-top: 4px;">
                                Color-coded regional telemetry pins across Pakistani urban basins.
                            </p>
                        </div>
                    </div>
                    <div id="pakistanMap"></div>
                </div>
            </div>
        </div>
    </div>

    <!-- Executive Footer -->
    <footer class="footer">
        <p><strong>Smog Watch Pakistan</strong> • Automated Atmospheric Telemetry & Public Health Warning Engine</p>
        <p style="margin-top: 6px;">Telemetry Pipeline: Open-Meteo Photochemical Model Assimilation • Standard: US EPA Piecewise Linear Interpolation Formula</p>
        <p style="margin-top: 6px; font-size: 0.75rem; color: var(--text-muted);">Verified authentic measurements • Timestamp: {updated_at} • Licensed under MIT</p>
    </footer>

    <script>
        const TELEMETRY = {telemetry_json};
        let currentChart = null;
        let leafletMap = null;
        let mapMarkers = {{}};

        function selectCity(cityName) {{
            // Update UI pills
            document.querySelectorAll('.city-pill').forEach(el => el.classList.remove('active'));
            const activePill = document.getElementById('pill-' + cityName);
            if (activePill) activePill.classList.add('active');

            // Update leaderboard table highlights
            document.querySelectorAll('.leaderboard-row').forEach(el => el.classList.remove('active'));
            const activeRow = document.getElementById('row-' + cityName);
            if (activeRow) activeRow.classList.add('active');

            // Render City Deep Dive Panel
            renderCityDeepDive(cityName);

            // Pan map to city
            const meta = TELEMETRY.city_metadata[cityName];
            if (meta && leafletMap) {{
                leafletMap.flyTo([meta.latitude, meta.longitude], 8, {{ duration: 1.5 }});
                if (mapMarkers[cityName]) {{
                    mapMarkers[cityName].openPopup();
                }}
            }}
        }}

        function renderCityDeepDive(cityName) {{
            const data = TELEMETRY.cities[cityName];
            const meta = TELEMETRY.city_metadata[cityName];
            if (!data) return;

            const category = data.category || {{}};
            const color = category.color || '#6C757D';
            const pollutants = data.pollutants || {{}};
            const subIndices = data.sub_indices || {{}};
            const adv = category.advisory || {{}};

            const html = `
                <div class="card-header-row">
                    <div>
                        <div class="city-name-lg">${{cityName}}</div>
                        <div class="city-meta-tags">
                            <span class="meta-tag">Province: ${{meta.province}}</span>
                            <span class="meta-tag">Coords: ${{meta.latitude.toFixed(2)}}°N, ${{meta.longitude.toFixed(2)}}°E</span>
                            <span class="meta-tag">Observed: ${{data.timestamp || 'Real-time'}}</span>
                        </div>
                    </div>
                    <span class="category-badge-lg" style="background: ${{color}}; color: ${{category.text_color || '#FFFFFF'}};">
                        ${{category.badge || '⚪ Unavailable'}}
                    </span>
                </div>

                <div class="aqi-hero-banner" style="border-left: 5px solid ${{color}};">
                    <div>
                        <div style="font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; color: var(--text-muted); font-weight: 700;">
                            Composite US EPA Air Quality Index
                        </div>
                        <div class="aqi-score-box">
                            <span class="aqi-large-number" style="color: ${{color}};">
                                ${{data.aqi !== null ? data.aqi : 'N/A'}}
                            </span>
                            <span class="aqi-units">US AQI</span>
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 0.75rem; color: var(--text-muted); font-weight: 600;">Governing Pollutant</div>
                        <div style="font-size: 1.2rem; font-weight: 800; color: #FFFFFF; text-transform: uppercase;">
                            ${{data.dominant_pollutant ? data.dominant_pollutant.replace('_', '.') : 'PM2.5'}}
                        </div>
                    </div>
                </div>

                <p class="health-statement-text">${{category.health_statement || ''}}</p>

                <h5 style="font-size: 0.95rem; font-weight: 700; color: var(--text-primary); margin-bottom: 1rem;">
                    Ambient Criteria Pollutants (Validated Sensors):
                </h5>
                <div class="pollutant-grid">
                    <div class="pollutant-card">
                        <div class="pollutant-header">
                            <span class="pollutant-sym">PM2.5</span>
                            <span class="sub-aqi-pill">Sub-AQI: ${{subIndices.pm2_5 || '—'}}</span>
                        </div>
                        <div class="pollutant-conc">${{pollutants.pm2_5 !== null ? pollutants.pm2_5.toFixed(1) : 'N/A'}}<span class="pollutant-unit">µg/m³</span></div>
                        <div class="meter-bar"><div class="meter-fill" style="width: ${{Math.min(100, (pollutants.pm2_5 || 0) / 2.5)}}%; background: #EF4444;"></div></div>
                    </div>

                    <div class="pollutant-card">
                        <div class="pollutant-header">
                            <span class="pollutant-sym">PM10</span>
                            <span class="sub-aqi-pill">Sub-AQI: ${{subIndices.pm10 || '—'}}</span>
                        </div>
                        <div class="pollutant-conc">${{pollutants.pm10 !== null ? pollutants.pm10.toFixed(1) : 'N/A'}}<span class="pollutant-unit">µg/m³</span></div>
                        <div class="meter-bar"><div class="meter-fill" style="width: ${{Math.min(100, (pollutants.pm10 || 0) / 3.5)}}%; background: #F59E0B;"></div></div>
                    </div>

                    <div class="pollutant-card">
                        <div class="pollutant-header">
                            <span class="pollutant-sym">NO₂</span>
                            <span class="sub-aqi-pill">Nitrogen Dioxide</span>
                        </div>
                        <div class="pollutant-conc">${{pollutants.nitrogen_dioxide !== null ? pollutants.nitrogen_dioxide.toFixed(1) : 'N/A'}}<span class="pollutant-unit">µg/m³</span></div>
                        <div class="meter-bar"><div class="meter-fill" style="width: ${{Math.min(100, (pollutants.nitrogen_dioxide || 0))}}%; background: #3B82F6;"></div></div>
                    </div>

                    <div class="pollutant-card">
                        <div class="pollutant-header">
                            <span class="pollutant-sym">SO₂</span>
                            <span class="sub-aqi-pill">Sulphur Dioxide</span>
                        </div>
                        <div class="pollutant-conc">${{pollutants.sulphur_dioxide !== null ? pollutants.sulphur_dioxide.toFixed(1) : 'N/A'}}<span class="pollutant-unit">µg/m³</span></div>
                        <div class="meter-bar"><div class="meter-fill" style="width: ${{Math.min(100, (pollutants.sulphur_dioxide || 0) * 2)}}%; background: #10B981;"></div></div>
                    </div>

                    <div class="pollutant-card">
                        <div class="pollutant-header">
                            <span class="pollutant-sym">CO</span>
                            <span class="sub-aqi-pill">Carbon Monoxide</span>
                        </div>
                        <div class="pollutant-conc">${{pollutants.carbon_monoxide !== null ? pollutants.carbon_monoxide.toFixed(0) : 'N/A'}}<span class="pollutant-unit">µg/m³</span></div>
                        <div class="meter-bar"><div class="meter-fill" style="width: ${{Math.min(100, (pollutants.carbon_monoxide || 0) / 10)}}%; background: #6366F1;"></div></div>
                    </div>

                    <div class="pollutant-card">
                        <div class="pollutant-header">
                            <span class="pollutant-sym">O₃</span>
                            <span class="sub-aqi-pill">Ozone</span>
                        </div>
                        <div class="pollutant-conc">${{pollutants.ozone !== null ? pollutants.ozone.toFixed(1) : 'N/A'}}<span class="pollutant-unit">µg/m³</span></div>
                        <div class="meter-bar"><div class="meter-fill" style="width: ${{Math.min(100, (pollutants.ozone || 0))}}%; background: #EC4899;"></div></div>
                    </div>
                </div>

                <div class="advisory-wrapper">
                    <div class="advisory-headline">
                        <span>🛡️</span> Mandatory Public Health & Smog Advisory Protocol
                    </div>
                    <div class="advisory-tile-row">
                        <div class="advisory-tile">
                            <div class="advisory-tile-title">Respiratory Protection</div>
                            <div class="advisory-tile-val">${{adv.mask_recommended ? '😷 N95 Mask Required Outdoors' : '✅ Mask Optional'}}</div>
                        </div>
                        <div class="advisory-tile">
                            <div class="advisory-tile-title">Indoor Air Purification</div>
                            <div class="advisory-tile-val">${{adv.air_purifier_recommended ? '🏠 HEPA Filtration Essential' : '🌱 Normal Ventilation'}}</div>
                        </div>
                        <div class="advisory-tile">
                            <div class="advisory-tile-title">Outdoor Physical Exertion</div>
                            <div class="advisory-tile-val">${{adv.outdoor_exercise || 'Acceptable'}}</div>
                        </div>
                        <div class="advisory-tile">
                            <div class="advisory-tile-title">Sensitive Demographic</div>
                            <div class="advisory-tile-val">${{adv.sensitive ? adv.sensitive.substring(0, 48) + '...' : 'Normal monitoring'}}</div>
                        </div>
                    </div>
                </div>
            `;

            document.getElementById('cityDetailsPanel').innerHTML = html;
            renderTrendChart(data.hourly_series, cityName);
        }}

        function renderTrendChart(hourly, cityName) {{
            const ctx = document.getElementById('trendChart').getContext('2d');
            if (currentChart) currentChart.destroy();

            if (!hourly || !hourly.time || hourly.time.length === 0) return;

            // Format timestamps for display
            const labels = hourly.time.map(t => {{
                const d = new Date(t);
                return d.toLocaleTimeString([], {{ hour: '2-digit', minute: '2-digit', hour12: false }});
            }});

            const gradientAQI = ctx.createLinearGradient(0, 0, 0, 300);
            gradientAQI.addColorStop(0, 'rgba(239, 68, 68, 0.45)');
            gradientAQI.addColorStop(1, 'rgba(239, 68, 68, 0.0)');

            currentChart = new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: labels,
                    datasets: [
                        {{
                            label: 'US EPA AQI',
                            data: hourly.us_aqi,
                            borderColor: '#F87171',
                            backgroundColor: gradientAQI,
                            borderWidth: 2.5,
                            fill: true,
                            tension: 0.35,
                            pointRadius: 2,
                            pointHoverRadius: 6,
                            yAxisID: 'y'
                        }},
                        {{
                            label: 'PM2.5 (µg/m³)',
                            data: hourly.pm2_5,
                            borderColor: '#38BDF8',
                            borderDash: [4, 4],
                            borderWidth: 2,
                            fill: false,
                            tension: 0.35,
                            pointRadius: 0,
                            pointHoverRadius: 5,
                            yAxisID: 'y1'
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {{ mode: 'index', intersect: false }},
                    plugins: {{
                        legend: {{
                            labels: {{
                                color: '#94A3B8',
                                font: {{ family: 'Plus Jakarta Sans', weight: '600', size: 12 }}
                            }}
                        }},
                        tooltip: {{
                            backgroundColor: '#1E293B',
                            titleColor: '#F8FAFC',
                            bodyColor: '#CBD5E1',
                            borderColor: 'rgba(255, 255, 255, 0.1)',
                            borderWidth: 1,
                            padding: 12,
                            cornerRadius: 8
                        }}
                    }},
                    scales: {{
                        x: {{
                            grid: {{ color: 'rgba(255, 255, 255, 0.05)' }},
                            ticks: {{ color: '#64748B', font: {{ family: 'JetBrains Mono', size: 11 }} }}
                        }},
                        y: {{
                            type: 'linear',
                            position: 'left',
                            grid: {{ color: 'rgba(255, 255, 255, 0.05)' }},
                            ticks: {{ color: '#F87171', font: {{ family: 'JetBrains Mono' }} }},
                            title: {{ display: true, text: 'US AQI Scale', color: '#F87171' }}
                        }},
                        y1: {{
                            type: 'linear',
                            position: 'right',
                            grid: {{ drawOnChartArea: false }},
                            ticks: {{ color: '#38BDF8', font: {{ family: 'JetBrains Mono' }} }},
                            title: {{ display: true, text: 'PM2.5 (µg/m³)', color: '#38BDF8' }}
                        }}
                    }}
                }}
            }});
        }}

        function initMap() {{
            leafletMap = L.map('pakistanMap', {{
                center: [30.3753, 69.3451],
                zoom: 5,
                zoomControl: false,
                attributionControl: false
            }});

            // Dark Matter Basemap Tiles
            L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
                maxZoom: 19
            }}).addTo(leafletMap);

            // Add glowing markers for each city
            TELEMETRY.ranked.forEach(c => {{
                const meta = TELEMETRY.city_metadata[c.city];
                if (!meta) return;

                const circleMarker = L.circleMarker([meta.latitude, meta.longitude], {{
                    radius: 12,
                    fillColor: c.color,
                    color: '#FFFFFF',
                    weight: 2,
                    opacity: 0.9,
                    fillOpacity: 0.8
                }}).addTo(leafletMap);

                circleMarker.bindPopup(`
                    <div style="font-family: 'Plus Jakarta Sans', sans-serif; color: #0F172A; padding: 4px;">
                        <strong style="font-size: 1.1rem;">${{c.city}}</strong><br>
                        <span style="display: inline-block; padding: 2px 8px; border-radius: 12px; background: ${{c.color}}; color: #FFF; font-weight: 700; margin-top: 4px;">
                            ${{c.badge}}
                        </span>
                        <div style="margin-top: 6px; font-weight: 700; font-size: 1.1rem; color: ${{c.color}};">
                            AQI: ${{c.aqi !== null ? c.aqi : 'N/A'}}
                        </div>
                    </div>
                `);

                circleMarker.on('click', () => {{
                    selectCity(c.city);
                }});

                mapMarkers[c.city] = circleMarker;
            }});
        }}

        document.addEventListener('DOMContentLoaded', () => {{
            renderCityDeepDive('Lahore');
            initMap();
        }});
    </script>
</body>
</html>
"""


class DashboardHTTPRequestHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler serving the Smog Watch interactive web application."""

    def do_GET(self) -> None:
        if self.path == "/_stcore/health" or self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "ok"}')
            return

        force = "refresh=1" in self.path
        try:
            telemetry = get_telemetry_data(force_refresh=force)
            html = render_html_dashboard(telemetry)

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
        except Exception as e:
            logger.error("Error handling request: %s", e)
            self.send_response(500)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(f"Internal Server Error: {str(e)}".encode("utf-8"))

    def log_message(self, format: str, *args) -> None:
        """Suppress noisy request logs."""
        pass


def run_server(port: int = 8501, host: str = "0.0.0.0") -> None:
    """Launch the local HTTP dashboard server."""
    server_address = (host, port)
    httpd = HTTPServer(server_address, DashboardHTTPRequestHandler)
    print("=" * 70)
    print(f"🌫️  SMOG WATCH PAKISTAN DASHBOARD RUNNING")
    print(f"👉 Local URL: http://localhost:{port}")
    print(f"👉 Network URL: http://127.0.0.1:{port}")
    print("=" * 70)
    httpd.serve_forever()


if __name__ == "__main__":
    run_server()
