from pathlib import Path
import pandas as pd
import plotly.express as px

BASE_DIR = Path.cwd()
DATA_DIR = BASE_DIR / "data" / "processed"
FIG_DIR = BASE_DIR / "outputs" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

county_file = DATA_DIR / "county_demographics_acs2024.csv"
region_file = DATA_DIR / "regional_demographics_acs2024.csv"

if not county_file.exists():
    raise FileNotFoundError("Missing county demographics file. Run scripts\\03_fetch_census.py first.")

if not region_file.exists():
    raise FileNotFoundError("Missing regional demographics file. Run scripts\\03_fetch_census.py first.")

county = pd.read_csv(county_file)
region = pd.read_csv(region_file)

# -----------------------------
# Create a simple mitigation priority score
# Higher poverty, older population, vacancy, and lower education increase score.
# This is a prototype decision-support score, not an official FEMA score.
# -----------------------------

county["education_risk"] = 100 - county["bachelors_or_higher_rate"]

score_cols = [
    "poverty_rate",
    "age_65_plus_rate",
    "vacancy_rate",
    "education_risk"
]

for col in score_cols:
    min_val = county[col].min()
    max_val = county[col].max()
    county[col + "_norm"] = (county[col] - min_val) / (max_val - min_val) * 100

county["prototype_priority_score"] = county[
    [col + "_norm" for col in score_cols]
].mean(axis=1)

county = county.sort_values("prototype_priority_score", ascending=False)

county.to_csv(DATA_DIR / "county_priority_scores.csv", index=False)

# -----------------------------
# Regional poverty chart
# -----------------------------

fig1 = px.bar(
    region.sort_values("poverty_rate", ascending=False),
    x="region",
    y="poverty_rate",
    title="Poverty Rate by Illinois Mitigation Planning Region",
    text_auto=".1f"
)
fig1.update_layout(
    xaxis_title="Region",
    yaxis_title="Poverty Rate (%)",
    title_x=0.02
)
fig1.write_html(FIG_DIR / "regional_poverty_rate.html")

# -----------------------------
# Regional age 65+ chart
# -----------------------------

fig2 = px.bar(
    region.sort_values("age_65_plus_rate", ascending=False),
    x="region",
    y="age_65_plus_rate",
    title="Older Adult Population Share by Region",
    text_auto=".1f"
)
fig2.update_layout(
    xaxis_title="Region",
    yaxis_title="Population Age 65+ (%)",
    title_x=0.02
)
fig2.write_html(FIG_DIR / "regional_age_65_plus.html")

# -----------------------------
# Top 15 counties priority chart
# -----------------------------

top15 = county.head(15).copy()

fig3 = px.bar(
    top15.sort_values("prototype_priority_score", ascending=True),
    x="prototype_priority_score",
    y="county_name",
    orientation="h",
    title="Top 15 Counties by Prototype Mitigation Priority Score",
    text_auto=".1f",
    hover_data=[
        "region",
        "poverty_rate",
        "age_65_plus_rate",
        "vacancy_rate",
        "bachelors_or_higher_rate"
    ]
)
fig3.update_layout(
    xaxis_title="Prototype Priority Score",
    yaxis_title="County",
    title_x=0.02
)
fig3.write_html(FIG_DIR / "top15_priority_counties.html")

# -----------------------------
# Scatterplot: poverty vs age 65+
# -----------------------------

fig4 = px.scatter(
    county,
    x="poverty_rate",
    y="age_65_plus_rate",
    color="region",
    size="total_population",
    hover_name="county_name",
    title="County Vulnerability Pattern: Poverty vs Older Adult Population",
    trendline="ols"
)
fig4.update_layout(
    xaxis_title="Poverty Rate (%)",
    yaxis_title="Population Age 65+ (%)",
    title_x=0.02
)
fig4.write_html(FIG_DIR / "poverty_vs_age65_scatter.html")

print("Created presentation visuals:")
print(FIG_DIR / "regional_poverty_rate.html")
print(FIG_DIR / "regional_age_65_plus.html")
print(FIG_DIR / "top15_priority_counties.html")
print(FIG_DIR / "poverty_vs_age65_scatter.html")
print()
print("Created:")
print(DATA_DIR / "county_priority_scores.csv")
