# Data-source assessment

This project does not bundle mortality observations. The sources below were
checked on 2 September 2026. A source is **PRIMARY** only when it can support
the proposed daily, location-specific all-cause mortality calibration; none of
the investigated sources currently meets that threshold as a directly usable
public download.

| Dataset | Source | Location | Period | Resolution | Suitable? |
|---|---|---|---|---|---|
| NCRB heat/sun-stroke deaths | [data.gov.in](https://www.data.gov.in/resource/stateut-wise-number-deaths-due-heatsun-stroke-national-crime-record-bureau-ncrbfrom-2018) | India, State/UT | 2018–2022 | Annual | SUPPORTING |
| Vital Statistics / CRS | [ORGI / Census India](https://censusindia.gov.in/nada/index.php/catalog/45564) | India, State/UT aggregates | 2022 report; annual series | Annual | SUPPORTING |
| WHO Mortality Database | [WHO](https://www.who.int/data/data-collection-tools/who-mortality-database) | Country reporting | 1950 onward where reported | Annual, cause/age/sex | SUPPORTING |
| Ahmedabad 2010 heat-wave study | [Environmental Health Perspectives](https://pmc.ncbi.nlm.nih.gov/articles/PMC3954798/) | Ahmedabad | 2009–2011 | Daily all-cause mortality in study | NOT_SUITABLE |
| Indian ten-city heatwave study | [Lancet Planetary Health article](https://pmc.ncbi.nlm.nih.gov/articles/PMC11790314/) | Ten Indian cities | 2008–2019, varies by city | Daily all-cause mortality in study | NOT_SUITABLE |
| India Mortality Dataset | [Stats of India / GitHub](https://github.com/statsofindia/india-mortality) | Selected states and districts | 2018–2021 | Monthly all-cause deaths | SUPPORTING |
| Humid heatwaves and heat-related deaths | [Zenodo](https://zenodo.org/records/15126391) | India, state level | 2001–2022 | State-level study/code outputs | SUPPORTING |
| IndiaWeatherBench | [Hugging Face](https://huggingface.co/datasets/tungnd/IndiaWeatherBench) | India | Historical/climatology files | Weather/climate only | SUPPORTING |
| Indian Climate Dataset 2024–2025 | [Kaggle](https://www.kaggle.com/datasets/ankushnarwade/indian-climate-dataset-20242025) | Major Indian cities | 2024–2025 | Daily weather/AQI only | NOT_SUITABLE |
| Open-Meteo Forecast API | [Open-Meteo](https://open-meteo.com/en/docs) | Global | Current forecast | Hourly/daily, up to 16 days | SUPPORTING |

## Provenance and limitations

### NCRB heat/sun-stroke deaths — SUPPORTING

- **Original provider:** National Crime Records Bureau, Ministry of Home Affairs, India.
- **Variables/units:** State/UT heat or sun-stroke death counts (persons).
- **Licence/usage:** Use the OGD resource terms and preserve attribution.
- **Limitations:** It is heat/sun-stroke mortality, not daily all-cause mortality; the published resource is annual 2018–2022 data. It cannot train a daily all-cause mortality response model or be merged as though it were all-cause mortality.

### Civil Registration System — SUPPORTING

- **Original provider:** Office of the Registrar General & Census Commissioner, India.
- **Variables/units:** Registered births, deaths, infant deaths and stillbirths (counts), with published demographic breakouts.
- **Licence/usage:** ORGI/Census India rights apply; cite the report.
- **Limitations:** The reviewed publication is an annual reporting product, not a downloadable daily city-level death series. Use it for demographic context and aggregate plausibility checks only.

### WHO Mortality Database — SUPPORTING

- **Original provider:** World Health Organization from national civil-registration systems.
- **Variables/units:** Country/year/age/sex/cause mortality counts and populations.
- **Licence/usage:** WHO requests non-commercial use of the detailed raw files and adherence to its data-use guidance.
- **Limitations:** The data are country-level annual cause-of-death reporting, and WHO notes India death-registration data are unavailable or unusable in its country presentation. It is not daily local mortality training data.

### Indian municipal heat-mortality studies — NOT_SUITABLE as a public input

- **Ahmedabad 2010 study:** The paper analysed daily all-cause counts from the Ahmedabad Municipal Corporation registrar, but says its de-identified data were not distributable. It is methodological evidence, not a public source to ingest.
- **Ten-city study:** It reports daily municipal death-register data for Ahmedabad, Bangalore, Chennai, Delhi, Hyderabad, Kolkata, Mumbai, Pune, Shimla and Varanasi. The publication documents methodology but does not provide a verified unrestricted daily download in the investigated materials.

### Public repositories — SUPPORTING / NOT_SUITABLE

- **Stats of India / GitHub:** A public compilation, mostly sourced from CRS, has monthly all-cause mortality for selected states/districts during 2018–2021. It is potentially useful for a monthly model or aggregate baseline, subject to its documented coverage gaps, but not for a daily 3–5-day forecast model. Treat the underlying CRS source as the original provider and preserve the repository's attribution.
- **Zenodo humid-heatwave study:** The record provides a manuscript and code for a state-level 2001–2022 study relating ERA5 wet-bulb heatwaves, population and heat-related deaths. Its record does not present a ready daily all-cause mortality table; it is supporting methodological/state-level evidence, not a daily local calibration source. The record shows no licence in its metadata, so reuse requires checking author permission.
- **Hugging Face:** IndiaWeatherBench is weather/climate data only (CC BY-NC-SA 4.0; very large files). Searches did not identify an India daily mortality-plus-weather dataset with documented provenance. It may support exposure research but cannot supply deaths.
- **Kaggle:** The investigated India climate dataset contains weather and AQI only and describes its records as realistic. It has no mortality variable and is not an authoritative exposure source; it is excluded from this system. No Kaggle dataset is treated as primary merely because it is downloadable.

### Open-Meteo — SUPPORTING weather input

- **Original provider:** Open-Meteo aggregates multiple national weather models.
- **Variables/units:** temperature (°C), humidity (%), wind and solar-radiation fields; hourly/daily forecast.
- **Licence/usage:** API data are CC BY 4.0; attribution is required.
- **Limitations:** Weather exposure is not mortality data. This project should preferentially consume the teammate's already-existing neutral HTSI forecast rather than replace it.

## Operational decision

Until a permitted, real daily location-level all-cause mortality dataset is supplied and linked to neutral daily thermal stress, API responses remain `NOT_CALIBRATED` or `INSUFFICIENT_DATA`. The manual fallback is intentionally source-agnostic, but its provenance must be explicitly declared; it is never silently treated as real or calibrated.
