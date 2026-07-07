import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
import folium
from streamlit_folium import st_folium

st.set_page_config(
    page_title="Illinois Hazard Mitigation Plan Update Assistant",
    layout="wide"
)

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data" / "processed"

priority_file = DATA_DIR / "county_priority_scores.csv"
region_file = DATA_DIR / "regional_demographics_acs2024.csv"
county_file = DATA_DIR / "county_demographics_acs2024.csv"
geojson_file = DATA_DIR / "illinois_counties_priority.geojson"
comparison_file = DATA_DIR / "regional_2021_vs_latest_comparison.csv"

st.title("Illinois Hazard Mitigation Plan Update Assistant")
st.caption("GIS + Census Update + Plan Review + Analytics Assistant")

tabs = st.tabs([
    "Executive Dashboard",
    "Census Update",
    "2021 vs Latest",
    "GIS Map",
    "Regression Lab",
    "Plan Review",
    "Email Draft"
])

with tabs[0]:
    st.header("Executive Dashboard")

    if priority_file.exists() and region_file.exists():
        county = pd.read_csv(priority_file)
        region = pd.read_csv(region_file)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Illinois Counties", "102")
        col2.metric("Planning Regions", "4")
        col3.metric("Highest Priority County", county.iloc[0]["county_name"])
        col4.metric("Top Priority Score", round(county.iloc[0]["prototype_priority_score"], 1))

        st.subheader("Regional Vulnerability Snapshot")

        metric = st.selectbox(
            "Select indicator",
            [
                "poverty_rate",
                "age_65_plus_rate",
                "vacancy_rate",
                "bachelors_or_higher_rate"
            ]
        )

        fig = px.bar(
            region.sort_values(metric, ascending=False),
            x="region",
            y=metric,
            text_auto=".1f",
            title=f"{metric.replace('_', ' ').title()} by Region"
        )
        fig.update_layout(
            xaxis_title="Region",
            yaxis_title=metric.replace("_", " ").title(),
            title_x=0.02
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Top 15 Counties by Prototype Mitigation Priority Score")

        top15 = county.head(15).copy()
        fig2 = px.bar(
            top15.sort_values("prototype_priority_score", ascending=True),
            x="prototype_priority_score",
            y="county_name",
            orientation="h",
            color="region",
            hover_data=[
                "poverty_rate",
                "age_65_plus_rate",
                "vacancy_rate",
                "bachelors_or_higher_rate"
            ],
            title="Counties with Highest Combined Vulnerability Indicators"
        )
        fig2.update_layout(
            xaxis_title="Prototype Priority Score",
            yaxis_title="County",
            title_x=0.02
        )
        st.plotly_chart(fig2, use_container_width=True)

        st.info(
            "This prototype priority score is based on Census vulnerability indicators. "
            "It is for planning review and presentation support, not an official FEMA or IEMA-OHS score."
        )
    else:
        st.warning("Run scripts 03 and 04 first.")

with tabs[1]:
    st.header("Census Update")

    if county_file.exists():
        county = pd.read_csv(county_file)
        st.success("ACS county demographics loaded.")

        selected_region = st.selectbox(
            "Filter by mitigation region",
            ["All"] + sorted(county["region"].dropna().unique().tolist())
        )

        show = county.copy()
        if selected_region != "All":
            show = show[show["region"] == selected_region]

        st.dataframe(show, use_container_width=True)
    else:
        st.warning("County Census file not found.")

with tabs[2]:
    st.header("2021 Plan Baseline vs Latest ACS")

    if comparison_file.exists():
        compare = pd.read_csv(comparison_file)

        st.success("Comparison file loaded.")
        st.subheader("Regional comparison table")
        st.dataframe(compare.round(2), use_container_width=True)

        metric_choice = st.selectbox(
            "Select comparison metric",
            [
                "total_population",
                "poverty_rate",
                "vacancy_rate",
                "bachelors_or_higher_rate"
            ]
        )

        if metric_choice == "total_population":
            old_col = "total_population_2021"
            new_col = "total_population"
            y_title = "Population"
        else:
            old_col = metric_choice + "_2021"
            new_col = metric_choice
            y_title = metric_choice.replace("_", " ").title()

        chart_df = compare[["region", old_col, new_col]].copy()
        chart_df = chart_df.rename(
            columns={
                old_col: "Plan 2021 baseline",
                new_col: "Latest ACS"
            }
        )

        chart_long = chart_df.melt(
            id_vars="region",
            var_name="Source",
            value_name="Value"
        )

        fig = px.bar(
            chart_long,
            x="region",
            y="Value",
            color="Source",
            barmode="group",
            text_auto=".1f",
            title=f"2021 Plan Baseline vs Latest ACS: {y_title}"
        )
        fig.update_layout(
            xaxis_title="Mitigation planning region",
            yaxis_title=y_title,
            title_x=0.02
        )
        st.plotly_chart(fig, use_container_width=True)

        st.info(
            "This comparison uses the 2021 ACS values printed in the plan as the baseline, "
            "and the latest ACS regional aggregation generated by the assistant as the update. "
            "Northeast will be added after exact PDF table values are extracted and verified."
        )

    else:
        st.warning("Comparison file not found. Run scripts\\06_compare_plan_2021_vs_latest.py first.")

with tabs[3]:
    st.header("GIS Map")

    if geojson_file.exists() and priority_file.exists():
        st.success("GIS layer loaded.")

        county = pd.read_csv(priority_file)

        map_metric = st.selectbox(
            "Select map indicator",
            [
                "prototype_priority_score",
                "poverty_rate",
                "age_65_plus_rate",
                "vacancy_rate",
                "bachelors_or_higher_rate"
            ]
        )

        with open(geojson_file, "r", encoding="utf-8") as f:
            geojson_data = json.load(f)

        m = folium.Map(
            location=[40.0, -89.2],
            zoom_start=6,
            tiles="cartodbpositron"
        )

        choropleth_data = county[["full_fips", map_metric]].dropna()

        folium.Choropleth(
            geo_data=geojson_data,
            data=choropleth_data,
            columns=["full_fips", map_metric],
            key_on="feature.id",
            fill_opacity=0.75,
            line_opacity=0.25,
            legend_name=map_metric.replace("_", " ").title()
        ).add_to(m)

        tooltip = folium.GeoJsonTooltip(
            fields=[
                "county_name",
                "region",
                "total_population",
                "poverty_rate",
                "age_65_plus_rate",
                "vacancy_rate",
                "prototype_priority_score"
            ],
            aliases=[
                "County:",
                "Region:",
                "Population:",
                "Poverty rate:",
                "Age 65+ rate:",
                "Vacancy rate:",
                "Priority score:"
            ],
            localize=True,
            sticky=False
        )

        folium.GeoJson(
            geojson_data,
            name="County details",
            tooltip=tooltip,
            style_function=lambda feature: {
                "fillOpacity": 0,
                "color": "black",
                "weight": 0.4
            }
        ).add_to(m)

        folium.LayerControl().add_to(m)
        st_folium(m, width=None, height=650)

        st.caption(
            "Interactive Illinois county choropleth map using ACS vulnerability indicators and prototype mitigation priority scoring."
        )

    else:
        st.warning("GIS layer not ready.")
        st.write("Expected files:")
        st.code(str(geojson_file))
        st.code(str(priority_file))

with tabs[4]:
    st.header("Regression Lab")

    if priority_file.exists():
        county = pd.read_csv(priority_file)

        st.subheader("Exploratory Relationship: Poverty vs Older Adult Population")

        fig = px.scatter(
            county,
            x="poverty_rate",
            y="age_65_plus_rate",
            color="region",
            size="total_population",
            hover_name="county_name",
            trendline="ols",
            title="Poverty Rate and Older Adult Share Across Illinois Counties"
        )
        fig.update_layout(
            xaxis_title="Poverty Rate (%)",
            yaxis_title="Population Age 65+ (%)",
            title_x=0.02
        )
        st.plotly_chart(fig, use_container_width=True)

        st.caption("This is exploratory decision-support analysis, not causal proof.")
    else:
        st.warning("Run scripts\\04_make_visuals.py first.")

with tabs[5]:
    st.header("Plan Review")

    review_rows = [
        {
            "Review Area": "Goals Modification",
            "Task": "Check whether goals reflect climate change, vulnerable populations, critical facilities, and measurable implementation.",
            "Status": "To review"
        },
        {
            "Review Area": "Attendees",
            "Task": "Check whether agencies, sectors, utilities, hospitals, universities, and local partners are represented.",
            "Status": "To review"
        },
        {
            "Review Area": "Goals/Actions Relevancy",
            "Task": "Check whether mitigation actions connect to hazards, risk assessment, vulnerable populations, and funding.",
            "Status": "To review"
        },
        {
            "Review Area": "Critical Facilities",
            "Task": "Check whether facilities are mapped and linked to hazards, lifelines, vulnerabilities, and mitigation actions.",
            "Status": "To review"
        },
        {
            "Review Area": "Chapter 1 Census Tables",
            "Task": "Update 2021 ACS tables to latest ACS/Census values.",
            "Status": "In progress"
        }
    ]

    st.dataframe(pd.DataFrame(review_rows), use_container_width=True)

with tabs[6]:
    st.header("Email Draft")

    email = """Subject: Proposed GIS and Data Assistant for Illinois Hazard Mitigation Plan Review

Dear Russell and Camden,

I hope you are both doing well.

I wanted to share a proposed workflow I am developing to support review and update work for the Illinois Natural Hazard Mitigation Plan. My idea is to build a small GIS-enabled data assistant that can help with Chapter 1 Census table updates, hazard mitigation goal/action review, critical facilities analysis, and presentation-ready visualizations.

The first phase would focus on updating the Chapter 1 demographic and regional tables that are currently based on 2021 ACS 5-year estimates. The assistant would pull the latest available Census/ACS data, aggregate county-level data into the four mitigation planning regions used in the plan, recreate the regional tables, and generate updated charts and maps.

The second phase would add GIS and analytical features, including county-level hazard and vulnerability mapping, critical facilities overlays, regional comparison visuals, and basic statistical analysis to identify counties where hazard exposure, social vulnerability, and facility concentration overlap. The goal would not be to replace subject-matter review, but to make the review process faster, more transparent, and easier to present.

I would appreciate your guidance on the official county-to-region list used in the plan, and whether there are preferred internal datasets for critical facilities, shelters, state facilities, or mitigation actions that should be used instead of public datasets.

Best regards,

Muhammad Usman
"""
    st.text_area("Email", email, height=450)
pdf_path = BASE_DIR / "outputs" / "reports" / "IL_Hazard_Plan_Update_Senior_Brief.pdf"

if pdf_path.exists():
    with open(pdf_path, "rb") as pdf_file:
        st.download_button(
            label="Download Senior Brief PDF",
            data=pdf_file,
            file_name="IL_Hazard_Plan_Update_Senior_Brief.pdf",
            mime="application/pdf"
        )
else:
    st.warning("PDF brief not found. Run scripts\\07_generate_senior_brief_pdf.py first.")
