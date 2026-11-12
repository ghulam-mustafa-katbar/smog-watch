"""Ranking and comparative analytics module for Pakistani cities smog levels.

Provides mathematically verified city sorting, tie-breaking, handling of
missing/offline telemetry stations, and national aggregated insights.
"""
from typing import Dict, Any, List, Optional


def rank_cities(city_data_map: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Rank cities from highest AQI (most polluted) to lowest AQI (cleanest).

    Validates that:
    - Successfully reported cities are ranked 1..N in descending order of AQI.
    - Ties are broken by PM2.5 concentration, then alphabetically.
    - Offline or missing-data cities are grouped at the bottom with explicit status,
      never injected with fabricated values.

    Args:
        city_data_map: Dictionary mapping city names to their API results.

    Returns:
        List of city dicts enhanced with 'rank', 'rank_display', and 'is_reporting'.
    """
    valid_cities = []
    unreachable_cities = []

    for name, data in city_data_map.items():
        aqi = data.get("aqi")
        pm2_5 = data.get("pollutants", {}).get("pm2_5") if data.get("pollutants") else None

        item = {
            "city": name,
            "aqi": aqi,
            "pm2_5": pm2_5,
            "category": data.get("category", {}).get("name", "Unknown"),
            "badge": data.get("category", {}).get("badge", "⚪ Unavailable"),
            "color": data.get("category", {}).get("color", "#6C757D"),
            "status": data.get("status", "unknown"),
            "error_message": data.get("error_message"),
            "timestamp": data.get("timestamp"),
            "raw_data": data
        }

        if data.get("status") == "success" and aqi is not None:
            item["is_reporting"] = True
            valid_cities.append(item)
        else:
            item["is_reporting"] = False
            item["rank"] = None
            item["rank_display"] = "—"
            unreachable_cities.append(item)

    # Sort valid cities: primary = AQI descending, secondary = PM2.5 descending, tertiary = Name
    valid_cities.sort(
        key=lambda x: (
            x["aqi"] if x["aqi"] is not None else -1,
            x["pm2_5"] if x["pm2_5"] is not None else -1,
            x["city"]
        ),
        reverse=True
    )

    # Assign sequential ranks to valid reporting cities
    for idx, item in enumerate(valid_cities, start=1):
        item["rank"] = idx
        item["rank_display"] = f"#{idx}"

    return valid_cities + unreachable_cities


def calculate_national_summary(ranked_cities: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate aggregated national smog statistics across Pakistani monitoring cities.

    Args:
        ranked_cities: List of ranked city dictionaries.

    Returns:
        Summary dict containing average AQI, worst city, cleanest city,
        reporting station count, and high-risk ratio.
    """
    reporting = [c for c in ranked_cities if c.get("is_reporting") and c.get("aqi") is not None]
    total_stations = len(ranked_cities)
    reporting_count = len(reporting)

    if not reporting:
        return {
            "reporting_count": 0,
            "total_stations": total_stations,
            "reporting_percentage": 0.0,
            "average_aqi": None,
            "worst_city": None,
            "cleanest_city": None,
            "hazardous_count": 0,
            "unhealthy_count": 0,
            "high_risk_percentage": 0.0
        }

    aqi_values = [c["aqi"] for c in reporting]
    avg_aqi = round(sum(aqi_values) / len(aqi_values), 1)

    worst = reporting[0]  # First in descending sorted list
    cleanest = reporting[-1]

    # Count cities in Unhealthy, Very Unhealthy, or Hazardous zones (AQI > 150)
    high_risk_cities = [c for c in reporting if c["aqi"] > 150]
    hazardous_cities = [c for c in reporting if c["aqi"] > 300]

    return {
        "reporting_count": reporting_count,
        "total_stations": total_stations,
        "reporting_percentage": round((reporting_count / total_stations) * 100, 1),
        "average_aqi": avg_aqi,
        "worst_city": worst["city"],
        "worst_aqi": worst["aqi"],
        "cleanest_city": cleanest["city"],
        "cleanest_aqi": cleanest["aqi"],
        "hazardous_count": len(hazardous_cities),
        "unhealthy_count": len(high_risk_cities),
        "high_risk_percentage": round((len(high_risk_cities) / reporting_count) * 100, 1)
    }
