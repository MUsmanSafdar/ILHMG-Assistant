from pathlib import Path
import pandas as pd

BASE_DIR = Path.cwd()
DATA_DIR = BASE_DIR / "data" / "processed"

old_file = DATA_DIR / "plan_2021_regional_baseline.csv"
latest_file = DATA_DIR / "regional_demographics_acs2024.csv"
out_file = DATA_DIR / "regional_2021_vs_latest_comparison.csv"

old = pd.read_csv(old_file)
latest = pd.read_csv(latest_file)

compare = old.merge(latest, on="region", how="left")

compare["population_change"] = compare["total_population"] - compare["total_population_2021"]
compare["population_pct_change"] = compare["population_change"] / compare["total_population_2021"] * 100

compare["poverty_rate_pp_change"] = compare["poverty_rate"] - compare["poverty_rate_2021"]
compare["vacancy_rate_pp_change"] = compare["vacancy_rate"] - compare["vacancy_rate_2021"]
compare["bachelors_or_higher_rate_pp_change"] = (
    compare["bachelors_or_higher_rate"] - compare["bachelors_or_higher_rate_2021"]
)

cols = [
    "region",
    "total_population_2021",
    "total_population",
    "population_change",
    "population_pct_change",
    "poverty_rate_2021",
    "poverty_rate",
    "poverty_rate_pp_change",
    "vacancy_rate_2021",
    "vacancy_rate",
    "vacancy_rate_pp_change",
    "bachelors_or_higher_rate_2021",
    "bachelors_or_higher_rate",
    "bachelors_or_higher_rate_pp_change",
]

compare = compare[cols]
compare.to_csv(out_file, index=False)

print("Created comparison file:")
print(out_file)
print()
print(compare.round(2).to_string(index=False))
