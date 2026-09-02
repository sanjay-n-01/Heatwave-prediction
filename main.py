"""Standalone personalized heat-risk API component.

This module deliberately does not calculate WBGT.  Pass the WBGT value from
the existing WBGT service to ``get_risk`` or to the API endpoints below.
"""

from datetime import date
from pathlib import Path
from typing import Annotated, Literal

from fastapi import FastAPI, Query
from pydantic import BaseModel, Field, model_validator

from data_sources import MANUAL_FALLBACK_SOURCE
from mortality import (
    calibrate_mortality_model,
    calculate_mortality_risk,
    create_mortality_forecast,
)


app = FastAPI(title="Heatwave Risk API")

TIER_ORDER = ["Safe", "Caution", "Danger", "Extreme"]
SCORES = {
    "Safe": 25,
    "Caution": 50,
    "Danger": 75,
    "Extreme": 100,
}


class MortalityProvenance(BaseModel):
    """Source details shown with every population mortality response."""

    mortality_source: str
    source_type: str
    date_range: str
    location: str
    original_provider: str | None = None
    source_url: str | None = None
    is_real_historical_data: bool = False


class HistoricalObservation(BaseModel):
    """One joined, daily population mortality and neutral-stress observation."""

    date: date
    location: str
    deaths: float = Field(ge=0)
    thermal_stress: float


class CalibrationRequest(BaseModel):
    historical_records: list[HistoricalObservation] = Field(min_length=1)
    data_provenance: MortalityProvenance


class MortalityModel(BaseModel):
    calibration_status: Literal["CALIBRATED", "NOT_CALIBRATED", "INSUFFICIENT_DATA"]
    beta: float | None = None
    reference_stress: float | None = None

    @model_validator(mode="after")
    def calibrated_model_needs_parameters(self) -> "MortalityModel":
        if self.calibration_status == "CALIBRATED" and (
            self.beta is None or self.reference_stress is None
        ):
            raise ValueError("A calibrated model requires beta and reference_stress.")
        return self


class MortalityRiskRequest(BaseModel):
    thermal_stress: float
    baseline_deaths: float | None = Field(default=None, ge=0)
    model: MortalityModel
    data_provenance: MortalityProvenance

    @model_validator(mode="after")
    def calibrated_request_needs_real_provenance(self) -> "MortalityRiskRequest":
        if self.model.calibration_status == "CALIBRATED" and not self.data_provenance.is_real_historical_data:
            raise ValueError("A calibrated model must cite declared-real historical mortality data.")
        return self


class ThermalForecastDay(BaseModel):
    date: date
    thermal_stress: float


class MortalityForecastRequest(BaseModel):
    thermal_forecast: list[ThermalForecastDay] = Field(min_length=3, max_length=5)
    baseline_deaths: float | None = Field(default=None, ge=0)
    model: MortalityModel
    data_provenance: MortalityProvenance

    @model_validator(mode="after")
    def calibrated_request_needs_real_provenance(self) -> "MortalityForecastRequest":
        if self.model.calibration_status == "CALIBRATED" and not self.data_provenance.is_real_historical_data:
            raise ValueError("A calibrated model must cite declared-real historical mortality data.")
        return self


def _response_provenance(provenance: MortalityProvenance, status: str) -> dict[str, object]:
    """Attach explicit provenance without exposing implementation-only fields."""
    return {
        "mortality_source": provenance.mortality_source,
        "source_type": provenance.source_type,
        "date_range": provenance.date_range,
        "location": provenance.location,
        "original_provider": provenance.original_provider,
        "source_url": provenance.source_url,
        "calibration_status": status,
    }


def get_risk(
    wbgt: float,
    age: int,
    has_cardio: bool,
    has_respiratory: bool,
    outdoor_labor: bool,
) -> dict[str, int | str]:
    """Return a personalized heat-risk tier and its fixed numeric score."""
    if wbgt < 27:
        tier = "Safe"
    elif wbgt < 32:
        tier = "Caution"
    elif wbgt <= 38:
        tier = "Danger"
    else:
        tier = "Extreme"

    is_vulnerable = (
        age > 60 or has_cardio or has_respiratory or outdoor_labor
    )
    if is_vulnerable:
        tier_index = min(TIER_ORDER.index(tier) + 1, len(TIER_ORDER) - 1)
        tier = TIER_ORDER[tier_index]

    return {"tier": tier, "score": SCORES[tier]}


