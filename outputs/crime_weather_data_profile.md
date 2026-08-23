# Crime–Weather Analysis: Data Profile

## Project Scope
- Crime period: 2021-01-01 → 2025-12-31
- Weather period: 2021-01-01 → 2025-12-31
- Modeling unit: community_area × date
- Weather granularity: daily
- Merge key: date

## Crime Dataset
- File: `crime_raw_2021_2025.parquet`
- Shape: `(1210172, 19)`
- Rows: `1,210,172`
- Columns: `19`
- Unique dates: `1,826`
- Community areas: `77`
- Districts: `24`
- Beats: `275`
- Crime types: `31`
- Duplicate rows: `0`
- Duplicate IDs: `0`

### Crime Columns
- `id` — `object`
- `case_number` — `object`
- `date` — `datetime64[ns]`
- `block` — `object`
- `iucr` — `object`
- `primary_type` — `object`
- `description` — `object`
- `location_description` — `object`
- `arrest` — `bool`
- `domestic` — `bool`
- `beat` — `object`
- `district` — `object`
- `ward` — `object`
- `community_area` — `object`
- `fbi_code` — `object`
- `x_coordinate` — `object`
- `y_coordinate` — `object`
- `latitude` — `object`
- `longitude` — `object`

## Weather Dataset
- File: `weather_raw_2021_2025.parquet`
- Shape: `(1826, 7)`
- Rows: `1,826`
- Columns: `7`
- Unique dates: `1,826`
- Station(s): `['USW00094846']`
- Duplicate rows: `0`

### Weather Columns
- `DATE` — `datetime64[ns]`
- `AWND` — `object`
- `STATION` — `object`
- `SNOW` — `object`
- `TMAX` — `object`
- `TMIN` — `object`
- `PRCP` — `object`

## Compatibility
- Date overlap: `2021-01-01 → 2025-12-31`
- Crime dates without weather: `0`
- Weather dates without crime: `0`
- Crime × date rows: `1,826`
- Community area × date rows: `134,371`
- Test merge match rate: `100.00%`

## Existing Crime Features
- `id`
- `case_number`
- `date`
- `block`
- `iucr`
- `primary_type`
- `description`
- `location_description`
- `arrest`
- `domestic`
- `beat`
- `district`
- `ward`
- `community_area`
- `fbi_code`
- `x_coordinate`
- `y_coordinate`
- `latitude`
- `longitude`

## Top Crime Types
- THEFT: 268,968
- BATTERY: 214,485
- CRIMINAL DAMAGE: 137,238
- ASSAULT: 108,872
- MOTOR VEHICLE THEFT: 100,301
- DECEPTIVE PRACTICE: 84,445
- OTHER OFFENSE: 78,309
- ROBBERY: 42,856
- BURGLARY: 39,926
- WEAPONS VIOLATION: 39,653
- NARCOTICS: 29,044
- CRIMINAL TRESPASS: 22,628
- OFFENSE INVOLVING CHILDREN: 8,909
- CRIMINAL SEXUAL ASSAULT: 8,148
- SEX OFFENSE: 6,345