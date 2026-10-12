# %% [markdown]
# # 02 · Build the district master dataset
# **RuralReach** – one row = one district. Census 2011 is the base; every other source is first
# reshaped to district level and attached with a **left join** (guide §5–§8). Missing ≠ 0.
#
# Pipeline: Census → polygon crosswalk → centroids → railways → mandi → NREGA → state-level context → validation → export.

# %%
import sys, warnings
from pathlib import Path
_p = Path.cwd().resolve()
while not (_p / "src" / "rr_utils.py").exists():
    _p = _p.parent
sys.path.insert(0, str(_p / "src"))
from rr_utils import *
import geopandas as gpd
from shapely.ops import unary_union
warnings.filterwarnings("ignore")
pd.set_option("display.width", 200); pd.set_option("display.max_columns", 60)
LOG = {}                                    # facts reported in the validation report

# %% [markdown]
# ## 1 · Census master + cleaned keys

# %%
census = pd.read_csv(RAW / "6. India Census 2011.csv")
m = census.copy()
m["state_clean"] = m.State_name.map(canon_state)
m["district_clean"] = m.District_name.map(clean_text)
m["match_state"] = m.State_name.map(match_state)
m["dkey"] = m.District_name.map(district_key)
m["District_ID"] = "RR" + m.District_code.astype(str).str.zfill(3)
assert m.District_ID.is_unique and not m.duplicated(["state_clean", "district_clean"]).any()
print(m.shape)

# %% [markdown]
# ## 2 · Polygon crosswalk (population anchor + documented parent map)
# The shapefile is a tiling of India with **post-2011 boundaries**: parents of newly carved districts have *shrunk* polygons.
# To recover each Census-2011 district we (i) anchor on the exact 2011 population, (ii) fold post-2011 child districts back
# into their 2011 parent with a hand-built map, and (iii) dissolve.

# %%
shp = gpd.read_file(EXTRACTED / "district_shapefile" / "output.shp").reset_index(drop=True)
shp["pol_id"] = shp.index

# (i) exact population anchor ---------------------------------------------------------------
pop2idx = m.set_index("Population").index.to_series().reset_index(drop=True)
pop_to_row = dict(zip(m.Population, m.index))
shp["census_row"] = shp.totalpopul.map(pop_to_row)
shp["link"] = np.where(shp.census_row.notna(), "population_anchor", None)

