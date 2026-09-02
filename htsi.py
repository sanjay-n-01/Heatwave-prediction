import math
import httpx

def calculate_htsi(
    temperature: float, 
    humidity: float, 
    wind_speed: float, 
    radiation: float, 
    age: int = 30,
    has_cardiac_condition: bool = False,
    has_respiratory_condition: bool = False,
    is_outdoor_worker: bool = False
) -> dict:
    """Calculates personalized HTSI score, risk level, and advisory."""
    T = (temperature * 9 / 5) + 32
    RH = humidity

    hi_f = 0.5 * (T + 61.0 + ((T - 68.0) * 1.2) + (RH * 0.094))

    if hi_f >= 80:
        hi_f = (
            -42.379 + (2.04901523 * T) + (10.14333127 * RH)
            - (0.22475541 * T * RH) - (6.83783e-3 * T**2)
            - (5.481717e-2 * RH**2) + (1.22874e-3 * (T**2) * RH)
            + (8.5282e-4 * T * (RH**2)) - (1.99e-6 * (T**2) * (RH**2))
        )
        if RH < 13 and 80 <= T <= 112:
            hi_f -= ((13 - RH) / 4) * math.sqrt((17 - abs(T - 95.0)) / 17)
        elif RH > 85 and 80 <= T <= 87:
            hi_f += ((RH - 85) / 10) * ((87 - T) / 5)

    heat_index_c = (hi_f - 32) * 5 / 9
    base_htsi = heat_index_c + (0.015 * radiation) - (0.5 * wind_speed)

    # Age Group Logic
    if age < 18:
        age_category = "Child"
        vulnerability_multiplier = 1.10
    elif 18 <= age <= 25:
        age_category = "Young Adult"
        vulnerability_multiplier = 1.00
    elif 26 <= age <= 39:
        age_category = "Adult"
        vulnerability_multiplier = 1.00
    elif 40 <= age <= 59:
        age_category = "Middle Age"
        vulnerability_multiplier = 1.05
    else:
        age_category = "Senior Citizen"
        vulnerability_multiplier = 1.15

    # Health & Labor Multipliers
    risk_factors = []
    if has_cardiac_condition:
        vulnerability_multiplier += 0.12
        risk_factors.append("Cardiac Condition")
    if has_respiratory_condition:
        vulnerability_multiplier += 0.10
        risk_factors.append("Respiratory Condition")
    if is_outdoor_worker:
        vulnerability_multiplier += 0.15
        risk_factors.append("Outdoor Physical Labor")

    adjusted_htsi = base_htsi * vulnerability_multiplier

    if adjusted_htsi < 30:
        risk_level, alert_color = "Low Risk", "Green"
        advice = "Normal outdoor activities are safe."
    elif adjusted_htsi < 38:
        risk_level, alert_color = "Moderate Risk", "Yellow"
        advice = "Maintain constant hydration. Avoid continuous direct sunlight."
    elif adjusted_htsi < 46:
        risk_level, alert_color = "High Risk", "Orange"
        advice = "Vulnerable groups should remain indoors in cooled areas." if (has_cardiac_condition or has_respiratory_condition or age >= 60) else "Limit outdoor exertion."
    else:
        risk_level, alert_color = "Extreme Risk", "Red"
        advice = "Heat Emergency! High risk of heatstroke. Seek immediate cooling."

    return {
        "base_htsi_score": round(base_htsi, 2),
        "personalized_htsi_score": round(adjusted_htsi, 2),
        "age_group": age_category,
        "vulnerability_factors_detected": risk_factors if risk_factors else ["None"],
        "risk_level": risk_level,
        "alert_color": alert_color,
        "advisory": advice
    }


async def fetch_location_name(lat: float, lon: float) -> str:
    """Converts GPS Coordinates into a human-readable city/area name using Open-Meteo Geocoding."""
    url = "https://geocoding-api.open-meteo.com/v1/reverse"
    params = {"latitude": lat, "longitude": lon, "count": 1}
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(url, params=params)
            data = res.json()
            if "results" in data and len(data["results"]) > 0:
                result = data["results"][0]
                name = result.get("name", "")
                admin1 = result.get("admin1", "")
                return f"{name}, {admin1}".strip(", ")
        except Exception:
            pass
    return "Detected GPS Location"


async def fetch_weather_and_forecast(latitude: float, longitude: float) -> dict:
    """Fetches real-time weather and 4-day daily forecast from Open-Meteo."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": ["temperature_2m", "relative_humidity_2m", "wind_speed_10m", "direct_radiation"],
        "daily": ["temperature_2m_max", "relative_humidity_2m_mean", "wind_speed_10m_max", "shortwave_radiation_sum"],
        "forecast_days": 5,
        "timezone": "auto"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        if response.status_code != 200:
            raise Exception("Failed to fetch weather forecast data.")
        
        data = response.json()
        current_data = data.get("current", {})
        daily_data = data.get("daily", {})
        
        current_weather = {
            "temperature": current_data.get("temperature_2m", 0.0),
            "humidity": current_data.get("relative_humidity_2m", 0.0),
            "wind_speed": current_data.get("wind_speed_10m", 0.0),
            "radiation": current_data.get("direct_radiation", 0.0)
        }

        forecast_list = []
        dates = daily_data.get("time", [])
        temps = daily_data.get("temperature_2m_max", [])
        humidities = daily_data.get("relative_humidity_2m_mean", [])
        winds = daily_data.get("wind_speed_10m_max", [])
        radiations = daily_data.get("shortwave_radiation_sum", [])

        for i in range(1, min(5, len(dates))):
            rad_approx = (radiations[i] * 1000000) / 86400 if i < len(radiations) and radiations[i] else 0.0
            forecast_list.append({
                "date": dates[i],
                "expected_max_temp": temps[i] if i < len(temps) else 0.0,
                "expected_avg_humidity": humidities[i] if i < len(humidities) else 0.0,
                "expected_max_wind": winds[i] if i < len(winds) else 0.0,
                "expected_radiation": round(rad_approx, 2)
            })

        return {
            "current": current_weather,
            "forecast_4_days": forecast_list
        }
