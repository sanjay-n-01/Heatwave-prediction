from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

from htsi import calculate_htsi, fetch_weather_by_coords, fetch_batch_weather

app = FastAPI(
    title="Human Thermal Stress Index (HTSI) API",
    description="Automated, location & age-aware Heat Stress Early Warning Backend",
    version="2.1.0"
)

# Request Model for Single Location + Age
class LocationRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, example=21.1458)
    longitude: float = Field(..., ge=-180, le=180, example=79.0882)
    age: int = Field(30, ge=1, le=120, description="Age of person to evaluate risk profile", example=70)

# Request Models for Batch Locations (GIS Heatmap)
class WardLocation(BaseModel):
    ward_name: str = Field(..., example="Ward 12 - Sitabuldi")
    latitude: float = Field(..., example=21.1458)
    longitude: float = Field(..., example=79.0882)
    age: Optional[int] = Field(30, example=68)

class BatchLocationRequest(BaseModel):
    wards: List[WardLocation]


@app.get("/")
def home():
    return {
        "status": "online", 
        "system": "Human Thermal Stress Index (HTSI) Age-Aware Early Warning Module"
    }


@app.post("/calculate-by-location")
async def get_htsi_by_location(req: LocationRequest):
    """Calculates real-time age-adjusted HTSI for a single location."""
    try:
        weather = await fetch_weather_by_coords(req.latitude, req.longitude)
        
        htsi_result = calculate_htsi(
            temperature=weather["temperature"],
            humidity=weather["humidity"],
            wind_speed=weather["wind_speed"],
            radiation=weather["radiation"],
            age=req.age
        )

        return {
            "coordinates": {
                "latitude": req.latitude,
                "longitude": req.longitude
            },
            "user_profile": {
                "input_age": req.age
            },
            "fetched_weather_data": weather,
            "thermal_stress_result": htsi_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/calculate-htsi/batch")
async def get_batch_htsi(req: BatchLocationRequest):
    """Calculates real-time HTSI for multiple wards concurrently to power GIS heatmaps."""
    try:
        coords_payload = [ward.model_dump() for ward in req.wards]
        data = await fetch_batch_weather(coords_payload)
        return {
            "status": "success", 
            "total_wards_processed": len(data), 
            "zone_data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))