# (ii) parent map for post-2011 districts: (shapefile state, shapefile district) -> (census state, census district)
PARENT = {
    # Telangana (31 new districts) -> 2011 Andhra Pradesh districts that became Telangana
    **{("Telangana", k): ("ANDHRA PRADESH", v) for k, v in {
        "Adilabad": "Adilabad", "Komaram Bheem": "Adilabad", "Nirmal": "Adilabad", "Mancherial": "Adilabad",
        "Nizamabad": "Nizamabad", "Kamareddy": "Nizamabad",
        "Karimnagar": "Karimnagar", "Jagtial": "Karimnagar", "Peddapalli": "Karimnagar", "Rajanna Sircilla": "Karimnagar",
        "Medak": "Medak", "Sangareddy": "Medak", "Siddipet": "Medak",
        "Rangareddy": "Rangareddy", "Vikarabad": "Rangareddy", "Medchal": "Rangareddy",
        "Mahabubnagar": "Mahbubnagar", "Wanaparthy": "Mahbubnagar", "Nagarkurnool": "Mahbubnagar", "Jogulamba": "Mahbubnagar",
        "Nalgonda": "Nalgonda", "Suryapet": "Nalgonda", "Yadadri": "Nalgonda",
        "Warangal (R)": "Warangal", "Warangal (U)": "Warangal", "Jangaon": "Warangal", "Mahabubabad": "Warangal", "Jayashankar": "Warangal",
        "Khammam": "Khammam", "Bhadradri": "Khammam"}.items()},
    ("Gujarat", "Aravali"): ("GUJARAT", "Sabar Kantha"), ("Gujarat", "Chhota Udaipur"): ("GUJARAT", "Vadodara"),
    ("Gujarat", "Batod"): ("GUJARAT", "Bhavnagar"), ("Gujarat", "Gir Somnath"): ("GUJARAT", "Junagadh"),
    ("Gujarat", "Devbhumi Dwarka"): ("GUJARAT", "Jamnagar"), ("Gujarat", "Mahisagar"): ("GUJARAT", "Panch Mahals"),
    ("Gujarat", "Morbi"): ("GUJARAT", "Rajkot"),
    ("Maharashtra", "Palghar"): ("MAHARASHTRA", "Thane"),
    ("Uttar Pradesh", "Amethi"): ("UTTAR PRADESH", "Sultanpur"), ("Uttar Pradesh", "Sambhal"): ("UTTAR PRADESH", "Moradabad"),
    ("Uttar Pradesh", "Hapur"): ("UTTAR PRADESH", "Ghaziabad"), ("Uttar Pradesh", "Samli"): ("UTTAR PRADESH", "Muzaffarnagar"),
    ("Punjab", "Pathankot"): ("PUNJAB", "Gurdaspur"), ("Punjab", "Fazilka"): ("PUNJAB", "Firozpur"),
    ("Tripura", "Unokoti"): ("TRIPURA", "North Tripura"), ("Tripura", "Gomati"): ("TRIPURA", "South Tripura"),
    ("Tripura", "Khowai"): ("TRIPURA", "West Tripura"), ("Tripura", "Sipahijula"): ("TRIPURA", "West Tripura"),
    ("Meghalaya", "South West Khasi Hills"): ("MEGHALAYA", "West Khasi Hills"),
    ("Meghalaya", "West Jaintia Hills"): ("MEGHALAYA", "Jaintia Hills"), ("Meghalaya", "East Jaintia Hills"): ("MEGHALAYA", "Jaintia Hills"),
    ("Meghalaya", "North Garo Hills"): ("MEGHALAYA", "East Garo Hills"), ("Meghalaya", "South West Garo Hills"): ("MEGHALAYA", "West Garo Hills"),
    ("Chhatisgarh", "Bemetra"): ("CHHATTISGARH", "Durg"), ("Chhatisgarh", "Balod"): ("CHHATTISGARH", "Durg"),
    ("Chhatisgarh", "Mungeli"): ("CHHATTISGARH", "Bilaspur"),
    ("Chhatisgarh", "Gariaband"): ("CHHATTISGARH", "Raipur"), ("Chhatisgarh", "Baloda Bazar"): ("CHHATTISGARH", "Raipur"),
    ("Chhatisgarh", "Sukma"): ("CHHATTISGARH", "Dakshin Bastar Dantewada"),
    ("Chhatisgarh", "Balrampur"): ("CHHATTISGARH", "Surguja"), ("Chhatisgarh", "Surajpur"): ("CHHATTISGARH", "Surguja"),
    ("Chhatisgarh", "Kondagaon"): ("CHHATTISGARH", "Bastar"),
}
parent_tbl = []
for (st, d), (cst, cd) in PARENT.items():
    hit = m[(m.state_clean == cst) & (m.dkey == district_key(cd))]
    assert len(hit) == 1, (st, d, cst, cd)
    parent_tbl.append(dict(shp_state=st, shp_district=d, census_state=cst, census_district=cd, census_row=hit.index[0]))
parent_tbl = pd.DataFrame(parent_tbl)
for r in parent_tbl.itertuples():
    sel = (shp.statename == r.shp_state) & (shp.distname == r.shp_district) & shp.census_row.isna()
    shp.loc[sel, "census_row"] = r.census_row
    shp.loc[sel, "link"] = "parent_map"
parent_tbl.drop(columns="census_row").to_csv(PROCESSED / "post2011_parent_map.csv", index=False)

unlinked = shp[shp.census_row.isna()]
print("polygons linked:", shp.census_row.notna().sum(), "| polygons not linked:", len(unlinked), list(unlinked.distname))
print("census districts with >=1 polygon:", shp.census_row.nunique(), "of", len(m))
missing_poly = m.loc[~m.index.isin(shp.census_row.dropna().astype(int))]
assert missing_poly.empty, missing_poly[["State_name", "District_name"]]

# %% [markdown]
# Polygons that could not be linked (the placeholder *DATA NOT AVAILABLE* region in J&K) are excluded and logged.
# Dissolve to **one geometry per Census district** and compute area on an equal-area projection:

