"""CSV ingestion and normalization utilities.

The loader does not download data and does not manufacture observations.  It
accepts a supplied local CSV so that its calculation code stays source-agnostic.
"""

import csv
from datetime import date
from pathlib import Path
from typing import Any


MORTALITY_ALIASES = {
    "date": ("date", "day"),
    "location": ("location", "city", "district", "state"),
    "deaths": ("deaths", "death_count", "all_cause_deaths"),
}
THERMAL_ALIASES = {
    "date": ("date", "day"),
    "location": ("location", "city", "district", "state"),
    "temperature": ("temperature", "temp", "temperature_c"),
    "humidity": ("humidity", "relative_humidity"),
    "wind_speed": ("wind_speed", "wind", "wind_speed_ms"),
    "radiation": ("radiation", "shortwave_radiation"),
    "thermal_stress": ("thermal_stress", "htsi", "wbgt", "utci"),
}


def _value(row: dict[str, str], aliases: tuple[str, ...], required: bool = True) -> str | None:
    for alias in aliases:
        value = row.get(alias)
        if value not in (None, ""):
            return value
    if required:
        raise ValueError(f"Missing required column; expected one of: {', '.join(aliases)}")
    return None


def _iso_date(value: str) -> str:
    return date.fromisoformat(value).isoformat()


def load_mortality_history(path: str | Path) -> list[dict[str, Any]]:
    """Load a CSV into the normalized date, location, deaths format."""
    records: list[dict[str, Any]] = []
    with Path(path).open(newline="", encoding="utf-8-sig") as file:
        for row in csv.DictReader(file):
            records.append(
                {
                    "date": _iso_date(str(_value(row, MORTALITY_ALIASES["date"]))),
                    "location": str(_value(row, MORTALITY_ALIASES["location"])),
                    "deaths": float(_value(row, MORTALITY_ALIASES["deaths"])),
                    "population": _optional_float(row.get("population")),
                    "age_0_17": _optional_float(row.get("age_0_17")),
                    "age_18_59": _optional_float(row.get("age_18_59")),
                    "age_60_plus": _optional_float(row.get("age_60_plus")),
                    "hospitalizations": _optional_float(row.get("hospitalizations")),
                    "cause_of_death": row.get("cause_of_death") or None,
                }
            )
    return records


def load_thermal_history(path: str | Path) -> list[dict[str, Any]]:
    """Load a CSV into the normalized weather/thermal-stress format."""
    records: list[dict[str, Any]] = []
    with Path(path).open(newline="", encoding="utf-8-sig") as file:
        for row in csv.DictReader(file):
            record: dict[str, Any] = {
                "date": _iso_date(str(_value(row, THERMAL_ALIASES["date"]))),
                "location": str(_value(row, THERMAL_ALIASES["location"])),
            }
            for field in ("temperature", "humidity", "wind_speed", "radiation", "thermal_stress"):
                record[field] = _optional_float(_value(row, THERMAL_ALIASES[field], False))
            if record["thermal_stress"] is None:
                raise ValueError("Thermal history requires thermal_stress, htsi, wbgt, or utci.")
            records.append(record)
    return records


def join_daily_histories(
    mortality_records: list[dict[str, Any]], thermal_records: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Join normalized records only on the shared date and location keys."""
    thermal_by_key = {(row["date"], row["location"]): row for row in thermal_records}
    return [
        {**mortality, **thermal_by_key[(mortality["date"], mortality["location"])]}
        for mortality in mortality_records
        if (mortality["date"], mortality["location"]) in thermal_by_key
    ]


def _optional_float(value: str | None) -> float | None:
    return None if value in (None, "") else float(value)
