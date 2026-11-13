# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Custom web frontend (hand-built HTML/CSS/JS) served by a small Python FastAPI backend that reuses the existing `utils/` matching, parsing and export modules. Chosen by the user 2026-11-13, replacing the Streamlit UI. Deploy target moves off Streamlit Community Cloud; host not yet decided.

## Users

Primary: department coordinators assigning final-year project supervisors, once or twice a year, usually under time pressure, and not technical. (Inferred and recommended; the user asked for the best option.) Secondary: lecturers and students who only see the results and exported lists, so the output must make sense without the tool.

## Product Purpose

Turn two lists (students, lecturers) into a fair, field-matched supervision list that a coordinator can review, adjust and export in minutes. Success: every student assigned to a fitting supervisor, workloads within limits, and an export ready to circulate.

## Positioning

It reads messy, real-world field text (abbreviations, typos, different wording, multi-topic specializations) and finds the best overall assignment under per-lecturer limits, then shows how good each match is and lets a person override it. Most tools either split students randomly or require exact department matches.

## Operating Context

Inputs are spreadsheets or Word tables exported from department records (CSV, XLSX, DOCX). Outputs are circulated as Excel, PDF, Word or CSV, often printed or posted. Typical size is tens to a few hundred students and a handful to a few dozen lecturers; the hard limit is 2,000 rows per file.

## Capabilities and Constraints

- Upload validation: 5 MB, 2,000 rows, zip-bomb check; files processed in memory only, never stored.
- Column auto-detection with manual override.
- Smart match (TF-IDF char n-gram similarity, acronym expansion, Hungarian assignment with balanced load) and balanced random mode.
- Limits: per-lecturer `Max_Students`, a global maximum, or an even split; optional minimum match.
- Per-student match score and label (Strong ≥ 75%, Partial ≥ 40%, Weak), manual reassignment, workload view.
- Exports: Excel (with workload sheet), PDF, Word, CSV; spreadsheet formula injection escaped.

## Brand Commitments

Name: Student–Lecturer Assignment Tool. Existing logo (`logo.png`, navy graduate-cap pictogram with wordmark) and `favicon.ico`. Tone chosen by the user: academic editorial.

## Evidence on Hand

Built-in synthetic sample data (40 students, 6 lecturers, Nigerian names, computing fields) in `utils/samples.py`. No real usage numbers, institutions, or testimonials exist; do not invent any.

## Product Principles

1. The coordinator's time matters most: from upload to export in a few clicks.
2. Show the reasoning: every match carries a visible score, and weak ones surface first.
3. A person has the final say: any assignment can be changed by hand.
4. Student data is handled with care: in memory only, validated at the door.

## Accessibility & Inclusion

Non-technical staff on ordinary office laptops and sometimes phones; WCAG AA contrast and full keyboard operation expected.