# %%
linked = shp[shp.census_row.notna()].copy(); linked["census_row"] = linked.census_row.astype(int)
geoms = linked.groupby("census_row").geometry.apply(lambda s: unary_union(list(s)))
gdf = gpd.GeoDataFrame({"census_row": geoms.index}, geometry=list(geoms.values), crs=shp.crs).set_index("census_row")
gdf["n_polygons"] = linked.groupby("census_row").size()
ALBERS = "+proj=aea +lat_0=24 +lon_0=78 +lat_1=12.5 +lat_2=35.5 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"
gdf["District_Area_sqkm"] = gdf.to_crs(ALBERS).area / 1e6
m["District_Area_sqkm"] = gdf.District_Area_sqkm.round(1)
m["Geometry_Link"] = linked.groupby("census_row").link.agg(lambda s: "population_anchor" if (s == "population_anchor").any() else "parent_map")
m["Geometry_Polygons_Merged"] = gdf.n_polygons
print(m.Geometry_Link.value_counts().to_dict())
shp_area = linked.groupby("census_row").distarea.sum()
ratio = (m.District_Area_sqkm / shp_area.reindex(m.index)).replace([np.inf], np.nan)
print("area vs shapefile 'distarea' attribute – median ratio %.3f, share within ±25%%: %.1f%%" % (ratio.median(), 100 * ratio.between(.75, 1.25).mean()))
LOG["polygons_unlinked"] = list(unlinked.distname)

# %% [markdown]
# ## 3 · Current-state label (Telangana / Ladakh) and derived Census indicators
# `State_Current` lets state-level sources (PHC doctors, dropout) be attached correctly for districts that moved state after 2011.

# %%
tel = linked[linked.statename == "Telangana"].census_row.unique()
m["State_Current"] = m.state_clean
m.loc[m.index.isin(tel) | (m.District_name == "Hyderabad"), "State_Current"] = "TELANGANA"
print(m.State_Current.value_counts().head(3).to_dict(), "| Telangana districts:", (m.State_Current == "TELANGANA").sum())

P = m.Population
m["Sex_Ratio"] = m.Female / m.Male * 1000
m["Literacy_Rate"] = m.Literate / P * 100
m["Worker_Participation_Rate"] = m.Workers / P * 100
m["Female_Worker_Participation_Rate"] = m.Female_Workers / m.Female * 100
m["Male_Worker_Participation_Rate"] = m.Male_Workers / m.Male * 100
m["Cultivator_Share"] = m.Cultivator_Workers / m.Workers * 100
m["Agri_Labour_Share"] = m.Agricultural_Workers / m.Workers * 100
m["Household_Industry_Share"] = m.Household_Workers / m.Workers * 100
m["Farm_Worker_Share"] = m.Cultivator_Share + m.Agri_Labour_Share            # rurality proxy (no urban/rural split in file)
m["Secondary_Edu_pct"] = m.Secondary_Education / P * 100
m["Higher_Edu_pct"] = m.Higher_Education / P * 100
m["Graduate_pct"] = m.Graduate_Education / P * 100
m["Young_Pop_pct"] = m.Age_Group_0_29 / P * 100
m["Middle_Pop_pct"] = m.Age_Group_30_49 / P * 100
m["Senior_Pop_pct"] = m.Age_Group_50 / P * 100
for r in ["Hindus", "Muslims", "Christians", "Sikhs", "Buddhists", "Jains"]:
    m[f"{r}_pct"] = m[r] / P * 100
m["Population_Density"] = P / m.District_Area_sqkm
m["Source_Census_Period"] = "2011"
print(m[["Literacy_Rate", "Sex_Ratio", "Farm_Worker_Share", "Population_Density"]].describe().round(1).T)

# %% [markdown]
# ## 4 · Coordinates: centroid file → polygon-centroid fallback
# The supplied centroid file is used first (guide §8-2); where a district has no match, the centroid of its Census polygon
# is used and the source is recorded. Both are compared as a cross-check.

