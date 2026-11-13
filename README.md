# Student–Lecturer Assignment Tool

A Streamlit app that assigns students to lecturers (supervisors) fairly and by field, in three steps:
**add your lists → choose a method → review, adjust and export.**

## Features

- **Any common file:** CSV (comma, semicolon or tab), Excel `.xlsx`, or Word `.docx` (first table).
- **Automatic column detection:** *Name / Full name*, *Matric / Reg No / Student ID*,
  *Field / Department / Specialization*, *Max_Students / Capacity* are recognised; you can override them.
- **Smart match (ML):** each student's field is scored against each lecturer's specializations using
  character n-gram TF-IDF embeddings with acronym expansion, so `AI` ↔ *Artificial Intelligence*,
  `HCI` ↔ *Human-Computer Interaction* and typos like *Machine learnig* still match. The Hungarian algorithm
  then finds the best overall assignment while keeping workloads even and respecting every limit.
- **Random (balanced):** even random split when fields don't matter.
- **Limits:** per-lecturer `Max_Students` from the file, a global maximum, or an automatic even split.
  Optional *minimum match* leaves a student unassigned rather than give a poor match.
- **Review & edit:** every student gets a match score (Strong / Partial / Weak); weak and unassigned rows are
  listed first, and you can change any lecturer from a dropdown. Scores, workload and exports update instantly.
- **Exports:** Excel (with workload sheet), PDF and Word (grouped by lecturer), CSV.
- **Try it instantly:** built-in sample data and downloadable templates.

## Run locally

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt   # macOS/Linux: .venv/bin/pip
.venv/Scripts/streamlit run assignment.py
```

Tests: `.venv/Scripts/python -m pytest -q`

## Security

- Uploads are limited to 5 MB and 2,000 rows; Excel/Word files are checked for zip bombs before parsing.
- Data is processed in memory for the session only; nothing is written to disk.
- Exported CSV/Excel cells that start with `= + - @` are escaped to block spreadsheet formula injection.
- User data is never rendered as HTML; PDF text is escaped.
- XSRF protection on, stack traces hidden from users, usage telemetry off (`.streamlit/config.toml`).

## Project layout

```
assignment.py          Streamlit UI
utils/file_reader.py   safe file parsing + column detection
utils/matcher.py       field similarity (TF-IDF + acronym expansion)
utils/assigner.py      optimal assignment with capacities
utils/reports.py       Excel / PDF / Word / CSV export
utils/samples.py       sample data and templates
tests/                 pytest suite
```
