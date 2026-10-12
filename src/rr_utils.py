"""Shared helpers for the RuralReach pipeline: path constants, name cleaning,
state canonicalisation and a conservative fuzzy district matcher."""
from __future__ import annotations

import difflib
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw"
EXTRACTED = ROOT / "extracted"
PROCESSED = ROOT / "processed"
FINAL = ROOT / "final"
DOCS = ROOT / "docs"
ASSETS = ROOT / "assets"

# ---------------------------------------------------------------- states
# Every spelling seen in the 9 sources -> one canonical (2011-Census style) label.
STATE_CANON = {
    "ANDAMAN AND NICOBAR": "ANDAMAN AND NICOBAR ISLANDS",
    "ANDAMAN AND NICOBAR ISLANDS": "ANDAMAN AND NICOBAR ISLANDS",
    "A AND N ISLANDS": "ANDAMAN AND NICOBAR ISLANDS",
    "A AND N ISLAND": "ANDAMAN AND NICOBAR ISLANDS",
    "ORISSA": "ODISHA",
    "PONDICHERRY": "PUDUCHERRY",
    "UTTARANCHAL": "UTTARAKHAND",
    "UTTRAKHAND": "UTTARAKHAND",
    "CHHATISGARH": "CHHATTISGARH",
    "NCT OF DELHI": "DELHI",
    "DADRA AND NAGAR HAVELI": "DADRA AND NAGAR HAVELI",
}
# States that did not exist (or were part of another unit) in the 2011 Census.
# For *district matching* against the 2011 Census they are folded into the parent.
MATCH_STATE = {"TELANGANA": "ANDHRA PRADESH", "LADAKH": "JAMMU AND KASHMIR"}


def canon_state(s) -> str:
    if pd.isna(s):
        return np.nan
    t = re.sub(r"\s+", " ", str(s).replace("&", " AND ")).strip().upper()
    t = re.sub(r"\s+", " ", t)
    return STATE_CANON.get(t, t)


def match_state(s) -> str:
    c = canon_state(s)
    return MATCH_STATE.get(c, c)


# -------------------------------------------------------------- districts
_DROP_WORDS = r"\b(DISTRICT|DIST|DISTT|URBAN|RURAL|CITY)\b"


def clean_text(s) -> str:
    """Trim, collapse whitespace, upper-case."""
    if pd.isna(s):
        return ""
    return re.sub(r"\s+", " ", str(s)).strip().upper()


def district_key(s) -> str:
    """Aggressive key: upper, drop bracketed text & generic words, letters only."""
    t = clean_text(s)
    t = t.replace("(METRO)", " METROPOLITAN")
    t = re.sub(r"\(.*?\)", "", t)
    t = t.replace("&", " AND ")
    t = re.sub(_DROP_WORDS, "", t)
    return re.sub(r"[^A-Z]", "", t)


def _ratio(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()


def fuzzy_match(
    left: pd.DataFrame,
    right: pd.DataFrame,
    left_cols=("match_state", "dkey"),
    right_cols=("match_state", "dkey"),
    threshold: float = 0.86,
    alias: dict | None = None,
    dedupe: bool = True,
) -> pd.DataFrame:
    """Map each row of `right` to at most one row of `left` (the Census master).

    Order of evidence: (1) manual alias, (2) exact key inside the same state,
    (3) fuzzy key inside the same state if the best score >= threshold and it
    beats the runner-up by >= 0.03.  Returns right-index -> left-index with the
    method used.  Nothing is matched across states.
    """
    alias = alias or {}
    lstate, lkey = left_cols
    rstate, rkey = right_cols
    by_state = {s: g for s, g in left.groupby(lstate)}
    rows = []
    for ridx, r in right.iterrows():
        cand = by_state.get(r[rstate])
        out = dict(r_index=ridx, l_index=None, method="unmatched", score=np.nan)
        if cand is not None and len(cand):
            akey = alias.get((r[rstate], r[rkey]))
            if akey is not None:
                hit = cand[cand[lkey] == akey]
                if len(hit):
                    out.update(l_index=hit.index[0], method="alias", score=1.0)
            if out["l_index"] is None:
                hit = cand[cand[lkey] == r[rkey]]
                if len(hit) == 1:
                    out.update(l_index=hit.index[0], method="exact", score=1.0)
            if out["l_index"] is None and r[rkey]:
                sc = cand[lkey].map(lambda k: _ratio(k, r[rkey])).sort_values(ascending=False)
                if len(sc) and sc.iloc[0] >= threshold and (len(sc) == 1 or sc.iloc[0] - sc.iloc[1] >= 0.03):
                    out.update(l_index=sc.index[0], method="fuzzy", score=round(float(sc.iloc[0]), 3))
        rows.append(out)
    res = pd.DataFrame(rows).set_index("r_index")
    if not dedupe:
        return res
    # One source row per Census district: if several rows point at the same
    # district keep the strongest evidence (alias/exact > fuzzy, then score).
    rank = res.method.map({"alias": 0, "exact": 0, "fuzzy": 1}).fillna(9)
    order = pd.DataFrame({"l": res.l_index, "rk": rank, "sc": -res.score.fillna(0)}).dropna(subset=["l"])
    order = order.sort_values(["l", "rk", "sc"])
    losers = order[order.duplicated("l", keep="first")].index
    res.loc[losers, "method"] = "duplicate_target_dropped"
    res.loc[losers, "l_index"] = None
    return res


def haversine_km(lat1, lon1, lat2, lon2):
    """Vectorised great-circle distance in km."""
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 6371.0088 * 2 * np.arcsin(np.sqrt(a))