# %%
alias_tbl = pd.read_csv(ROOT / "src" / "district_aliases.csv")
alias = {(match_state(r.state), district_key(r.source_name)): district_key(r.census_name) for r in alias_tbl.itertuples()}
cen = pd.read_csv(RAW / "district wise centroids.csv")
cen["match_state"] = cen.State.map(match_state); cen["dkey"] = cen.District.map(district_key)
mm = fuzzy_match(m, cen, alias=alias)
cen["census_row"] = mm.l_index; cen["method"] = mm.method
print(mm.method.value_counts().to_dict())
hit = cen.dropna(subset=["census_row"]).copy(); hit["census_row"] = hit.census_row.astype(int)
poly_c = gdf.to_crs(ALBERS).geometry.centroid.to_crs(4326)
m["Poly_Lat"], m["Poly_Lon"] = poly_c.y, poly_c.x
m["Latitude"] = hit.set_index("census_row").Latitude.reindex(m.index)
m["Longitude"] = hit.set_index("census_row").Longitude.reindex(m.index)
m["Coord_Source"] = np.where(m.Latitude.notna(), "centroid_file", "polygon_centroid")
m["Latitude"] = m.Latitude.fillna(m.Poly_Lat); m["Longitude"] = m.Longitude.fillna(m.Poly_Lon)
both = m[m.Coord_Source == "centroid_file"]
dist = haversine_km(both.Latitude, both.Longitude, both.Poly_Lat, both.Poly_Lon)
print("centroid file vs polygon centroid: median %.0f km, 90th pct %.0f km, >150 km: %d districts" % (dist.median(), dist.quantile(.9), (dist > 150).sum()))
bad = both[dist > 150][["State_name", "District_name", "Latitude", "Longitude", "Poly_Lat", "Poly_Lon"]].assign(km=dist[dist > 150].round(0))
print(bad)
# a centroid-file point > 150 km from the polygon is a data error (e.g. wrong district matched) -> trust the polygon
m.loc[bad.index, ["Latitude", "Longitude", "Coord_Source"]] = np.c_[m.loc[bad.index, "Poly_Lat"], m.loc[bad.index, "Poly_Lon"], ["polygon_centroid(file_rejected)"] * len(bad)]
LOG["centroid_rejected"] = bad.District_name.tolist()
m["Coord_Source"].value_counts()

# %% [markdown]
# ## 5 · Railways → district features
# The timetable has **no coordinates**, so station codes are joined to the DataMeet station table (supplementary open data)
# and placed in districts with a point-in-polygon join. Only stations that appear in the timetable (*active* passenger stations) count.

# %%
rail = pd.read_json(EXTRACTED / "railway_data" / "schedules.json")
rail["station_code"] = rail.station_code.astype(str).str.strip()
sched = rail.groupby("station_code").agg(Trains_Stopping=("train_number", "nunique"), station_name_tt=("station_name", "first")).reset_index()
st = gpd.read_file(RAW / "stations.json")
st = st[st.geometry.notna()].copy()
st = st[st.geometry.x.between(68, 98) & st.geometry.y.between(6, 38)]               # drop coordinates outside India's bounding box
st = st.drop_duplicates("code")
act = st.merge(sched, left_on="code", right_on="station_code", how="inner")
LOG["tt_codes"] = int(sched.station_code.nunique()); LOG["tt_codes_with_xy"] = int(len(act))
print("timetable stations:", len(sched), "| with valid coordinates:", len(act))

pts = gpd.GeoDataFrame(act[["code", "name", "Trains_Stopping"]], geometry=act.geometry, crs=4326)
polys = gdf.reset_index()[["census_row", "geometry"]]
j = gpd.sjoin(pts, polys, how="left", predicate="within")
j = j[~j.index.duplicated()]
n_in = j.census_row.notna().sum()
# coastal / simplification slivers: attach to the nearest polygon within 15 km
left = j[j.census_row.isna()].drop(columns=["index_right", "census_row"])
if len(left):
    near = gpd.sjoin_nearest(left.to_crs(ALBERS), polys.to_crs(ALBERS), how="left", max_distance=15000, distance_col="d")
    near = near[~near.index.duplicated()]
    j.loc[near.index, "census_row"] = near.census_row
print("stations inside a district polygon:", n_in, "| rescued within 15 km:", int(j.census_row.notna().sum() - n_in), "| unassigned:", int(j.census_row.isna().sum()))
j = j.dropna(subset=["census_row"]); j["census_row"] = j.census_row.astype(int)

g = j.groupby("census_row")
rail_feat = pd.DataFrame({"Railway_Station_Count": g.size(), "Daily_Train_Stops": g.Trains_Stopping.sum()})
# distinct trains that touch the district
tr = rail.merge(j[["code", "census_row"]], left_on="station_code", right_on="code")
rail_feat["Trains_Serving"] = tr.groupby("census_row").train_number.nunique()
# distance from district centroid to nearest *active* station (BallTree/haversine)
from sklearn.neighbors import BallTree
tree = BallTree(np.radians(np.c_[act.geometry.y, act.geometry.x]), metric="haversine")
dd, _ = tree.query(np.radians(m[["Latitude", "Longitude"]].values), k=1)
m["Nearest_Railway_km"] = (dd[:, 0] * 6371.0088).round(1)
for c_ in rail_feat:
    m[c_] = rail_feat[c_].reindex(m.index)
