"""Unit tests for the resilient AirQualityAPIClient."""
from unittest.mock import patch, MagicMock
import requests
import pytest

from src.api import AirQualityAPIClient
from src.config import API_CONNECT_TIMEOUT, API_READ_TIMEOUT


class TestAirQualityAPIClient:
    """Test suite verifying resilience, HTTP error handling, and zero data fabrication."""

    def test_client_initialization_defaults(self):
        """Verify client respects timeout and retry defaults."""
        client = AirQualityAPIClient()
        assert client.timeout == (API_CONNECT_TIMEOUT, API_READ_TIMEOUT)
        assert client.session is not None

    def test_zero_fabrication_on_error(self):
        """Verify error response contains strictly None for measurements, never mock numbers."""
        client = AirQualityAPIClient()
        err_resp = client._build_error_response("TestCity", "Simulated connection drop")

        assert err_resp["city"] == "TestCity"
        assert err_resp["status"] == "error"
        assert err_resp["error_message"] == "Simulated connection drop"
        assert err_resp["aqi"] is None
        assert err_resp["timestamp"] is None
        for pol, val in err_resp["pollutants"].items():
            assert val is None, f"Fabricated measurement detected for {pol}: {val}"

    @patch("requests.Session.get")
    def test_timeout_handling(self, mock_get):
        """Verify graceful error response when network times out."""
        mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")

        client = AirQualityAPIClient()
        result = client.fetch_city_air_quality("Lahore", 31.5204, 74.3587)

        assert result["status"] == "error"
        assert "timed out" in result["error_message"]
        assert result["aqi"] is None

    @patch("requests.Session.get")
    def test_http_error_handling(self, mock_get):
        """Verify graceful error response on HTTP 500 error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")
        mock_get.return_value = mock_response

        client = AirQualityAPIClient()
        result = client.fetch_city_air_quality("Karachi", 24.8607, 67.0011)

        assert result["status"] == "error"
        assert "HTTP error" in result["error_message"]
        assert result["aqi"] is None

    @patch("requests.Session.get")
    def test_malformed_json_handling(self, mock_get):
        """Verify handling of corrupt or malformed JSON payloads."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = ValueError("Invalid JSON format")
        mock_get.return_value = mock_response

        client = AirQualityAPIClient()
        result = client.fetch_city_air_quality("Islamabad", 33.6844, 73.0479)

        assert result["status"] == "error"
        assert "Malformed response" in result["error_message"]

    @patch("requests.Session.get")
    def test_successful_payload_parsing(self, mock_get):
        """Verify parsing of valid payload with genuine sensor numbers."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "current": {
                "time": "2026-11-12T12:00",
                "pm2_5": 85.2,
                "pm10": 130.0,
                "nitrogen_dioxide": 22.1,
                "sulphur_dioxide": 8.4,
                "carbon_monoxide": 450.0,
                "ozone": 30.5,
                "us_aqi": 166
            },
            "hourly": {
                "time": ["2026-11-12T11:00", "2026-11-12T12:00"],
                "pm2_5": [80.0, 85.2],
                "pm10": [120.0, 130.0],
                "us_aqi": [160, 166]
            }
        }
        mock_get.return_value = mock_response

        client = AirQualityAPIClient()
        result = client.fetch_city_air_quality("Faisalabad", 31.4504, 73.1350)

        assert result["status"] == "success"
        assert result["pollutants"]["pm2_5"] == 85.2
        assert result["pollutants"]["pm10"] == 130.0
        assert result["aqi"] == 166
        assert result["category"]["name"] == "Unhealthy"
        assert len(result["hourly_series"]["time"]) == 2
