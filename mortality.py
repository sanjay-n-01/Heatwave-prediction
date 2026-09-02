"""Transparent population-level heat-mortality modelling utilities.

This module estimates statistical population mortality, never an individual's
chance of death.  It requires genuine daily historical mortality plus neutral
thermal-stress observations before it may report a calibrated model.
"""

from datetime import date
from math import exp, log
from statistics import median
from typing import Any, Iterable


MIN_CALIBRATION_DAYS = 30


def calculate_baseline_mortality(
    mortality_history: Iterable[dict[str, Any]], location: str, target_date: str
) -> dict[str, float | int | str | None]:
    """Average same-location, same-month deaths from a normalized history."""
    month = date.fromisoformat(target_date).month
    comparable = [
        float(row["deaths"])
        for row in mortality_history
        if row.get("location") == location
        and date.fromisoformat(str(row["date"])).month == month
    ]
    if not comparable:
        return {
            "baseline_deaths": None,
            "observations": 0,
            "method": "No same-month historical observations available",
        }
    return {
        "baseline_deaths": sum(comparable) / len(comparable),
        "observations": len(comparable),
        "method": "Mean daily deaths for the same location and calendar month",
    }


def calibrate_mortality_model(
    history: Iterable[dict[str, Any]],
    source_is_real_historical_data: bool,
    location: str | None = None,
) -> dict[str, Any]:
    """Fit a Poisson log-linear exposure-response model when data permit it.

    The fitted relationship is RR(x) = exp(beta * (x - reference_stress)).
    It is intentionally withheld for unverified/synthetic data or fewer than
    30 daily observations.
    """
    if not source_is_real_historical_data:
        return _uncalibrated("NOT_CALIBRATED", "Historical data is not declared real.")

    rows = [row for row in history if location is None or row.get("location") == location]
    try:
        stress = [float(row["thermal_stress"]) for row in rows]
        deaths = [float(row["deaths"]) for row in rows]
    except (KeyError, TypeError, ValueError):
        return _uncalibrated("INSUFFICIENT_DATA", "Each record needs numeric thermal_stress and deaths.")

    if len(rows) < MIN_CALIBRATION_DAYS:
        return _uncalibrated(
            "INSUFFICIENT_DATA",
            f"At least {MIN_CALIBRATION_DAYS} daily joined observations are required.",
        )
    if any(value < 0 for value in deaths) or len(set(stress)) < 2 or sum(deaths) <= 0:
        return _uncalibrated(
            "INSUFFICIENT_DATA",
            "Deaths must be non-negative and thermal stress must vary.",
        )

    reference_stress = float(median(stress))
    beta = _fit_poisson_beta(stress, deaths, reference_stress)
    if beta is None:
        return _uncalibrated("INSUFFICIENT_DATA", "Exposure-response coefficient could not be estimated.")

    baseline_at_reference = _baseline_at_reference(stress, deaths, reference_stress, beta)
    return {
        "calibration_status": "CALIBRATED",
        "method": "Poisson log-linear exposure-response fit",
        "formula": "RR(x) = exp(beta * (x - reference_stress))",
        "records_used": len(rows),
        "reference_stress": reference_stress,
        "beta": beta,
        "baseline_at_reference": baseline_at_reference,
        "scope": "Population-level statistical estimate; not individual mortality prediction.",
    }


def calculate_mortality_risk(
    thermal_stress: float,
    baseline_deaths: float | None,
    reference_stress: float | None,
    beta: float | None,
    calibration_status: str,
) -> dict[str, Any]:
    """Calculate calibrated expected and excess population mortality."""
    result: dict[str, Any] = {
        "thermal_stress": thermal_stress,
        "reference_stress": reference_stress,
        "relative_risk": None,
        "baseline_deaths": baseline_deaths,
        "expected_deaths": None,
        "excess_deaths": None,
        "risk_category": "Unavailable",
        "calibration_status": calibration_status,
        "scope": "Population-level statistical estimate; not individual mortality prediction.",
    }
    if (
        calibration_status != "CALIBRATED"
        or beta is None
        or reference_stress is None
        or baseline_deaths is None
    ):
        return result

    relative_risk = exp(beta * (thermal_stress - reference_stress))
    expected_deaths = baseline_deaths * relative_risk
    result.update(
        {
            "relative_risk": relative_risk,
            "expected_deaths": expected_deaths,
            "excess_deaths": expected_deaths - baseline_deaths,
            "risk_category": _risk_category(relative_risk),
        }
    )
    return result


def create_mortality_forecast(
    thermal_forecast: Iterable[dict[str, Any]],
    baseline_deaths: float | None,
    reference_stress: float | None,
    beta: float | None,
    calibration_status: str,
) -> list[dict[str, Any]]:
    """Estimate each supplied forecast day independently from its own stress."""
    forecast = []
    for day in thermal_forecast:
        estimate = calculate_mortality_risk(
            float(day["thermal_stress"]),
            baseline_deaths,
            reference_stress,
            beta,
            calibration_status,
        )
        forecast.append({"date": day["date"], **estimate})
    return forecast


def _fit_poisson_beta(stress: list[float], deaths: list[float], reference: float) -> float | None:
    """Fit one Poisson slope by stable bisection of the likelihood score."""
    centered = [value - reference for value in stress]
    observed_mean = sum(value * count for value, count in zip(centered, deaths)) / sum(deaths)

    def score(beta: float) -> float:
        scaled = [beta * value for value in centered]
        shift = max(scaled)
        weights = [exp(value - shift) for value in scaled]
        weighted_mean = sum(value * weight for value, weight in zip(centered, weights)) / sum(weights)
        return observed_mean - weighted_mean

    lower, upper = -20.0, 20.0
    if score(lower) * score(upper) > 0:
        return None
    for _ in range(80):
        midpoint = (lower + upper) / 2
        if score(midpoint) > 0:
            lower = midpoint
        else:
            upper = midpoint
    return (lower + upper) / 2


def _baseline_at_reference(stress: list[float], deaths: list[float], reference: float, beta: float) -> float:
    scaled = [beta * (value - reference) for value in stress]
    shift = max(scaled)
    scaled_total = sum(exp(value - shift) for value in scaled)
    return exp(log(sum(deaths)) - shift - log(scaled_total))


def _risk_category(relative_risk: float) -> str:
    if relative_risk < 1.05:
        return "Low"
    if relative_risk < 1.20:
        return "Moderate"
    if relative_risk < 1.50:
        return "High"
    return "Extreme"


def _uncalibrated(status: str, reason: str) -> dict[str, Any]:
    return {
        "calibration_status": status,
        "reason": reason,
        "beta": None,
        "reference_stress": None,
        "baseline_at_reference": None,
        "scope": "Population-level statistical estimate; not individual mortality prediction.",
    }
