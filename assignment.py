from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Student–Lecturer Assignment", page_icon=str(Path(__file__).with_name("favicon.ico")),
                   layout="wide")

import pandas as pd  # noqa: E402

from utils import reports, samples  # noqa: E402
from utils.assigner import PARTIAL, STRONG, assign, capacities, rescore  # noqa: E402
from utils.file_reader import DataError, detect_column, parse_capacity, read_table  # noqa: E402

NONE = "— none —"
ss = st.session_state

st.html("""<style>
.block-container { max-width: 1180px; padding-top: 2.2rem; }
.step { display:inline-flex; align-items:center; justify-content:center; width:1.7rem; height:1.7rem;
        border-radius:50%; background: var(--primary-color, #1E3A8A); color:#fff; font-size:.9rem;
        font-weight:700; margin-right:.55rem; vertical-align: .15rem; }
@media (max-width: 640px) { h1 { font-size: 1.9rem !important; } }
</style>""")


def step(n, title):
    st.markdown(f'<span class="step">{n}</span> <span style="font-size:1.35rem;font-weight:700">{title}</span>',
                unsafe_allow_html=True)  # constant text only, never user data


# ---------- header ----------
head, help_col = st.columns([5, 1], vertical_alignment="center")
with head:
    st.title(":material/school: Student–Lecturer Assignment")
    st.caption("Upload a student list and a lecturer list. Get a fair, field-matched supervision list "
               "you can review, adjust and export.")
with help_col, st.popover("How it works", icon=":material/help:", width="stretch"):
    st.markdown(f"""
**1. Add your lists.** CSV, Excel or Word (first table). Headers are detected automatically,
so *Name / Full name / Student*, *Matric / Reg No / Student ID*, *Field / Department / Specialization*
all work. Lecturers can have a *Max_Students* column.

**2. Choose a method.**
- **Smart match** reads each student's field and each lecturer's specializations, scores how close they are
  (it handles abbreviations like *AI*, typos and different wording), then finds the best overall
  assignment while keeping workloads even.
- **Random** spreads students evenly at random.

**3. Review and export.** Change any lecturer in the table, then download Excel, PDF, Word or CSV.

Match quality: **Strong** ≥ {STRONG:.0%}, **Partial** ≥ {PARTIAL:.0%}, otherwise **Weak**.

Your files are processed in memory for this session only and are never stored.
""")


# ---------- step 1: data ----------
def load(kind, upload):
    """Return (raw DataFrame, signature) for the uploaded file or the sample, else (None, None)."""
    if upload is not None:
        try:
            return read_table(upload.name, upload.getvalue()), upload.file_id
        except DataError as e:
            st.error(str(e), icon=":material/error:")
            return None, None
    if ss.get("sample"):
        return (samples.sample_students() if kind == "students" else samples.sample_lecturers()), "sample"
    return None, None


def pick(label, df, kind, sig, key, optional=False, exclude=()):
    cols = list(df.columns)
    guess = detect_column(cols, kind, exclude)
    options = ([NONE] if optional else []) + cols
    index = options.index(guess) if guess in options else 0
    choice = st.selectbox(label, options, index=index, key=f"{key}_{sig}")
    return None if choice == NONE else choice


def prepare_students(raw, sig):
    with st.expander("Columns", icon=":material/table_chart:"):
        c1, c2, c3 = st.columns(3)
        with c1:
            name = pick("Name", raw, "name", sig, "s_name")
        with c2:
            matric = pick("Matric / ID", raw, "matric", sig, "s_matric", exclude=[name])
        with c3:
            field = pick("Field (optional)", raw, "field", sig, "s_field", optional=True, exclude=[name, matric])
        st.dataframe(raw.head(50), hide_index=True, height=220)
    df = pd.DataFrame({"name": raw[name], "matric": raw[matric], "field": raw[field] if field else ""})
    df = df[df["name"] != ""].reset_index(drop=True)
    problems = []
    if name == matric:
        problems.append("Name and Matric / ID can't be the same column.")
    if (df["matric"] == "").any():
        problems.append(f"{(df['matric'] == '').sum()} student(s) have no matric number.")
    dups = df.loc[df["matric"].duplicated() & (df["matric"] != ""), "matric"].unique()
    if len(dups):
        problems.append(f"Duplicate matric numbers: {', '.join(dups[:5])}{'…' if len(dups) > 5 else ''}")
    return df, problems


