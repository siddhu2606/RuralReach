# %% [markdown]
# # 01 · Data audit
# **RuralReach – Rural Service Accessibility Intelligence System** · Fundamentals of Data Science
#
# Following the *Dataset Integration Guide*, the first pass is an **audit, not a merge**:
# rows/columns, dtypes, geographic coverage, duplicates, missingness, time period and candidate join keys
# for every source. Original files in `raw/` are never edited; archives are unpacked into `extracted/`.

# %%
import sys, zipfile, json, warnings
from pathlib import Path
_p = Path.cwd().resolve()
while not (_p / "src" / "rr_utils.py").exists():
    _p = _p.parent
sys.path.insert(0, str(_p / "src"))
from rr_utils import *
warnings.filterwarnings("ignore")
pd.set_option("display.width", 200); pd.set_option("display.max_columns", 40)

# %% [markdown]
# ## 1 · Unpack archives (guide §3)
# `archive.zip` turned out to be the **district shapefile** (`output.shp/.dbf/.shx/.prj/.cpg` – kept together)
# and `schedules.json.zip` is the **Indian Railways timetable** (train × station rows).

# %%
for zname, target in [("archive.zip", EXTRACTED / "district_shapefile"), ("schedules.json.zip", EXTRACTED / "railway_data")]:
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(RAW / zname) as z:
        for info in z.infolist():
            if not (target / info.filename).exists():
                z.extract(info, target)
    print(zname, "->", sorted(p.name for p in target.iterdir()))

# %% [markdown]
# ## 2 · Load every source

# %%
import geopandas as gpd
census = pd.read_csv(RAW / "6. India Census 2011.csv")
centroids = pd.read_csv(RAW / "district wise centroids.csv")
literacy = pd.read_csv(RAW / "Literacy Data 2011.csv")
nrega = pd.read_csv(RAW / "NREGA.csv")
mandi = pd.read_csv(RAW / "commodity_price.csv")
dropout = pd.read_csv(RAW / "dropout-ratio-2012-2015.csv")
phc = pd.read_csv(RAW / "allo-doc-PHCS_2017.csv")
colnames = pd.read_csv(RAW / "hlpca-colnames.csv", header=None, names=["code", "description", "x", "y"], usecols=[0, 1], on_bad_lines="skip", engine="python")  # a few malformed lines (unquoted commas) are skipped: metadata only
shp = gpd.read_file(EXTRACTED / "district_shapefile" / "output.shp")
rail = pd.read_json(EXTRACTED / "railway_data" / "schedules.json")
stations = gpd.read_file(RAW / "stations.json")          # DataMeet – coordinates for station codes (supplementary)

# %% [markdown]
# ## 3 · Audit table
# One row per source: size, duplicate rows, missing cells, geography and period.

# %%
def audit(name, df, role, level, period, geo_cols=None, key=None, note=""):
    d = pd.DataFrame(df.drop(columns="geometry", errors="ignore"))
    miss = int(d.isna().sum().sum())
    nobj = int((d.dtypes == "object").sum())
    return dict(
        source=name, role=role, rows=len(d), cols=d.shape[1], numeric_cols=d.shape[1] - nobj, text_cols=nobj,
        duplicate_rows=int(d.duplicated().sum()), missing_cells=miss,
        missing_pct=round(100 * miss / max(d.size, 1), 2), geographic_level=level, period=period,
        states=d[geo_cols[0]].nunique() if geo_cols else np.nan,
        join_key=key, note=note)

