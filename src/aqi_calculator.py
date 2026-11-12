"""AQI calculation and categorization engine compliant with US EPA standards.

Provides rigorous mathematical interpolation, edge-case bounds handling,
and explicit missing-data handling without mock/fabricated values.
"""
import math
from typing import Optional, Dict, Any, Union
from src.config import EPA_BREAKPOINTS, AQI_CATEGORIES


def calculate_sub_aqi(pollutant: str, concentration: Optional[Union[float, int]]) -> Optional[int]:
    """Calculate the individual AQI sub-index for a specific pollutant concentration.

    Uses the official US EPA piecewise linear interpolation equation:
        Ip = ((I_high - I_low) / (BP_high - BP_low)) * (Cp - BP_low) + I_low

    Args:
        pollutant: The pollutant key ('pm2_5' or 'pm10').
        concentration: Measured ambient concentration in µg/m³.

    Returns:
        Integer AQI sub-index, or None if concentration is invalid/missing.
    """
    if concentration is None:
        return None

    try:
        val = float(concentration)
    except (ValueError, TypeError):
        return None

    if math.isnan(val) or val < 0.0:
        return None

    breakpoints = EPA_BREAKPOINTS.get(pollutant)
    if not breakpoints:
        return None

    # EPA rounding convention
    if pollutant == "pm2_5":
        cp = math.floor(val * 10) / 10.0  # Truncate to 1 decimal place
    elif pollutant == "pm10":
        cp = float(round(val))  # Round to nearest integer
    else:
        cp = val

    for bp in breakpoints:
        c_low = bp["c_low"]
        c_high = bp["c_high"]
        i_low = bp["i_low"]
        i_high = bp["i_high"]

        if c_low <= cp <= c_high:
            raw_aqi = ((i_high - i_low) / (c_high - c_low)) * (cp - c_low) + i_low
            return int(round(raw_aqi))

    # Handle concentration beyond standard scale (Hazardous / Beyond Index)
    highest_bp = breakpoints[-1]
    if cp > highest_bp["c_high"]:
        # Extrapolate linearly based on highest bracket slope
        c_range = highest_bp["c_high"] - highest_bp["c_low"]
        i_range = highest_bp["i_high"] - highest_bp["i_low"]
        excess = cp - highest_bp["c_high"]
        extrapolated = highest_bp["i_high"] + (i_range / c_range) * excess
        return int(round(extrapolated))

    return 0


def calculate_overall_aqi(pollutants: Dict[str, Optional[float]]) -> Dict[str, Any]:
    """Calculate composite overall AQI based on maximum sub-index across measured pollutants.

    According to US EPA methodology, the composite Air Quality Index for a site is
    governed by the highest individual pollutant sub-index.

    Args:
        pollutants: Dictionary mapping pollutant key to numeric concentration.

    Returns:
        Dictionary containing:
            - 'aqi': int overall AQI (or None if no valid data)
            - 'responsible_pollutant': str key of dominant pollutant
            - 'sub_indices': dict of sub-AQI values for each pollutant
            - 'category': category dictionary with health advisory
            - 'status': 'valid' or 'insufficient_data'
    """
    if not pollutants:
        return {
            "aqi": None,
            "responsible_pollutant": None,
            "sub_indices": {},
            "category": get_aqi_category(None),
            "status": "insufficient_data"
        }

    sub_indices: Dict[str, Optional[int]] = {}
    valid_sub_indices: Dict[str, int] = {}

    for pol, conc in pollutants.items():
        sub_idx = calculate_sub_aqi(pol, conc)
        sub_indices[pol] = sub_idx
        if sub_idx is not None:
            valid_sub_indices[pol] = sub_idx

    if not valid_sub_indices:
        return {
            "aqi": None,
            "responsible_pollutant": None,
            "sub_indices": sub_indices,
            "category": get_aqi_category(None),
            "status": "insufficient_data"
        }

    # Dominant pollutant is the one with highest sub-index
    dominant_pollutant = max(valid_sub_indices, key=valid_sub_indices.get)
    overall_value = valid_sub_indices[dominant_pollutant]

    category = get_aqi_category(overall_value)

    return {
        "aqi": overall_value,
        "responsible_pollutant": dominant_pollutant,
        "sub_indices": sub_indices,
        "category": category,
        "status": "valid"
    }


def get_aqi_category(aqi: Optional[int]) -> Dict[str, Any]:
    """Retrieve official category, color coding, and health advisory for an AQI score.

    Args:
        aqi: Integer AQI score, or None.

    Returns:
        Category dictionary containing label, color, advisory, and badges.
    """
    if aqi is None:
        return {
            "name": "Data Unavailable",
            "min_aqi": None,
            "max_aqi": None,
            "color": "#6C757D",
            "text_color": "#FFFFFF",
            "badge": "⚪ Unavailable",
            "health_statement": "Official real-time monitoring data is currently unavailable for this station.",
            "advisory": {
                "general": "Awaiting sensor or atmospheric model ingestion feed.",
                "sensitive": "Consult local environmental advisories if in doubt.",
                "mask_recommended": False,
                "air_purifier_recommended": False,
                "outdoor_exercise": "Unknown"
            }
        }

    for cat in AQI_CATEGORIES:
        if cat["min_aqi"] <= aqi <= cat["max_aqi"]:
            return cat

    # Fallback to extreme category if above all listed
    return AQI_CATEGORIES[-1]
