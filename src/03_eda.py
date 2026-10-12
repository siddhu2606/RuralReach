# %% [markdown]
# # 03 · Exploratory data analysis
# **RuralReach** – what does district-level access look like across India, and which factors move together?
# Input: `final/RuralReach_Master_base.csv` (validated in notebook 02). All figures are also saved to `assets/`.

# %%
import sys, warnings
from pathlib import Path
_p = Path.cwd().resolve()
while not (_p / "src" / "rr_utils.py").exists():
    _p = _p.parent
sys.path.insert(0, str(_p / "src"))
from rr_utils import *
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib as mpl
import seaborn as sns
from scipy import stats
warnings.filterwarnings("ignore")

PAL = dict(primary="#1f6f78", accent="#e07a1f", muted="#8a9aa3", bad="#b5382a", good="#2f8f5b", ink="#1d2b32")
mpl.rcParams.update({"figure.dpi": 110, "savefig.dpi": 140, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titleweight": "bold", "axes.titlesize": 12, "axes.labelsize": 10, "axes.edgecolor": "#9aa7ad",
                     "axes.labelcolor": PAL["ink"], "text.color": PAL["ink"], "font.size": 10, "axes.grid": True,
                     "grid.color": "#e6ebee", "grid.linewidth": .8, "axes.axisbelow": True})
sns.set_palette([PAL["primary"], PAL["accent"], PAL["muted"], PAL["good"], PAL["bad"]])
ASSETS.mkdir(exist_ok=True)
def save(fig, name):
    fig.savefig(ASSETS / f"{name}.png", bbox_inches="tight", facecolor="white")

df = pd.read_csv(FINAL / "RuralReach_Master_base.csv")
geo = gpd.read_file(FINAL / "RuralReach_Districts.gpkg").merge(df.drop(columns=["State_name", "District_name"]), on="District_ID")
print(df.shape)

# %% [markdown]
# ## 1 · What is missing, and why?
# Missingness is *informative* here: it follows how each source was collected, so it is **not** filled with zeros.

# %%
miss = df.isna().mean().mul(100)
miss = miss[miss > 0].sort_values()
fig, ax = plt.subplots(figsize=(8, .32 * len(miss) + 1))
ax.barh(miss.index, miss.values, color=PAL["muted"])
for i, v in enumerate(miss.values):
    ax.text(v + .5, i, f"{v:.0f}%", va="center", fontsize=8)
ax.set_xlabel("% of districts missing"); ax.set_title("Missing values by column (only columns with gaps)"); ax.grid(axis="y", visible=False)
save(fig, "eda_missingness"); plt.show()

# %% [markdown]
# * **Mandi_*** (~76 %): the mandi file is a one-day snapshot of 16 states - absence means *not observed*, never "no market".
# * **NREGA_*** (~30 %): present-day districts; 2011 districts without a name match stay empty.
# * **Literacy_Rate_Effective**: a single district (Bangalore Rural) is absent from the reference file.
# * Everything else (Census, geography, railway, state-level context) is complete.

# %% [markdown]
# ## 2 · Distributions of the core indicators

# %%
core = ["Literacy_Rate_Effective", "Sex_Ratio", "Farm_Worker_Share", "Female_Worker_Participation_Rate",
        "Graduate_pct", "Population_Density", "Nearest_Railway_km", "Railway_Station_Count", "Trains_Serving"]
fig, axes = plt.subplots(3, 3, figsize=(12, 8.5))
for ax, c in zip(axes.ravel(), core):
    x = df[c].dropna()
    ax.hist(x, bins=36, color=PAL["primary"], alpha=.85)
    ax.axvline(x.median(), color=PAL["accent"], lw=1.6)
    ax.set_title(f"{c}\nmedian {x.median():.1f} · skew {stats.skew(x):.1f}", fontsize=9.5)
fig.suptitle("Distributions of core district indicators (orange = median)", fontweight="bold", y=1.01)
fig.tight_layout(); save(fig, "eda_distributions"); plt.show()

# %% [markdown]
# Population density, railway distance and the station/train counts are **heavily right-skewed** (a few metros and remote islands),
# so the index in notebook 04 uses log transforms and winsorised scaling rather than raw min-max.

