"""Assign students to lecturers.

Both modes solve one optimal assignment (Hungarian algorithm) over lecturer "slots":
  - smart:  maximise total field similarity (see utils.matcher), workloads kept even
  - random: random preferences, workloads kept even
Each extra slot a lecturer fills costs a little, so ties spread students evenly.
"""
import math

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment

from utils.matcher import similarity_matrix

STRONG, PARTIAL = 0.75, 0.40
_BLOCKED = 1e6


def match_label(score, has_fields: bool) -> str:
    if not has_fields or pd.isna(score):
        return "No field data"
    return "Strong" if score >= STRONG else "Partial" if score >= PARTIAL else "Weak"


def capacities(lecturers: pd.DataFrame, n_students: int, global_max=None) -> list[int]:
    """Per-lecturer limit: own value from the file, else the global max, else an even share."""
    fair = math.ceil(n_students / max(len(lecturers), 1))
    default = global_max or fair
    return [int(c) if pd.notna(c) and c else default for c in lecturers["capacity"]]


def assign(students: pd.DataFrame, lecturers: pd.DataFrame, mode="smart",
           global_max=None, min_score=0.0, seed=None) -> dict:
    """
    students:  columns name, matric, field
    lecturers: columns name, field, capacity (int or None)
    Returns {"table": one row per student, "scores": student x lecturer DataFrame, "caps": {lecturer: cap}}.
    """
    n, m = len(students), len(lecturers)
    if n == 0 or m == 0:
        raise ValueError("Need at least one student and one lecturer.")
    rng = np.random.default_rng(seed)
    caps = capacities(lecturers, n, global_max)
    has_fields = bool((students["field"] != "").any() and (lecturers["field"] != "").any())
    scores = similarity_matrix(students["field"], lecturers["field"]) if has_fields else np.zeros((n, m))

    # shortcut: slots per lecturer capped at 3x the even share to bound matrix size;
    # only matters if one lecturer should take >3x their share. Use min-cost flow if that bites.
    slot_cap = min(n, 3 * math.ceil(n / m) + 1)
    slot_owner = np.repeat(np.arange(m), [min(c, slot_cap) for c in caps])
    slot_rank = np.concatenate([np.arange(min(c, slot_cap)) for c in caps])

    pref = scores if mode == "smart" else np.zeros((n, m))
    noise = rng.random((n, m)) * 1e-6  # random tie-breaks; this is all "random" mode uses
    load_penalty = 0.01 * slot_rank / max(slot_rank.max(initial=0), 1)
    cost = -(pref + noise)[:, slot_owner] + load_penalty
    if mode == "smart" and has_fields and min_score > 0:
        cost[scores[:, slot_owner] < min_score] = _BLOCKED

    rows, cols = linear_sum_assignment(cost)
    chosen = {r: slot_owner[c] for r, c in zip(rows, cols) if cost[r, c] < _BLOCKED}

    lect_names = lecturers["name"].tolist()
    table = students[["name", "matric", "field"]].copy().reset_index(drop=True)
    table["lecturer"] = [lect_names[chosen[i]] if i in chosen else "" for i in range(n)]
    lect_fields = dict(zip(lecturers["name"], lecturers["field"]))
    table["lecturer_field"] = table["lecturer"].map(lect_fields).fillna("")
    table["score"] = [scores[i, chosen[i]] if i in chosen and has_fields else np.nan for i in range(n)]
    table["match"] = [match_label(s, has_fields) if lec else "Unassigned"
                      for s, lec in zip(table["score"], table["lecturer"])]

    score_df = pd.DataFrame(scores, index=table["matric"], columns=lect_names)
    return {"table": table, "scores": score_df, "caps": dict(zip(lect_names, caps)),
            "lecturer_fields": lect_fields, "has_fields": has_fields}


def rescore(table: pd.DataFrame, result: dict) -> pd.DataFrame:
    """Refresh lecturer field / score / match after manual edits to the lecturer column."""
    scores, has_fields = result["scores"], result["has_fields"]
    t = table.copy()
    t["lecturer"] = t["lecturer"].fillna("")
    t["lecturer_field"] = t["lecturer"].map(result["lecturer_fields"]).fillna("")
    known = t["lecturer"].isin(scores.columns)
    t["score"] = [scores.at[mat, lec] if ok and has_fields else np.nan
                  for mat, lec, ok in zip(t["matric"], t["lecturer"], known)]
    t["match"] = [match_label(s, has_fields) if lec else "Unassigned"
                  for s, lec in zip(t["score"], t["lecturer"])]
    return t
