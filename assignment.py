import streamlit as st
import pandas as pd
st.title("")
st.markdown("""
    <style>
    .block-container > img:first-child {
        margin-top: 2.5rem;
    }
    </style>
    """, unsafe_allow_html=True)
st.image("logo.png", width=110)
st.title("Student–Lecturer Assignment Tool")
st.caption("Upload your data, configure assignment settings, and generate assignment reports.")
st.markdown("---")
from sample_xlsx import generate_xlsx_template_student, generate_xlsx_template_lecturer
from sample_docx import generate_docx_template_student, generate_docx_template_lecturer
from sample_csv import generate_csv_template_student, generate_csv_template_lecturer
from utils.file_reader import read_uploaded_file
from utils.reports import generate_report
from utils.assigner import assign_students

st.set_page_config(page_title="Student–Lecturer Assignment Tool", layout="centered")


# Accessibility: Larger font and high-contrast for headers
st.markdown('<h2 style="font-size:2rem;color:#1a237e;">Upload Data Files</h2>', unsafe_allow_html=True)
st.markdown('<span style="font-size:1.1rem;">Upload your student and lecturer data files below. Supported formats: CSV, Excel, or Word.</span>', unsafe_allow_html=True)

# Responsive: Stack uploaders vertically for mobile
st.subheader("Student Data File")
student_file = st.file_uploader(
    "Choose a student file",
    type=["csv", "xlsx", "docx"],
    help="Must include columns: Name, Matric Number. Optionally: Field, Department, or Specialization."
)
st.subheader("Lecturer Data File")
lecturer_file = st.file_uploader(
    "Choose a lecturer file",
    type=["csv", "xlsx", "docx"],
    help="Must include column: Name. Optionally: Field, Specialization, Department, Max_Students."
)

with st.expander("File Format Examples and Tips"):
    st.markdown("""
    **Student File Example:**
    | Name      | Matric Number | Field                  |
    |-----------|---------------|------------------------|
    | John Doe  | CSC/1234/21   | Artificial Intelligence|
    - Required: Name, Matric Number
    - Optional: Field, Department, or Specialization (any of these will work)

    **Lecturer File Example:**
    | Name      | Max_Students | Field                  |
    |-----------|--------------|------------------------|
    | Dr. Smith | 8            | Artificial Intelligence|
    - Required: Name
    - Optional: Field, Specialization, Department, Max_Students (any of these will work)
    """)

with st.expander("Download Sample Templates"):
    colA, colB = st.columns(2)
    with colA:
        st.subheader("Student Templates")
        st.download_button("CSV", generate_csv_template_student(), "student_template.csv")
        st.download_button("Excel", generate_xlsx_template_student(), "student_template.xlsx")
        st.download_button("Word", generate_docx_template_student(), "student_template.docx")
    with colB:
        st.subheader("Lecturer Templates")
        st.download_button("CSV", generate_csv_template_lecturer(), "lecturer_template.csv")
        st.download_button("Excel", generate_xlsx_template_lecturer(), "lecturer_template.xlsx")
        st.download_button("Word", generate_docx_template_lecturer(), "lecturer_template.docx")
st.markdown("---")


# Assignment Settings
st.markdown('<h2 style="font-size:2rem;color:#1a237e;">Assignment Settings</h2>', unsafe_allow_html=True)
assignment_strategy = st.radio(
    "Assignment Method",
    ["Random Assignment", "Field-Based Assignment"],
    key="assignment_method",
    help="Choose how students are assigned to lecturers."
)
if assignment_strategy == "Field-Based Assignment":
    st.info("Both files must contain a 'Field', 'Department', or 'Specialization' column for field-based assignment.")
use_global_max = st.checkbox("Set a global maximum number of students per lecturer", key="global_max_checkbox")
if use_global_max:
    max_students = st.number_input(
        "Maximum students per lecturer",
        min_value=1,
        step=1,
        help="Overrides individual lecturer limits unless specified in the file."
    )
else:
    max_students = None
st.markdown("---")

# User Customization: Column Mapping
st.markdown('<h2 style="font-size:1.3rem;color:#1565c0;">Column Mapping (Advanced)</h2>', unsafe_allow_html=True)
with st.expander("Customize column names for your files (optional)"):
    st.markdown("If your files use different column names, map them here. Leave blank to use the default.")
    col_map = {}
    col_map['student_name'] = st.text_input("Student Name column", value="name", help="Column in student file for student names.", key="student_name_col")
    col_map['matric_number'] = st.text_input("Matric Number column", value="matric number", help="Column in student file for matric numbers.", key="matric_col")
    col_map['student_field'] = st.text_input("Student Field column", value="field", help="Column in student file for field/department/specialization.", key="student_field_col")
    col_map['lecturer_name'] = st.text_input("Lecturer Name column", value="name", help="Column in lecturer file for lecturer names.", key="lecturer_name_col")
    col_map['lecturer_field'] = st.text_input("Lecturer Field column", value="field", help="Column in lecturer file for field/department/specialization.", key="lecturer_field_col")
    col_map['max_students'] = st.text_input("Lecturer Max Students column", value="max_students", help="Column in lecturer file for max students.", key="max_students_col")


