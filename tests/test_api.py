from fastapi.testclient import TestClient

from app import app
from utils.samples import template

client = TestClient(app)


def _people():
    s = client.get("/api/sample").json()
    st, lt = s["students"], s["lecturers"]
    c = {k: st["columns"].index(v) for k, v in st["detected"].items() if v}
    students = [{"name": r[c["name"]], "matric": r[c["matric"]], "field": r[c["field"]]} for r in st["rows"]]
    c = {k: lt["columns"].index(v) for k, v in lt["detected"].items() if v}
    lecturers = [{"name": r[c["name"]], "field": r[c["field"]],
                  "capacity": int(r[c["capacity"]]) if r[c["capacity"]] else None} for r in lt["rows"]]
    return students, lecturers


def test_read_upload_detects_columns():
    r = client.post("/api/read", files={"file": ("s.xlsx", template("students", "xlsx"))})
    assert r.status_code == 200
    assert r.json()["detected"]["matric"] == "Matric Number"


def test_read_rejects_bad_file():
    r = client.post("/api/read", files={"file": ("s.docx", b"nope")})
    assert r.status_code == 422 and "corrupted" in r.json()["detail"]


def test_assign_and_export_round_trip():
    students, lecturers = _people()
    r = client.post("/api/assign", json={"students": students, "lecturers": lecturers})
    assert r.status_code == 200
    body = r.json()
    assert len(body["assignments"]) == len(students) and all(body["assignments"])
    assert len(body["scores"]) == len(students) and len(body["scores"][0]) == len(lecturers)
    rows = [dict(s, lecturer=a) for s, a in zip(students, body["assignments"])]
    for fmt in ("Excel", "PDF", "Word", "CSV"):
        e = client.post(f"/api/export/{fmt}", json={"rows": rows})
        assert e.status_code == 200 and len(e.content) > 100


def test_assign_validates_input():
    students, lecturers = _people()
    dup = students + students[:1]
    assert client.post("/api/assign", json={"students": dup, "lecturers": lecturers}).status_code == 422
    long = [{"name": "x" * 500, "matric": "1"}]
    assert client.post("/api/assign", json={"students": long, "lecturers": lecturers}).status_code == 422


def test_security_headers_and_no_docs():
    r = client.get("/api/sample")
    assert "default-src 'self'" in r.headers["content-security-policy"]
    assert client.get("/docs").status_code == 404