# %%
desc = df[core].describe(percentiles=[.05, .25, .5, .75, .95]).T.round(2)
desc["skew"] = [stats.skew(df[c].dropna()) for c in core]
desc

# %% [markdown]
# ## 3 · Outliers (IQR rule)

# %%
def iqr_out(s):
    q1, q3 = s.quantile([.25, .75]); i = q3 - q1
    return ((s < q1 - 1.5 * i) | (s > q3 + 1.5 * i)).sum()
out = pd.Series({c: iqr_out(df[c].dropna()) for c in core}, name="IQR outliers").to_frame()
out["%"] = (out.iloc[:, 0] / len(df) * 100).round(1)
print(out)
print("\nLargest Nearest_Railway_km (islands / remote):")
print(df.nlargest(6, "Nearest_Railway_km")[["State_name", "District_name", "Nearest_Railway_km"]].to_string(index=False))
print("\nDensest districts:")
print(df.nlargest(5, "Population_Density")[["State_name", "District_name", "Population_Density"]].round(0).to_string(index=False))

# %% [markdown]
# These outliers are **real** (Lakshadweep/Andaman are >1,000 km from the mainland network; Delhi and Mumbai are extremely dense),
# so they are kept and handled by transformation, not deleted.

# %% [markdown]
# ## 4 · Which indicators move together? (Spearman)

# %%
cols = ["Literacy_Rate_Effective", "Graduate_pct", "Secondary_Edu_pct", "Farm_Worker_Share", "Female_Worker_Participation_Rate",
        "Worker_Participation_Rate", "Sex_Ratio", "Young_Pop_pct", "Population_Density", "Nearest_Railway_km", "Stations_per_1000sqkm",
        "Trains_Serving", "StateLvl_PHC_Doctor_Staffing_pct", "StateLvl_Dropout_Secondary"]
cm = df[cols].corr(method="spearman")
fig, ax = plt.subplots(figsize=(9.5, 8))
sns.heatmap(cm, cmap="RdBu_r", center=0, vmin=-1, vmax=1, annot=True, fmt=".2f", annot_kws={"size": 7}, linewidths=.5,
            cbar_kws={"shrink": .7}, ax=ax)
ax.set_title("Spearman correlation – district indicators"); ax.grid(False)
fig.tight_layout(); save(fig, "eda_correlation"); plt.show()

# %%
pairs = cm.where(np.triu(np.ones(cm.shape), 1).astype(bool)).stack().rename("rho").reset_index()
pairs["abs"] = pairs.rho.abs()
pairs.sort_values("abs", ascending=False).head(10).drop(columns="abs").round(2)

# %% [markdown]
# ## 5 · Rurality vs outcomes
# `Farm_Worker_Share` (cultivators + agricultural labourers as a share of all workers) is the rurality proxy,
# because the supplied Census file has no urban/rural split.

# %%
fig, axes = plt.subplots(1, 3, figsize=(14, 4.2))
for ax, (x, y, t) in zip(axes, [("Farm_Worker_Share", "Literacy_Rate_Effective", "Farm dependence vs literacy"),
                                ("Female_Worker_Participation_Rate", "Literacy_Rate_Effective", "Female work participation vs literacy"),
                                ("Farm_Worker_Share", "Nearest_Railway_km", "Farm dependence vs distance to rail")]):
    d = df[[x, y]].dropna()
    ax.scatter(d[x], d[y], s=12, alpha=.45, color=PAL["primary"], edgecolor="none")
    if y == "Nearest_Railway_km":
        ax.set_yscale("log")
    z = np.polyfit(d[x], np.log10(d[y]) if y == "Nearest_Railway_km" else d[y], 1)
    xs = np.linspace(d[x].min(), d[x].max(), 50)
    ax.plot(xs, 10 ** np.polyval(z, xs) if y == "Nearest_Railway_km" else np.polyval(z, xs), color=PAL["accent"], lw=2)
    rho, p = stats.spearmanr(d[x], d[y])
    ax.set_title(f"{t}\nρ = {rho:.2f}", fontsize=10); ax.set_xlabel(x); ax.set_ylabel(y)
fig.tight_layout(); save(fig, "eda_rurality_scatter"); plt.show()