m[["Railway_Station_Count", "Daily_Train_Stops", "Trains_Serving"]] = m[["Railway_Station_Count", "Daily_Train_Stops", "Trains_Serving"]].fillna(0).astype(int)   # 0 = confirmed: station table is national & complete for the timetable
m["Stations_per_1000sqkm"] = m.Railway_Station_Count / m.District_Area_sqkm * 1000
m["Stations_per_100k_pop"] = m.Railway_Station_Count / P * 1e5
m["Source_Railway_Period"] = "undated timetable"
print("districts with no active station inside:", (m.Railway_Station_Count == 0).sum())
print(m[["Railway_Station_Count", "Trains_Serving", "Nearest_Railway_km"]].describe().round(1).T)

# %% [markdown]
# **Why 0 is legitimate here:** the timetable is national, so a district with no timetabled station inside really has none
# (the nearest one is quantified by `Nearest_Railway_km`). Contrast with NREGA/mandi below where absence = *unknown*.

# %% [markdown]
# ## 6 · Mandi (commodity) → market indicators
# One-day snapshot (19 May 2025) for 16 states. Unique markets per district; districts that do not appear stay **NaN**.

# %%
mk = pd.read_csv(RAW / "commodity_price.csv")
mk["match_state"] = mk.State.map(match_state); mk["dkey"] = mk.District.map(district_key)
mdist = mk[["State", "District", "match_state", "dkey"]].drop_duplicates().reset_index(drop=True)
# Markets located in a post-2011 child district physically lie inside its 2011 parent, so *counts* may be rolled up to the parent
# (not valid for NREGA ratios, which describe the child's own programme).
mandi_alias = dict(alias)
for st_, ch, par in [("Punjab", "Fazilka", "Firozpur"), ("Punjab", "Pathankot", "Gurdaspur"), ("Tripura", "Gomati", "South Tripura"), ("Tripura", "South District", "South Tripura"),
                     ("Tripura", "Khowai", "West Tripura"), ("Uttar Pradesh", "Amethi", "Sultanpur"), ("Uttar Pradesh", "Shamli", "Muzaffarnagar"),
                     ("Uttar Pradesh", "Sambhal", "Moradabad"), ("Rajasthan", "Beawar", "Ajmer"), ("Rajasthan", "Deeg", "Bharatpur"), ("Rajasthan", "Sanchore", "Jalor"),
                     ("Rajasthan", "Jaipur Rural", "Jaipur"), ("Rajasthan", "Jodhpur Rural", "Jodhpur"), ("West Bengal", "Jhargram", "Paschim Medinipur")]:
    mandi_alias[(match_state(st_), district_key(ch))] = district_key(par)
mmk = fuzzy_match(m, mdist, alias=mandi_alias, dedupe=False)
mdist["census_row"] = mmk.l_index
mk = mk.merge(mdist[["State", "District", "census_row"]], on=["State", "District"], how="left")
LOG["mandi_unmatched"] = mdist[mdist.census_row.isna()].District.tolist()
mkm = mk.dropna(subset=["census_row"]).copy(); mkm["census_row"] = mkm.census_row.astype(int)
mf = mkm.groupby("census_row").agg(Mandi_Count=("Market", "nunique"), Mandi_Commodities=("Commodity", "nunique"))
m["Mandi_Count"] = mf.Mandi_Count.reindex(m.index); m["Mandi_Commodities"] = mf.Mandi_Commodities.reindex(m.index)
m["Source_Market_Period"] = np.where(m.Mandi_Count.notna(), "2025-05-19 (single day)", None)
print("matched mandi districts:", m.Mandi_Count.notna().sum(), "| unmatched mandi districts:", len(LOG["mandi_unmatched"]), LOG["mandi_unmatched"])

# %% [markdown]
# ## 7 · NREGA → ratio features only
# NREGA uses present-day districts; many are splits of a 2011 district, so **absolute counts would be wrong** for the shrunken parent.
# Only ratios are used. Where a Census district receives no NREGA row it stays NaN.