rows = [
    audit("India Census 2011", census, "CORE / master", "district (640)", "2011", ["State_name"], "State+District", "no urban/rural split, no facilities; District_code is a 1..640 serial, not the official code"),
    audit("District centroids", centroids, "CORE", "district (594)", "undated (older district list)", ["State"], "State+District", "names follow older spellings (Orissa, Uttaranchal)"),
    audit("District shapefile (archive.zip)", shp, "MAP", "district polygons (693)", "post-2011 boundaries + 2011 pop", ["statename"], "Population anchor + name", "33 post-2011 districts have no population; Telangana split out"),
    audit("Railway schedules", rail, "CORE", "train x station stop (417k)", "undated timetable", None, "station_code", "NO coordinates -> need station coordinate table"),
    audit("Railway stations (DataMeet)", stations, "SUPPLEMENT", "station point (8.5k)", "undated", ["state"], "station_code", "supplementary open data, supplies lat/lon for timetable codes"),
    audit("Commodity / mandi prices", mandi, "SUPPORTING", "market x commodity (2.7k)", "single day 19-May-2025", ["State"], "State+District", "only 16 states / 158 districts"),
    audit("NREGA", nrega, "SUPPORTING", "district (740, current)", "latest FY snapshot (undated)", ["state_name"], "State+District", "uses present-day districts (incl. new splits)"),
    audit("Literacy Data 2011", literacy, "SUPPORTING", "district (640)", "2011", ["State"], "State+District", "duplicates Census-derived literacy -> validation only"),
    audit("Dropout ratio 2012-15", dropout, "OPTIONAL", "state/UT x year", "2012-13..2014-15", ["State_UT"], "State", "contains 'NR' / corrupt text cells"),
    audit("PHC doctors 2017", phc, "CORE (health)", "state/UT (37)", "2017", ["State/ UT"], "State", "state-level only; not a district facility file"),
    audit("hlpca-colnames", colnames, "METADATA", "n/a", "2011 HLPCA", None, None, "column dictionary - NOT merged"),
]
audit_df = pd.DataFrame(rows)
audit_df.to_csv(PROCESSED / "data_audit_summary.csv", index=False)
audit_df

# %% [markdown]
# ## 4 · Deep checks on the master (Census)

# %%
c = census.copy()
checks = {
    "districts": len(c),
    "duplicate State+District": int(c.duplicated(["State_name", "District_name"]).sum()),
    "Male + Female != Population": int((c.Male + c.Female != c.Population).sum()),
    "Literate > Population": int((c.Literate > c.Population).sum()),
    "Workers > Population": int((c.Workers > c.Population).sum()),
    "Male_Workers + Female_Workers != Workers": int((c.Male_Workers + c.Female_Workers != c.Workers).sum()),
    "Age groups != Population": int((c.Age_Group_0_29 + c.Age_Group_30_49 + c.Age_Group_50 != c.Population).sum()),
    "Religion sum > Population": int((c[["Hindus","Muslims","Christians","Sikhs","Buddhists","Jains"]].sum(axis=1) > c.Population).sum()),
    "missing cells": int(c.isna().sum().sum()),
    "negative values": int((c.select_dtypes("number") < 0).sum().sum()),
}
pd.Series(checks, name="value").to_frame()

# %% [markdown]
# **Reading:** the Census table is internally consistent (no gaps, no negatives, gender and age totals reconcile),
# so it is a sound master. Everything else must be reshaped to *one row per district* before joining.

# %% [markdown]
# ## 5 · Geographic coverage vs the Census master
# Using the state + district key (after name cleaning) each source is tested for how many of its rows
# can be placed on a Census district – this drives how each source is used.

# %%
c["match_state"] = c.State_name.map(match_state); c["dkey"] = c.District_name.map(district_key)
alias_tbl = pd.read_csv(ROOT / "src" / "district_aliases.csv")
alias = {(match_state(r.state), district_key(r.source_name)): district_key(r.census_name) for r in alias_tbl.itertuples()}

def coverage(name, df, st, di):
    d = df[[st, di]].drop_duplicates().copy(); d["match_state"] = d[st].map(match_state); d["dkey"] = d[di].map(district_key)
    m = fuzzy_match(c, d, alias=alias)
    got = m.l_index.notna().sum()
    return dict(source=name, source_districts=len(d), matched_to_census=int(got),
                census_districts_covered=int(m.l_index.nunique()), census_coverage_pct=round(100 * m.l_index.nunique() / len(c), 1),
                exact=int((m.method == "exact").sum()), alias=int((m.method == "alias").sum()), fuzzy=int((m.method == "fuzzy").sum()),
                unmatched=int((m.method.isin(["unmatched", "duplicate_target_dropped"])).sum()))

cov = pd.DataFrame([coverage("District centroids", centroids, "State", "District"),
                    coverage("Literacy 2011", literacy, "State", "District"),
                    coverage("NREGA", nrega, "state_name", "district_name"),
                    coverage("Mandi prices", mandi, "State", "District")])
cov.to_csv(PROCESSED / "name_match_coverage.csv", index=False)
cov

# %% [markdown]
# **Reading:** centroid and literacy files align with the Census almost 1:1. NREGA uses *present-day* districts, so
# ~150 new districts (post-2011 splits) have no 2011 counterpart – they are **documented, not forced**.
# The mandi file covers only a quarter of districts, so it is *supporting*, never a complete market-access measure.

# %% [markdown]
# ## 6 · Shapefile ↔ Census: population as an anchor
# The shapefile carries the 2011 population (`totalpopul`). Because Census populations are unique, an exact
# population match is a far safer key than spelling.

# %%
anchor = census.merge(shp[["distname", "statename", "totalpopul"]], left_on="Population", right_on="totalpopul", how="left")
print("Census districts with an exact-population polygon:", anchor.distname.notna().sum(), "of", len(census))
print("Census districts without one:", anchor[anchor.distname.isna()][["State_name", "District_name"]].shape[0])
print("Polygons without population (post-2011 new districts):", int(shp.totalpopul.isna().sum()))

# %% [markdown]
# The 10 unmatched Census districts are the 9 old **Telangana** districts (Census files them under Andhra Pradesh,
# the shapefile uses the 31 new Telangana districts) plus **Jaintia Hills** (split into West/East). These are handled with an
# explicit, documented parent map in notebook 02 – exactly the "correction/mapping table" the guide asks for.

# %% [markdown]
# ## 7 · Railway timetable & station table

# %%
print(rail.head(3).to_string())
print("\nunique trains:", rail.train_number.nunique(), "| unique station codes:", rail.station_code.nunique())
st = stations[stations.geometry.notna()]
print("stations with coordinates:", len(st), "of", len(stations))
print("timetable station codes found in coordinate table:",
      round(100 * rail.station_code.drop_duplicates().isin(st.code).mean(), 1), "%")

# %% [markdown]
# ## 8 · Dropout & PHC files (state level)
# Both are *state* tables, so they can only enter the district master as **state-level context** (flagged as such).
# The dropout file is dirty (`NR`, corrupted headers, double spaces in state names):

# %%
num = dropout.drop(columns=["State_UT", "year"]).apply(pd.to_numeric, errors="coerce")
print("non-numeric / NR cells:", int(num.isna().sum().sum()), "of", num.size)
print("state spellings:", sorted(set(dropout.State_UT[dropout.State_UT.str.contains("  ")])))

# %% [markdown]
# ## 9 · Audit conclusions → integration plan
# | Source | Decision |
# |---|---|
# | Census 2011 | **Master table** (one row = one district) |
# | Centroids | Join on cleaned State+District via alias table; fall back to polygon centroid |
# | Shapefile | Geometry + area; dissolved to the 640 Census districts via population anchor + parent map |
# | Railways | Station coordinates → spatial join → station count, trains, distance to nearest station |
# | NREGA | **Ratios only** (counts are unsafe because new districts split old ones) |
# | Mandi | Market counts for covered districts, NaN elsewhere (not 0) |
# | Literacy 2011 | Validation of Census literacy only (would duplicate) |
# | Dropout / PHC | State-level context columns, clearly flagged |
# | hlpca-colnames | Metadata only |
# | **Not supplied** | Indian School Education Statistics (district) and a district PHC/CHC facility file → documented gap |