def prepare_lecturers(raw, sig):
    with st.expander("Columns", icon=":material/table_chart:"):
        c1, c2, c3 = st.columns(3)
        with c1:
            name = pick("Name", raw, "name", sig, "l_name")
        with c2:
            field = pick("Specialization (optional)", raw, "field", sig, "l_field", optional=True, exclude=[name])
        with c3:
            cap = pick("Max students (optional)", raw, "capacity", sig, "l_cap", optional=True, exclude=[name, field])
        st.dataframe(raw.head(50), hide_index=True, height=220)
    df = pd.DataFrame({"name": raw[name], "field": raw[field] if field else "",
                       "capacity": [parse_capacity(v) for v in raw[cap]] if cap else None})
    df = df[df["name"] != ""].reset_index(drop=True)
    problems = []
    dups = df.loc[df["name"].duplicated(), "name"].unique()
    if len(dups):
        problems.append(f"Duplicate lecturer names: {', '.join(dups[:5])}{'…' if len(dups) > 5 else ''}")
    return df, problems


with st.container(border=True):
    top, sample_col = st.columns([3, 2], vertical_alignment="center")
    with top:
        step(1, "Add your lists")
    with sample_col:
        b1, b2 = st.columns(2)
        if ss.get("sample"):
            b1.button("Clear sample", icon=":material/close:", width="stretch",
                      on_click=lambda: ss.update(sample=False, result=None))
        else:
            b1.button("Try sample data", icon=":material/science:", width="stretch",
                      on_click=lambda: ss.update(sample=True))
        with b2.popover("Templates", icon=":material/download:", width="stretch"):
            for kind in ("students", "lecturers"):
                st.markdown(f"**{kind.title()}**")
                for c, (fmt, label) in zip(st.columns(3), [("csv", "CSV"), ("xlsx", "Excel"), ("docx", "Word")]):
                    c.download_button(label, samples.template(kind, fmt), f"{kind}_template.{fmt}",
                                      key=f"tpl_{kind}_{fmt}", on_click="ignore", width="stretch")

    left, right = st.columns(2, gap="large")
    students = lecturers = None
    problems = []
    with left:
        st.markdown("**Students**")
        up = st.file_uploader("Student list", type=["csv", "xlsx", "docx"], label_visibility="collapsed",
                              help="Needs a name and a matric number column. A field/department column enables smart matching.")
        raw, sig = load("students", up)
        if raw is not None:
            students, p = prepare_students(raw, sig)
            problems += p
            st.caption(f"{len(students)} students · {students['field'].replace('', pd.NA).nunique()} fields"
                       + (" · sample data" if sig == "sample" else ""))
    with right:
        st.markdown("**Lecturers**")
        up = st.file_uploader("Lecturer list", type=["csv", "xlsx", "docx"], label_visibility="collapsed",
                              help="Needs a name column. Specialization and Max_Students columns are optional.")
        raw, sig = load("lecturers", up)
        if raw is not None:
            lecturers, p = prepare_lecturers(raw, sig)
            problems += p
            st.caption(f"{len(lecturers)} lecturers" + (" · sample data" if sig == "sample" else ""))
    for p in problems:
        st.warning(p, icon=":material/warning:")

ready = students is not None and lecturers is not None and not problems and len(students) and len(lecturers)

# ---------- step 2: settings ----------
with st.container(border=True):
    step(2, "Choose how to match")
    c1, c2, c3 = st.columns([2, 1.3, 1.3], gap="large")
    with c1:
        method = st.segmented_control("Method", ["Smart match", "Random"], default="Smart match",
                                      required=True, width="stretch")
        has_fields = ready and (students["field"] != "").any() and (lecturers["field"] != "").any()
        if method == "Smart match" and ready and not has_fields:
            st.caption(":material/info: No field columns found, so this will behave like an even random split.")
        else:
            st.caption("Pairs students with lecturers in the closest field, keeping workloads even."
                       if method == "Smart match" else "Spreads students evenly, ignoring fields.")
    with c2:
        global_max = st.number_input("Max students per lecturer", min_value=0, value=0, step=1,
                                     help="0 = split evenly. Limits in the lecturer file take priority.")
    with c3:
        min_pct = st.slider("Minimum match", 0, 100, 0, step=5, format="%d%%",
                            disabled=method != "Smart match",
                            help="Leave a student unassigned rather than give them a lecturer below this match.")
    if ready:
        total = sum(capacities(lecturers, len(students), global_max or None))
        if total < len(students):
            st.warning(f"Lecturer limits add up to {total} places for {len(students)} students. "
                       f"{len(students) - total} will be left unassigned.", icon=":material/warning:")

    settings = (method, global_max, min_pct)
    if st.button("Assign students", type="primary", icon=":material/auto_awesome:", width="stretch",
                 disabled=not ready):
        with st.spinner("Matching…"):
            ss.result = assign(students, lecturers, "smart" if method == "Smart match" else "random",
                               global_max=global_max or None, min_score=min_pct / 100)
        t = ss.result["table"]
        order = t["match"].map({"Unassigned": 0, "Weak": 1, "Partial": 2}).fillna(3)
        ss.table = t.assign(_o=order).sort_values(["_o", "lecturer", "name"]).drop(columns="_o").reset_index(drop=True)
        ss.editor_v = ss.get("editor_v", 0) + 1
        ss.inputs = (students.to_json(), lecturers.to_json(), settings)
    if not ready and students is None and lecturers is None:
        st.caption("Add both lists (or try the sample data) to continue.")

