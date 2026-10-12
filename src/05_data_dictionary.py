"""Writes final/RuralReach_Data_Dictionary.csv and docs/DATA_DICTIONARY.md; fails if any master column is undocumented."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from rr_utils import *

# (column, group, unit, source, description)
D = [
    ("District_ID", "Geography", "id", "derived", "Stable key RR### built from the Census serial (the Census 'District_code' is a 1..640 serial, not the official code)."),
    ("State_name", "Geography", "text", "Census 2011", "State/UT as spelled in the Census file."),
    ("District_name", "Geography", "text", "Census 2011", "District as spelled in the Census file."),
    ("state_clean", "Geography", "text", "derived", "Upper-cased, whitespace-cleaned, canonical state label (Orissa->ODISHA etc.)."),
    ("district_clean", "Geography", "text", "derived", "Upper-cased, whitespace-cleaned district label."),
    ("State_Current", "Geography", "text", "derived", "State as of today for state-level joins (the 10 old Telangana districts moved out of ANDHRA PRADESH)."),
    ("Latitude", "Geography", "deg", "centroid file / polygon", "District centroid latitude."),
    ("Longitude", "Geography", "deg", "centroid file / polygon", "District centroid longitude."),
    ("Coord_Source", "Geography", "text", "derived", "centroid_file, or polygon_centroid where the centroid file has no usable row."),
    ("District_Area_sqkm", "Geography", "km2", "shapefile", "Area of the dissolved 2011-district polygon on an India equal-area projection."),
    ("Geometry_Link", "Geography", "text", "derived", "population_anchor (exact 2011 population match) or parent_map (post-2011 children folded into the 2011 parent)."),
    ("Geometry_Polygons_Merged", "Geography", "count", "shapefile", "Number of shapefile polygons dissolved into this district."),
    ("Population", "Population", "persons", "Census 2011", "Total population."),
    ("Male", "Population", "persons", "Census 2011", "Male population."),
    ("Female", "Population", "persons", "Census 2011", "Female population."),
    ("Sex_Ratio", "Population", "F per 1000 M", "derived", "Female/Male x 1000."),
    ("Population_Density", "Population", "per km2", "derived", "Population / District_Area_sqkm."),
    ("Young_Pop_pct", "Population", "%", "derived", "Share aged 0-29."),
    ("Middle_Pop_pct", "Population", "%", "derived", "Share aged 30-49."),
    ("Senior_Pop_pct", "Population", "%", "derived", "Share aged 50+."),
    ("Literate", "Education", "persons", "Census 2011", "Literate persons."),
    ("Literacy_Rate", "Education", "%", "derived", "Crude literacy = Literate / total population (all ages)."),
    ("Literacy_Rate_Effective", "Education", "%", "Literacy Data 2011", "Official effective literacy (population aged 7+). r=0.99 with the crude rate; kept because it is the standard, interpretable definition. Missing for Bangalore Rural."),
    ("Secondary_Education", "Education", "persons", "Census 2011", "Persons with secondary education."),
    ("Higher_Education", "Education", "persons", "Census 2011", "Persons with higher(-secondary) education."),
    ("Graduate_Education", "Education", "persons", "Census 2011", "Graduates and above."),
    ("Secondary_Edu_pct", "Education", "%", "derived", "Secondary_Education / Population."),
    ("Higher_Edu_pct", "Education", "%", "derived", "Higher_Education / Population."),
    ("Graduate_pct", "Education", "%", "derived", "Graduate_Education / Population."),
    ("Workers", "Livelihood", "persons", "Census 2011", "Total workers."),
    ("Male_Workers", "Livelihood", "persons", "Census 2011", "Male workers."),
    ("Female_Workers", "Livelihood", "persons", "Census 2011", "Female workers."),
    ("Cultivator_Workers", "Livelihood", "persons", "Census 2011", "Cultivators."),
    ("Agricultural_Workers", "Livelihood", "persons", "Census 2011", "Agricultural labourers."),
    ("Household_Workers", "Livelihood", "persons", "Census 2011", "Household-industry workers."),
    ("Worker_Participation_Rate", "Livelihood", "%", "derived", "Workers / Population."),
    ("Male_Worker_Participation_Rate", "Livelihood", "%", "derived", "Male workers / male population."),
    ("Female_Worker_Participation_Rate", "Livelihood", "%", "derived", "Female workers / female population. High values in poor agrarian districts reflect farm labour, not opportunity."),
    ("Cultivator_Share", "Livelihood", "%", "derived", "Cultivators / Workers."),
    ("Agri_Labour_Share", "Livelihood", "%", "derived", "Agricultural labourers / Workers."),
    ("Household_Industry_Share", "Livelihood", "%", "derived", "Household-industry workers / Workers."),
    ("Farm_Worker_Share", "Livelihood", "%", "derived", "Cultivators + agricultural labourers as % of workers. RURALITY PROXY (the supplied Census file has no urban/rural split)."),
    ("Hindus", "Religion", "persons", "Census 2011", "Context only - not used in scoring."),
    ("Muslims", "Religion", "persons", "Census 2011", "Context only - not used in scoring."),
    ("Christians", "Religion", "persons", "Census 2011", "Context only - not used in scoring."),
    ("Sikhs", "Religion", "persons", "Census 2011", "Context only - not used in scoring."),
    ("Buddhists", "Religion", "persons", "Census 2011", "Context only - not used in scoring."),
    ("Jains", "Religion", "persons", "Census 2011", "Context only - not used in scoring."),
    ("Hindus_pct", "Religion", "%", "derived", "Share of population."),
    ("Muslims_pct", "Religion", "%", "derived", "Share of population."),
    ("Christians_pct", "Religion", "%", "derived", "Share of population."),
    ("Sikhs_pct", "Religion", "%", "derived", "Share of population."),
    ("Buddhists_pct", "Religion", "%", "derived", "Share of population."),
    ("Jains_pct", "Religion", "%", "derived", "Share of population."),
    ("Railway_Station_Count", "Transport", "count", "timetable + DataMeet stations", "Active (timetabled) stations inside the district polygon. 0 is a confirmed zero (national timetable)."),
    ("Daily_Train_Stops", "Transport", "count", "timetable", "Sum over the district's stations of distinct trains stopping (timetable is undated; treat as a relative service level)."),
    ("Trains_Serving", "Transport", "count", "timetable", "Distinct trains that stop at >=1 station in the district."),
    ("Nearest_Railway_km", "Transport", "km", "derived", "Great-circle distance from district centroid to the nearest active station (can exceed 1,000 km for islands)."),
    ("Stations_per_1000sqkm", "Transport", "per 1000 km2", "derived", "Station density."),
    ("Stations_per_100k_pop", "Transport", "per 100k", "derived", "Stations per 100,000 people."),
    ("Mandi_Count", "Markets", "count", "commodity_price", "Distinct markets reporting on 19-May-2025. NaN = district not in the snapshot (NOT zero)."),
    ("Mandi_Commodities", "Markets", "count", "commodity_price", "Distinct commodities reported in the district. NaN as above."),
    ("NREGA_Active_JobCard_pct", "NREGA", "%", "NREGA", "Active job cards / job cards issued."),
    ("NREGA_Avg_Days_per_HH", "NREGA", "days", "NREGA", "Average days of employment per household (financial year of the file, undated)."),
    ("NREGA_Avg_Wage_Rs", "NREGA", "Rs/day", "NREGA", "Average wage rate per person-day."),
    ("NREGA_100Day_HH_pct", "NREGA", "%", "NREGA", "Households completing 100 days / households that worked."),
    ("NREGA_Women_Persondays_pct", "NREGA", "%", "NREGA", "Women's share of persondays."),
    ("NREGA_SC_ST_Persondays_pct", "NREGA", "%", "NREGA", "SC+ST share of persondays."),
    ("NREGA_Works_Completed_pct", "NREGA", "%", "NREGA", "Completed works / works taken up."),
    ("NREGA_Match_Method", "NREGA", "text", "derived", "How the NREGA row was matched to the 2011 district (exact / alias / fuzzy). Ratios only, because new districts split old ones."),
    ("StateLvl_PHC_Doctor_Staffing_pct", "Health (STATE-level)", "%", "PHC doctors 2017", "Doctors in position / required at PHCs, capped at 100. Same value for every district of the state."),
    ("StateLvl_PHC_Doctor_Vacancy_pct", "Health (STATE-level)", "%", "PHC doctors 2017", "Vacant / sanctioned posts (NaN where the state did not report)."),
    ("StateLvl_PHC_Doctors_per_100k", "Health (STATE-level)", "per 100k", "PHC doctors 2017 + Census", "PHC doctors in position per 100,000 state population."),
    ("StateLvl_Dropout_Primary", "Education (STATE-level)", "%", "Dropout 2012-15", "Mean of available years of the primary dropout ratio ('NR' cells ignored)."),
    ("StateLvl_Dropout_UpperPrimary", "Education (STATE-level)", "%", "Dropout 2012-15", "Same for upper primary."),
    ("StateLvl_Dropout_Secondary", "Education (STATE-level)", "%", "Dropout 2012-15", "Same for secondary."),
    ("Source_Census_Period", "Provenance", "text", "-", "Reference period of the Census block."),
    ("Source_Railway_Period", "Provenance", "text", "-", "Reference period of the railway block."),
    ("Source_Market_Period", "Provenance", "text", "-", "Reference date of the mandi snapshot (blank where not observed)."),
    ("Source_NREGA_Period", "Provenance", "text", "-", "Reference period of the NREGA block."),
    ("Source_Health_Period", "Provenance", "text", "-", "Reference period of the health block."),
    ("Source_Dropout_Period", "Provenance", "text", "-", "Reference period of the dropout block."),
    ("NonFarm_Worker_Share", "Livelihood", "%", "derived", "100 - Farm_Worker_Share."),
    ("Education_Access_Score", "RAI pillar", "0-100", "derived", "Mean of winsorised-scaled: Literacy_Rate_Effective, Secondary_Edu_pct, log Graduate_pct."),
    ("Transport_Access_Score", "RAI pillar", "0-100", "derived", "Mean of: inverted log Nearest_Railway_km, log Stations_per_1000sqkm, log Trains_Serving."),
    ("Health_Access_Score", "RAI pillar", "0-100", "derived", "Mean of state-level PHC staffing % and log doctors per 100k. STATE resolution."),
    ("Livelihood_Access_Score", "RAI pillar", "0-100", "derived", "Scaled NonFarm_Worker_Share."),
    ("Overall_Accessibility_Index", "RAI", "0-100", "derived", "RuralReach Accessibility Index = 0.30 Education + 0.30 Transport + 0.20 Health + 0.20 Livelihood (weights renormalised over available pillars)."),
    ("RAI_Rank", "RAI", "rank", "derived", "1 = best access among 640 districts."),
    ("Access_Tier", "RAI", "text", "derived", "Low (bottom quartile) / Medium / High (top quartile) of RAI."),
    ("Priority_Group", "RAI", "text", "derived", "1 Critical gap (Farm share >= median and Low tier); 2 High priority; 3 Monitor; 4 Well served."),
    ("LISA_Cluster", "Spatial", "text", "derived", "Local Moran's I class of RAI (k=8 neighbours, 499 permutations, p<0.05)."),
    ("Cluster", "Typology", "0-4", "derived", "K-Means typology (k=5), ordered by mean RAI."),
    ("Cluster_Name", "Typology", "text", "derived", "Descriptive label of the cluster."),
    ("Source_Index_Version", "Provenance", "text", "-", "Index version and weights."),
]
dd = pd.DataFrame(D, columns=["column", "group", "unit", "source", "description"])
master = pd.read_csv(FINAL / "RuralReach_Master.csv")
cols = list(master.columns)
miss = [c for c in cols if c not in set(dd.column)]
extra = [c for c in dd.column if c not in set(cols)]
assert not miss and not extra, (miss, extra)
dd["missing_pct"] = dd.column.map(master.isna().mean().mul(100).round(1))
dd = dd.set_index("column").loc[cols].reset_index()
dd.to_csv(FINAL / "RuralReach_Data_Dictionary.csv", index=False)
lines = ["# Data dictionary - `final/RuralReach_Master.csv`", "",
         f"{len(dd)} columns x {len(master)} districts. `missing_pct` = share of districts with NaN (NaN means *unknown*, never zero).", ""]
for g, sub in dd.groupby("group", sort=False):
    lines += [f"## {g}", "", "| Column | Unit | Source | Missing % | Description |", "|---|---|---|---|---|"]
    lines += [f"| `{r.column}` | {r.unit} | {r.source} | {r.missing_pct:g} | {r.description} |" for r in sub.itertuples()]
    lines.append("")
DOCS.mkdir(exist_ok=True)
(DOCS / "DATA_DICTIONARY.md").write_text("\n".join(lines), encoding="utf-8")
print("documented", len(dd), "columns")
