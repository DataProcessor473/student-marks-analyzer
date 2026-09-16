from fpdf import FPDF
from datetime import datetime
import os

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

GRADE_COLORS = {
    "A+": (16, 185, 129),
    "A": (52, 211, 153),
    "B": (251, 191, 36),
    "C": (245, 158, 11),
    "D": (249, 115, 22),
    "E": (239, 68, 68),
    "F": (220, 38, 38),
}


class ReportCardPDF(FPDF):
    def __init__(self, student_name="Student"):
        super().__init__()
        self.student_name = student_name
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        self.set_fill_color(102, 126, 234)
        self.rect(0, 0, 210, 35, 'F')

        self.set_text_color(255, 255, 255)
        self.set_font('Helvetica', 'B', 22)
        self.set_y(10)
        self.cell(0, 10, 'Student Marks Analyzer Pro', 0, 1, 'C')

        self.set_font('Helvetica', '', 11)
        self.cell(0, 5, 'Academic Performance Report', 0, 1, 'C')

        self.set_text_color(0, 0, 0)
        self.ln(12)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Generated on {datetime.now().strftime("%Y-%m-%d %H:%M")}  |  Page {self.page_no()}', 0, 0, 'C')


def generate_report_card(student: dict, output_path: str):
    pdf = ReportCardPDF(student.get("name", "Student"))
    pdf.add_page()

    # Student Info
    pdf.set_font('Helvetica', 'B', 13)
    pdf.set_fill_color(240, 242, 246)
    pdf.cell(0, 8, '  Student Information', 0, 1, 'L', True)
    pdf.ln(2)

    pdf.set_font('Helvetica', '', 11)
    info = [
        ("Name:", student.get("name", "N/A")),
        ("Student ID:", str(student.get("id", "N/A"))),
        ("Semester:", student.get("semester") or "N/A"),
        ("Department:", student.get("department") or "N/A"),
        ("Batch Year:", student.get("batch_year") or "N/A"),
    ]
    for label, value in info:
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(45, 7, label, 0, 0)
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(0, 7, str(value), 0, 1)

    pdf.ln(5)

    # Performance Summary
    pdf.set_font('Helvetica', 'B', 13)
    pdf.set_fill_color(240, 242, 246)
    pdf.cell(0, 8, '  Performance Summary', 0, 1, 'L', True)
    pdf.ln(2)

    grade = student.get("grade", "F")
    gc = GRADE_COLORS.get(grade, (128, 128, 128))

    pdf.set_fill_color(*gc)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Helvetica', 'B', 24)
    pdf.cell(40, 20, grade, 1, 0, 'C', True)
    pdf.set_text_color(0, 0, 0)

    pdf.set_xy(55, pdf.get_y())
    pdf.set_font('Helvetica', '', 10)

    stats = [
        f"Average: {student.get('average', 0):.2f}%",
        f"Total Marks: {student.get('total_marks', 0):.0f}",
        f"Subjects: {len(student.get('marks', []))}",
    ]
    start_y = pdf.get_y()
    for i, s in enumerate(stats):
        pdf.set_xy(55, start_y + (i * 6))
        pdf.cell(0, 6, s, 0, 1)

    pdf.set_y(start_y + 25)

    # Subject-wise Table
    pdf.set_font('Helvetica', 'B', 13)
    pdf.set_fill_color(240, 242, 246)
    pdf.cell(0, 8, '  Subject-wise Performance', 0, 1, 'L', True)
    pdf.ln(2)

    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_fill_color(102, 126, 234)
    pdf.set_text_color(255, 255, 255)

    pdf.cell(15, 8, '#', 1, 0, 'C', True)
    pdf.cell(85, 8, 'Subject', 1, 0, 'L', True)
    pdf.cell(25, 8, 'Marks', 1, 0, 'C', True)
    pdf.cell(35, 8, 'Status', 1, 0, 'C', True)
    pdf.cell(30, 8, 'Grade', 1, 1, 'C', True)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Helvetica', '', 10)

    marks = student.get("marks", [])
    subjects = student.get("subjects", [])

    for i, (subj, mark) in enumerate(zip(subjects, marks)):
        fill = (i % 2 == 0)
        if fill:
            pdf.set_fill_color(249, 250, 251)

        pdf.cell(15, 8, str(i + 1), 1, 0, 'C', fill)
        pdf.cell(85, 8, str(subj)[:40], 1, 0, 'L', fill)
        pdf.cell(25, 8, f"{mark:.0f}", 1, 0, 'C', fill)
        pdf.cell(35, 8, "Pass" if mark >= 40 else "Fail", 1, 0, 'C', fill)

        if mark >= 90:
            sg = "A+"
        elif mark >= 80:
            sg = "A"
        elif mark >= 70:
            sg = "B"
        elif mark >= 60:
            sg = "C"
        elif mark >= 50:
            sg = "D"
        elif mark >= 40:
            sg = "E"
        else:
            sg = "F"
        pdf.cell(30, 8, sg, 1, 1, 'C', fill)

    pdf.ln(8)

    # Recommendations
    recs = student.get("recommendations", [])
    if recs:
        pdf.set_font('Helvetica', 'B', 13)
        pdf.set_fill_color(240, 242, 246)
        pdf.cell(0, 8, '  Recommendations', 0, 1, 'L', True)
        pdf.ln(2)

        pdf.set_font('Helvetica', '', 10)
        for rec in recs[:6]:
            clean = rec.encode('latin-1', 'ignore').decode('latin-1').replace('*', '').strip()
            # Remove emoji and non-ASCII
            clean = clean.encode('ascii', 'ignore').decode('ascii').strip()
            if clean:
                pdf.set_x(pdf.l_margin)
                try:
                    pdf.multi_cell(0, 6, f"- {clean}")
                except Exception:
                    # Truncate if still failing
                    short = clean[:80]
                    pdf.set_x(pdf.l_margin)
                    pdf.multi_cell(0, 6, f"- {short}...")
        pdf.ln(3)

    # Signatures
    pdf.ln(5)
    pdf.set_font('Helvetica', 'I', 10)
    pdf.cell(90, 10, '____________________________', 0, 0, 'L')
    pdf.cell(90, 10, '____________________________', 0, 1, 'L')
    pdf.cell(90, 5, 'Class Teacher', 0, 0, 'L')
    pdf.cell(90, 5, 'Principal', 0, 1, 'L')

    pdf.output(output_path)
    return output_path
