from pathlib import Path
from datetime import datetime
import pandas as pd

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak
)

BASE_DIR = Path.cwd()
DATA_DIR = BASE_DIR / "data" / "processed"
OUT_DIR = BASE_DIR / "outputs" / "reports"
OUT_DIR.mkdir(parents=True, exist_ok=True)

comparison_file = DATA_DIR / "regional_2021_vs_latest_comparison.csv"
priority_file = DATA_DIR / "county_priority_scores.csv"
region_file = DATA_DIR / "regional_demographics_acs2024.csv"

output_pdf = OUT_DIR / "IL_Hazard_Plan_Update_Senior_Brief.pdf"

styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle(
        name="SmallText",
        parent=styles["BodyText"],
        fontSize=8,
        leading=10
    )
)

doc = SimpleDocTemplate(
    str(output_pdf),
    pagesize=landscape(letter),
    rightMargin=0.45 * inch,
    leftMargin=0.45 * inch,
    topMargin=0.45 * inch,
    bottomMargin=0.45 * inch,
)

story = []

title = "Illinois Hazard Mitigation Plan Update Assistant - Senior Brief"
story.append(Paragraph(title, styles["Title"]))
story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y')}", styles["SmallText"]))
story.append(Spacer(1, 0.2 * inch))

story.append(Paragraph("Purpose", styles["Heading1"]))
story.append(Paragraph(
    "This brief summarizes a GIS-enabled data assistant developed to support review and update work for the Illinois Natural Hazard Mitigation Plan. "
    "The assistant focuses on Chapter 1 Census table updates, regional vulnerability comparison, GIS mapping, exploratory statistical analysis, and review tracking for goals, attendees, mitigation actions, and critical facilities.",
    styles["BodyText"]
))
story.append(Spacer(1, 0.15 * inch))

story.append(Paragraph("Current Automated Outputs", styles["Heading1"]))
outputs = [
    ["Module", "Current Function"],
    ["Census Update", "Pulls ACS county-level data and aggregates it into the four mitigation planning regions."],
    ["2021 vs Latest", "Compares plan baseline values against the latest ACS regional aggregation."],
    ["GIS Map", "Displays an Illinois county choropleth map using vulnerability indicators and a prototype priority score."],
    ["Regression Lab", "Shows exploratory relationships such as poverty rate versus older adult population share."],
    ["Plan Review", "Tracks review areas: goals, attendees, action relevancy, critical facilities, and Chapter 1 Census updates."],
]
t = Table(outputs, colWidths=[2.2 * inch, 7.8 * inch])
t.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, -1), 8),
]))
story.append(t)
story.append(Spacer(1, 0.25 * inch))

if comparison_file.exists():
    story.append(Paragraph("2021 Plan Baseline vs Latest ACS Regional Comparison", styles["Heading1"]))
    compare = pd.read_csv(comparison_file).round(2)

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
        "vacancy_rate_pp_change"
    ]

    available_cols = [c for c in cols if c in compare.columns]
    table_data = [available_cols] + compare[available_cols].astype(str).values.tolist()

    t = Table(table_data, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.2 * inch))
else:
    story.append(Paragraph("2021 vs Latest comparison file not found. Run scripts/06_compare_plan_2021_vs_latest.py first.", styles["BodyText"]))

if priority_file.exists():
    story.append(PageBreak())
    story.append(Paragraph("Top 15 Counties by Prototype Mitigation Priority Score", styles["Heading1"]))

    county = pd.read_csv(priority_file).head(15).round(2)

    cols = [
        "county_name",
        "region",
        "total_population",
        "poverty_rate",
        "age_65_plus_rate",
        "vacancy_rate",
        "bachelors_or_higher_rate",
        "prototype_priority_score"
    ]

    available_cols = [c for c in cols if c in county.columns]
    table_data = [available_cols] + county[available_cols].astype(str).values.tolist()

    t = Table(table_data, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.2 * inch))

story.append(Paragraph("Interpretation Note", styles["Heading1"]))
story.append(Paragraph(
    "The prototype mitigation priority score is a decision-support index created from selected ACS indicators, including poverty, older adult population share, housing vacancy, and educational attainment. "
    "It is not an official FEMA or IEMA-OHS score. It is intended to help identify counties where social vulnerability indicators may warrant closer review alongside hazard exposure, critical facilities, and local mitigation priorities.",
    styles["BodyText"]
))
story.append(Spacer(1, 0.15 * inch))

story.append(Paragraph("Feedback Requested", styles["Heading1"]))
feedback = [
    ["Review Area", "Feedback Requested"],
    ["County-to-region list", "Confirm whether the county assignments reflect the official mitigation planning regions."],
    ["Census update", "Confirm whether ACS 2024 should be used, or whether another Census/ACS year is preferred."],
    ["Critical facilities", "Identify preferred internal datasets for facilities, shelters, hospitals, state assets, and lifelines."],
    ["Goals/actions", "Advise whether goal and action review should follow a specific IEMA-OHS or FEMA crosswalk format."],
    ["GIS outputs", "Advise whether the map should include additional layers such as hazards, repetitive loss, shelters, or state facilities."],
]
t = Table(feedback, colWidths=[2.4 * inch, 7.6 * inch])
t.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, -1), 8),
]))
story.append(t)

doc.build(story)

print(f"Created PDF brief: {output_pdf}")