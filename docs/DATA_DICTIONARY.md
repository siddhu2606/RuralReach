# Data dictionary - `final/RuralReach_Master.csv`

95 columns x 640 districts. `missing_pct` = share of districts with NaN (NaN means *unknown*, never zero).

## Geography

| Column | Unit | Source | Missing % | Description |
|---|---|---|---|---|
| `District_ID` | id | derived | 0 | Stable key RR### built from the Census serial (the Census 'District_code' is a 1..640 serial, not the official code). |
| `State_name` | text | Census 2011 | 0 | State/UT as spelled in the Census file. |
| `District_name` | text | Census 2011 | 0 | District as spelled in the Census file. |
| `state_clean` | text | derived | 0 | Upper-cased, whitespace-cleaned, canonical state label (Orissa->ODISHA etc.). |
| `district_clean` | text | derived | 0 | Upper-cased, whitespace-cleaned district label. |
| `State_Current` | text | derived | 0 | State as of today for state-level joins (the 10 old Telangana districts moved out of ANDHRA PRADESH). |
| `Latitude` | deg | centroid file / polygon | 0 | District centroid latitude. |
| `Longitude` | deg | centroid file / polygon | 0 | District centroid longitude. |
| `Coord_Source` | text | derived | 0 | centroid_file, or polygon_centroid where the centroid file has no usable row. |
| `District_Area_sqkm` | km2 | shapefile | 0 | Area of the dissolved 2011-district polygon on an India equal-area projection. |
| `Geometry_Link` | text | derived | 0 | population_anchor (exact 2011 population match) or parent_map (post-2011 children folded into the 2011 parent). |
| `Geometry_Polygons_Merged` | count | shapefile | 0 | Number of shapefile polygons dissolved into this district. |

## Population

| Column | Unit | Source | Missing % | Description |
|---|---|---|---|---|
| `Population` | persons | Census 2011 | 0 | Total population. |
| `Male` | persons | Census 2011 | 0 | Male population. |
| `Female` | persons | Census 2011 | 0 | Female population. |
| `Sex_Ratio` | F per 1000 M | derived | 0 | Female/Male x 1000. |
| `Population_Density` | per km2 | derived | 0 | Population / District_Area_sqkm. |
| `Young_Pop_pct` | % | derived | 0 | Share aged 0-29. |
| `Middle_Pop_pct` | % | derived | 0 | Share aged 30-49. |
| `Senior_Pop_pct` | % | derived | 0 | Share aged 50+. |

## Education

| Column | Unit | Source | Missing % | Description |
|---|---|---|---|---|
| `Literate` | persons | Census 2011 | 0 | Literate persons. |
| `Literacy_Rate` | % | derived | 0 | Crude literacy = Literate / total population (all ages). |
| `Literacy_Rate_Effective` | % | Literacy Data 2011 | 0.2 | Official effective literacy (population aged 7+). r=0.99 with the crude rate; kept because it is the standard, interpretable definition. Missing for Bangalore Rural. |
| `Secondary_Education` | persons | Census 2011 | 0 | Persons with secondary education. |
| `Higher_Education` | persons | Census 2011 | 0 | Persons with higher(-secondary) education. |
| `Graduate_Education` | persons | Census 2011 | 0 | Graduates and above. |
| `Secondary_Edu_pct` | % | derived | 0 | Secondary_Education / Population. |
| `Higher_Edu_pct` | % | derived | 0 | Higher_Education / Population. |
| `Graduate_pct` | % | derived | 0 | Graduate_Education / Population. |

## Livelihood

