import pandas as pd
import random
from collections import defaultdict

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = df.columns.str.strip().str.lower()
    return df

def assign_students_randomly(students: pd.DataFrame, lecturers: pd.DataFrame) -> dict:
    students = normalize_columns(students)
    lecturers = normalize_columns(lecturers)

    assignment = defaultdict(list)
    lecturer_pool = []

    for _, row in lecturers.iterrows():
        lecturer_pool.extend([row['name']] * int(row['max_students']))

    random.shuffle(lecturer_pool)

    if len(students) > len(lecturer_pool):
        raise ValueError("Not enough lecturer slots to assign all students.")

    for _, student in students.iterrows():
        assigned_lecturer = lecturer_pool.pop()
        assignment[assigned_lecturer].append(student.to_dict())

    return assignment

def assign_students_by_field_balanced(students: pd.DataFrame, lecturers: pd.DataFrame) -> dict:
    students = normalize_columns(students)
    lecturers = normalize_columns(lecturers)

    assignment = defaultdict(list)
    lecturers_copy = lecturers.copy()
    lecturers_copy['remaining_slots'] = lecturers_copy['max_students']

    grouped_students = students.groupby('field')
    lecturers_pool = lecturers_copy.to_dict(orient='records')

    for field, group in grouped_students:
        student_list = group.to_dict(orient='records')
        lecturer_index = 0
        for student in student_list:
            assigned = False
            attempts = 0
            while not assigned and attempts < len(lecturers_pool):
                lecturer = lecturers_pool[lecturer_index]
                if lecturer['remaining_slots'] > 0:
                    assignment[lecturer['name']].append(student)
                    lecturer['remaining_slots'] -= 1
                    assigned = True
                lecturer_index = (lecturer_index + 1) % len(lecturers_pool)
                attempts += 1
            if not assigned:
                raise ValueError("Unable to assign student: All lecturer slots are filled.")

    return assignment

def flatten_assignment(assignment: dict) -> pd.DataFrame:
    rows = []
    for lecturer, students in assignment.items():
        for student in students:
            row = student.copy()
            row['assigned lecturer'] = lecturer
            rows.append(row)
    return pd.DataFrame(rows)
