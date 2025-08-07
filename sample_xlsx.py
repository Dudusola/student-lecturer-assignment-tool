from openpyxl import Workbook
import io

def generate_xlsx_template_student():
    wb = Workbook()
    ws = wb.active
    ws.title = "Students"
    ws.append(["Name", "Matric Number", "Field"])
    ws.append(["John Doe", "CSC/1234/21", "Artificial Intelligence"])
    ws.append(["Jane Smith", "CSC/5678/21", "Artificial Intelligence"])

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer

def generate_xlsx_template_lecturer():
    wb = Workbook()
    ws = wb.active
    ws.title = "Lecturers"
    ws.append(["Name", "Max_Students", "Field"])
    ws.append(["Dr. Smith", 8, "Artificial Intelligence"])
    ws.append(["Dr. Johnson", 10, "Artificial Intelligence"])

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer
