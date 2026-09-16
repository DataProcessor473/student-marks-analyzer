"""
Phase 3: PDF Report Card Templates
"""
from fpdf import FPDF
from datetime import datetime
import os

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


class ModernReportCard(FPDF):
    def __init__(self, student, school_name="Student Marks Analyzer Pro"):
        super().__init__()
        self.student = student
        self.school_name = school_name
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        self.set_fill_color(102, 126, 234)
        self.rect(0, 0, 210, 35, "F")
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 22)
        self.set_y(8)
        self.cell(0, 10, self.school_name, 0, 1, "C")
        self.set_font("Helvetica", "", 11)
        self.cell(0, 5, "Academic Performance Report Card", 0, 1, "C")
        self.set_text_color(0, 0, 0)
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10,
                  f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} | Page {self.page_no()}",
                  0, 0, "C")


def generate_modern_report(student: dict, output_path: str):
    pdf = ModernReportCard(student)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 12)
    pdf.set_fill_color(240, 242, 246)
    pdf.cell(0, 8, "  Student Information", 0, 1, "L", True)
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 11)
    info = [
        ("Name:", student.get("name", "N/A")),
        ("ID:", str(student.get("id", "N/A"))),
        ("Class:", student.get("class_name") or "N/A"),
        ("Semester:", student.get("semester") or "N/A"),
        ("Department:", student.get("department") or "N/A"),
    ]
    for label, value in info:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(45, 7, label, 0, 0)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 7, str(value), 0, 1)

    pdf.ln(5)

    grade = student.get("grade", "F")
    grade_colors = {
        "A+": (16, 185, 129), "A": (52, 211, 153), "B": (251, 191, 36),
        "C": (245, 158, 11), "D": (249, 115, 22), "E": (239, 68, 68),
        "F": (220, 38, 38),
    }
    gc = grade_colors.get(grade, (128, 128, 128))
    pdf.set_fill_color(*gc)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 28)
    pdf.cell(50, 25, grade, 1, 0, "C", True)
    pdf.set_text_color(0, 0, 0)

    pdf.set_xy(60, pdf.get_y())
    pdf.set_font("Helvetica", "", 10)
    stats = [
        f"Average: {student.get('average', 0):.2f}%",
        f"Total: {student.get('total_marks', 0):.0f}",
        f"Subjects: {len(student.get('marks', []))}",
    ]
    y_start = pdf.get_y()
    for i, s in enumerate(stats):
        pdf.set_xy(60, y_start + i * 7)
        pdf.cell(0, 7, s, 0, 1)
    pdf.set_y(y_start + 30)

    pdf.set_font("Helvetica", "B", 12)
    pdf.set_fill_color(240, 242, 246)
    pdf.cell(0, 8, "  Subject-wise Performance", 0, 1, "L", True)
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(102, 126, 234)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(15, 8, "#", 1, 0, "C", True)
    pdf.cell(80, 8, "Subject", 1, 0, "L", True)
    pdf.cell(25, 8, "Marks", 1, 0, "C", True)
    pdf.cell(35, 8, "Status", 1, 0, "C", True)
    pdf.cell(35, 8, "Grade", 1, 1, "C", True)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 10)

    for i, (subj, mark) in enumerate(zip(student.get("subjects", []), student.get("marks", []))):
        fill = i % 2 == 0
        if fill:
            pdf.set_fill_color(249, 250, 251)
        pdf.cell(15, 8, str(i + 1), 1, 0, "C", fill)
        pdf.cell(80, 8, str(subj)[:40], 1, 0, "L", fill)
        pdf.cell(25, 8, f"{mark:.0f}", 1, 0, "C", fill)
        pdf.cell(35, 8, "Pass" if mark >= 40 else "Fail", 1, 0, "C", fill)
        if mark >= 90: sg = "A+"
        elif mark >= 80: sg = "A"
        elif mark >= 70: sg = "B"
        elif mark >= 60: sg = "C"
        elif mark >= 50: sg = "D"
        elif mark >= 40: sg = "E"
        else: sg = "F"
        pdf.cell(35, 8, sg, 1, 1, "C", fill)

    pdf.ln(8)

    recs = student.get("recommendations", [])
    if recs:
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_fill_color(240, 242, 246)
        pdf.cell(0, 8, "  Recommendations", 0, 1, "L", True)
        pdf.ln(2)
        pdf.set_font("Helvetica", "", 10)
        for rec in recs[:6]:
            clean = rec.encode("latin-1", "ignore").decode("latin-1").replace("*", "").strip()
            if clean:
                pdf.multi_cell(0, 6, f"- {clean}")

    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 10)
    pdf.cell(90, 10, "____________________________", 0, 0, "L")
    pdf.cell(90, 10, "____________________________", 0, 1, "L")
    pdf.cell(90, 5, "Class Teacher", 0, 0, "L")
    pdf.cell(90, 5, "Principal", 0, 1, "L")

    pdf.output(output_path)
    return output_path


def generate_minimal_report(student: dict, output_path: str):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 15, "Report Card", 0, 1, "C")
    pdf.ln(5)
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 8, f"Name: {student.get('name', 'N/A')}", 0, 1)
    pdf.cell(0, 8, f"Grade: {student.get('grade', 'N/A')}", 0, 1)
    pdf.cell(0, 8, f"Average: {student.get('average', 0):.2f}%", 0, 1)
    pdf.cell(0, 8, f"Class: {student.get('class_name', 'N/A')}", 0, 1)
    pdf.output(output_path)
    return output_path