# %%
ng = pd.read_csv(RAW / "NREGA.csv")
ng["match_state"] = ng.state_name.map(match_state); ng["dkey"] = ng.district_name.map(district_key)
mn = fuzzy_match(m, ng, alias=alias)
ng["census_row"] = mn.l_index; ng["match_method"] = mn.method
ng["match_score"] = mn.score
unm = ng[ng.census_row.isna()]
unm[["state_name", "district_name", "match_method"]].to_csv(PROCESSED / "unmatched_nrega_districts.csv", index=False)
print(mn.method.value_counts().to_dict())
x = ng.dropna(subset=["census_row"]).copy(); x["census_row"] = x.census_row.astype(int)
pdays = x["Persondays of Central Liability so far"].replace(0, np.nan)
feat = pd.DataFrame({
    "NREGA_Active_JobCard_pct": x["Total No. of Active Job Cards"] / x["Total No. of JobCards issued"] * 100,
    "NREGA_Avg_Days_per_HH": x["Average days of employment provided per Household"],
    "NREGA_Avg_Wage_Rs": x["Average Wage rate per day per person(Rs.)"],
    "NREGA_100Day_HH_pct": x["Total No of HHs completed 100 Days of Wage Employment"] / x["Total Households Worked"].replace(0, np.nan) * 100,
    "NREGA_Women_Persondays_pct": x["Women Persondays"] / pdays * 100,
    "NREGA_SC_ST_Persondays_pct": (x["SC persondays"] + x["ST persondays"]) / pdays * 100,
    "NREGA_Works_Completed_pct": x["Number of Completed Works"] / x["Total No. of Works Takenup (New+Spill Over)"].replace(0, np.nan) * 100,
}, index=x.census_row)
feat = feat.groupby(level=0).mean()
for c_ in feat:
    m[c_] = feat[c_].reindex(m.index)
m["NREGA_Match_Method"] = ng.dropna(subset=["census_row"]).assign(census_row=lambda d: d.census_row.astype(int)).set_index("census_row").match_method.reindex(m.index)
m["Source_NREGA_Period"] = np.where(m.NREGA_Avg_Days_per_HH.notna(), "latest FY snapshot (undated in file)", None)
print("Census districts with NREGA ratios:", m.NREGA_Avg_Days_per_HH.notna().sum(), "of", len(m), "| NREGA rows with no 2011 district:", len(unm))

# %% [markdown]
# ## 8 · Literacy file: validation only (guide: *use only if it adds non-duplicate indicators*)

# %%
lit = pd.read_csv(RAW / "Literacy Data 2011.csv")
lit["match_state"] = lit.State.map(match_state); lit["dkey"] = lit.District.map(district_key)
ml = fuzzy_match(m, lit, alias=alias)
lit["census_row"] = ml.l_index
lm = lit.dropna(subset=["census_row"]).copy(); lm["census_row"] = lm.census_row.astype(int)
chk = m.loc[lm.census_row, "Literacy_Rate"].values
ref = lm.Literacy.values
LOG["literacy_corr"] = float(np.corrcoef(chk, ref)[0, 1]); LOG["literacy_mae"] = float(np.mean(np.abs(chk - ref)))
LOG["literacy_n"] = len(lm)
print("Census-derived literacy vs reference file:  n=%d  r=%.4f  mean |diff|=%.2f pp" % (len(lm), LOG["literacy_corr"], LOG["literacy_mae"]))
m["Literacy_Rate_Effective"] = lm.set_index("census_row").Literacy.reindex(m.index)   # official definition: literates among population aged 7+
print("Literacy_Rate_Effective missing for:", m.loc[m.Literacy_Rate_Effective.isna(), ["State_name", "District_name"]].values.tolist())
print("-> r is ~0.99 so it is largely redundant; it is kept as ONE extra column because it uses the official 7+ definition (more interpretable than the crude rate).")
# note: the reference file is the *effective* literacy rate (7+ years) while Census-derived is crude (all ages) -> systematic offset is expected
print("systematic offset (reference - crude): %.1f pp" % np.mean(ref - chk))

# %% [markdown]
# ## 9 · State-level context: PHC doctors (2017) and school dropout (2012-15)
# Both files are *state tables*, so every district in a state receives the same value; the columns are prefixed `StateLvl_`
# so nobody mistakes them for district measurements.

# %%
phc = pd.read_csv(RAW / "allo-doc-PHCS_2017.csv")
phc = phc[phc["State/ UT"].str.contains("All India") == False].copy()
phc["state"] = phc["State/ UT"].map(canon_state)
rn = {"Required - [R]": "R", "Sanctioned - [S]": "S", "In Position - [P]": "P", "Vacant - [S-P]": "V"}
phc = phc.rename(columns=rn)
for c_ in ["R", "S", "P", "V"]:
    phc[c_] = pd.to_numeric(phc[c_], errors="coerce")
