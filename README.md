# Smog Watch PK

Real-time air quality index monitoring and smog tracking dashboard for major Pakistani urban centers.

## Overview
Smog Watch PK provides verified atmospheric telemetry across Pakistan without synthetic or fabricated data. The application consumes real-time observation feeds from Open-Meteo, calculates pollutant-specific sub-indices and composite air quality indices adhering to US EPA piecewise linear interpolation guidelines, and renders interactive trends and health advisories.

## Monitored Urban Centers
- **Lahore** (Punjab): 31.5204° N, 74.3587° E
- **Karachi** (Sindh): 24.8607° N, 67.0011° E
- **Islamabad** (Federal Capital): 33.6844° N, 73.0479° E
- **Faisalabad** (Punjab): 31.4504° N, 73.1350° E
- **Peshawar** (KPK): 34.0151° N, 71.5249° E

Supplementary monitoring is also configured for Multan and Gujranwala.

## Technical Architecture
- `src/config.py`: City geographic parameters, EPA breakpoint bands, and connection parameters.
- `src/api.py`: Open-Meteo API client with exponential backoff retries, connection timeouts, and isolated error reporting.
- `src/aqi_calculator.py`: Mathematical EPA AQI interpolation and advisory determination.
- `src/ranking.py`: Sorting engine prioritizing reporting stations by pollution severity with tie-breaking rules.
- `src/ui_components.py`: Streamlit layout components, Plotly visualizations, and health guidance cards.
- `app.py`: Streamlit application entry point with 10-minute caching and manual refresh.

## Data Integrity Guarantee
In case of upstream network timeouts or sensor station outages, the application marks the station as offline or unavailable. It does not generate synthetic, estimated, or mock pollutant concentrations.

## Running Locally

### Clone Repository
```bash
git clone https://github.com/ghulam-mustafa-katbar/smog-watch.git
cd smog-watch
```

### Installation
```bash
pip install -r requirements.txt
```

### Run Streamlit App
```bash
streamlit run app.py
```

### Run Test Suite
```bash
pytest -v
```

## Docker Deployment
```bash
docker build -t smog-watch-pk .
docker run -p 8501:8501 smog-watch-pk
```
