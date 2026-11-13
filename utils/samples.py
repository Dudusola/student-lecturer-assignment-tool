"""Demo data and downloadable templates."""
import io

import pandas as pd
from docx import Document

_FIRST = ["Ada", "Tunde", "Chioma", "Emeka", "Fatima", "Kemi", "Ibrahim", "Ngozi", "Seun", "Amaka",
          "Bola", "Yusuf", "Zainab", "Obinna", "Halima", "Femi", "Aisha", "Chidi", "Tola", "Musa"]
_LAST = ["Okafor", "Adeyemi", "Bello", "Eze", "Lawal", "Nwosu", "Balogun", "Okoro", "Sani", "Ojo"]
# Deliberately messy: abbreviations, typos and different wording, to show the smart matcher.
_FIELDS = ["Artificial Intelligence", "AI", "Machine Learning", "Cyber Security", "Cybersecurity",
           "Computer Networks", "Networking", "Software Engineering", "Software Eng.",
           "Data Science", "Data Analytics", "Machine learnig", "Human Computer Interaction", "HCI"]


def sample_students(n=40) -> pd.DataFrame:
    return pd.DataFrame({
        "Name": [f"{_FIRST[i % 20]} {_LAST[(i * 7) % 10]}" for i in range(n)],
        "Matric Number": [f"CSC/{21000 + i * 37}" for i in range(n)],
        "Field": [_FIELDS[(i * 5) % len(_FIELDS)] for i in range(n)],
    })


def sample_lecturers() -> pd.DataFrame:
    return pd.DataFrame({
        "Name": ["Dr. Grace Adebayo", "Prof. Ahmed Musa", "Dr. Linda Okeke", "Dr. Paul Ibe",
                 "Dr. Sarah Danjuma", "Prof. Kunle Ade"],
        "Specialization": ["Artificial Intelligence, Machine Learning", "Cybersecurity; Computer Networks",
                           "Software Engineering", "Data Science / Analytics",
                           "Human-Computer Interaction", "Machine Learning, Data Science"],
        "Max_Students": ["10", "12", "8", "", "6", "8"],
    })


def template(kind: str, fmt: str) -> bytes:
    df = sample_students(3) if kind == "students" else sample_lecturers().head(3)
    if fmt == "csv":
        return df.to_csv(index=False).encode("utf-8-sig")
    buf = io.BytesIO()
    if fmt == "xlsx":
        df.to_excel(buf, index=False, sheet_name=kind.title())
    else:
        doc = Document()
        doc.add_heading(f"{kind.title()} template", level=1)
        t = doc.add_table(rows=1, cols=len(df.columns))
        t.style = "Table Grid"
        for c, col in enumerate(df.columns):
            t.rows[0].cells[c].text = col
        for row in df.itertuples(index=False):
            for c, v in enumerate(t.add_row().cells):
                v.text = str(row[c])
        doc.save(buf)
    return buf.getvalue()
