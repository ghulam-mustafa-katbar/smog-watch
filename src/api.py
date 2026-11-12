"""API client module for fetching atmospheric air quality data from Open-Meteo.

Includes connection pooling, exponential backoff retries, strict timeouts,
structured error handling, and zero data fabrication.
"""
import logging
from typing import Dict, Any, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from src.config import (
    API_BASE_URL,
    API_CONNECT_TIMEOUT,
    API_READ_TIMEOUT,
    API_RETRY_TOTAL,
    API_RETRY_BACKOFF,
    PAKISTAN_CITIES
)
from src.aqi_calculator import calculate_overall_aqi, get_aqi_category

logger = logging.getLogger(__name__)


class AirQualityAPIError(Exception):
    """Custom exception raised when an API network or parsing error occurs."""
    pass


class AirQualityAPIClient:
    """Client for Open-Meteo Air Quality API with enterprise-grade resilience."""

    def __init__(
        self,
        base_url: str = API_BASE_URL,
        connect_timeout: float = API_CONNECT_TIMEOUT,
        read_timeout: float = API_READ_TIMEOUT,
        retry_total: int = API_RETRY_TOTAL,
        retry_backoff: float = API_RETRY_BACKOFF
    ):
        self.base_url = base_url
        self.timeout = (connect_timeout, read_timeout)
        self.session = self._create_resilient_session(retry_total, retry_backoff)

    @staticmethod
    def _create_resilient_session(retry_total: int, backoff_factor: float) -> requests.Session:
        """Create a requests Session configured with urllib3 Retry adapter."""
        session = requests.Session()
        retry_strategy = Retry(
            total=retry_total,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def fetch_city_air_quality(
        self,
        city_name: str,
        latitude: float,
        longitude: float
    ) -> Dict[str, Any]:
        """Fetch real-time ambient pollutant measurements and hourly trends for a city.

        Args:
            city_name: Display name of the city.
            latitude: Latitude coordinate in decimal degrees.
            longitude: Longitude coordinate in decimal degrees.

        Returns:
            Dictionary with structure:
                - 'city': str
                - 'status': 'success' | 'error'
                - 'error_message': Optional[str]
                - 'timestamp': Optional[str]
                - 'pollutants': Dict[str, Optional[float]] (actual readings in µg/m³)
                - 'aqi': Optional[int]
                - 'dominant_pollutant': Optional[str]
                - 'category': Dict[str, Any]
                - 'hourly_series': Optional[Dict[str, list]]
        """
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": [
                "us_aqi",
                "european_aqi",
                "pm10",
                "pm2_5",
                "carbon_monoxide",
                "nitrogen_dioxide",
                "sulphur_dioxide",
                "ozone"
            ],
            "hourly": ["pm2_5", "pm10", "us_aqi"],
            "timezone": "Asia/Karachi",
            "past_days": 1,
            "forecast_days": 1
        }

        try:
            response = self.session.get(
                self.base_url,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            payload = response.json()

        except requests.exceptions.Timeout as e:
            logger.error("Timeout fetching air quality for %s: %s", city_name, e)
            return self._build_error_response(
                city_name,
                f"Network request timed out ({self.timeout[0]}s connect / {self.timeout[1]}s read limit)."
            )
        except requests.exceptions.HTTPError as e:
            logger.error("HTTP error for %s: %s", city_name, e)
            status_code = response.status_code if 'response' in locals() else "Unknown"
            return self._build_error_response(
                city_name,
                f"Upstream HTTP error (Status: {status_code})."
            )
        except requests.exceptions.RequestException as e:
            logger.error("Connection error for %s: %s", city_name, e)
            return self._build_error_response(
                city_name,
                f"Connection failure communicating with Open-Meteo Air Quality service: {str(e)}"
            )
        except ValueError as e:
            logger.error("Invalid JSON response for %s: %s", city_name, e)
            return self._build_error_response(
                city_name,
                "Malformed response payload received from air quality service."
            )

        return self._parse_api_payload(city_name, payload)

    def _parse_api_payload(self, city_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and validate real measurements from the API payload without fabrication."""
        current = payload.get("current", {})
        if not current:
            return self._build_error_response(city_name, "Payload missing 'current' observations.")

        timestamp = current.get("time")

        # Extract authentic raw readings (preserving None if unavailable)
        pollutants: Dict[str, Optional[float]] = {
            "pm2_5": current.get("pm2_5"),
            "pm10": current.get("pm10"),
            "nitrogen_dioxide": current.get("nitrogen_dioxide"),
            "sulphur_dioxide": current.get("sulphur_dioxide"),
            "carbon_monoxide": current.get("carbon_monoxide"),
            "ozone": current.get("ozone")
        }

        # Calculate EPA compliant composite AQI from measured pollutants
        calc_result = calculate_overall_aqi(pollutants)

        # Compare or fallback to Open-Meteo calculated US AQI if available
        api_us_aqi = current.get("us_aqi")
        resolved_aqi = calc_result["aqi"]
        if resolved_aqi is None and api_us_aqi is not None:
            resolved_aqi = int(round(api_us_aqi))

        category = get_aqi_category(resolved_aqi)

        # Parse hourly time-series safely
        hourly = payload.get("hourly", {})
        hourly_series = {
            "time": hourly.get("time", []),
            "pm2_5": hourly.get("pm2_5", []),
            "pm10": hourly.get("pm10", []),
            "us_aqi": hourly.get("us_aqi", [])
        }

        return {
            "city": city_name,
            "status": "success",
            "error_message": None,
            "timestamp": timestamp,
            "pollutants": pollutants,
            "aqi": resolved_aqi,
            "dominant_pollutant": calc_result.get("responsible_pollutant"),
            "sub_indices": calc_result.get("sub_indices", {}),
            "category": category,
            "hourly_series": hourly_series
        }

    @staticmethod
    def _build_error_response(city_name: str, message: str) -> Dict[str, Any]:
        """Build explicit error representation with null measurements.

        Guarantees NO fabricated or estimated measurements are injected.
        """
        return {
            "city": city_name,
            "status": "error",
            "error_message": message,
            "timestamp": None,
            "pollutants": {
                "pm2_5": None,
                "pm10": None,
                "nitrogen_dioxide": None,
                "sulphur_dioxide": None,
                "carbon_monoxide": None,
                "ozone": None
            },
            "aqi": None,
            "dominant_pollutant": None,
            "sub_indices": {},
            "category": get_aqi_category(None),
            "hourly_series": None
        }

    def fetch_all_cities(
        self,
        cities: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """Fetch air quality readings for all configured Pakistani cities.

        Isolates errors per city so that single endpoint or regional connectivity
        glitches do not halt the entire application dashboard.
        """
        targets = cities or PAKISTAN_CITIES
        results: Dict[str, Dict[str, Any]] = {}

        for name, meta in targets.items():
            results[name] = self.fetch_city_air_quality(
                city_name=name,
                latitude=meta["latitude"],
                longitude=meta["longitude"]
            )

        return results
