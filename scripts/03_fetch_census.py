from pathlib import Path
import os
import requests
import pandas as pd

BASE_DIR = Path.cwd()
REGION_FILE = BASE_DIR / "data" / "processed" / "illinois_county_regions.csv"
OUT_DIR = BASE_DIR / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

YEARS_TO_TRY = [2024, 2023, 2022]

variables = [
    "NAME",
    "B01003_001E",
    "B19013_001E",
    "B17001_001E",
    "B17001_002E",
    "B25001_001E",
    "B25002_003E",
    "B15003_001E",
    "B15003_022E",
    "B15003_023E",
    "B15003_024E",
    "B15003_025E",
    "B01001_020E",
    "B01001_021E",
    "B01001_022E",
    "B01001_023E",
    "B01001_024E",
    "B01001_025E",
    "B01001_044E",
    "B01001_045E",
    "B01001_046E",
    "B01001_047E",
    "B01001_048E",
    "B01001_049E",
]

api_key = os.getenv("CENSUS_API_KEY")

if not api_key:
    raise SystemExit(
        'Missing Census API key. Set it using: setx CENSUS_API_KEY "YOUR_KEY"'
    )

def fetch_acs(year):
    url = f"https://api.census.gov/data/{year}/acs/acs5"
    params = {
        "get": ",".join(variables),
        "for": "county:*",
        "in": "state:17",
        "key": api_key
    }

    print(f"\nTrying ACS {year} 5-year county data...")
    response = requests.get(url, params=params, timeout=60)

    print("Status code:", response.status_code)
    print("URL:", response.url)

    if response.status_code != 200:
        print("Response preview:")
        print(response.text[:500])
        return None, year

    try:
        data = response.json()
        return data, year
    except Exception:
        print("Could not parse Census response as JSON.")
        print("Response preview:")
        print(response.text[:1000])
        return None, year

data = None
used_year = None

for year in YEARS_TO_TRY:
    data, used_year = fetch_acs(year)
    if data is not None:
        break

if data is None:
    raise SystemExit("Census API failed for all attempted years.")

df = pd.DataFrame(data[1:], columns=data[0])

rename_map = {
    "B01003_001E": "total_population",
    "B19013_001E": "median_household_income",
    "B17001_001E": "poverty_universe",
    "B17001_002E": "people_below_poverty",
    "B25001_001E": "total_housing_units",
    "B25002_003E": "vacant_housing_units",
    "B15003_001E": "education_population_25_plus",
    "B15003_022E": "bachelors_degree",
    "B15003_023E": "masters_degree",
    "B15003_024E": "professional_degree",
    "B15003_025E": "doctorate_degree"
}

df = df.rename(columns=rename_map)

for col in df.columns:
    if col not in ["NAME", "state", "county"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

df["state_fips"] = df["state"].astype(str).str.zfill(2)
df["county_fips"] = df["county"].astype(str).str.zfill(3)
df["full_fips"] = df["state_fips"] + df["county_fips"]
df["county_name"] = df["NAME"].str.replace(" County, Illinois", "", regex=False)

age_cols = [
    "B01001_020E", "B01001_021E", "B01001_022E", "B01001_023E", "B01001_024E", "B01001_025E",
    "B01001_044E", "B01001_045E", "B01001_046E", "B01001_047E", "B01001_048E", "B01001_049E"
]

df["population_65_plus"] = df[age_cols].sum(axis=1)

df["bachelors_or_higher"] = (
    df["bachelors_degree"] +
    df["masters_degree"] +
    df["professional_degree"] +
    df["doctorate_degree"]
)

df["poverty_rate"] = df["people_below_poverty"] / df["poverty_universe"] * 100
df["vacancy_rate"] = df["vacant_housing_units"] / df["total_housing_units"] * 100
df["age_65_plus_rate"] = df["population_65_plus"] / df["total_population"] * 100
df["bachelors_or_higher_rate"] = df["bachelors_or_higher"] / df["education_population_25_plus"] * 100

regions = pd.read_csv(REGION_FILE, dtype={"state_fips": str, "county_fips": str})
regions["state_fips"] = regions["state_fips"].astype(str).str.zfill(2)
regions["county_fips"] = regions["county_fips"].astype(str).str.zfill(3)

merged = df.merge(
    regions[["county", "state_fips", "county_fips", "region"]],
    on=["state_fips", "county_fips"],
    how="left"
)

if merged["region"].isna().any():
    print("Some counties did not match a region:")
    print(merged[merged["region"].isna()][["county_name", "county_fips"]])
    raise SystemExit("Region merge failed.")

region_summary = merged.groupby("region").agg(
    total_population=("total_population", "sum"),
    poverty_universe=("poverty_universe", "sum"),
    people_below_poverty=("people_below_poverty", "sum"),
    total_housing_units=("total_housing_units", "sum"),
    vacant_housing_units=("vacant_housing_units", "sum"),
    population_65_plus=("population_65_plus", "sum"),
    education_population_25_plus=("education_population_25_plus", "sum"),
    bachelors_or_higher=("bachelors_or_higher", "sum")
).reset_index()

region_summary["poverty_rate"] = region_summary["people_below_poverty"] / region_summary["poverty_universe"] * 100
region_summary["vacancy_rate"] = region_summary["vacant_housing_units"] / region_summary["total_housing_units"] * 100
region_summary["age_65_plus_rate"] = region_summary["population_65_plus"] / region_summary["total_population"] * 100
region_summary["bachelors_or_higher_rate"] = region_summary["bachelors_or_higher"] / region_summary["education_population_25_plus"] * 100

county_out = OUT_DIR / f"county_demographics_acs{used_year}.csv"
region_out = OUT_DIR / f"regional_demographics_acs{used_year}.csv"

county_standard = OUT_DIR / "county_demographics_acs2024.csv"
region_standard = OUT_DIR / "regional_demographics_acs2024.csv"

merged.to_csv(county_out, index=False)
region_summary.to_csv(region_out, index=False)

merged.to_csv(county_standard, index=False)
region_summary.to_csv(region_standard, index=False)

print("\nDone.")
print(f"ACS year used: {used_year}")
print(f"Created: {county_out}")
print(f"Created: {region_out}")
print(f"Created standard file: {county_standard}")
print(f"Created standard file: {region_standard}")

print("\nRegional summary:")
print(
    region_summary[
        ["region", "total_population", "poverty_rate", "age_65_plus_rate", "vacancy_rate"]
    ].round(2).to_string(index=False)
)