| Column | Unit | Source | Missing % | Description |
|---|---|---|---|---|
| `Workers` | persons | Census 2011 | 0 | Total workers. |
| `Male_Workers` | persons | Census 2011 | 0 | Male workers. |
| `Female_Workers` | persons | Census 2011 | 0 | Female workers. |
| `Cultivator_Workers` | persons | Census 2011 | 0 | Cultivators. |
| `Agricultural_Workers` | persons | Census 2011 | 0 | Agricultural labourers. |
| `Household_Workers` | persons | Census 2011 | 0 | Household-industry workers. |
| `Worker_Participation_Rate` | % | derived | 0 | Workers / Population. |
| `Male_Worker_Participation_Rate` | % | derived | 0 | Male workers / male population. |
| `Female_Worker_Participation_Rate` | % | derived | 0 | Female workers / female population. High values in poor agrarian districts reflect farm labour, not opportunity. |
| `Cultivator_Share` | % | derived | 0 | Cultivators / Workers. |
| `Agri_Labour_Share` | % | derived | 0 | Agricultural labourers / Workers. |
| `Household_Industry_Share` | % | derived | 0 | Household-industry workers / Workers. |
| `Farm_Worker_Share` | % | derived | 0 | Cultivators + agricultural labourers as % of workers. RURALITY PROXY (the supplied Census file has no urban/rural split). |
| `NonFarm_Worker_Share` | % | derived | 0 | 100 - Farm_Worker_Share. |

## Religion

| Column | Unit | Source | Missing % | Description |
|---|---|---|---|---|
| `Hindus` | persons | Census 2011 | 0 | Context only - not used in scoring. |
| `Muslims` | persons | Census 2011 | 0 | Context only - not used in scoring. |
| `Christians` | persons | Census 2011 | 0 | Context only - not used in scoring. |
| `Sikhs` | persons | Census 2011 | 0 | Context only - not used in scoring. |
| `Buddhists` | persons | Census 2011 | 0 | Context only - not used in scoring. |
| `Jains` | persons | Census 2011 | 0 | Context only - not used in scoring. |
| `Hindus_pct` | % | derived | 0 | Share of population. |
| `Muslims_pct` | % | derived | 0 | Share of population. |
| `Christians_pct` | % | derived | 0 | Share of population. |
| `Sikhs_pct` | % | derived | 0 | Share of population. |
| `Buddhists_pct` | % | derived | 0 | Share of population. |
| `Jains_pct` | % | derived | 0 | Share of population. |

## Transport

| Column | Unit | Source | Missing % | Description |
|---|---|---|---|---|
| `Railway_Station_Count` | count | timetable + DataMeet stations | 0 | Active (timetabled) stations inside the district polygon. 0 is a confirmed zero (national timetable). |
| `Daily_Train_Stops` | count | timetable | 0 | Sum over the district's stations of distinct trains stopping (timetable is undated; treat as a relative service level). |
| `Trains_Serving` | count | timetable | 0 | Distinct trains that stop at >=1 station in the district. |
| `Nearest_Railway_km` | km | derived | 0 | Great-circle distance from district centroid to the nearest active station (can exceed 1,000 km for islands). |
| `Stations_per_1000sqkm` | per 1000 km2 | derived | 0 | Station density. |
| `Stations_per_100k_pop` | per 100k | derived | 0 | Stations per 100,000 people. |

## Markets

| Column | Unit | Source | Missing % | Description |
|---|---|---|---|---|
| `Mandi_Count` | count | commodity_price | 76.4 | Distinct markets reporting on 19-May-2025. NaN = district not in the snapshot (NOT zero). |
| `Mandi_Commodities` | count | commodity_price | 76.4 | Distinct commodities reported in the district. NaN as above. |

## NREGA

| Column | Unit | Source | Missing % | Description |
|---|---|---|---|---|
| `NREGA_Active_JobCard_pct` | % | NREGA | 29.5 | Active job cards / job cards issued. |
| `NREGA_Avg_Days_per_HH` | days | NREGA | 29.5 | Average days of employment per household (financial year of the file, undated). |
| `NREGA_Avg_Wage_Rs` | Rs/day | NREGA | 29.5 | Average wage rate per person-day. |
| `NREGA_100Day_HH_pct` | % | NREGA | 29.5 | Households completing 100 days / households that worked. |
| `NREGA_Women_Persondays_pct` | % | NREGA | 29.5 | Women's share of persondays. |
| `NREGA_SC_ST_Persondays_pct` | % | NREGA | 29.5 | SC+ST share of persondays. |
| `NREGA_Works_Completed_pct` | % | NREGA | 29.5 | Completed works / works taken up. |
| `NREGA_Match_Method` | text | derived | 8.9 | How the NREGA row was matched to the 2011 district (exact / alias / fuzzy). Ratios only, because new districts split old ones. |