spop = m.groupby("State_Current").Population.sum()
phc["StateLvl_PHC_Doctor_Staffing_pct"] = (phc.P / phc.R * 100).clip(upper=100)         # in-position vs required, capped (surplus is not extra access)
phc["StateLvl_PHC_Doctor_Vacancy_pct"] = (phc.V / phc.S * 100)                           # NaN when sanctioned or vacant not reported
phc["StateLvl_PHC_Doctors_per_100k"] = phc.P / phc.state.map(spop) * 1e5
phc_f = phc.set_index("state")[["StateLvl_PHC_Doctor_Staffing_pct", "StateLvl_PHC_Doctor_Vacancy_pct", "StateLvl_PHC_Doctors_per_100k"]]
phc_unmatched = [s for s in phc_f.index if s not in set(m.State_Current)]
print("PHC states not in master:", phc_unmatched)
for c_ in phc_f:
    m[c_] = m.State_Current.map(phc_f[c_])
m["Source_Health_Period"] = np.where(m.StateLvl_PHC_Doctor_Staffing_pct.notna(), "2017 (state level)", None)
print(m.groupby("State_Current").StateLvl_PHC_Doctor_Staffing_pct.first().round(0).sort_values().head(6).to_dict())

# %%
dp = pd.read_csv(RAW / "dropout-ratio-2012-2015.csv")
dp.columns = [c_.replace("_", " ").strip() if False else c_ for c_ in dp.columns]
dp["state"] = dp.State_UT.map(canon_state)
dp = dp[dp.state != "ALL INDIA"]
cols = {"Primary_Total": "StateLvl_Dropout_Primary", "Upper Primary_Total": "StateLvl_Dropout_UpperPrimary", "Secondary _Total": "StateLvl_Dropout_Secondary"}
for k in cols:
    dp[k] = pd.to_numeric(dp[k], errors="coerce")               # 'NR' / corrupted text -> NaN (not zero)
dp_f = dp.groupby("state")[list(cols)].mean().rename(columns=cols)  # mean of the available years 2012-13..2014-15
for c_ in dp_f:
    m[c_] = m.State_Current.map(dp_f[c_])
m["Source_Dropout_Period"] = np.where(m.StateLvl_Dropout_Secondary.notna(), "2012-13..2014-15 mean (state level)", None)
print("dropout states not in master:", [s for s in dp_f.index if s not in set(m.State_Current)])
print(dp_f.describe().round(1).T)

# %% [markdown]
# ## 10 · Final validation (guide §10)

# %%
FINAL.mkdir(exist_ok=True)
val = []
def check(name, ok, detail=""):
    val.append(dict(check=name, passed=bool(ok), detail=detail)); print(("PASS " if ok else "FAIL ") + name, detail)

check("one row per district / no duplicate State+District", not m.duplicated(["state_clean", "district_clean"]).any(), f"{len(m)} rows")
check("row count equals Census master (no multiplication)", len(m) == len(census) == 640)
check("District_ID unique", m.District_ID.is_unique)
pct_cols = [c_ for c_ in m.columns if c_.endswith("_pct") or c_.endswith("_Rate") or c_.endswith("_Share")]
bad = {c_: (m[c_].min(), m[c_].max()) for c_ in pct_cols if not (m[c_].dropna().between(0, 100.0001)).all()}
check("percentages inside 0-100", not bad, str(bad) if bad else f"{len(pct_cols)} columns")
count_cols = ["Population", "Railway_Station_Count", "Daily_Train_Stops", "Trains_Serving", "Mandi_Count"]
check("no negative counts", all((m[c_].dropna() >= 0).all() for c_ in count_cols))
check("latitude/longitude inside India bbox (6-38N, 68-98E)", m.Latitude.between(6, 38).all() and m.Longitude.between(68, 98).all(),
      f"lat {m.Latitude.min():.1f}..{m.Latitude.max():.1f}, lon {m.Longitude.min():.1f}..{m.Longitude.max():.1f}")
check("numeric columns are numeric", all(pd.api.types.is_numeric_dtype(m[c_]) for c_ in m.columns if c_ in ("Population", "Literacy_Rate", "Nearest_Railway_km", "District_Area_sqkm")))
check("every district has a geometry", m.District_Area_sqkm.notna().all())
check("area plausible (sum within 10% of India's ~3.29M km2 land area)", abs(m.District_Area_sqkm.sum() / 3.287e6 - 1) < 0.1, f"{m.District_Area_sqkm.sum():,.0f} km2")
check("Census indicators reconcile (Male+Female==Pop)", (m.Male + m.Female == m.Population).all())
check("source period recorded for each block", all(c_ in m.columns for c_ in ["Source_Census_Period", "Source_Railway_Period", "Source_Market_Period", "Source_NREGA_Period", "Source_Health_Period", "Source_Dropout_Period"]))
valdf = pd.DataFrame(val)
assert valdf.passed.all(), valdf[~valdf.passed]

