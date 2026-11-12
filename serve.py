"""Standalone Web Server & Live Dashboard for Smog Watch Pakistan.

Provides an immediate, dependency-free local web server running on port 8501.
Renders the full real-time atmospheric telemetry dashboard using authentic
Open-Meteo API data and US EPA standard calculations.
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
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S PKT")
        },
        "timestamp": now
    }
    return _CACHE["data"]


def render_html_dashboard(telemetry: Dict[str, Any]) -> str:
    """Generate the full responsive HTML/CSS/JS dashboard."""
    ranked = telemetry["ranked"]
    summary = telemetry["summary"]
    updated_at = telemetry["updated_at"]

    # Pre-encode JSON payload for client-side interactivity
    telemetry_json = json.dumps(telemetry)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smog Watch Pakistan | Live Atmospheric Telemetry</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <style>
        body {{
            background-color: #F8F9FA;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            color: #212529;
        }}
        .navbar-brand {{
            font-weight: 700;
            font-size: 1.4rem;
            color: #1A365D !important;
        }}
        .kpi-card {{
            background: #FFFFFF;
            border-radius: 10px;
            padding: 1.2rem;
            border: 1px solid #E2E8F0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.04);
            margin-bottom: 1rem;
        }}
        .kpi-title {{
            font-size: 0.85rem;
            color: #6C757D;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 600;
        }}
        .kpi-value {{
            font-size: 1.8rem;
            font-weight: 700;
            color: #1A202C;
            margin-top: 0.2rem;
        }}
        .status-badge {{
            display: inline-block;
            padding: 0.35rem 0.75rem;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            color: #FFFFFF;
        }}
        .city-card {{
            background: #FFFFFF;
            border-radius: 10px;
            border: 1px solid #E2E8F0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }}
        .pollutant-box {{
            background: #F8F9FA;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
        }}
        .advisory-card {{
            background: #FFFFFF;
            border-radius: 8px;
            border-left: 6px solid #4A5568;
            padding: 1.2rem;
            margin-top: 1rem;
        }}
        .badge-chip {{
            background: #EDF2F7;
            padding: 0.4rem 0.8rem;
            border-radius: 6px;
            font-size: 0.85rem;
            display: inline-block;
            margin-right: 0.5rem;
            margin-bottom: 0.5rem;
        }}
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-light bg-white border-bottom shadow-sm">
        <div class="container-fluid px-4">
            <span class="navbar-brand">🌫️ Smog Watch Pakistan</span>
            <div class="d-flex align-items-center">
                <span class="badge bg-light text-dark border me-3">Telemetry: {updated_at}</span>
                <a href="/?refresh=1" class="btn btn-outline-success btn-sm">🔄 Refresh Telemetry</a>
            </div>
        </div>
    </nav>

    <div class="container-fluid px-4 py-4">
        <!-- National KPI Metrics Row -->
        <div class="row">
            <div class="col-md-3">
                <div class="kpi-card">
                    <div class="kpi-title">Active Stations</div>
                    <div class="kpi-value">{summary.get('reporting_count', 0)} / {summary.get('total_stations', 0)}</div>
                    <small class="text-success font-monospace">{summary.get('reporting_percentage', 0)}% Online</small>
                </div>
            </div>
            <div class="col-md-3">
                <div class="kpi-card">
                    <div class="kpi-title">National Average AQI</div>
                    <div class="kpi-value">{summary.get('average_aqi', 'N/A')}</div>
                    <small class="text-muted">US EPA Standard</small>
                </div>
            </div>
            <div class="col-md-3">
                <div class="kpi-card">
                    <div class="kpi-title">Most Polluted City</div>
                    <div class="kpi-value text-danger">{summary.get('worst_city', 'N/A')}</div>
                    <small class="text-danger">AQI {summary.get('worst_aqi', '—')}</small>
                </div>
            </div>
            <div class="col-md-3">
                <div class="kpi-card">
                    <div class="kpi-title">Cleanest Air Quality</div>
                    <div class="kpi-value text-success">{summary.get('cleanest_city', 'N/A')}</div>
                    <small class="text-success">AQI {summary.get('cleanest_aqi', '—')}</small>
                </div>
            </div>
        </div>

        <!-- City Selector Navigation -->
        <div class="card mb-4 border-0 shadow-sm">
            <div class="card-body">
                <div class="row align-items-center">
                    <div class="col-md-4">
                        <label for="citySelect" class="form-label fw-bold mb-1">Select Pakistani Urban Center:</label>
                        <select id="citySelect" class="form-select form-select-lg" onchange="switchCity(this.value)">
                            <option value="Lahore" selected>Lahore (Punjab) - Smog Epicenter</option>
                            <option value="Karachi">Karachi (Sindh) - Coastal Hub</option>
                            <option value="Islamabad">Islamabad (Federal Capital)</option>
                            <option value="Faisalabad">Faisalabad (Punjab) - Industrial Belts</option>
                            <option value="Peshawar">Peshawar (Khyber Pakhtunkhwa)</option>
                            <option value="Multan">Multan (Southern Punjab)</option>
                            <option value="Gujranwala">Gujranwala (Industrial North)</option>
                        </select>
                    </div>
                    <div class="col-md-8 text-md-end text-muted mt-2 mt-md-0">
                        <span class="badge bg-primary me-1">US EPA Standard</span>
                        <span class="badge bg-secondary me-1">Open-Meteo High-Resolution Feed</span>
                        <span class="badge bg-success">Zero Fabricated Data</span>
                    </div>
                </div>
            </div>
        </div>

        <div class="row">
            <!-- Left: City Deep Dive -->
            <div class="col-lg-7">
                <div id="cityDetailContainer"></div>

                <!-- 48-Hour Trend Chart -->
                <div class="city-card">
                    <h5 class="fw-bold mb-3">📈 48-Hour Atmospheric Telemetry Trend (AQI & PM2.5)</h5>
                    <div style="height: 320px;">
                        <canvas id="trendChart"></canvas>
                    </div>
                </div>
            </div>

            <!-- Right: National Leaderboard -->
            <div class="col-lg-5">
                <div class="city-card">
                    <h5 class="fw-bold mb-3">🏆 National Smog Severity Leaderboard</h5>
                    <p class="text-muted small">Ranked #1 (Most Polluted) to Cleanest based on composite EPA AQI.</p>
                    <div class="table-responsive">
                        <table class="table table-hover align-middle mb-0">
                            <thead class="table-light">
                                <tr>
                                    <th>Rank</th>
                                    <th>City</th>
                                    <th>US AQI</th>
                                    <th>Category</th>
                                </tr>
                            </thead>
                            <tbody>
                                {"".join(f'''
                                <tr onclick="selectAndScrollCity('{c["city"]}')" style="cursor: pointer;">
                                    <td class="fw-bold">{c["rank_display"]}</td>
                                    <td>
                                        <strong>{c["city"]}</strong>
                                        <div class="text-muted small">{PAKISTAN_CITIES[c["city"]]["province"]}</div>
                                    </td>
                                    <td>
                                        <span class="fw-bold" style="color: {c["color"]}; font-size: 1.1rem;">
                                            {c["aqi"] if c["aqi"] is not None else 'N/A'}
                                        </span>
                                    </td>
                                    <td>
                                        <span class="status-badge" style="background-color: {c["color"]};">
                                            {c["badge"]}
                                        </span>
                                    </td>
                                </tr>
                                ''' for c in ranked)}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        const TELEMETRY = {telemetry_json};
        let currentChart = null;

        function renderCity(cityName) {{
            const data = TELEMETRY.cities[cityName];
            if (!data) return;

            const category = data.category || {{}};
            const color = category.color || '#6C757D';
            const pollutants = data.pollutants || {{}};
            const subIndices = data.sub_indices || {{}};
            const adv = category.advisory || {{}};

            const html = `
                <div class="city-card" style="border-left: 6px solid ${{color}};">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h2 class="fw-bold mb-0">${{cityName}}</h2>
                            <small class="text-muted">Observation Time: ${{data.timestamp || 'N/A'}}</small>
                        </div>
                        <span class="status-badge" style="background-color: ${{color}};">${{category.badge || '⚪ Unavailable'}}</span>
                    </div>

                    <div class="my-3">
                        <span style="font-size: 2.8rem; font-weight: 800; color: ${{color}};">
                            ${{data.aqi !== null ? data.aqi : 'N/A'}}
                        </span>
                        <span class="text-muted ms-2 fs-5">US AQI</span>
                    </div>

                    <p class="text-secondary">${{category.health_statement || ''}}</p>

                    <h6 class="fw-bold text-dark mt-4 mb-3">Authentic Ambient Pollutant Telemetry:</h6>
                    <div class="row">
                        <div class="col-md-4">
                            <div class="pollutant-box">
                                <small class="text-muted">PM2.5 (Fine Particles)</small>
                                <div class="fw-bold fs-4">${{pollutants.pm2_5 !== null ? pollutants.pm2_5.toFixed(1) : 'N/A'}} <small class="fw-normal fs-6 text-muted">µg/m³</small></div>
                                <small class="text-secondary">Sub-AQI: <strong>${{subIndices.pm2_5 || '—'}}</strong></small>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="pollutant-box">
                                <small class="text-muted">PM10 (Coarse Particles)</small>
                                <div class="fw-bold fs-4">${{pollutants.pm10 !== null ? pollutants.pm10.toFixed(1) : 'N/A'}} <small class="fw-normal fs-6 text-muted">µg/m³</small></div>
                                <small class="text-secondary">Sub-AQI: <strong>${{subIndices.pm10 || '—'}}</strong></small>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="pollutant-box">
                                <small class="text-muted">NO₂ (Nitrogen Dioxide)</small>
                                <div class="fw-bold fs-4">${{pollutants.nitrogen_dioxide !== null ? pollutants.nitrogen_dioxide.toFixed(1) : 'N/A'}} <small class="fw-normal fs-6 text-muted">µg/m³</small></div>
                                <small class="text-secondary">Sub-AQI: <strong>${{subIndices.nitrogen_dioxide || '—'}}</strong></small>
                            </div>
                        </div>
                    </div>

                    <div class="advisory-card" style="border-left-color: ${{color}};">
                        <h6 class="fw-bold text-dark mb-2">📋 Public Health & Smog Advisory</h6>
                        <p class="mb-1"><strong>General Population:</strong> ${{adv.general || 'Standard precautions.'}}</p>
                        <p class="mb-2"><strong>Sensitive Groups:</strong> ${{adv.sensitive || 'Standard precautions.'}}</p>
                        <div class="mt-2">
                            <span class="badge-chip">😷 <strong>N95 Mask:</strong> ${{adv.mask_recommended ? 'Required Outdoors' : 'Optional'}}</span>
                            <span class="badge-chip">🏠 <strong>HEPA Air Purifier:</strong> ${{adv.air_purifier_recommended ? 'Recommended' : 'Not critical'}}</span>
                            <span class="badge-chip">🏃 <strong>Outdoor Exertion:</strong> ${{adv.outdoor_exercise || 'Safe'}}</span>
                        </div>
                    </div>
                </div>
            `;

            document.getElementById('cityDetailContainer').innerHTML = html;
            renderChart(data.hourly_series, cityName);
        }}

        function renderChart(hourly, cityName) {{
            const ctx = document.getElementById('trendChart').getContext('2d');
            if (currentChart) currentChart.destroy();

            if (!hourly || !hourly.time || hourly.time.length === 0) return;

            const labels = hourly.time.map(t => t.split('T')[1] || t);

            currentChart = new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: labels,
                    datasets: [
                        {{
                            label: 'US AQI',
                            data: hourly.us_aqi,
                            borderColor: '#D97706',
                            backgroundColor: 'rgba(217, 119, 6, 0.1)',
                            borderWidth: 2.5,
                            yAxisID: 'y'
                        }},
                        {{
                            label: 'PM2.5 (µg/m³)',
                            data: hourly.pm2_5,
                            borderColor: '#DC2626',
                            borderDash: [5, 5],
                            borderWidth: 1.8,
                            yAxisID: 'y1'
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {{ mode: 'index', intersect: false }},
                    scales: {{
                        y: {{
                            type: 'linear',
                            display: true,
                            position: 'left',
                            title: {{ display: true, text: 'US AQI Index' }}
                        }},
                        y1: {{
                            type: 'linear',
                            display: true,
                            position: 'right',
                            grid: {{ drawOnChartArea: false }},
                            title: {{ display: true, text: 'PM2.5 (µg/m³)' }}
                        }}
                    }}
                }}
            }});
        }}

        function switchCity(cityName) {{
            renderCity(cityName);
        }}

        function selectAndScrollCity(cityName) {{
            document.getElementById('citySelect').value = cityName;
            renderCity(cityName);
            window.scrollTo({{ top: 0, behavior: 'smooth' }});
        }}

        // Initial render on load
        document.addEventListener('DOMContentLoaded', () => {{
            renderCity('Lahore');
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