# %% [markdown]
# ## 6 · State view – where are the gaps?

# %%
st = (df.groupby("State_Current").apply(lambda g: pd.Series({
    "districts": len(g), "population_m": g.Population.sum() / 1e6,
    "literacy_eff_median": g.Literacy_Rate_Effective.median(), "farm_share_median": g.Farm_Worker_Share.median(),
    "nearest_rail_km_median": g.Nearest_Railway_km.median(), "pct_districts_no_station": (g.Railway_Station_Count == 0).mean() * 100,
    "female_wpr_median": g.Female_Worker_Participation_Rate.median()})).round(1)).sort_values("literacy_eff_median")
st.to_csv(PROCESSED / "state_summary.csv")
order = df.groupby("State_Current").Literacy_Rate_Effective.median().sort_values().index
big = df.State_Current.value_counts()[lambda s: s >= 5].index
fig, ax = plt.subplots(figsize=(8, 9))
sns.boxplot(data=df[df.State_Current.isin(big)], y="State_Current", x="Literacy_Rate_Effective", order=[o for o in order if o in big],
            color=PAL["primary"], fliersize=2, linewidth=.9, ax=ax)
ax.axvline(df.Literacy_Rate_Effective.median(), color=PAL["accent"], ls="--", lw=1.4)
ax.set_title("Effective literacy rate by state (states with ≥5 districts)\ndashed = national district median"); ax.set_ylabel("")
save(fig, "eda_state_literacy"); plt.show()
st.head(8)

# %% [markdown]
# ### Is the state a bigger driver than local factors?
# Share of variance in each indicator that sits *between* states (η² from one-way ANOVA):

# %%
def eta2(col, log=False):
    d = df[["State_Current", col]].dropna()
    if log:
        d[col] = np.log1p(d[col])
    grand = d[col].mean()
    ssb = d.groupby("State_Current")[col].apply(lambda s: len(s) * (s.mean() - grand) ** 2).sum()
    return ssb / ((d[col] - grand) ** 2).sum()
e = pd.Series({**{c: eta2(c) for c in ["Literacy_Rate_Effective", "Farm_Worker_Share", "Female_Worker_Participation_Rate", "Sex_Ratio", "Graduate_pct"]},
               **{c + " (log)": eta2(c, log=True) for c in ["Nearest_Railway_km", "Stations_per_1000sqkm"]}}).sort_values()
fig, ax = plt.subplots(figsize=(7, 3.4))
ax.barh(e.index, e.values * 100, color=PAL["primary"]); ax.set_xlabel("% of variance between states (η²)")
ax.set_title("How much of each indicator is explained by the state?"); ax.grid(axis="y", visible=False)
save(fig, "eda_state_variance"); plt.show()
(e * 100).round(1)

# %% [markdown]
# For every indicator **roughly half (46-59 %) of the variance lies between states and half within them**.
# A state average therefore hides as much variation as it reveals – district-level measurement is justified for
# social *and* physical-access indicators. (Raw `Nearest_Railway_km` would be dominated by the island groups, so the log is used.)

# %% [markdown]
# ## 7 · Rail access across India

# %%
fig, axes = plt.subplots(1, 2, figsize=(13, 6.2))
geo.plot(column="Literacy_Rate_Effective", cmap="YlGnBu", linewidth=.1, edgecolor="white", legend=True,
         legend_kwds={"shrink": .6, "label": "effective literacy %"}, ax=axes[0], missing_kwds={"color": "#dddddd"})
axes[0].set_title("Effective literacy rate (2011)")
geo.assign(d=np.log10(geo.Nearest_Railway_km.clip(lower=1))).plot(column="d", cmap="YlOrRd", linewidth=.1, edgecolor="white", legend=True,
         legend_kwds={"shrink": .6, "label": "log10 km to nearest station"}, ax=axes[1])
axes[1].set_title("Distance from district centroid to nearest active station")
for a in axes: a.set_axis_off(); a.grid(False)
fig.tight_layout(); save(fig, "eda_maps_literacy_rail"); plt.show()

