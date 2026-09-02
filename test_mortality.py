"""Tests for mortality safeguards and arithmetic.

SYNTHETIC TEST DATA — NOT REAL. These observations exercise the calibration
routine only and are not packaged as data or presented as epidemiology.
"""

from datetime import date, timedelta
from math import exp

from fastapi.testclient import TestClient

from data_loader import join_daily_histories, load_mortality_history, load_thermal_history
from main import app
from mortality import (
    calculate_baseline_mortality,
    calculate_mortality_risk,
    calibrate_mortality_model,
    create_mortality_forecast,
)


client = TestClient(app)


def synthetic_history() -> list[dict[str, float | str]]:
    start = date(2025, 5, 1)
    records = []
    for offset in range(40):
        stress = 25.0 + (offset % 11)
        deaths = max(1, round(20 * exp(0.08 * (stress - 30))))
        records.append(
            {
                "date": (start + timedelta(days=offset)).isoformat(),
                "location": "Synthetic City",
                "thermal_stress": stress,
                "deaths": float(deaths),
            }
        )
    return records


def test_unverified_data_is_never_calibrated() -> None:
    result = calibrate_mortality_model(synthetic_history(), False)
    assert result["calibration_status"] == "NOT_CALIBRATED"
    assert result["beta"] is None


def test_calibration_and_population_mortality_math() -> None:
    model = calibrate_mortality_model(synthetic_history(), True, "Synthetic City")
    assert model["calibration_status"] == "CALIBRATED"
    assert model["beta"] is not None
    assert model["reference_stress"] is not None

    estimate = calculate_mortality_risk(32, 20, 30, 0.1, "CALIBRATED")
    assert round(estimate["relative_risk"], 6) == round(exp(0.2), 6)
    assert round(estimate["expected_deaths"], 6) == round(20 * exp(0.2), 6)
    assert round(estimate["excess_deaths"], 6) == round(20 * (exp(0.2) - 1), 6)
    assert estimate["risk_category"] == "High"


def test_same_month_baseline_and_day_specific_forecast() -> None:
    baseline = calculate_baseline_mortality(synthetic_history(), "Synthetic City", "2026-05-15")
    assert baseline["observations"] == 31
    assert baseline["baseline_deaths"] is not None

    forecast = create_mortality_forecast(
        [
            {"date": "2026-05-01", "thermal_stress": 30},
            {"date": "2026-05-02", "thermal_stress": 32},
            {"date": "2026-05-03", "thermal_stress": 35},
        ],
        20,
        30,
        0.1,
        "CALIBRATED",
    )
    assert forecast[0]["relative_risk"] < forecast[1]["relative_risk"] < forecast[2]["relative_risk"]


def test_csv_normalization_and_date_location_join(tmp_path) -> None:
    """SYNTHETIC TEST DATA — NOT REAL."""
    mortality_file = tmp_path / "mortality.csv"
    mortality_file.write_text(
        "date,city,death_count\n2025-05-01,Synthetic City,12\n", encoding="utf-8"
    )
    thermal_file = tmp_path / "thermal.csv"
    thermal_file.write_text(
        "date,location,temp,relative_humidity,wind,shortwave_radiation,htsi\n"
        "2025-05-01,Synthetic City,35,50,3,200,31\n",
        encoding="utf-8",
    )
    joined = join_daily_histories(
        load_mortality_history(mortality_file), load_thermal_history(thermal_file)
    )
    assert joined == [
        {
            "date": "2025-05-01",
            "location": "Synthetic City",
            "deaths": 12.0,
            "population": None,
            "age_0_17": None,
            "age_18_59": None,
            "age_60_plus": None,
            "hospitalizations": None,
            "cause_of_death": None,
            "temperature": 35.0,
            "humidity": 50.0,
            "wind_speed": 3.0,
            "radiation": 200.0,
            "thermal_stress": 31.0,
        }
    ]


def test_mortality_endpoints_keep_unavailable_model_unavailable() -> None:
    provenance = {
        "mortality_source": "SYNTHETIC TEST DATA — NOT REAL",
        "source_type": "TEST",
        "date_range": "2025-05",
        "location": "Synthetic City",
        "is_real_historical_data": False,
    }
    health = client.get("/mortality/health")
    assert health.status_code == 200
    assert health.json()["data_provenance"]["calibration_status"] == "NOT_CALIBRATED"

    calibration = client.post(
        "/mortality/calibrate",
        json={"historical_records": synthetic_history(), "data_provenance": provenance},
    )
    assert calibration.status_code == 200
    assert calibration.json()["model"]["calibration_status"] == "NOT_CALIBRATED"

    forecast = client.post(
        "/mortality/forecast",
        json={
            "thermal_forecast": [
                {"date": "2026-05-01", "thermal_stress": 30},
                {"date": "2026-05-02", "thermal_stress": 32},
                {"date": "2026-05-03", "thermal_stress": 35},
            ],
            "baseline_deaths": 20,
            "model": {"calibration_status": "NOT_CALIBRATED"},
            "data_provenance": provenance,
        },
    )
    assert forecast.status_code == 200
    assert all(day["expected_deaths"] is None for day in forecast.json()["forecast"])

    rejected = client.post(
        "/mortality/risk",
        json={
            "thermal_stress": 35,
            "baseline_deaths": 20,
            "model": {"calibration_status": "CALIBRATED", "beta": 0.1, "reference_stress": 30},
            "data_provenance": provenance,
        },
    )
    assert rejected.status_code == 422