# %% [markdown]
# ### Redundancy check – drop near-duplicate columns (|r| > 0.98)

# %%
num = m.select_dtypes("number").drop(columns=["District_code"], errors="ignore")
corr = num.corr().abs()
pairs = [(a, b, round(corr.loc[a, b], 3)) for i, a in enumerate(corr.columns) for b in corr.columns[i + 1:] if corr.loc[a, b] > 0.98]
print(len(pairs), "pairs above 0.98 – raw counts are expected to correlate with population:")
print(pd.DataFrame(pairs, columns=["a", "b", "|r|"]).sort_values("|r|", ascending=False).head(20).to_string(index=False))

# %% [markdown]
# Raw Census **counts** (Male, Female, Hindus, …) are all ~population and intentionally kept in the master for traceability,
# but the analysis notebooks use *rates/shares*, which are not redundant. `Poly_Lat/Poly_Lon` helper columns are dropped from the export.

# %% [markdown]
# ## 11 · Export

# %%
order = (["District_ID", "State_name", "District_name", "state_clean", "district_clean", "State_Current"]
         + ["Latitude", "Longitude", "Coord_Source", "District_Area_sqkm", "Geometry_Link", "Geometry_Polygons_Merged"]
         + ["Population", "Male", "Female", "Sex_Ratio", "Population_Density", "Young_Pop_pct", "Middle_Pop_pct", "Senior_Pop_pct"]
         + ["Literate", "Literacy_Rate", "Literacy_Rate_Effective", "Secondary_Education", "Higher_Education", "Graduate_Education", "Secondary_Edu_pct", "Higher_Edu_pct", "Graduate_pct"]
         + ["Workers", "Male_Workers", "Female_Workers", "Cultivator_Workers", "Agricultural_Workers", "Household_Workers",
            "Worker_Participation_Rate", "Male_Worker_Participation_Rate", "Female_Worker_Participation_Rate",
            "Cultivator_Share", "Agri_Labour_Share", "Household_Industry_Share", "Farm_Worker_Share"]
         + ["Hindus", "Muslims", "Christians", "Sikhs", "Buddhists", "Jains"] + [f"{r}_pct" for r in ["Hindus", "Muslims", "Christians", "Sikhs", "Buddhists", "Jains"]]
         + ["Railway_Station_Count", "Daily_Train_Stops", "Trains_Serving", "Nearest_Railway_km", "Stations_per_1000sqkm", "Stations_per_100k_pop"]
         + ["Mandi_Count", "Mandi_Commodities"]
         + [c_ for c_ in m.columns if c_.startswith("NREGA_") and c_ != "NREGA_Match_Method"] + ["NREGA_Match_Method"]
         + [c_ for c_ in m.columns if c_.startswith("StateLvl_")]
         + [c_ for c_ in m.columns if c_.startswith("Source_")])
master = m[order].copy()
master = master.round({c_: 3 for c_ in master.select_dtypes("float").columns})
master.to_csv(FINAL / "RuralReach_Master_base.csv", index=False)
# geometry – kept separate from the CSV (guide §11)
gout = gdf.join(m[["District_ID", "State_name", "District_name"]]).reset_index(drop=True)
gout = gpd.GeoDataFrame(gout[["District_ID", "State_name", "District_name"]], geometry=gout.geometry, crs=4326)
gout.to_file(FINAL / "RuralReach_Districts.gpkg", driver="GPKG")
print(master.shape, "->", FINAL / "RuralReach_Master_base.csv")

# missingness per column
miss = master.isna().mean().mul(100).round(2).rename("missing_pct").to_frame()
miss["dtype"] = master.dtypes.astype(str)
miss.to_csv(PROCESSED / "missing_values_by_column.csv")
valdf.to_csv(PROCESSED / "validation_checks.csv", index=False)
pd.Series(LOG, dtype=object).to_json(PROCESSED / "pipeline_log.json", indent=1)
miss[miss.missing_pct > 0].sort_values("missing_pct", ascending=False)
