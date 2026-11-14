import pytest

from utils import service
from utils.file_reader import DataError
from utils.samples import template


def _people():
    s = service.sample()
    st, lt = s["students"], s["lecturers"]
    c = {k: st["columns"].index(v) for k, v in st["detected"].items() if v}
    students = [{"name": r[c["name"]], "matric": r[c["matric"]], "field": r[c["field"]]} for r in st["rows"]]
    c = {k: lt["columns"].index(v) for k, v in lt["detected"].items() if v}
    lecturers = [{"name": r[c["name"]], "field": r[c["field"]],
                  "capacity": int(r[c["capacity"]]) if r[c["capacity"]] else None} for r in lt["rows"]]
    return students, lecturers


def test_read_upload_detects_columns():
    out = service.read_upload("s.xlsx", memoryview(template("students", "xlsx")))
    assert out["detected"]["matric"] == "Matric Number" and len(out["rows"]) == 3


def test_read_upload_rejects_bad_file():
    with pytest.raises(DataError, match="corrupted"):
        service.read_upload("s.docx", b"nope")


def test_assign_and_export_round_trip():
    students, lecturers = _people()
    body = service.run_assign(students, lecturers)
    assert len(body["assignments"]) == len(students) and all(body["assignments"])
    assert len(body["scores"]) == len(students) and len(body["scores"][0]) == len(lecturers)
    rows = [dict(s, lecturer=a, score=None) for s, a in zip(students, body["assignments"])]
    for fmt in ("Excel", "PDF", "Word", "CSV"):
        assert len(service.export(fmt, rows)) > 100


def test_assign_validates_input():
    students, lecturers = _people()
    with pytest.raises(DataError, match="Duplicate matric"):
        service.run_assign(students + students[:1], lecturers)
    with pytest.raises(DataError):
        service.run_assign([], lecturers)
    long = service.run_assign([{"name": "x" * 500, "matric": "1"}], lecturers)
    assert len(long["assignments"]) == 1


def test_templates_and_sample_names_unique():
    assert service.template("lecturers", "docx")[:2] == b"PK"
    names = [r[0] for r in service.sample()["students"]["rows"]]
    assert len(names) == len(set(names))
