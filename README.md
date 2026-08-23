# Spatial-Temporal Crime Trajectory Analytics 
# (👮🚓🚨) (❄️🌨️☁️🌥️⛅🌤️☀️🌦️🌧️🌩️⛈️🌪️)

## What this project does 🔎

Analyzes Chicago crime (2021-2025) alongside NOAA weather data (O'Hare station) at the community-area x date level, to answer three questions: 
- how crime varies across space and time ?
- how it associates with weather ?
- can history classify unusually high-crime days ?

(`high_crime_day`, defined as a community area's daily crime count exceeding its own 75th-percentile historical baseline).

### **Key results** 📌

- Weather associates with crime (Spearman r = 0.552 citywide, strongest for extreme cold and extreme heat) — an association, not a causal claim.
- Weather improves prediction, and it is weather doing the work, not calendar features: weather alone reaches ROC-AUC 0.562, statistically indistinguishable from the full feature set's 0.563, while calendar alone trails at 0.548.
- Random Forest (tuned) is the model this project carries forward — not the model its own F1-based selection rule chose. That rule picked Logistic Regression (validation F1 0.492), which then degenerated to a near-constant positive classifier on test (recall 0.999, negative-class recall 0.00). Random Forest reached test F1 0.425, ROC-AUC 0.589, with real discrimination on both classes.
- The model's errors follow a seasonal cycle: false negatives dominate January-April, false positives dominate May-December, repeating across both test years.
- Citywide crime peaked in 2023 (263,409 incidents) and has declined for two years since (237,629 in 2025), independently confirmed by the `high_crime_day` target rate peaking the same year.

📕 Full results: [`docs/findings.md`](docs/findings.md). 

  Methodology: [`docs/methodology.md`](docs/methodology.md). 

  Model details: [`docs/modeling.md`](docs/modeling.md). 
  
  Column definitions: [`docs/data_dictionary.md`](docs/data_dictionary.md). 
  
  Known limitations: [`docs/limitations.md`](docs/limitations.md).

## Repository structure 🗂️

```
spatial-temporal-crime-trajectory-analytics/
├── README.md, LICENSE, .gitignore, requirements.txt, pyproject.toml
├── data/
│   ├── raw/{crime,weather}/     # not committed
│   ├── interim/                 # not committed
│   └── processed/               # not committed
├── notebooks/                   # 01-10, run in order
├── src/                         # ingestion, cleaning, features, modeling code
├── models/                      # trained model files
├── outputs/
│   ├── figures/{temporal,spatial,weather,modeling,final}/
│   └── tables/
└── docs/
    ├── methodology.md, findings.md, modeling.md, data_dictionary.md, limitations.md
```

## How to run 🚀

```bash
git clone <this-repo>
cd spatial-temporal-crime-trajectory-analytics
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Data is not committed — run the notebooks in `notebooks/` in order, 01 through 10. Each writes the file the next one reads:

| Notebook | Produces |
|---|---|
| 01 data ingestion and quality | `data/raw/crime/`, `data/raw/weather/` |
| 02 crime cleaning | `data/interim/crime_cleaned.parquet` |
| 03 spatiotemporal feature engineering | `data/interim/crime_daily.parquet` |
| 04 crime EDA | `outputs/figures/temporal/`, `outputs/figures/spatial/` |
| 05 weather analysis | `data/interim/weather_cleaned.parquet` |
| 06 crime-weather analysis | `data/interim/crime_weather_daily.parquet`, weather-crime statistics tables |
| 07 model dataset creation | `data/processed/modeling_dataset.parquet` |
| 08 model training and comparison | `models/*.joblib`, model comparison tables |
| 09 model interpretation | feature importance, error analysis, weather ablation tables |
| 10 final analysis | `outputs/tables/final_model_comparison.csv`, `outputs/figures/final/` |

## Data source 📚

- **Crime**: [Chicago Data Portal — Crimes 2001-Present](https://data.cityofchicago.org/Public-Safety/Crimes-2001-to-Present/ijzp-q8t2), Socrata dataset `ijzp-q8t2`, queried for 2021-2025 only. No authentication required. Reported/police-recorded incidents, block-level location.
- **Weather**: NOAA GHCN-Daily, station `USW00094846` (Chicago O'Hare), 2021-2025. No authentication required. TMAX, TMIN, PRCP, SNOW, AWND.
