"""The app's operations, called from the browser through Pyodide (see web/app.js).

Everything takes and returns plain JSON-able values or bytes. Heavy modules are imported
inside the functions that need them so the browser can download them on demand.
"""
import pandas as pd

from utils.file_reader import MAX_ROWS, DataError, detect_column, read_table

MAX_LECTURERS = 300
MAX_TEXT = 200


def _table_payload(df: pd.DataFrame) -> dict:
    cols = list(df.columns)
    found = {}
    for kind in ("name", "matric", "field", "capacity"):
        found[kind] = detect_column(cols, kind, exclude=[v for v in found.values() if v])
    return {"columns": cols, "rows": df.values.tolist(), "detected": found}


def read_upload(filename: str, data) -> dict:
    data = data.to_bytes() if hasattr(data, "to_bytes") else bytes(data)  # JS Uint8Array or bytes
    return _table_payload(read_table(str(filename), data))


def sample() -> dict:
    from utils import samples
    return {"students": _table_payload(samples.sample_students()),
            "lecturers": _table_payload(samples.sample_lecturers())}


def template(kind: str, fmt: str) -> bytes:
    from utils import samples
    if kind not in ("students", "lecturers") or fmt not in ("csv", "xlsx", "docx"):
        raise DataError("Unknown template.")
    return samples.template(kind, fmt)


def _text(v) -> str:
    return str(v if v is not None else "").strip()[:MAX_TEXT]


def run_assign(students: list, lecturers: list, mode="smart", global_max=None, min_score=0.0) -> dict:
    from utils.assigner import assign

    if not 1 <= len(students) <= MAX_ROWS or not 1 <= len(lecturers) <= MAX_LECTURERS:
        raise DataError(f"Need 1–{MAX_ROWS} students and 1–{MAX_LECTURERS} lecturers.")
    s = pd.DataFrame({"name": [_text(x.get("name")) for x in students],
                      "matric": [_text(x.get("matric")) for x in students],
                      "field": [_text(x.get("field")) for x in students]})
    caps = [x.get("capacity") for x in lecturers]
    l = pd.DataFrame({"name": [_text(x.get("name")) for x in lecturers],
                      "field": [_text(x.get("field")) for x in lecturers],
                      "capacity": [int(c) if c and int(c) > 0 else None for c in caps]})
    for df, col, what in ((s, "matric", "matric numbers"), (l, "name", "lecturer names")):
        dups = df.loc[df[col].duplicated(), col].unique()
        if len(dups):
            raise DataError(f"Duplicate {what}: {', '.join(dups[:5])}")
    r = assign(s, l, "random" if mode == "random" else "smart",
               int(global_max) if global_max else None, min(max(float(min_score or 0), 0.0), 1.0))
    return {
        "assignments": r["table"]["lecturer"].tolist(),  # index-aligned with `students`
        "caps": r["caps"],
        "has_fields": r["has_fields"],
        "scores": r["scores"].round(3).values.tolist(),  # student x lecturer, for re-scoring hand edits
    }


def export(fmt: str, rows: list) -> bytes:
    from utils import reports
    if fmt not in reports.FORMATS or not 1 <= len(rows) <= MAX_ROWS:
        raise DataError("Nothing to export.")
    keys = ("name", "matric", "field", "lecturer", "lecturer_field", "match")
    table = pd.DataFrame([{**{k: _text(r.get(k)) for k in keys}, "score": r.get("score")} for r in rows])
    return reports.build(fmt, table)
