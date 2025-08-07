import random
import pandas as pd

def assign_students(student_df, lecturer_df, mode="random", max_per_lecturer=None):
    """
    Assigns students to lecturers based on the selected mode.
    :param student_df: DataFrame with student data
    :param lecturer_df: DataFrame with lecturer data
    :param mode: "random" or "field"
    :param max_per_lecturer: maximum number of students per lecturer
    :return: DataFrame with assignments
    """
    if mode == "field":
        return assign_by_field(student_df, lecturer_df, max_per_lecturer)
    else:
        return assign_random(student_df, lecturer_df, max_per_lecturer)

def assign_random(student_df, lecturer_df, max_per_lecturer=None):
    students = student_df.copy()
    lecturers = lecturer_df.copy()
    lecturer_names = lecturers["name"].tolist()
    assignments = {lecturer: [] for lecturer in lecturer_names}

    if max_per_lecturer is None:
        max_per_lecturer = len(students) // len(lecturer_names) + 1

    student_indices = list(students.index)
    random.shuffle(student_indices)

    for student_idx in student_indices:
        assigned = False
        random.shuffle(lecturer_names)

        for lecturer in lecturer_names:
            if len(assignments[lecturer]) < max_per_lecturer:
                assignments[lecturer].append(student_idx)
                assigned = True
                break

        if not assigned:
            raise Exception("Not enough lecturer slots to assign all students.")

    # Flatten the assignment into a DataFrame, including student and lecturer fields if present
    records = []
    for lecturer, indices in assignments.items():
        # Get lecturer field if present
        lecturer_field = ''
        if "field" in lecturers.columns:
            match = lecturers[lecturers["name"] == lecturer]
            if not match.empty:
                lecturer_field = match.iloc[0]["field"]
        for idx in indices:
            student = students.loc[idx]
            record = {
                "assigned lecturer": lecturer,
                "lecturer field": lecturer_field,
                "student name": student.get("name", ""),
                "matric number": student.get("matric number", ""),
                "student field": student.get("field", "")
            }
            records.append(record)

    return pd.DataFrame(records)

def assign_by_field(student_df, lecturer_df, max_per_lecturer=None):
    students = student_df.copy()
    lecturers = lecturer_df.copy()
    # Normalize and check that both have a 'field' column
    if "field" not in students.columns or "field" not in lecturers.columns:
        raise ValueError("Both student and lecturer files must include a 'Field' column for field-based assignment.")

    assignments = []

    for field in students["field"].unique():
        students_in_field = students[students["field"] == field]
        lecturers_in_field = lecturers[lecturers["field"] == field]

        if lecturers_in_field.empty:
            continue  # No lecturer in this field

        lecturer_list = lecturers_in_field["name"].tolist()
        lecturer_capacity = {name: 0 for name in lecturer_list}

        for _, student in students_in_field.iterrows():
            random.shuffle(lecturer_list)
            assigned = False

            for lecturer in lecturer_list:
                if max_per_lecturer is None or lecturer_capacity[lecturer] < max_per_lecturer:
                    # Get lecturer field if present
                    lecturer_field = ''
                    match = lecturers_in_field[lecturers_in_field["name"] == lecturer]
                    if not match.empty:
                        lecturer_field = match.iloc[0]["field"]
                    assignments.append({
                        "assigned lecturer": lecturer,
                        "lecturer field": lecturer_field,
                        "student name": student.get("name", ""),
                        "matric number": student.get("matric number", ""),
                        "student field": student.get("field", "")
                    })
                    lecturer_capacity[lecturer] += 1
                    assigned = True
                    break

            if not assigned:
                raise Exception(f"No available lecturer slots for student '{student['name']}' in field '{field}'.")

    return pd.DataFrame(assignments)
