"""Data: API ingestion for crime, weather, and community-area boundaries
(Phases 2, 6, choropleth support). Re-exports the main entrypoints so
callers can `from src.data import load_crime_data, load_weather_data,
load_or_fetch_boundaries` instead of reaching into submodules.
"""
from src.data.crime_loader import load_crime_data, save_raw_crime
from src.data.geo_loader import load_or_fetch_boundaries
from src.data.validators import validate_crime_data, validate_weather_data
from src.data.weather_loader import load_weather_data, save_raw_weather

__all__ = [
    "load_crime_data",
    "save_raw_crime",
    "load_weather_data",
    "save_raw_weather",
    "load_or_fetch_boundaries",
    "validate_crime_data",
    "validate_weather_data",
]
