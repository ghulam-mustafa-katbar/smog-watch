"""Integration and compliance tests verifying all five mandatory Pakistani cities."""
import pytest
from src.config import PRIMARY_FIVE_CITIES, PAKISTAN_CITIES
from src.api import AirQualityAPIClient


class TestPakistaniCitiesCompliance:
    """Test suite ensuring strict compliance with Pakistan city coverage and live telemetry."""

    def test_five_pakistani_cities_configured(self):
        """Verify that all five mandatory Pakistani cities are defined in configuration."""
        expected_cities = {"Lahore", "Karachi", "Islamabad", "Faisalabad", "Peshawar"}
        assert set(PRIMARY_FIVE_CITIES) == expected_cities

        for city in expected_cities:
            assert city in PAKISTAN_CITIES, f"Missing city configuration: {city}"
            city_meta = PAKISTAN_CITIES[city]
            assert "latitude" in city_meta
            assert "longitude" in city_meta
            assert "province" in city_meta
            assert city_meta["is_primary"] is True

            # Geographic bounding box verification for Pakistan (Lat: ~23-37, Lon: ~60-78)
            lat = city_meta["latitude"]
            lon = city_meta["longitude"]
            assert 23.0 <= lat <= 37.5, f"Latitude {lat} for {city} outside Pakistan boundary."
            assert 60.0 <= lon <= 78.5, f"Longitude {lon} for {city} outside Pakistan boundary."

    def test_live_api_telemetry_all_five_cities(self):
        """Live integration test: verify authentic, non-fabricated API responses for all 5 cities."""
        client = AirQualityAPIClient()

        for city_name in PRIMARY_FIVE_CITIES:
            meta = PAKISTAN_CITIES[city_name]
            result = client.fetch_city_air_quality(
                city_name=city_name,
                latitude=meta["latitude"],
                longitude=meta["longitude"]
            )

            # Verification assertions
            assert result["city"] == city_name
            assert result["status"] == "success", f"Live API failed for {city_name}: {result.get('error_message')}"
            assert result["aqi"] is not None, f"AQI is None for {city_name}"
            assert isinstance(result["aqi"], int), f"AQI must be an integer for {city_name}"
            assert result["aqi"] >= 0, f"AQI must be non-negative for {city_name}"

            # Verify authentic pollutant data is present
            pm2_5 = result["pollutants"].get("pm2_5")
            assert pm2_5 is not None, f"PM2.5 missing for {city_name}"
            assert isinstance(pm2_5, (int, float))
            assert pm2_5 >= 0.0

            # Verify time-series data
            hourly = result.get("hourly_series")
            assert hourly is not None
            assert len(hourly.get("time", [])) > 0
            assert len(hourly.get("pm2_5", [])) > 0
