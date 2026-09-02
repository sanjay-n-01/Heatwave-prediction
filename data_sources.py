"""Known data-source metadata for the population mortality layer.

This registry is documentation, not bundled training data.  Daily all-cause
mortality is not available from these sources as a ready-to-train public file.
"""

from typing import Final


MANUAL_FALLBACK_SOURCE: Final = {
    "source_name": "Local mortality_history.csv",
    "source_type": "MANUAL_FALLBACK",
    "original_provider": "Provided by deployment operator",
    "source_url": None,
    "date_range": "Unknown until supplied",
    "location": "Unknown until supplied",
    "is_real_historical_data": False,
}


DATA_SOURCE_REGISTRY: Final = [
    {
        "source_name": "NCRB heat/sun-stroke deaths",
        "source_type": "OFFICIAL",
        "original_provider": "National Crime Records Bureau, India",
        "source_url": (
            "https://www.data.gov.in/resource/stateut-wise-number-deaths-due-"
            "heatsun-stroke-national-crime-record-bureau-ncrbfrom-2018"
        ),
        "resolution": "State/UT annual values, 2018-2022",
        "suitable": "SUPPORTING",
    },
    {
        "source_name": "Civil Registration System annual report",
        "source_type": "OFFICIAL",
        "original_provider": "Office of the Registrar General & Census Commissioner, India",
        "source_url": "https://censusindia.gov.in/nada/index.php/catalog/45564",
        "resolution": "Annual registered deaths; national/state/UT reporting",
        "suitable": "SUPPORTING",
    },
    {
        "source_name": "WHO Mortality Database",
        "source_type": "OFFICIAL",
        "original_provider": "World Health Organization",
        "source_url": "https://www.who.int/data/data-collection-tools/who-mortality-database",
        "resolution": "Country/year/sex/age/cause of death",
        "suitable": "SUPPORTING",
    },
    {
        "source_name": "Open-Meteo Weather Forecast API",
        "source_type": "SUPPORTING_WEATHER",
        "original_provider": "Open-Meteo; underlying national weather services",
        "source_url": "https://open-meteo.com/en/docs",
        "resolution": "Hourly and daily forecast, up to 16 days",
        "suitable": "SUPPORTING",
    },
]
