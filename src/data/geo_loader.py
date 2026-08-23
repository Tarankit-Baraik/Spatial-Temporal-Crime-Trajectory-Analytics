"""Chicago community-area boundary loader (choropleth support). Mirrors
crime_loader.py/weather_loader.py's cache-and-save pattern: fetched once,
saved untouched to data/raw/geo/, then reused.

Source: City of Chicago Data Portal, "Boundaries - Community Areas" (Socrata
resource `igwz-8jzy`) -- the same portal used for crime data, kept as the
single source of truth for community area geometry so it never drifts from
what crime_loader.py's `community_area` field means. 77 community areas,
boundaries fixed since the 1920s (do not change over time).
"""
import json

import requests

from src.config import DATA_RAW

GEOJSON_URL = "https://data.cityofchicago.org/resource/igwz-8jzy.geojson"
# Socrata's export field naming has varied across this dataset's revisions;
# check known candidates in order rather than hardcoding one -- but never
# guess silently. get_area_number_field() raises if none match.
AREA_NUMBER_FIELD_CANDIDATES = ["area_num_1", "area_numbe", "area_number", "community_area"]
BOUNDARIES_PATH = DATA_RAW / "geo" / "community_areas.geojson"


def fetch_community_area_boundaries(limit: int = 100) -> dict:
    """Fetches the 77 community area polygons as GeoJSON. Raises on non-200
    or an empty response -- never returns a partial/malformed result silently."""
    resp = requests.get(GEOJSON_URL, params={"$limit": limit}, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"Chicago boundary API request failed: {resp.status_code} {resp.text[:300]}")
    geojson = resp.json()
    if not geojson.get("features"):
        raise RuntimeError("No community area features returned -- check the API/resource ID before proceeding.")
    return geojson


def save_raw_boundaries(geojson: dict) -> None:
    BOUNDARIES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(BOUNDARIES_PATH, "w") as f:
        json.dump(geojson, f)


def get_area_number_field(geojson: dict) -> str:
    """Detects which GeoJSON property holds the community area number, by
    checking AREA_NUMBER_FIELD_CANDIDATES in order. Raises if none of them
    are present -- never silently joins on a guessed/wrong field."""
    props = geojson["features"][0]["properties"]
    for candidate in AREA_NUMBER_FIELD_CANDIDATES:
        if candidate in props:
            return candidate
    raise KeyError(
        f"None of {AREA_NUMBER_FIELD_CANDIDATES} found in boundary properties "
        f"({sorted(props.keys())}) -- add the correct field name to "
        f"AREA_NUMBER_FIELD_CANDIDATES in geo_loader.py."
    )


def load_or_fetch_boundaries() -> dict:
    """Cache-and-load: returns the saved GeoJSON if present, else fetches and
    saves it first. Same pattern as crime_loader.load_crime_data /
    weather_loader.load_weather_data."""
    if BOUNDARIES_PATH.exists():
        with open(BOUNDARIES_PATH) as f:
            return json.load(f)
    geojson = fetch_community_area_boundaries()
    save_raw_boundaries(geojson)
    return geojson


if __name__ == "__main__":
    load_or_fetch_boundaries()
