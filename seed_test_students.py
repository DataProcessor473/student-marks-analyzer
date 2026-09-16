"""Add 10 test students with varied marks for ML training."""
import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB = Path(__file__).parent / "backend" / "student_marks.db"

students = [
    ("Aarav Sharma",   [85, 90, 78, 82, 88], "A"),
    ("Priya Patel",    [92, 95, 88, 90, 94], "A+"),
    ("Rohan Kumar",    [65, 70, 58, 62, 68], "B"),
    ("Ananya Singh",   [45, 38, 42, 50, 40], "D"),
    ("Vikram Reddy",   [78, 82, 75, 80, 79], "B"),
    ("Diya Mehta",     [35, 40, 32, 38, 45], "E"),
    ("Arjun Nair",     [88, 92, 85, 90, 87], "A"),
    ("Kavya Iyer",     [72, 68, 75, 70, 73], "B"),
    ("Karan Desai",    [55, 48, 62, 58, 52], "C"),
    ("Sneha Ghosh",    [95, 92, 98, 94, 96], "A+"),
]

subjects = ["Math", "Science", "English", "History", "Computer"]

conn = sqlite3.connect(str(DB))
cur = conn.cursor()

cur.execute("SELECT COUNT(*) FROM students")
existing = cur.fetchone()[0]

if existing > 0:
    print(f"⚠️  {existing} students already exist.")
    ans = input("Add 10 more anyway? (y/n): ").strip().lower()
    if ans != "y":
        print("Aborted.")
        conn.close()
        exit()

for name, marks, grade in students:
    avg = sum(marks) / len(marks)
    cur.execute("""
        INSERT INTO students (name, marks, subjects, grade, average, total_marks, timestamp, semester, department, class_name)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        name,
        json.dumps(marks),
        json.dumps(subjects),
        grade,
        avg,
        sum(marks),
        datetime.now().isoformat(),
        "Fall 2024",
        "Computer Science",
        "CS-A",
    ))

conn.commit()
cur.execute("SELECT COUNT(*) FROM students")
print(f"✅ Total students: {cur.fetchone()[0]}")
conn.close()
