# sample_csv.py
import pandas as pd
import io

def generate_csv_template_student():
    df = pd.DataFrame({
        "Name": ["John Doe", "Jane Smith"],
        "Matric Number": ["CSC/1234/21", "CSC/5678/21"],
        "Field": ["Artificial Intelligence", "Artificial Intelligence"]
    })
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue()

def generate_csv_template_lecturer():
    df = pd.DataFrame({
        "Name": ["Dr. Smith", "Dr. Johnson"],
        "Max_Students": [8, 10],
        "Field": ["Artificial Intelligence", "Artificial Intelligence"]
    })
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue()
