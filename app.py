"""Web server: stateless JSON API over utils/ plus the static frontend in web/.

Nothing is stored server-side: files are parsed in memory and the browser holds the data.
Run: uvicorn app:app
"""
from pathlib import Path
from typing import Literal

import pandas as pd
from fastapi import FastAPI, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, conint, constr

from utils import reports, samples
from utils.assigner import assign
from utils.file_reader import MAX_FILE_BYTES, MAX_ROWS, DataError, detect_column, read_table

WEB = Path(__file__).with_name("web")
Text = constr(max_length=200)
MAX_LECTURERS = 300

app = FastAPI(title="Student–Lecturer Assignment", docs_url=None, redoc_url=None, openapi_url=None)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    if int(request.headers.get("content-length") or 0) > MAX_FILE_BYTES * 3:
        return JSONResponse({"detail": "Request too large."}, status_code=413)
    resp = await call_next(request)
    resp.headers.update({
        "Content-Security-Policy": "default-src 'self'; style-src 'self' https://fonts.googleapis.com; "
                                   "font-src https://fonts.gstatic.com; img-src 'self' data:; "
                                   "frame-ancestors 'none'; base-uri 'none'; form-action 'self'",
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "no-referrer",
        "Cache-Control": "no-store" if request.url.path.startswith("/api/") else "no-cache",
    })
    return resp


def _table_payload(df: pd.DataFrame) -> dict:
    cols = list(df.columns)
    found = {}
    for kind in ("name", "matric", "field", "capacity"):
        found[kind] = detect_column(cols, kind, exclude=[v for v in found.values() if v])
    return {"columns": cols, "rows": df.values.tolist(), "detected": found}


@app.post("/api/read")
async def read_file(file: UploadFile):
    data = await file.read(MAX_FILE_BYTES + 1)
    try:
        return _table_payload(read_table(file.filename or "", data))
    except DataError as e:
        raise HTTPException(422, str(e))


@app.get("/api/sample")
def sample():
    return {"students": _table_payload(samples.sample_students()),
            "lecturers": _table_payload(samples.sample_lecturers())}


@app.get("/api/template/{kind}.{fmt}")
def template(kind: Literal["students", "lecturers"], fmt: Literal["csv", "xlsx", "docx"]):
    mime = {"csv": "text/csv", "xlsx": reports.FORMATS["Excel"][1], "docx": reports.FORMATS["Word"][1]}[fmt]
    return Response(samples.template(kind, fmt), media_type=mime,
                    headers={"Content-Disposition": f'attachment; filename="{kind}_template.{fmt}"'})


class Student(BaseModel):
    name: Text
    matric: Text
    field: Text = ""


class Lecturer(BaseModel):
    name: Text
    field: Text = ""
    capacity: conint(ge=1, le=MAX_ROWS) | None = None


class AssignRequest(BaseModel):
    students: list[Student] = Field(min_length=1, max_length=MAX_ROWS)
    lecturers: list[Lecturer] = Field(min_length=1, max_length=MAX_LECTURERS)
    mode: Literal["smart", "random"] = "smart"
    global_max: conint(ge=1, le=MAX_ROWS) | None = None
    min_score: float = Field(0.0, ge=0, le=1)


@app.post("/api/assign")
def run_assign(req: AssignRequest):
    students = pd.DataFrame([s.model_dump() for s in req.students])
    lecturers = pd.DataFrame([l.model_dump() for l in req.lecturers])
    problems = []
    if students["matric"].duplicated().any():
        problems.append("Duplicate matric numbers: " + ", ".join(students.loc[students["matric"].duplicated(), "matric"].unique()[:5]))
    if lecturers["name"].duplicated().any():
        problems.append("Duplicate lecturer names: " + ", ".join(lecturers.loc[lecturers["name"].duplicated(), "name"].unique()[:5]))
    if problems:
        raise HTTPException(422, " · ".join(problems))
    r = assign(students, lecturers, req.mode, req.global_max, req.min_score)
    t = r["table"]
    return {
        "assignments": t["lecturer"].tolist(),  # index-aligned with the request's students
        "caps": r["caps"],
        "has_fields": r["has_fields"],
        "scores": r["scores"].round(3).values.tolist(),  # student x lecturer, for re-scoring hand edits
    }


class Row(BaseModel):
    name: Text
    matric: Text
    field: Text = ""
    lecturer: Text = ""
    lecturer_field: Text = ""
    score: float | None = None
    match: Text = ""


class ExportRequest(BaseModel):
    rows: list[Row] = Field(min_length=1, max_length=MAX_ROWS)


@app.post("/api/export/{fmt}")
def export(fmt: Literal["Excel", "PDF", "Word", "CSV"], req: ExportRequest):
    table = pd.DataFrame([r.model_dump() for r in req.rows])
    ext, mime = reports.FORMATS[fmt]
    return Response(reports.build(fmt, table), media_type=mime,
                    headers={"Content-Disposition": f'attachment; filename="supervision-list.{ext}"'})


@app.get("/")
def index():
    return FileResponse(WEB / "index.html")


app.mount("/", StaticFiles(directory=WEB), name="web")