# %%
far = (df.Nearest_Railway_km > 50)
print(f"Districts whose centroid is >50 km from any active station: {far.sum()} ({far.mean() * 100:.1f}%), home to {df.loc[far, 'Population'].sum() / 1e6:.1f} M people (2011)")
print(f"Districts with no timetabled station inside: {(df.Railway_Station_Count == 0).sum()} ({(df.Railway_Station_Count == 0).mean() * 100:.1f}%)")

# %% [markdown]
# ## 8 · Hypothesis tests
# Non-parametric tests are used because the indicators are skewed.
#
# **H1.** Districts with at least one timetabled railway station have higher literacy than those without.
# **H2.** Literacy is related to female worker participation (two-sided Spearman, bootstrap CI).
# **H3.** Literacy differs across *regions* (Kruskal–Wallis by state).

# %%
has = df.Railway_Station_Count > 0
a, b = df.loc[has, "Literacy_Rate_Effective"].dropna(), df.loc[~has, "Literacy_Rate_Effective"].dropna()
u = stats.mannwhitneyu(a, b, alternative="greater")
cles = u.statistic / (len(a) * len(b))
print(f"H1  median literacy {a.median():.1f} (station) vs {b.median():.1f} (no station) | Mann-Whitney p={u.pvalue:.2g} | P(station > none)={cles:.2f}")
d = df[["Female_Worker_Participation_Rate", "Literacy_Rate_Effective"]].dropna()
rho, p = stats.spearmanr(*d.values.T)
boot = [stats.spearmanr(*d.sample(len(d), replace=True, random_state=i).values.T)[0] for i in range(500)]
print(f"H2  Spearman rho = {rho:.2f} (95% bootstrap CI {np.percentile(boot, 2.5):.2f}..{np.percentile(boot, 97.5):.2f}), p={p:.2g}")
groups = [g.Literacy_Rate_Effective.dropna().values for _, g in df.groupby("State_Current") if len(g) >= 5]
kw = stats.kruskal(*groups)
print(f"H3  Kruskal-Wallis H={kw.statistic:.1f}, p={kw.pvalue:.2g} over {len(groups)} states")

# %% [markdown]
# **Reading.**
# * **H1 is rejected** (p ≈ 0.4, effect ≈ 0.5 = coin-flip): having a timetabled station inside the district is *not* associated with literacy.
#   Rail access and social development are largely independent dimensions – a key reason an *index* needs several pillars rather than one proxy.
# * **H2** has a negative sign: women's *recorded* work participation is highest in poor, farm-dependent districts (farm labour out of necessity),
#   so female participation is **not** used as a positive access indicator in notebook 04.
# * **H3**: literacy differs strongly between states (p ≈ 1e-48).

# %% [markdown]
# ## 9 · NREGA and market coverage (supporting data)

# %%
fig, axes = plt.subplots(1, 2, figsize=(11, 4))
d = df[["Farm_Worker_Share", "NREGA_Avg_Days_per_HH"]].dropna()
axes[0].scatter(d.Farm_Worker_Share, d.NREGA_Avg_Days_per_HH, s=12, alpha=.5, color=PAL["primary"], edgecolor="none")
axes[0].set_xlabel("Farm_Worker_Share"); axes[0].set_ylabel("Avg days of NREGA work per household")
axes[0].set_title(f"NREGA days vs farm dependence (ρ={stats.spearmanr(d.iloc[:,0], d.iloc[:,1])[0]:.2f}, n={len(d)})")
mc = df.groupby("State_Current").Mandi_Count.apply(lambda s: s.notna().mean() * 100).sort_values()
mc = mc[mc > 0]
axes[1].barh(mc.index, mc.values, color=PAL["muted"]); axes[1].set_title("Share of districts covered by mandi snapshot")
axes[1].set_xlabel("% of state's districts"); axes[1].grid(axis="y", visible=False)
fig.tight_layout(); save(fig, "eda_nrega_mandi"); plt.show()

# %% [markdown]
# ## 10 · Take-aways that shape the modelling
# 1. The **Census gives the social base**; **railways give the only district-level physical-access measure** (nearly independent of literacy); health is only state-level.
# 2. Skew → log transforms + winsorised scaling.
# 3. About half of the variance in every indicator is **within** states → district-level scoring is justified.
# 4. NREGA and mandi coverage are partial → supporting evidence, not index components.
