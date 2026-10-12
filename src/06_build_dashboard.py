"""Builds the static, self-contained interactive dashboard: docs/index.html (served by GitHub Pages).
Only external dependency in the page: Leaflet from cdnjs."""
import json, shutil, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from rr_utils import *
import geopandas as gpd
from shapely.geometry import mapping

df = pd.read_csv(FINAL / "RuralReach_Master.csv")
geo = gpd.read_file(FINAL / "RuralReach_Districts.gpkg")
geo = geo.merge(df[["District_ID"]], on="District_ID").set_index("District_ID").loc[df.District_ID].reset_index()
geo["geometry"] = geo.geometry.simplify(0.012, preserve_topology=True)

def rnd(c, n=3):
    return [round(c[0], n), round(c[1], n)]
def ring(r): return [rnd(p) for p in r.coords]
def geom_json(g):
    if g.geom_type == "Polygon":
        return {"type": "Polygon", "coordinates": [ring(g.exterior)] + [ring(i) for i in g.interiors]}
    parts = [p for p in g.geoms if p.area > 0.0004] or list(g.geoms)       # drop microscopic slivers
    return {"type": "MultiPolygon", "coordinates": [[ring(p.exterior)] + [ring(i) for i in p.interiors] for p in parts]}
features = [{"type": "Feature", "id": i, "properties": {}, "geometry": geom_json(g)} for i, g in enumerate(geo.geometry)]
gj = {"type": "FeatureCollection", "features": features}

# --- tabular payload (columnar arrays keep the page small) -----------------------------------------
cols = {
    "id": "District_ID", "d": "District_name", "s": "State_Current", "pop": "Population", "area": "District_Area_sqkm", "den": "Population_Density",
    "rai": "Overall_Accessibility_Index", "rank": "RAI_Rank", "edu": "Education_Access_Score", "tra": "Transport_Access_Score",
    "hea": "Health_Access_Score", "liv": "Livelihood_Access_Score", "lit": "Literacy_Rate_Effective", "farm": "Farm_Worker_Share",
    "rail": "Nearest_Railway_km", "stn": "Railway_Station_Count", "trn": "Trains_Serving", "grad": "Graduate_pct", "fwpr": "Female_Worker_Participation_Rate",
    "sr": "Sex_Ratio", "phc": "StateLvl_PHC_Doctor_Staffing_pct", "nd": "NREGA_Avg_Days_per_HH", "mc": "Mandi_Count",
    "tier": "Access_Tier", "pg": "Priority_Group", "lisa": "LISA_Cluster", "cl": "Cluster", "cn": "Cluster_Name",
}
tab = {}
for k, c in cols.items():
    s = df[c]
    if not pd.api.types.is_numeric_dtype(s):
        tab[k] = s.where(s.notna(), None).tolist()
    else:
        tab[k] = [None if pd.isna(v) else (round(float(v), 2) if abs(v) < 1e6 else int(v)) for v in s]
s = json.load(open(PROCESSED / "results_summary.json"))
crit = df[df.Priority_Group.str.startswith("1")]
state = (df.groupby("State_Current").apply(lambda g: pd.Series({
    "n": len(g), "pop": g.Population.sum(), "rai": np.average(g.Overall_Accessibility_Index, weights=g.Population),
    "crit": int(g.Priority_Group.str.startswith("1").sum())})).reset_index().sort_values("rai"))
meta = dict(
    kpi=dict(n=len(df), pop_m=round(df.Population.sum() / 1e6), crit_n=len(crit), crit_pop=round(crit.Population.sum() / 1e6),
             far_n=int((df.Nearest_Railway_km > 50).sum()), far_pop=round(df.loc[df.Nearest_Railway_km > 50, "Population"].sum() / 1e6, 1),
             moran=round(s["moran_rai"], 2), ml=round(s["ml_group"]["Gradient Boosting"], 2)),
    states=[dict(s=r.State_Current, n=int(r.n), pop=float(r.pop), rai=round(float(r.rai), 1), crit=int(r.crit)) for r in state.itertuples()],
    clusters=[dict(i=int(i), n=n) for i, n in df.Cluster_Name.groupby(df.Cluster).first().items()])
payload = json.dumps({"geo": gj, "tab": tab, "meta": meta}, separators=(",", ":"), ensure_ascii=False)

html = (Path(__file__).parent / "dashboard_template.html").read_text(encoding="utf-8").replace("/*__DATA__*/null", payload)
DOCS.mkdir(exist_ok=True)
(DOCS / "index.html").write_text(html, encoding="utf-8")
(DOCS / "data").mkdir(exist_ok=True)
shutil.copy(FINAL / "RuralReach_Master.csv", DOCS / "data" / "RuralReach_Master.csv")
shutil.copy(FINAL / "RuralReach_Data_Dictionary.csv", DOCS / "data" / "RuralReach_Data_Dictionary.csv")
(DOCS / ".nojekyll").write_text("")
print("index.html: %.2f MB" % (len(html.encode("utf-8")) / 1e6))
