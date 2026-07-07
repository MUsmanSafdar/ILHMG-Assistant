from pathlib import Path
import json
import requests
import pandas as pd

BASE_DIR = Path.cwd()
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

geojson_url = "https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json"

il_geojson = RAW_DIR / "illinois_counties.geojson"
priority_csv = PROCESSED_DIR / "county_priority_scores.csv"
out_geojson = PROCESSED_DIR / "illinois_counties_priority.geojson"

if not priority_csv.exists():
    raise FileNotFoundError(
        "Missing county_priority_scores.csv. Run scripts\\04_make_visuals.py first."
    )

print("Downloading county GeoJSON...")
response = requests.get(geojson_url, timeout=60)
response.raise_for_status()

geo = response.json()

# Keep only Illinois counties. Illinois state FIPS = 17.
features = []
for feature in geo["features"]:
    fips = str(feature["id"]).zfill(5)
    if fips.startswith("17"):
        features.append(feature)

il = {
    "type": "FeatureCollection",
    "features": features
}

with open(il_geojson, "w", encoding="utf-8") as f:
    json.dump(il, f)

print(f"Saved Illinois county boundaries: {il_geojson}")
print(f"Illinois county features: {len(features)}")

priority = pd.read_csv(priority_csv, dtype={"state_fips": str, "county_fips": str})
priority["state_fips"] = priority["state_fips"].astype(str).str.zfill(2)
priority["county_fips"] = priority["county_fips"].astype(str).str.zfill(3)
priority["full_fips"] = priority["state_fips"] + priority["county_fips"]

priority_lookup = priority.set_index("full_fips").to_dict(orient="index")

for feature in il["features"]:
    fips = str(feature["id"]).zfill(5)
    props = feature.get("properties", {})
    row = priority_lookup.get(fips)

    if row:
        props["county_name"] = row.get("county_name")
        props["region"] = row.get("region")
        props["total_population"] = row.get("total_population")
        props["poverty_rate"] = row.get("poverty_rate")
        props["age_65_plus_rate"] = row.get("age_65_plus_rate")
        props["vacancy_rate"] = row.get("vacancy_rate")
        props["bachelors_or_higher_rate"] = row.get("bachelors_or_higher_rate")
        props["prototype_priority_score"] = row.get("prototype_priority_score")
    else:
        props["county_name"] = props.get("NAME")
        props["region"] = None
        props["prototype_priority_score"] = None

    feature["properties"] = props

with open(out_geojson, "w", encoding="utf-8") as f:
    json.dump(il, f)

print(f"Saved joined GIS layer: {out_geojson}")
print("Done.")