# Read Data (with flexible column mapping) and show validation feedback
student_df = None
lecturer_df = None
validation_issues = []
error_log = []
if student_file:
    try:
        student_df = read_uploaded_file(student_file)
        # Map columns according to user mapping
        for key, default in zip(['student_name', 'matric_number', 'student_field'], ['name', 'matric number', 'field']):
            if col_map[key] != default and col_map[key] in student_df.columns:
                student_df[default] = student_df[col_map[key]]
        if "field" not in student_df.columns:
            for alt in [col_map['student_field'], "department", "specialization"]:
                if alt in student_df.columns:
                    student_df["field"] = student_df[alt]
        required_cols = ["name", "matric number"]
        missing_cols = [col for col in required_cols if col not in student_df.columns]
        if missing_cols:
            validation_issues.append(f"Student file is missing required columns: {', '.join(missing_cols)}.")
            student_df = None
        elif student_df.duplicated(['matric number']).any():
            validation_issues.append("Duplicate Matric Numbers found in student file.")
        elif student_df.empty:
            validation_issues.append("Student file is empty.")
            student_df = None
    except Exception as e:
        validation_issues.append(f"Error reading student file: {e}")
        error_log.append(f"Student file error: {e}")
        student_df = None
if lecturer_file:
    try:
        lecturer_df = read_uploaded_file(lecturer_file)
        for key, default in zip(['lecturer_name', 'lecturer_field', 'max_students'], ['name', 'field', 'max_students']):
            if col_map[key] != default and col_map[key] in lecturer_df.columns:
                lecturer_df[default] = lecturer_df[col_map[key]]
        if "field" not in lecturer_df.columns:
            for alt in [col_map['lecturer_field'], "specialization", "department"]:
                if alt in lecturer_df.columns:
                    lecturer_df["field"] = lecturer_df[alt]
        if "name" not in lecturer_df.columns:
            validation_issues.append("Lecturer file must contain at least a 'name' column.")
            lecturer_df = None
        elif lecturer_df.duplicated(['name']).any():
            validation_issues.append("Duplicate lecturer names found in lecturer file.")
        elif lecturer_df.empty:
            validation_issues.append("Lecturer file is empty.")
            lecturer_df = None
    except Exception as e:
        validation_issues.append(f"Error reading lecturer file: {e}")
        error_log.append(f"Lecturer file error: {e}")
        lecturer_df = None

if validation_issues:
    st.warning("**Validation Issues:**\n" + "\n".join(f"- {issue}" for issue in validation_issues))
st.markdown("---")


# Output Format
st.header("Output Format")
output_format = st.multiselect(
    "Select Output Formats",
    ["PDF", "Word", "CSV", "Excel"],
    default=["PDF"]
)
st.markdown("---")

# Help/FAQ Section
with st.expander("Help & FAQ"):
    st.markdown("""
    **Q: What file formats are supported?**  
    A: CSV, Excel (.xlsx), and Word (.docx) for both students and lecturers.

    **Q: What columns are required?**  
    A: Students: Name, Matric Number. Lecturers: Name. Field/Department/Specialization is optional but needed for field-based assignment.

    **Q: Can I use my own column names?**  
    A: Yes! Use the 'Column Mapping (Advanced)' section to map your file's columns to the required fields.

    **Q: What does 'Download All' do?**  
    A: It creates a ZIP file containing all selected report formats for easy download.

    **Q: How do I filter or search the assignment preview?**  
    A: Use the search box above the preview table to filter by student name, matric number, or lecturer.

    **Q: What if I see validation issues?**  
    A: Check your file columns and data for errors, then re-upload. Details will be shown above.

    **Q: How do I get help with errors?**  
    A: If any errors occur, a 'Download Error Log' button will appear so you can download and review the error details.

    **Q: Is this app accessible?**  
    A: Yes! The app uses larger, high-contrast headers and clear help text for better readability. Let us know if you need further accessibility improvements.
    """)

