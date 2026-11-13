import io
import zipfile

import openpyxl
import pandas as pd
import pytest

from utils.assigner import assign, rescore
from utils.file_reader import DataError, detect_column, read_table
from utils.matcher import similarity_matrix
from utils.reports import FORMATS, build
from utils.samples import sample_lecturers, sample_students, template


def frames(n=40):
    s, lec = sample_students(n), sample_lecturers()
    students = pd.DataFrame({"name": s["Name"], "matric": s["Matric Number"], "field": s["Field"]})
    lecturers = pd.DataFrame({"name": lec["Name"], "field": lec["Specialization"],
                              "capacity": [int(x) if x else None for x in lec["Max_Students"]]})
    return students, lecturers


def test_matcher_handles_acronyms_typos_and_lists():
    m = similarity_matrix(["AI", "Machine learnig", "HCI"],
                          ["Artificial Intelligence, Machine Learning", "Human-Computer Interaction"])
    assert m[0, 0] == pytest.approx(1.0) and m[2, 1] == pytest.approx(1.0)
    assert m[1, 0] > 0.75 and m[0, 1] < 0.3


def test_smart_assignment_respects_capacity_and_matches_fields():
    students, lecturers = frames()
    r = assign(students, lecturers, "smart", seed=0)
    loads = r["table"]["lecturer"].value_counts()
    assert all(loads[k] <= v for k, v in r["caps"].items() if k in loads)
    assert (r["table"]["lecturer"] != "").all()
    ai = r["table"][r["table"]["field"] == "AI"]
    assert set(ai["lecturer"]) == {"Dr. Grace Adebayo"}


def test_random_assignment_is_balanced():
    students, lecturers = frames(30)
    lecturers["capacity"] = None
    loads = assign(students, lecturers, "random", seed=3)["table"]["lecturer"].value_counts()
    assert loads.max() - loads.min() <= 1


def test_overflow_and_min_score_leave_students_unassigned():
    students, lecturers = frames(10)
    lecturers["capacity"] = 1
    t = assign(students, lecturers, "smart")["table"]
    assert (t["match"] == "Unassigned").sum() == 4
    t = assign(students, lecturers.assign(capacity=None), "smart", min_score=0.99)["table"]
    assert (t.loc[t["lecturer"] != "", "score"] >= 0.99).all()


def test_rescore_after_manual_edit():
    students, lecturers = frames(5)
    r = assign(students, lecturers, "smart")
    t = r["table"].copy()
    t.loc[0, "lecturer"] = "Dr. Linda Okeke"
    t = rescore(t, r)
    assert t.loc[0, "lecturer_field"] == "Software Engineering"
    assert t.loc[0, "score"] == r["scores"].at[t.loc[0, "matric"], "Dr. Linda Okeke"]


@pytest.mark.parametrize("fmt", ["csv", "xlsx", "docx"])
def test_templates_round_trip(fmt):
    df = read_table(f"t.{fmt}", template("students", fmt))
    assert detect_column(df.columns, "matric") == "Matric Number" and len(df) == 3


def test_reader_rejects_zip_bomb_and_garbage():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("x", b"0" * 60_000_000)
    with pytest.raises(DataError):
        read_table("big.xlsx", buf.getvalue())
    with pytest.raises(DataError):
        read_table("fake.docx", b"not a zip")


def test_reports_build_and_neutralise_formulas():
    students, lecturers = frames(8)
    students.loc[0, "name"] = '=HYPERLINK("http://evil","x")'
    t = assign(students, lecturers, "smart")["table"]
    for fmt in FORMATS:
        assert len(build(fmt, t)) > 100
    assert "'=HYPERLINK" in build("CSV", t).decode("utf-8-sig")
    ws = openpyxl.load_workbook(io.BytesIO(build("Excel", t)))["Assignments"]
    assert all(c.data_type != "f" for row in ws.iter_rows() for c in row)
