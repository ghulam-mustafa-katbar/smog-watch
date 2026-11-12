"""Configuration module for Smog Watch.

Defines supported Pakistani cities, EPA AQI breakpoints, color palettes,
health advisories, and API networking defaults.
"""
from typing import Dict, Any, List

# Supported Pakistani Cities with verified latitude & longitude
PAKISTAN_CITIES: Dict[str, Dict[str, Any]] = {
    "Lahore": {
        "name": "Lahore",
        "province": "Punjab",
        "latitude": 31.5204,
        "longitude": 74.3587,
        "is_primary": True,
        "description": "Second largest city in Pakistan, highly prone to winter smog."
    },
    "Karachi": {
        "name": "Karachi",
        "province": "Sindh",
        "latitude": 24.8607,
        "longitude": 67.0011,
        "is_primary": True,
        "description": "Financial hub and coastal megacity."
    },
    "Islamabad": {
        "name": "Islamabad",
        "province": "ICT",
        "latitude": 33.6844,
        "longitude": 73.0479,
        "is_primary": True,
        "description": "Federal capital located at the foothills of Margalla Hills."
    },
    "Faisalabad": {
        "name": "Faisalabad",
        "province": "Punjab",
        "latitude": 31.4504,
        "longitude": 73.1350,
        "is_primary": True,
        "description": "Major industrial & textile center in Punjab."
    },
    "Peshawar": {
        "name": "Peshawar",
        "province": "Khyber Pakhtunkhwa",
        "latitude": 34.0151,
        "longitude": 71.5249,
        "is_primary": True,
        "description": "Historic valley city and capital of Khyber Pakhtunkhwa."
    },
    # Secondary Pakistani cities (optional expansion)
    "Multan": {
        "name": "Multan",
        "province": "Punjab",
        "latitude": 30.1575,
        "longitude": 71.5249,
        "is_primary": False,
        "description": "Major urban center in southern Punjab."
    },
    "Gujranwala": {
        "name": "Gujranwala",
        "province": "Punjab",
        "latitude": 32.1877,
        "longitude": 74.1945,
        "is_primary": False,
        "description": "Industrial manufacturing hub in northern Punjab."
    }
}

# The five mandatory primary Pakistani cities required by assignment specs
PRIMARY_FIVE_CITIES: List[str] = [
    "Lahore",
    "Karachi",
    "Islamabad",
    "Faisalabad",
    "Peshawar"
]

# Open-Meteo Air Quality API parameters
API_BASE_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
API_CONNECT_TIMEOUT = 5.0
API_READ_TIMEOUT = 10.0
API_RETRY_TOTAL = 3
API_RETRY_BACKOFF = 0.5
CACHE_TTL_SECONDS = 600  # 10 minutes cache per Streamlit best practice

# Pollutants tracked with units
POLLUTANT_METADATA: Dict[str, Dict[str, str]] = {
    "pm2_5": {
        "label": "PM2.5",
        "name": "Fine Particulate Matter",
        "unit": "µg/m³",
        "description": "Inhalable particles with diameters 2.5 micrometers and smaller."
    },
    "pm10": {
        "label": "PM10",
        "name": "Coarse Particulate Matter",
        "unit": "µg/m³",
        "description": "Inhalable particles with diameters 10 micrometers and smaller."
    },
    "nitrogen_dioxide": {
        "label": "NO₂",
        "name": "Nitrogen Dioxide",
        "unit": "µg/m³",
        "description": "Formed from vehicle emissions and burning of fossil fuels."
    },
    "sulphur_dioxide": {
        "label": "SO₂",
        "name": "Sulphur Dioxide",
        "unit": "µg/m³",
        "description": "Produced by industrial processes and power generation."
    },
    "ozone": {
        "label": "O₃",
        "name": "Ground-Level Ozone",
        "unit": "µg/m³",
        "description": "Secondary pollutant created by chemical reactions in sunlight."
    },
    "carbon_monoxide": {
        "label": "CO",
        "name": "Carbon Monoxide",
        "unit": "µg/m³",
        "description": "Colorless, odorless gas emitted by combustion processes."
    }
}

