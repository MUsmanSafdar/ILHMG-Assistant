from pathlib import Path
import pandas as pd

base = Path.cwd()
region_file = base / "data" / "processed" / "illinois_county_regions.csv"

if not region_file.exists():
    raise FileNotFoundError(f"Missing file: {region_file}")

df = pd.read_csv(region_file, dtype={"state_fips": str, "county_fips": str})

regions = {
    "Northeast": [
        "Boone", "Cook", "DeKalb", "DuPage", "Grundy", "Kane",
        "Kankakee", "Kendall", "Lake", "Livingston", "McHenry", "Will"
    ],
    "Northwest": [
        "Bureau", "Carroll", "Henderson", "Henry", "Jo Daviess", "Knox",
        "Lee", "Marshall", "Mercer", "Ogle", "Putnam", "Rock Island",
        "Stark", "Stephenson", "Warren", "Whiteside", "Winnebago"
    ],
    "Central": [
        "Adams", "Brown", "Cass", "Champaign", "Christian", "Coles",
        "DeWitt", "Douglas", "Edgar", "Ford", "Fulton", "Hancock",
        "Iroquois", "Logan", "McDonough", "McLean", "Macon", "Mason",
        "Menard", "Morgan", "Moultrie", "Peoria", "Piatt", "Pike",
        "Sangamon", "Schuyler", "Scott", "Shelby", "Tazewell",
        "Vermilion", "Woodford", "LaSalle", "Clark", "Cumberland"
    ],
    "Southern": [
        "Alexander", "Bond", "Calhoun", "Clay", "Clinton", "Crawford",
        "Edwards", "Effingham", "Fayette", "Franklin", "Gallatin",
        "Greene", "Hamilton", "Hardin", "Jackson", "Jasper", "Jefferson",
        "Jersey", "Johnson", "Lawrence", "Macoupin", "Madison", "Marion",
        "Massac", "Monroe", "Montgomery", "Perry", "Pope", "Pulaski",
        "Randolph", "Richland", "St. Clair", "Saline", "Union", "Wabash",
        "Washington", "Wayne", "White", "Williamson"
    ]
}

county_to_region = {}
for region, counties in regions.items():
    for county in counties:
        county_to_region[county] = region

df["region"] = df["county"].map(county_to_region)

missing = df[df["region"].isna()]
if not missing.empty:
    print("Missing region assignments:")
    print(missing[["county", "county_fips"]].to_string(index=False))
    raise SystemExit("Fix missing counties before continuing.")

df.to_csv(region_file, index=False)

print("Updated county-region file:")
print(region_file)
print()
print(df["region"].value_counts().sort_index())