## Health (STATE-level)

| Column | Unit | Source | Missing % | Description |
|---|---|---|---|---|
| `StateLvl_PHC_Doctor_Staffing_pct` | % | PHC doctors 2017 | 0 | Doctors in position / required at PHCs, capped at 100. Same value for every district of the state. |
| `StateLvl_PHC_Doctor_Vacancy_pct` | % | PHC doctors 2017 | 13.3 | Vacant / sanctioned posts (NaN where the state did not report). |
| `StateLvl_PHC_Doctors_per_100k` | per 100k | PHC doctors 2017 + Census | 0 | PHC doctors in position per 100,000 state population. |

## Education (STATE-level)

| Column | Unit | Source | Missing % | Description |
|---|---|---|---|---|
| `StateLvl_Dropout_Primary` | % | Dropout 2012-15 | 3.8 | Mean of available years of the primary dropout ratio ('NR' cells ignored). |
| `StateLvl_Dropout_UpperPrimary` | % | Dropout 2012-15 | 2.2 | Same for upper primary. |
| `StateLvl_Dropout_Secondary` | % | Dropout 2012-15 | 0.2 | Same for secondary. |

## Provenance

| Column | Unit | Source | Missing % | Description |
|---|---|---|---|---|
| `Source_Census_Period` | text | - | 0 | Reference period of the Census block. |
| `Source_Railway_Period` | text | - | 0 | Reference period of the railway block. |
| `Source_Market_Period` | text | - | 76.4 | Reference date of the mandi snapshot (blank where not observed). |
| `Source_NREGA_Period` | text | - | 29.5 | Reference period of the NREGA block. |
| `Source_Health_Period` | text | - | 0 | Reference period of the health block. |
| `Source_Dropout_Period` | text | - | 0.2 | Reference period of the dropout block. |
| `Source_Index_Version` | text | - | 0 | Index version and weights. |

## RAI pillar

| Column | Unit | Source | Missing % | Description |
|---|---|---|---|---|
| `Education_Access_Score` | 0-100 | derived | 0 | Mean of winsorised-scaled: Literacy_Rate_Effective, Secondary_Edu_pct, log Graduate_pct. |
| `Transport_Access_Score` | 0-100 | derived | 0 | Mean of: inverted log Nearest_Railway_km, log Stations_per_1000sqkm, log Trains_Serving. |
| `Health_Access_Score` | 0-100 | derived | 0 | Mean of state-level PHC staffing % and log doctors per 100k. STATE resolution. |
| `Livelihood_Access_Score` | 0-100 | derived | 0 | Scaled NonFarm_Worker_Share. |

## RAI

| Column | Unit | Source | Missing % | Description |
|---|---|---|---|---|
| `Overall_Accessibility_Index` | 0-100 | derived | 0 | RuralReach Accessibility Index = 0.30 Education + 0.30 Transport + 0.20 Health + 0.20 Livelihood (weights renormalised over available pillars). |
| `RAI_Rank` | rank | derived | 0 | 1 = best access among 640 districts. |
| `Access_Tier` | text | derived | 0 | Low (bottom quartile) / Medium / High (top quartile) of RAI. |
| `Priority_Group` | text | derived | 0 | 1 Critical gap (Farm share >= median and Low tier); 2 High priority; 3 Monitor; 4 Well served. |

## Spatial

| Column | Unit | Source | Missing % | Description |
|---|---|---|---|---|
| `LISA_Cluster` | text | derived | 0 | Local Moran's I class of RAI (k=8 neighbours, 499 permutations, p<0.05). |

## Typology

| Column | Unit | Source | Missing % | Description |
|---|---|---|---|---|
| `Cluster` | 0-4 | derived | 0 | K-Means typology (k=5), ordered by mean RAI. |
| `Cluster_Name` | text | derived | 0 | Descriptive label of the cluster. |
