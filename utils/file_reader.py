"""Safe loading of uploaded CSV / Excel / Word tables and column auto-detection."""
import io
import re
import zipfile

import docx
import pandas as pd

MAX_FILE_BYTES = 5 * 1024 * 1024        # matches server.maxUploadSize in .streamlit/config.toml
MAX_UNZIPPED_BYTES = 50 * 1024 * 1024   # xlsx/docx are zip files: refuse zip bombs
MAX_ROWS = 2000
MAX_COLS = 50
MAX_CELL_CHARS = 200

# Canonical field -> header names we recognise (compared after normalising case/punctuation).
SYNONYMS = {
    "name": ["name", "names", "full name", "student name", "student", "lecturer name", "lecturer",
             "supervisor", "supervisor name", "staff name", "staff"],
    "matric": ["matric number", "matric no", "matric", "matriculation number", "reg no",
               "registration number", "reg number", "student id", "id", "id number"],
    "field": ["field", "department", "dept", "specialization", "specialisation", "area",
              "research area", "research interest", "interest", "interests", "topic", "discipline"],
    "capacity": ["max students", "max_students", "capacity", "limit", "quota", "max", "slots"],
}


class DataError(ValueError):
    """A problem with the user's file that we can explain to them."""


def _norm(text) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(text).lower()).strip()


def read_table(filename: str, data: bytes) -> pd.DataFrame:
    """Parse an uploaded file into a DataFrame of trimmed strings."""
    if len(data) > MAX_FILE_BYTES:
        raise DataError(f"File is larger than {MAX_FILE_BYTES // 1024 // 1024} MB.")
    ext = filename.lower().rsplit(".", 1)[-1]
    if ext in ("xlsx", "docx"):
        _check_zip(data)

    try:
        if ext == "csv":
            df = _read_csv(data)
        elif ext == "xlsx":
            df = pd.read_excel(io.BytesIO(data), dtype=str, keep_default_na=False, engine="openpyxl")
        elif ext == "docx":
            df = _read_docx(data)
        else:
            raise DataError("Unsupported file type. Use CSV, Excel (.xlsx) or Word (.docx).")
    except DataError:
        raise
    except Exception as e:  # parser errors: give a plain message, not a stack trace
        raise DataError(f"Couldn't read this file. Is it a valid .{ext}? ({type(e).__name__})") from e

    df = df.iloc[:, :MAX_COLS]
    df.columns = [str(c).strip() or f"Column {i + 1}" for i, c in enumerate(df.columns)]
    df = df.loc[:, ~df.columns.duplicated()]
    df = df.fillna("").astype(str).apply(lambda s: s.str.strip().str.slice(0, MAX_CELL_CHARS))
    df = df[(df != "").any(axis=1)].reset_index(drop=True)
    if df.empty:
        raise DataError("The file has no data rows.")
    if len(df) > MAX_ROWS:
        raise DataError(f"Too many rows ({len(df)}). The limit is {MAX_ROWS}.")
    return df


def _check_zip(data: bytes):
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            if sum(i.file_size for i in z.infolist()) > MAX_UNZIPPED_BYTES:
                raise DataError("File expands to an unsafe size and was rejected.")
    except zipfile.BadZipFile as e:
        raise DataError("File is corrupted or not a real Office document.") from e


def _read_csv(data: bytes) -> pd.DataFrame:
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = data.decode("latin-1")
    # sep=None sniffs comma / semicolon / tab
    return pd.read_csv(io.StringIO(text), sep=None, engine="python", dtype=str, keep_default_na=False)


def _read_docx(data: bytes) -> pd.DataFrame:
    doc = docx.Document(io.BytesIO(data))
    if not doc.tables:
        raise DataError("The Word document has no table. Put your data in a table with a header row.")
    rows = [[c.text.strip() for c in r.cells] for r in doc.tables[0].rows]
    if len(rows) < 2:
        raise DataError("The Word table needs a header row and at least one data row.")
    return pd.DataFrame(rows[1:], columns=rows[0])


def detect_column(columns, kind: str, exclude=()):
    """Best header in `columns` for canonical `kind`, or None."""
    candidates = [c for c in columns if c not in exclude]
    normed = {c: _norm(c) for c in candidates}
    for syn in SYNONYMS[kind]:  # exact match, in priority order
        for c, n in normed.items():
            if n == _norm(syn):
                return c
    for syn in SYNONYMS[kind]:  # header contains a synonym, e.g. "Student Full Name"
        for c, n in normed.items():
            if re.search(rf"\b{re.escape(_norm(syn))}\b", n):
                return c
    return None


def parse_capacity(value):
    """Lecturer limit from a cell: positive int, or None if blank/invalid."""
    try:
        n = int(float(str(value).strip()))
    except ValueError:
        return None
    return n if n > 0 else None
