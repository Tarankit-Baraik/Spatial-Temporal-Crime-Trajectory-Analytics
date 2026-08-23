"""Central config. Single source of truth for paths, dates, split, seed."""
from pathlib import Path

# --- paths ---
ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
DATA_INTERIM = ROOT / "data" / "interim"
DATA_PROCESSED = ROOT / "data" / "processed"
MODELS_DIR = ROOT / "models"
OUTPUTS_DIR = ROOT / "outputs"

# --- scope ---
START_DATE = "2021-01-01"
END_DATE = "2025-12-31"

# --- data sources ---
CHICAGO_CRIME_DATASET_ID = "ijzp-q8t2"  # Crimes 2001-Present, Socrata
CHICAGO_SOCRATA_DOMAIN = "data.cityofchicago.org"
NOAA_STATION_ID = "USW00094846"  # Chicago O'Hare Intl Airport

# --- modeling ---
TARGET_PERCENTILE = 0.75  # high_crime_day threshold, train-period only
RANDOM_STATE = 42

# chronological split (edit if methodology changes; keep non-overlapping, no future leakage)
TRAIN_YEARS = (2021, 2022)
VALIDATION_YEARS = (2023,)
TEST_YEARS = (2024, 2025)