def create_alert_preview(
    lat: float,
    lon: float,
    wbgt: float,
    tier: str,
) -> dict[str, float | str | dict[str, float | int]]:
    """Build a fake alert payload for a demo UI; it does not send an alert."""
    return {
        "lat": lat,
        "lon": lon,
        "wbgt": wbgt,
        "tier": tier,
        "vitals": {
            "heart_rate": 105,
            "body_temperature": 38.1,
        },
    }


@app.get("/risk")
def risk(
    wbgt: float,
    age: Annotated[int, Query(ge=0)],
    has_cardio: bool,
    has_respiratory: bool,
    outdoor_labor: bool,
) -> dict[str, int | str]:
    """Return the personalized risk for a WBGT reading and user profile."""
    return get_risk(wbgt, age, has_cardio, has_respiratory, outdoor_labor)


@app.get("/alert-preview")
def alert_preview(
    wbgt: float,
    age: Annotated[int, Query(ge=0)],
    has_cardio: bool,
    has_respiratory: bool,
    outdoor_labor: bool,
    lat: float = 12.9,
    lon: float = 80.2,
) -> dict[str, float | str | dict[str, float | int]]:
    """Return a fake UI/demo alert preview based on the calculated risk."""
    risk_result = get_risk(
        wbgt, age, has_cardio, has_respiratory, outdoor_labor
    )
    return create_alert_preview(lat, lon, wbgt, str(risk_result["tier"]))


@app.get("/mortality/health")
def mortality_health() -> dict[str, object]:
    """Report readiness of the population mortality layer and its fallback."""
    fallback_path = Path(__file__).parent / "data" / "mortality_history.csv"
    provenance = MortalityProvenance(
        mortality_source=MANUAL_FALLBACK_SOURCE["source_name"],
        source_type=MANUAL_FALLBACK_SOURCE["source_type"],
        date_range=MANUAL_FALLBACK_SOURCE["date_range"],
        location=MANUAL_FALLBACK_SOURCE["location"],
        original_provider=MANUAL_FALLBACK_SOURCE["original_provider"],
        source_url=MANUAL_FALLBACK_SOURCE["source_url"],
        is_real_historical_data=False,
    )
    return {
        "status": "READY_FOR_REAL_DAILY_DATA",
        "daily_mortality_file_present": fallback_path.exists(),
        "scope": "Population-level statistical estimates only; not individual mortality prediction.",
        "data_provenance": _response_provenance(provenance, "NOT_CALIBRATED"),
    }


@app.post("/mortality/calibrate")
def calibrate_mortality(request: CalibrationRequest) -> dict[str, object]:
    """Calibrate only a declared-real daily population mortality history."""
    result = calibrate_mortality_model(
        [record.model_dump(mode="json") for record in request.historical_records],
        request.data_provenance.is_real_historical_data,
        request.data_provenance.location,
    )
    return {
        "model": result,
        "data_provenance": _response_provenance(
            request.data_provenance, str(result["calibration_status"])
        ),
    }


@app.post("/mortality/risk")
def mortality_risk(request: MortalityRiskRequest) -> dict[str, object]:
    """Return a calibrated population-level estimate for one stress value."""
    estimate = calculate_mortality_risk(
        request.thermal_stress,
        request.baseline_deaths,
        request.model.reference_stress,
        request.model.beta,
        request.model.calibration_status,
    )
    return {
        **estimate,
        "data_provenance": _response_provenance(
            request.data_provenance, request.model.calibration_status
        ),
    }


@app.post("/mortality/forecast")
def mortality_forecast(request: MortalityForecastRequest) -> dict[str, object]:
    """Estimate 3–5 days from each day's neutral HTSI/WBGT/UTCI value.

    The existing backend should obtain weather and calculate a neutral thermal
    measure first, then pass one value per day here. This deliberately avoids
    reimplementing or guessing the teammate's HTSI calculation.
    """
    forecast = create_mortality_forecast(
        [day.model_dump(mode="json") for day in request.thermal_forecast],
        request.baseline_deaths,
        request.model.reference_stress,
        request.model.beta,
        request.model.calibration_status,
    )
    return {
        "forecast": forecast,
        "scope": "Population-level statistical estimates only; not individual mortality prediction.",
        "data_provenance": _response_provenance(
            request.data_provenance, request.model.calibration_status
        ),
    }