# ---------- step 3: results ----------
if ss.get("result") is not None:
    result, table = ss.result, ss.table
    if ready and ss.get("inputs") != (students.to_json(), lecturers.to_json(), settings):
        st.info("Your data or settings changed. Press **Assign students** again to update.", icon=":material/info:")

    with st.container(border=True):
        step(3, "Review & export")
        n = len(table)
        assigned = (table["lecturer"] != "").sum()
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Assigned", f"{assigned} / {n}", border=True)
        m2.metric("Unassigned", n - assigned, border=True)
        if result["has_fields"]:
            m3.metric("Strong matches", f"{(table['match'] == 'Strong').mean():.0%}", border=True)
            m4.metric("Average match", f"{table['score'].mean():.0%}" if assigned else "–", border=True)
        else:
            m3.metric("Lecturers used", table.loc[table['lecturer'] != '', 'lecturer'].nunique(), border=True)
            loads = table[table["lecturer"] != ""]["lecturer"].value_counts()
            m4.metric("Load range", f"{loads.min()}–{loads.max()}" if len(loads) else "–", border=True)

        cols = st.columns(len(reports.FORMATS))
        for c, (fmt, (ext, mime)) in zip(cols, reports.FORMATS.items()):
            c.download_button(f"Download {fmt}", lambda f=fmt, t=table: reports.build(f, t),
                              f"assignments.{ext}", mime, key=f"dl_{fmt}", on_click="ignore",
                              icon=":material/download:", width="stretch",
                              type="primary" if fmt == "Excel" else "secondary")

        tab_edit, tab_lect, tab_load = st.tabs([":material/edit: Review & edit", ":material/groups: By lecturer",
                                                ":material/bar_chart: Workload"])
        lect_names = list(result["caps"])

        def apply_edits():
            edits = ss[f"editor_{ss.editor_v}"]["edited_rows"]
            t = ss.table.copy()
            for pos, change in edits.items():
                if "lecturer" in change:
                    t.loc[t.index[int(pos)], "lecturer"] = change["lecturer"] or ""
            ss.table = rescore(t, result)
            ss.editor_v += 1

        with tab_edit:
            st.caption("Rows needing attention are listed first. Change a lecturer from the dropdown; "
                       "scores and exports update instantly. Use the table's search icon to find a student.")
            st.data_editor(
                table, key=f"editor_{ss.editor_v}", on_change=apply_edits, hide_index=True, height=440,
                disabled=["name", "matric", "field", "lecturer_field", "score", "match"],
                column_order=["match", "name", "matric", "field", "lecturer", "score"],
                column_config={
                    "match": st.column_config.TextColumn("Match", width="small"),
                    "name": "Student", "matric": "Matric No.", "field": "Student field",
                    "lecturer": st.column_config.SelectboxColumn("Lecturer", options=lect_names, width="medium"),
                    "score": st.column_config.ProgressColumn("Score", min_value=0, max_value=1, format="percent"),
                })

        with tab_lect:
            for lec in sorted(lect_names, key=str.lower):
                group = table[table["lecturer"] == lec]
                cap = result["caps"][lec]
                label = f"{lec} · {len(group)}/{cap}" + (" · over limit" if len(group) > cap else "")
                with st.expander(label, icon=":material/person:"):
                    if result["lecturer_fields"].get(lec):
                        st.caption(result["lecturer_fields"][lec])
                    if group.empty:
                        st.caption("No students assigned.")
                    else:
                        st.dataframe(group[["name", "matric", "field", "match"]], hide_index=True,
                                     column_config={"name": "Student", "matric": "Matric No.",
                                                    "field": "Field", "match": "Match"})
            un = table[table["lecturer"] == ""]
            if len(un):
                with st.expander(f"Unassigned · {len(un)}", icon=":material/person_off:", expanded=True):
                    st.dataframe(un[["name", "matric", "field"]], hide_index=True,
                                 column_config={"name": "Student", "matric": "Matric No.", "field": "Field"})

        with tab_load:
            load = pd.DataFrame({"Lecturer": lect_names,
                                 "Assigned": [int((table["lecturer"] == l).sum()) for l in lect_names],
                                 "Limit": [result["caps"][l] for l in lect_names]})
            load["Load"] = load["Assigned"] / load["Limit"]
            st.dataframe(load.sort_values("Load", ascending=False), hide_index=True,
                         column_config={"Load": st.column_config.ProgressColumn(
                             "Load", min_value=0, max_value=1, format="percent")})
            if (load["Load"] > 1).any():
                st.warning("Some lecturers are over their limit after manual edits.", icon=":material/warning:")
