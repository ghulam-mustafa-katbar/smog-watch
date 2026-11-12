"""Unit tests for EPA AQI calculations and category mappings."""
import math
import pytest
from src.aqi_calculator import calculate_sub_aqi, calculate_overall_aqi, get_aqi_category


class TestAQICalculator:
    """Test suite for EPA AQI calculation engine."""

    def test_pm25_boundary_values(self):
        """Test PM2.5 standard breakpoint bounds."""
        assert calculate_sub_aqi("pm2_5", 0.0) == 0
        assert calculate_sub_aqi("pm2_5", 12.0) == 50
        assert calculate_sub_aqi("pm2_5", 35.4) == 100
        assert calculate_sub_aqi("pm2_5", 55.4) == 150
        assert calculate_sub_aqi("pm2_5", 150.4) == 200
        assert calculate_sub_aqi("pm2_5", 250.4) == 300
        assert calculate_sub_aqi("pm2_5", 350.4) == 400
        assert calculate_sub_aqi("pm2_5", 500.4) == 500

    def test_pm25_intermediate_interpolation(self):
        """Test linear interpolation between breakpoints for PM2.5."""
        # Between 12.1 and 35.4 (AQI 51 - 100)
        aqi = calculate_sub_aqi("pm2_5", 25.0)
        assert 51 <= aqi <= 100

        # Between 55.5 and 150.4 (AQI 151 - 200)
        aqi_high = calculate_sub_aqi("pm2_5", 100.0)
        assert 151 <= aqi_high <= 200

    def test_pm10_boundary_values(self):
        """Test PM10 standard breakpoint bounds."""
        assert calculate_sub_aqi("pm10", 0.0) == 0
        assert calculate_sub_aqi("pm10", 54.0) == 50
        assert calculate_sub_aqi("pm10", 154.0) == 100
        assert calculate_sub_aqi("pm10", 254.0) == 150
        assert calculate_sub_aqi("pm10", 354.0) == 200
        assert calculate_sub_aqi("pm10", 424.0) == 300
        assert calculate_sub_aqi("pm10", 504.0) == 400
        assert calculate_sub_aqi("pm10", 604.0) == 500

    def test_missing_and_invalid_data_handling(self):
        """Ensure no fabricated values when data is None, NaN, negative, or invalid."""
        assert calculate_sub_aqi("pm2_5", None) is None
        assert calculate_sub_aqi("pm2_5", float("nan")) is None
        assert calculate_sub_aqi("pm2_5", -10.5) is None
        assert calculate_sub_aqi("pm2_5", "invalid") is None
        assert calculate_sub_aqi("unknown_pollutant", 50.0) is None

    def test_composite_overall_aqi_selection(self):
        """Verify overall AQI is governed by the highest pollutant sub-index."""
        # Case 1: PM2.5 is dominant
        pollutants_1 = {"pm2_5": 60.0, "pm10": 40.0}
        res_1 = calculate_overall_aqi(pollutants_1)
        assert res_1["status"] == "valid"
        assert res_1["responsible_pollutant"] == "pm2_5"
        assert res_1["aqi"] == calculate_sub_aqi("pm2_5", 60.0)

        # Case 2: PM10 is dominant
        pollutants_2 = {"pm2_5": 10.0, "pm10": 200.0}
        res_2 = calculate_overall_aqi(pollutants_2)
        assert res_2["status"] == "valid"
        assert res_2["responsible_pollutant"] == "pm10"
        assert res_2["aqi"] == calculate_sub_aqi("pm10", 200.0)

    def test_all_missing_composite_aqi(self):
        """Verify that when no valid readings exist, overall AQI is None without fabrication."""
        res = calculate_overall_aqi({"pm2_5": None, "pm10": None})
        assert res["status"] == "insufficient_data"
        assert res["aqi"] is None
        assert res["responsible_pollutant"] is None
        assert res["category"]["name"] == "Data Unavailable"

    def test_aqi_category_mapping(self):
        """Verify correct category classification across full AQI range."""
        assert get_aqi_category(25)["name"] == "Good"
        assert get_aqi_category(75)["name"] == "Moderate"
        assert get_aqi_category(125)["name"] == "Unhealthy for Sensitive Groups"
        assert get_aqi_category(175)["name"] == "Unhealthy"
        assert get_aqi_category(250)["name"] == "Very Unhealthy"
        assert get_aqi_category(350)["name"] == "Hazardous"
        assert get_aqi_category(600)["name"] == "Beyond Index / Severe Hazard"
        assert get_aqi_category(None)["name"] == "Data Unavailable"