# US EPA AQI Categories, Breakpoints & Health Advisories
AQI_CATEGORIES: List[Dict[str, Any]] = [
    {
        "name": "Good",
        "min_aqi": 0,
        "max_aqi": 50,
        "color": "#00E400",
        "text_color": "#000000",
        "badge": "🟢 Good",
        "health_statement": "Air quality is considered satisfactory, and air pollution poses little or no risk.",
        "advisory": {
            "general": "Ideal air quality for outdoor activities.",
            "sensitive": "No special precautions needed.",
            "mask_recommended": False,
            "air_purifier_recommended": False,
            "outdoor_exercise": "Safe"
        }
    },
    {
        "name": "Moderate",
        "min_aqi": 51,
        "max_aqi": 100,
        "color": "#FFFF00",
        "text_color": "#000000",
        "badge": "🟡 Moderate",
        "health_statement": "Air quality is acceptable; however, very sensitive individuals may experience minor symptoms.",
        "advisory": {
            "general": "Acceptable air quality for most individuals.",
            "sensitive": "Unusually sensitive people should consider reducing prolonged outdoor exertion.",
            "mask_recommended": False,
            "air_purifier_recommended": False,
            "outdoor_exercise": "Acceptable"
        }
    },
    {
        "name": "Unhealthy for Sensitive Groups",
        "min_aqi": 101,
        "max_aqi": 150,
        "color": "#FF7E00",
        "text_color": "#FFFFFF",
        "badge": "🟠 Sensitive Beware",
        "health_statement": "Members of sensitive groups may experience health effects. The general public is less likely to be affected.",
        "advisory": {
            "general": "General public can still engage in normal activities.",
            "sensitive": "People with respiratory or heart disease, the elderly and children should limit prolonged outdoor exertion.",
            "mask_recommended": True,
            "air_purifier_recommended": False,
            "outdoor_exercise": "Reduce intensity"
        }
    },
    {
        "name": "Unhealthy",
        "min_aqi": 151,
        "max_aqi": 200,
        "color": "#FF0000",
        "text_color": "#FFFFFF",
        "badge": "🔴 Unhealthy",
        "health_statement": "Everyone may begin to experience health effects; members of sensitive groups may experience more serious health effects.",
        "advisory": {
            "general": "Everyone should reduce prolonged outdoor activities. Wear N95/KN95 masks outside.",
            "sensitive": "Avoid prolonged outdoor exertion; keep windows closed and run air filters.",
            "mask_recommended": True,
            "air_purifier_recommended": True,
            "outdoor_exercise": "Avoid heavy exertion"
        }
    },
    {
        "name": "Very Unhealthy",
        "min_aqi": 201,
        "max_aqi": 300,
        "color": "#8F3F97",
        "text_color": "#FFFFFF",
        "badge": "🟣 Very Unhealthy",
        "health_statement": "Health alert: The risk of health effects is increased for everyone in the population.",
        "advisory": {
            "general": "Active children and adults should avoid all outdoor exertion. Keep windows and doors tightly sealed.",
            "sensitive": "Remain indoors and keep activity levels low. Use certified HEPA air purifiers.",
            "mask_recommended": True,
            "air_purifier_recommended": True,
            "outdoor_exercise": "Strictly avoid"
        }
    },
    {
        "name": "Hazardous",
        "min_aqi": 301,
        "max_aqi": 500,
        "color": "#7E0023",
        "text_color": "#FFFFFF",
        "badge": "🟤 Hazardous",
        "health_statement": "Health warning of emergency conditions: The entire population is likely to be affected.",
        "advisory": {
            "general": "Emergency conditions. Entire population should avoid outdoor physical exertion. Wear N95 masks at all times outdoors.",
            "sensitive": "Remain indoors, sealed environment with air filtration. Seek medical attention if experiencing breathing distress.",
            "mask_recommended": True,
            "air_purifier_recommended": True,
            "outdoor_exercise": "Prohibited"
        }
    },
    {
        "name": "Beyond Index / Severe Hazard",
        "min_aqi": 501,
        "max_aqi": 9999,
        "color": "#4A0012",
        "text_color": "#FFFFFF",
        "badge": "⚠️ Beyond Index",
        "health_statement": "Catastrophic pollution level exceeding standard scale limits. Severe acute health risk.",
        "advisory": {
            "general": "Severe public health emergency. Strictly stay indoors. Comply with government smog lockdowns.",
            "sensitive": "High risk of acute pulmonary or cardiovascular exacerbation. Seek emergency shelter.",
            "mask_recommended": True,
            "air_purifier_recommended": True,
            "outdoor_exercise": "Prohibited"
        }
    }
]

# US EPA Breakpoint tables for AQI linear interpolation (concentration C_lo to C_hi -> AQI I_lo to I_hi)
# Units: PM2.5 (ug/m3), PM10 (ug/m3), NO2 (ug/m3 -> approx 1 ppb = 1.88 ug/m3), SO2 (ug/m3), O3 (ug/m3)
EPA_BREAKPOINTS: Dict[str, List[Dict[str, float]]] = {
    "pm2_5": [
        {"c_low": 0.0, "c_high": 12.0, "i_low": 0, "i_high": 50},
        {"c_low": 12.1, "c_high": 35.4, "i_low": 51, "i_high": 100},
        {"c_low": 35.5, "c_high": 55.4, "i_low": 101, "i_high": 150},
        {"c_low": 55.5, "c_high": 150.4, "i_low": 151, "i_high": 200},
        {"c_low": 150.5, "c_high": 250.4, "i_low": 201, "i_high": 300},
        {"c_low": 250.5, "c_high": 350.4, "i_low": 301, "i_high": 400},
        {"c_low": 350.5, "c_high": 500.4, "i_low": 401, "i_high": 500},
    ],
    "pm10": [
        {"c_low": 0.0, "c_high": 54.0, "i_low": 0, "i_high": 50},
        {"c_low": 55.0, "c_high": 154.0, "i_low": 51, "i_high": 100},
        {"c_low": 155.0, "c_high": 254.0, "i_low": 101, "i_high": 150},
        {"c_low": 255.0, "c_high": 354.0, "i_low": 151, "i_high": 200},
        {"c_low": 355.0, "c_high": 424.0, "i_low": 201, "i_high": 300},
        {"c_low": 425.0, "c_high": 504.0, "i_low": 301, "i_high": 400},
        {"c_low": 505.0, "c_high": 604.0, "i_low": 401, "i_high": 500},
    ]
}