# Assignment Generation
st.markdown('<h2 style="font-size:2rem;color:#1a237e;">Generate Assignment</h2>', unsafe_allow_html=True)
if st.button("Generate Assignment", key="generate_btn"):
    if student_df is None or lecturer_df is None:
        st.warning("Please upload both student and lecturer files.")
    elif not output_format:
        st.warning("Please select at least one output format.")
    else:
        mode = "field" if assignment_strategy == "Field-Based Assignment" else "random"
        if mode == "field":
            if "field" not in student_df.columns:
                st.error("Field-based assignment requires a 'field' column in the student file.")
                st.stop()
            if "field" not in lecturer_df.columns:
                st.error("Field-based assignment requires a 'field' column in the lecturer file.")
                st.stop()
        # Progress spinner
        with st.spinner("Assigning students to lecturers and generating reports..."):
            try:
                assignment_flat = assign_students(student_df, lecturer_df, mode, max_students)
            except Exception as e:
                error_log.append(f"Assignment error: {e}")
                st.error(f"Assignment failed: {e}")
                assignment_flat = None
        if assignment_flat is not None and not assignment_flat.empty:
            # Assignment summary
            total_students = len(student_df)
            total_assigned = len(assignment_flat)
            total_unassigned = total_students - total_assigned
            total_lecturers = len(assignment_flat['assigned lecturer'].unique())
            st.success(f"Assignment complete.\n\n**Summary:**\n- Total students: {total_students}\n- Assigned: {total_assigned}\n- Unassigned: {total_unassigned}\n- Lecturers: {total_lecturers}")
            # Search/filter in preview
            st.markdown("**Preview of first 20 students (search/filter below):**")
            search_term = st.text_input("Search by student name, matric number, or lecturer", "", key="search_box")
            preview_df = assignment_flat.copy()
            if search_term:
                search_term_lower = search_term.lower()
                preview_df = preview_df[
                    preview_df['student name'].str.lower().str.contains(search_term_lower) |
                    preview_df['matric number'].astype(str).str.lower().str.contains(search_term_lower) |
                    preview_df['assigned lecturer'].str.lower().str.contains(search_term_lower)
                ]
            st.dataframe(preview_df.head(20))
            # Collated View: Grouped by Lecturer
            st.markdown("#### Collated View (by Lecturer)")
            for lecturer, group in assignment_flat.groupby("assigned lecturer"):
                st.markdown(f"**{lecturer}:**")
                students_list = [f"{row['student name']} ({row['matric number']})" for _, row in group.iterrows()]
                st.markdown("\n".join([f"- {student}" for student in students_list]))
                st.markdown("---")
            unassigned = student_df[~student_df["matric number"].isin(assignment_flat["matric number"])]
            if not unassigned.empty:
                st.warning(f"{len(unassigned)} students could not be assigned.")
                st.dataframe(unassigned)
            # Download All Reports as ZIP
            import zipfile, io
            if len(output_format) > 1:
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w") as zipf:
                    for fmt in output_format:
                        try:
                            report_bytes, mime, file_name = generate_report(fmt, assignment_flat)
                            zipf.writestr(file_name, report_bytes)
                        except Exception as e:
                            error_log.append(f"Report ({fmt}) error: {e}")
                            st.error(f"Failed to generate {fmt.upper()} report: {e}")
                st.download_button("Download All Reports (ZIP)", data=zip_buffer.getvalue(), file_name="assignment_reports.zip", mime="application/zip")
            # Individual report downloads
            for fmt in output_format:
                try:
                    report_bytes, mime, file_name = generate_report(fmt, assignment_flat)
                    st.download_button(f"Download {fmt.upper()}", data=report_bytes, file_name=file_name, mime=mime)
                except Exception as e:
                    error_log.append(f"Report ({fmt}) error: {e}")
                    st.error(f"Failed to generate {fmt.upper()} report: {e}")
        else:
            st.error("No assignments were generated. Please check your data and try again.")
    # Error Logging: Download log if any errors
    if error_log:
        import io
        log_bytes = io.StringIO("\n".join(error_log)).getvalue().encode()
        st.download_button("Download Error Log", data=log_bytes, file_name="assignment_error_log.txt", mime="text/plain")

st.markdown(
    '''
    <style>
    /* Make tables scrollable on mobile */
    .css-1lcbmhc, .stDataFrame { overflow-x: auto; }
    /* Button styling (Generate Assignment and others) */
    .stButton>button {
        font-size: 1.1rem;
        padding: 0.6em 1.5em;
        border-radius: 6px;
        background-color: #636EFA;
        color: #fff;
        border: none;
        transition: background 0.2s;
        box-shadow: 0 2px 8px rgba(99,110,234,0.08);
    }
    .stButton>button:hover {
        background-color: #4a5bdc;
    }
    /* Multiselect (format selection) styling */
    .stMultiSelect [data-baseweb="tag"] {
        background-color: #636EFA !important;
        color: #fff !important;
        border-radius: 4px !important;
    }
    .stMultiSelect [data-baseweb="tag"]:hover {
        background-color: #4a5bdc !important;
    }
    /* Input styling */
    .stTextInput>div>div>input, .stNumberInput>div>div>input {
        font-size: 1.05rem;
        border-radius: 5px;
        border: 1px solid #b0bec5;
        padding: 0.5em;
    }
    /* Headings */
    h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        font-family: 'Segoe UI', 'Arial', sans-serif;
        font-weight: 700;
        color: #636EFA;
    }
    /* Headings: clearer color in dark mode */
    @media (prefers-color-scheme: dark) {
        h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
            color: #aab6fe !important;
        }
    }
    /* Section spacing */
    .block-container {
        padding-top: 2.5rem; /* Increased top padding so title is not cut off */
        padding-bottom: 1.5rem;
    }
    /* Responsive font for mobile */
    @media (max-width: 600px) {
        h1, h2, h3 { font-size: 6vw; }
        .block-container { padding: 1.5rem 0.5rem 0.5rem 0.5rem; }
    }
    </style>
    ''',
    unsafe_allow_html=True
)
