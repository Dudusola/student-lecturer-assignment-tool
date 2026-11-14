# Student–Lecturer Assignment Tool

A web app that turns a student list and a lecturer list into a fair, field-matched supervision list,
set like a published allocation list: **drop two files → publish → fix anything circled → export.**

**Live:** https://supervision-list.pages.dev — everything runs in your browser (Python via Pyodide),
so no file is ever uploaded. The first visit downloads about 20 MB of Python libraries; later visits use the cache.

## Features

- **Any common file:** CSV (comma, semicolon or tab), Excel `.xlsx`, or Word `.docx` (first table).
- **Automatic column detection:** *Name / Full name*, *Matric / Reg No / Student ID*,
  *Field / Department / Specialization*, *Max_Students / Capacity* are recognised; you can override them.
- **Smart match (ML):** each student's field is scored against each lecturer's specializations using
  character n-gram TF-IDF vectors (numpy) with acronym expansion, so `AI` ↔ *Artificial Intelligence*,
  `HCI` ↔ *Human-Computer Interaction* and typos like *Machine learnig* still match. The Hungarian algorithm
  then finds the best overall assignment while keeping workloads even and respecting every limit.
- **Random (balanced):** even random split when fields don't matter.
- **Limits:** per-lecturer `Max_Students` from the file, a global maximum, or an automatic even split.
  Optional *minimum match* leaves a student unassigned rather than give a poor match.
- **Review & edit:** every lecturer is a column with an exact load bar; weak matches are circled, partial ones
  underlined. Click a name to move that student (choices ranked by match, with each lecturer's load); click a
  lecturer to focus their column; search by name or matric number.
- **Exports:** Excel (with workload sheet), PDF and Word (grouped by lecturer), CSV, or print the page directly.
- **Try it instantly:** built-in sample data and downloadable templates.

## Run locally

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt   # macOS/Linux: .venv/bin/pip
.venv/Scripts/python build.py                   # writes the static site to dist/
.venv/Scripts/python -m http.server -d dist 8000
```

Then open http://localhost:8000.

## Deploy (Cloudflare Pages, free)

```bash
python build.py
wrangler pages deploy dist --project-name supervision-list --branch main
```

`dist/` is plain static files: `web/`, our `utils/` code zipped for Pyodide, and four pure-Python wheels
Pyodide doesn't ship (openpyxl, et-xmlfile, python-docx, reportlab). Pyodide itself and numpy, pandas,
scipy and lxml come from the jsDelivr Pyodide CDN. Security headers live in `web/_headers`.

Tests: `.venv/Scripts/python -m pytest -q`

## Security

- Uploads are limited to 5 MB and 2,000 rows; Excel/Word files are checked for zip bombs before parsing.
- Files never leave the user's computer: parsing, matching and exports all run in the browser.
- Exported CSV/Excel cells that start with `= + - @` are escaped to block spreadsheet formula injection.
- User data is never rendered as HTML; PDF text is escaped.
- Strict Content-Security-Policy (scripts only from this site and the pinned Pyodide CDN, no inline
  scripts), `nosniff`, no referrer, no framing (`web/_headers`).

## Project layout

```
build.py               builds dist/ for Cloudflare Pages
web/                   frontend (index.html, styles.css, tokens.css, app.js, _headers)
utils/service.py       the operations the page calls through Pyodide
utils/file_reader.py   safe file parsing + column detection
utils/matcher.py       field similarity (TF-IDF + acronym expansion)
utils/assigner.py      optimal assignment with capacities
utils/reports.py       Excel / PDF / Word / CSV export
utils/samples.py       sample data and templates
tests/                 pytest suite
```
