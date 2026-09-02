from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from htsi import calculate_htsi, fetch_weather_and_forecast, fetch_location_name

app = FastAPI(
    title="GPS Heat Stress Prediction API",
    description="Live GPS location-based HTSI Engine with 4-day forecast",
    version="5.0.0"
)

# Nested Schema for GPS Coordinates
class GPSCoordinates(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Device GPS Latitude", example=13.0827)
    longitude: float = Field(..., ge=-180, le=180, description="Device GPS Longitude", example=80.2707)

# Input Payload with GPS object
class GPSForecastRequest(BaseModel):
    gps_location: GPSCoordinates
    age: int = Field(..., ge=1, le=120, description="User's age", example=65)
    has_cardiac_condition: bool = Field(False, example=True)
    has_respiratory_condition: bool = Field(False, example=False)
    is_outdoor_worker: bool = Field(False, example=True)


@app.post("/calculate-htsi-by-gps")
async def get_htsi_by_gps(req: GPSForecastRequest):
    """Calculates HTSI & 4-day predictions directly using device GPS location."""
    try:
        lat = req.gps_location.latitude
        lon = req.gps_location.longitude

        # 1. Reverse Geocode Location Name
        place_name = await fetch_location_name(lat, lon)
        
        # 2. Fetch Weather Data
        weather_data = await fetch_weather_and_forecast(lat, lon)
        
        # 3. Today's Live Assessment
        current = weather_data["current"]
        current_htsi = calculate_htsi(
            temperature=current["temperature"],
            humidity=current["humidity"],
            wind_speed=current["wind_speed"],
            radiation=current["radiation"],
            age=req.age,
            has_cardiac_condition=req.has_cardiac_condition,
            has_respiratory_condition=req.has_respiratory_condition,
            is_outdoor_worker=req.is_outdoor_worker
        )

        # 4. 4-Day Forecast Assessment
        upcoming_forecast_results = []
        for day in weather_data["forecast_4_days"]:
            day_htsi = calculate_htsi(
                temperature=day["expected_max_temp"],
                humidity=day["expected_avg_humidity"],
                wind_speed=day["expected_max_wind"],
                radiation=day["expected_radiation"],
                age=req.age,
                has_cardiac_condition=req.has_cardiac_condition,
                has_respiratory_condition=req.has_respiratory_condition,
                is_outdoor_worker=req.is_outdoor_worker
            )
            upcoming_forecast_results.append({
                "date": day["date"],
                "predicted_max_temp": day["expected_max_temp"],
                "predicted_htsi_score": day_htsi["personalized_htsi_score"],
                "predicted_risk_level": day_htsi["risk_level"],
                "alert_color": day_htsi["alert_color"],
                "advisory": day_htsi["advisory"]
            })

        return {
            "gps_location": {
                "address": place_name,
                "latitude": lat,
                "longitude": lon
            },
            "user_profile": {
                "age": req.age,
                "cardiac_risk": req.has_cardiac_condition,
                "respiratory_risk": req.has_respiratory_condition,
                "outdoor_labor": req.is_outdoor_worker
            },
            "today_live_assessment": {
                "weather": current,
                "htsi_result": current_htsi
            },
            "upcoming_4_day_forecast": upcoming_forecast_results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
