import math
import httpx

def calculate_htsi(temperature: float, humidity: float, wind_speed: float, radiation: float, age: int = 30) -> dict:
    """
    Calculates Heat Index using NWS Rothfusz multi-regression formula (Celsius adjusted),
    factoring in wind, solar radiation, and age-based physiological vulnerability.
    """
    # Convert Celsius to Fahrenheit for standard NWS formula
    T = (temperature * 9 / 5) + 32
    RH = humidity

    # Simple Heat Index formula check
    hi_f = 0.5 * (T + 61.0 + ((T - 68.0) * 1.2) + (RH * 0.094))

    # If simple index is >= 80°F, use full Rothfusz regression
    if hi_f >= 80:
        hi_f = (
            -42.379 + (2.04901523 * T) + (10.14333127 * RH)
            - (0.22475541 * T * RH) - (6.83783e-3 * T**2)
            - (5.481717e-2 * RH**2) + (1.22874e-3 * (T**2) * RH)
            + (8.5282e-4 * T * (RH**2)) - (1.99e-6 * (T**2) * (RH**2))
        )
        
        # Adjustments for extreme conditions
        if RH < 13 and 80 <= T <= 112:
            hi_f -= ((13 - RH) / 4) * math.sqrt((17 - abs(T - 95.0)) / 17)
        elif RH > 85 and 80 <= T <= 87:
            hi_f += ((RH - 85) / 10) * ((87 - T) / 5)

    # Convert back to Celsius
    heat_index_c = (hi_f - 32) * 5 / 9

    # Apply adjustments for Solar Radiation (+ heat) and Wind Speed (- cooling)
    base_htsi = heat_index_c + (0.015 * radiation) - (0.5 * wind_speed)

    # Age Vulnerability Multiplier Logic
    if age >= 65:
        age_category = "Senior (High Risk Group)"
        age_multiplier = 1.15  # 15% increase in perceived heat stress
    elif age <= 10:
        age_category = "Child (High Risk Group)"
        age_multiplier = 1.10  # 10% increase in perceived heat stress
    elif age >= 50:
        age_category = "Older Adult"
        age_multiplier = 1.05  # 5% increase
    else:
        age_category = "Adult (Standard)"
        age_multiplier = 1.00  # Baseline

    # Final Age-Adjusted HTSI Score
    adjusted_htsi = base_htsi * age_multiplier

    # Risk classification & age-tailored advisories
    if adjusted_htsi < 30:
        risk_level = "Low Risk"
        alert_color = "Green"
        advice = "Normal outdoor activities are safe."
    elif adjusted_htsi < 38:
        risk_level = "Moderate Risk"
        alert_color = "Yellow"
        advice = "Drink water frequently. Limit outdoor exertion." if age < 60 else "Stay in shaded areas and maintain high hydration."
    elif adjusted_htsi < 46:
        risk_level = "High Risk"
        alert_color = "Orange"
        advice = "Restrict outdoor labor (12 PM - 4 PM)." if age < 60 else "Vulnerable age group: Stay indoors in air-conditioned or ventilated rooms."
    else:
        risk_level = "Extreme Risk"
        alert_color = "Red"
        advice = "Heat Emergency! High risk of heatstroke. Immediate cooling required."

    return {
        "base_htsi_score": round(base_htsi, 2),
        "age_adjusted_htsi_score": round(adjusted_htsi, 2),
        "age_group": age_category,
        "risk_level": risk_level,
        "alert_color": alert_color,
        "advisory": advice
    }


async def fetch_weather_by_coords(latitude: float, longitude: float) -> dict:
    """Fetches real-time weather data from Open-Meteo API using coordinates."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": ["temperature_2m", "relative_humidity_2m", "wind_speed_10m", "direct_radiation"],
        "timezone": "auto"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        if response.status_code != 200:
            raise Exception("Failed to fetch data from weather service.")
        
        data = response.json().get("current", {})
        
        return {
            "temperature": data.get("temperature_2m", 0.0),
            "humidity": data.get("relative_humidity_2m", 0.0),
            "wind_speed": data.get("wind_speed_10m", 0.0),
            "radiation": data.get("direct_radiation", 0.0)
        }


async def fetch_batch_weather(coordinates_list: list) -> list:
    """Fetches weather for multiple locations concurrently for GIS mapping."""
    results = []
    for coords in coordinates_list:
        try:
            weather = await fetch_weather_by_coords(coords["latitude"], coords["longitude"])
            age = coords.get("age", 30)
            htsi = calculate_htsi(
                weather["temperature"], 
                weather["humidity"], 
                weather["wind_speed"], 
                weather["radiation"],
                age=age
            )
            results.append({
                "ward_name": coords.get("ward_name", "Unknown Ward"),
                "latitude": coords["latitude"],
                "longitude": coords["longitude"],
                "target_age": age,
                "weather": weather,
                "htsi_result": htsi
            })
        except Exception:
            continue
    return results