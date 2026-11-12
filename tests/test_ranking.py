"""Unit tests for city ranking algorithms and national summaries."""
import pytest
from src.ranking import rank_cities, calculate_national_summary


class TestRankingEngine:
    """Test suite for ranking correctness and edge case handling."""

    def test_ranking_descending_order(self):
        """Verify cities are ranked strictly from highest AQI to lowest AQI."""
        input_data = {
            "CityA": {"status": "success", "aqi": 180, "pollutants": {"pm2_5": 70.0}},
            "CityB": {"status": "success", "aqi": 320, "pollutants": {"pm2_5": 140.0}},
            "CityC": {"status": "success", "aqi": 85, "pollutants": {"pm2_5": 28.0}}
        }
        ranked = rank_cities(input_data)
        assert len(ranked) == 3
        assert ranked[0]["city"] == "CityB"
        assert ranked[0]["rank"] == 1
        assert ranked[1]["city"] == "CityA"
        assert ranked[1]["rank"] == 2
        assert ranked[2]["city"] == "CityC"
        assert ranked[2]["rank"] == 3

    def test_tie_breaking(self):
        """Verify ties in AQI are broken by higher PM2.5 concentration."""
        input_data = {
            "CityX": {"status": "success", "aqi": 150, "pollutants": {"pm2_5": 54.0}},
            "CityY": {"status": "success", "aqi": 150, "pollutants": {"pm2_5": 55.0}}
        }
        ranked = rank_cities(input_data)
        assert ranked[0]["city"] == "CityY"
        assert ranked[0]["rank"] == 1
        assert ranked[1]["city"] == "CityX"
        assert ranked[1]["rank"] == 2

    def test_unreachable_and_error_handling(self):
        """Verify cities with error status or missing AQI are placed at bottom without fake ranks."""
        input_data = {
            "CityOnline": {"status": "success", "aqi": 120, "pollutants": {"pm2_5": 40.0}},
            "CityOffline": {"status": "error", "aqi": None, "pollutants": {}, "error_message": "Timeout"}
        }
        ranked = rank_cities(input_data)
        assert ranked[0]["city"] == "CityOnline"
        assert ranked[0]["rank"] == 1
        assert ranked[0]["is_reporting"] is True

        assert ranked[1]["city"] == "CityOffline"
        assert ranked[1]["rank"] is None
        assert ranked[1]["rank_display"] == "—"
        assert ranked[1]["is_reporting"] is False

    def test_national_summary_calculation(self):
        """Verify aggregation math for national metrics."""
        input_data = {
            "Lahore": {"status": "success", "aqi": 300, "pollutants": {"pm2_5": 150.0}},
            "Karachi": {"status": "success", "aqi": 100, "pollutants": {"pm2_5": 35.0}},
            "Islamabad": {"status": "success", "aqi": 80, "pollutants": {"pm2_5": 25.0}},
            "Quetta": {"status": "error", "aqi": None, "pollutants": {}}
        }
        ranked = rank_cities(input_data)
        summary = calculate_national_summary(ranked)

        assert summary["reporting_count"] == 3
        assert summary["total_stations"] == 4
        assert summary["reporting_percentage"] == 75.0
        assert summary["average_aqi"] == round((300 + 100 + 80) / 3, 1)
        assert summary["worst_city"] == "Lahore"
        assert summary["worst_aqi"] == 300
        assert summary["cleanest_city"] == "Islamabad"
        assert summary["cleanest_aqi"] == 80
        assert summary["unhealthy_count"] == 1  # 300 is > 150

    def test_national_summary_all_offline(self):
        """Verify summary does not fail or produce NaN when all stations are offline."""
        input_data = {
            "CityA": {"status": "error", "aqi": None, "pollutants": {}},
            "CityB": {"status": "error", "aqi": None, "pollutants": {}}
        }
        ranked = rank_cities(input_data)
        summary = calculate_national_summary(ranked)
        assert summary["reporting_count"] == 0
        assert summary["average_aqi"] is None
        assert summary["worst_city"] is None
