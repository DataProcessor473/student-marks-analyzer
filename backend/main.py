from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json
import sqlite3
import os
from contextlib import contextmanager
import hashlib
import re
from enum import Enum

app = FastAPI(
    title="Student Marks Analyzer API",
    description="Advanced API for analyzing student marks with AI-powered insights",
    version="3.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DB_PATH = "student_marks.db"

def init_database():
    """Initialize SQLite database with required tables"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Create students table with all columns
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                marks TEXT NOT NULL,
                subjects TEXT NOT NULL,
                grade TEXT NOT NULL,
                average REAL NOT NULL,
                total_marks REAL NOT NULL,
                timestamp TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                semester TEXT,
                batch_year TEXT,
                department TEXT
            )
        """)

        # Check if columns exist and add them if they don't
        cursor.execute("PRAGMA table_info(students)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'semester' not in columns:
            cursor.execute("ALTER TABLE students ADD COLUMN semester TEXT")
        if 'batch_year' not in columns:
            cursor.execute("ALTER TABLE students ADD COLUMN batch_year TEXT")
        if 'department' not in columns:
            cursor.execute("ALTER TABLE students ADD COLUMN department TEXT")

        # Create attendance table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                date TEXT NOT NULL,
                status TEXT NOT NULL,
                subject TEXT,
                FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE
            )
        """)

        # Create performance_trends table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_trends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                semester TEXT,
                average REAL,
                grade TEXT,
                timestamp TEXT,
                FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE
            )
        """)

        # Create notifications table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                message TEXT,
                type TEXT,
                is_read INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE
            )
        """)

        # Create indexes only after ensuring columns exist
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_student_name ON students(name)")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_student_grade ON students(grade)")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_student_average ON students(average)")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date)")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(is_read)")
        except sqlite3.OperationalError:
            pass

        conn.commit()

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# Initialize database on startup
init_database()

# Enums and Models
class GradeScheme(str, Enum):
    STANDARD = "standard"
    STRICT = "strict"
    LENIENT = "lenient"

class Department(str, Enum):
    COMPUTER_SCIENCE = "Computer Science"
    MATHEMATICS = "Mathematics"
    PHYSICS = "Physics"
    CHEMISTRY = "Chemistry"
    BIOLOGY = "Biology"
    ENGLISH = "English"
    HISTORY = "History"
    OTHER = "Other"

class MarksRequest(BaseModel):
    marks: List[float] = Field(..., description="List of marks for analysis")
    student_name: Optional[str] = Field(None, description="Student name")
    subject_names: Optional[List[str]] = Field(None, description="Subject names")
    passing_threshold: float = Field(40, description="Passing threshold")
    grade_scheme: GradeScheme = Field(GradeScheme.STANDARD, description="Grade scheme")
    semester: Optional[str] = Field(None, description="Semester/term")
    batch_year: Optional[str] = Field(None, description="Batch year")
    department: Optional[Department] = Field(None, description="Department")

    @validator('marks')
    def validate_marks(cls, v):
        if not v:
            raise ValueError("Marks list cannot be empty")
        if any(m < 0 or m > 100 for m in v):
            raise ValueError("Marks must be between 0 and 100")
        return v

class StudentRecord(BaseModel):
    name: str
    marks: List[float]
    subjects: List[str]
    grade: str
    average: float
    total_marks: Optional[float] = None
    timestamp: str
    semester: Optional[str] = None
    batch_year: Optional[str] = None
    department: Optional[str] = None

class AttendanceRecord(BaseModel):
    student_id: int
    date: str
    status: str  # Present, Absent, Late, Excused
    subject: Optional[str] = None

class NotificationCreate(BaseModel):
    student_id: int
    message: str
    type: str  # Warning, Info, Success, Achievement

# Helper Functions
def calculate_statistics(marks: List[float]) -> Dict[str, Any]:
    marks_array = np.array(marks)
    return {
        "total": float(np.sum(marks_array)),
        "average": float(np.mean(marks_array)),
        "highest": float(np.max(marks_array)),
        "lowest": float(np.min(marks_array)),
        "median": float(np.median(marks_array)),
        "std_deviation": float(np.std(marks_array)),
        "range": float(np.max(marks_array) - np.min(marks_array)),
        "variance": float(np.var(marks_array)),
        "quartiles": {
            "q1": float(np.percentile(marks_array, 25)),
            "q2": float(np.percentile(marks_array, 50)),
            "q3": float(np.percentile(marks_array, 75))
        }
    }

def determine_grade(average: float, scheme: str = "standard") -> tuple:
    grade_schemes = {
        "standard": {
            (90, 100): ("A+", 10),
            (80, 89.99): ("A", 9),
            (70, 79.99): ("B", 8),
            (60, 69.99): ("C", 7),
            (50, 59.99): ("D", 6),
            (40, 49.99): ("E", 5),
            (0, 39.99): ("F", 0)
        },
        "strict": {
            (93, 100): ("A+", 10),
            (85, 92.99): ("A", 9),
            (75, 84.99): ("B", 8),
            (65, 74.99): ("C", 7),
            (55, 64.99): ("D", 6),
            (45, 54.99): ("E", 5),
            (0, 44.99): ("F", 0)
        },
        "lenient": {
            (85, 100): ("A+", 10),
            (70, 84.99): ("A", 9),
            (60, 69.99): ("B", 8),
            (50, 59.99): ("C", 7),
            (40, 49.99): ("D", 6),
            (30, 39.99): ("E", 5),
            (0, 29.99): ("F", 0)
        }
    }

    scheme_data = grade_schemes.get(scheme, grade_schemes["standard"])

    for (lower, upper), (grade, points) in scheme_data.items():
        if lower <= average <= upper:
            return grade, points

    return "F", 0

def generate_ai_insights(marks: List[float], average: float, subject_names: List[str]) -> Dict[str, Any]:
    """Generate AI-powered insights and recommendations"""
    insights = {
        "strengths": [],
        "weaknesses": [],
        "recommendations": [],
        "predictions": [],
        "study_tips": []
    }

    # Analyze performance patterns
    marks_array = np.array(marks)

    # Find strong and weak subjects
    for i, mark in enumerate(marks):
        subject = subject_names[i] if i < len(subject_names) else f"Subject {i+1}"
        if mark >= 80:
            insights["strengths"].append({
                "subject": subject,
                "marks": mark,
                "level": "Excellent"
            })
        elif mark < 40:
            insights["weaknesses"].append({
                "subject": subject,
                "marks": mark,
                "level": "Needs Improvement"
            })

    # Generate recommendations based on performance
    if average < 40:
        insights["recommendations"].append({
            "priority": "High",
            "action": "Immediate intervention needed",
            "details": "Consider one-on-one tutoring and personalized learning plan"
        })
        insights["study_tips"].append("Focus on building fundamental concepts")
        insights["study_tips"].append("Practice basic problems daily")
    elif average < 60:
        insights["recommendations"].append({
            "priority": "Medium",
            "action": "Structured study plan",
            "details": "Create a daily study schedule with regular breaks"
        })
        insights["study_tips"].append("Join study groups for collaborative learning")
        insights["study_tips"].append("Use online resources for additional practice")
    elif average < 75:
        insights["recommendations"].append({
            "priority": "Low",
            "action": "Performance enhancement",
            "details": "Focus on weak areas to achieve excellence"
        })
        insights["study_tips"].append("Challenge yourself with advanced problems")
        insights["study_tips"].append("Teach concepts to peers to reinforce learning")
    else:
        insights["recommendations"].append({
            "priority": "Optional",
            "action": "Excellence program",
            "details": "Explore advanced topics and research opportunities"
        })
        insights["study_tips"].append("Consider peer tutoring to help others")
        insights["study_tips"].append("Participate in academic competitions")

    # Performance predictions
    if len(marks) >= 5:
        trend = np.polyfit(range(len(marks)), marks, 1)[0]
        if trend > 0:
            insights["predictions"].append("📈 Showing positive performance trend")
        elif trend < 0:
            insights["predictions"].append("📉 Performance trend declining - needs attention")
        else:
            insights["predictions"].append("➡️ Performance is stable")

    # Calculate improvement potential
    max_possible = 100
    current_total = sum(marks)
    max_total = len(marks) * max_possible
    improvement_potential = ((max_total - current_total) / max_total) * 100

    insights["improvement_potential"] = round(improvement_potential, 2)

    return insights

def detect_anomalies(marks: List[float]) -> List[Dict[str, Any]]:
    """Detect anomalies in marks using statistical methods"""
    anomalies = []
    marks_array = np.array(marks)

    if len(marks_array) < 3:
        return anomalies

    mean = np.mean(marks_array)
    std = np.std(marks_array)

    for i, mark in enumerate(marks):
        # Z-score method
        z_score = (mark - mean) / std if std > 0 else 0
        if abs(z_score) > 2:
            anomalies.append({
                "subject": f"Subject {i+1}",
                "marks": mark,
                "z_score": round(z_score, 2),
                "type": "Exceptionally High" if mark > mean else "Exceptionally Low",
                "suggestion": "Review this mark for possible errors or exceptional performance"
            })

    return anomalies

def calculate_performance_index(marks: List[float]) -> Dict[str, Any]:
    """Calculate comprehensive performance indices"""
    marks_array = np.array(marks)

    return {
        "consistency_score": round(100 - (np.std(marks_array) / np.mean(marks_array) * 100), 2) if np.mean(marks_array) > 0 else 0,
        "improvement_score": 0,  # Will be calculated with historical data
        "difficulty_adjusted_score": round(np.mean(marks_array) * 0.9 + 10, 2),  # Example adjustment
        "percentile_rank": 0,  # Will be calculated with population data
        "grade_points": 0  # Will be calculated with grade scheme
    }

def generate_recommendations(marks: List[float], average: float) -> List[str]:
    recommendations = []

    if average < 40:
        recommendations.append("🔴 Urgent: Consider additional tutoring or personalized learning plans")
        recommendations.append("📚 Focus on building foundational concepts in all subjects")
    elif average < 60:
        recommendations.append("🟡 Need improvement: Consider study groups and more practice")
        recommendations.append("📝 Create a structured study schedule")
    elif average < 75:
        recommendations.append("🟢 Good performance: Focus on weak areas to reach excellence")
        recommendations.append("🎯 Set higher targets for yourself")
    else:
        recommendations.append("🌟 Excellent! Consider helping peers and exploring advanced topics")
        recommendations.append("🏆 Aim for consistent top performance")

    weak_subjects = [i for i, m in enumerate(marks) if m < 40]
    if weak_subjects:
        recommendations.append(f"⚠️ Focus on subjects {', '.join([str(i+1) for i in weak_subjects])} - they need improvement")

    strong_subjects = [i for i, m in enumerate(marks) if m >= 80]
    if strong_subjects:
        recommendations.append(f"💪 Strong in subjects {', '.join([str(i+1) for i in strong_subjects])} - keep it up!")

    # Add smart recommendations based on patterns
    marks_array = np.array(marks)
    if np.std(marks_array) > 20:
        recommendations.append("📊 Your performance varies significantly across subjects. Consider balancing your study time.")

    if np.mean(marks_array) < 50 and np.max(marks_array) >= 80:
        recommendations.append("🎯 You have high potential in some subjects. Apply successful strategies to other subjects.")

    return recommendations

# API Endpoints
@app.get("/")
def home():
    return {
        "message": "Student Marks Analyzer API is running",
        "version": "3.0.0",
        "database": "SQLite",
        "features": [
            "AI-powered insights",
            "Performance predictions",
            "Anomaly detection",
            "Attendance tracking",
            "Notifications system",
            "Batch analysis",
            "Export functionality",
            "Student comparison",
            "Performance trends",
            "Smart recommendations"
        ],
        "endpoints": {
            "/analyze": "POST - Analyze marks with AI insights",
            "/analyze/batch": "POST - Analyze multiple students",
            "/students": "GET - Get all students with pagination",
            "/students/{id}": "GET - Get student by ID",
            "/students/save": "POST - Save student record",
            "/students/update/{id}": "PUT - Update student record",
            "/students/delete/{id}": "DELETE - Delete student record",
            "/students/search": "GET - Search students",
            "/students/filter": "GET - Filter students by criteria",
            "/stats/overall": "GET - Overall statistics",
            "/stats/grade-distribution": "GET - Grade distribution",
            "/stats/subject-analysis": "GET - Subject-wise analysis",
            "/attendance": "POST - Record attendance",
            "/attendance/{student_id}": "GET - Get attendance records",
            "/notifications": "GET - Get notifications",
            "/notifications/mark-read/{id}": "PUT - Mark notification as read",
            "/export/csv": "GET - Export data to CSV",
            "/export/json": "GET - Export data to JSON"
        }
    }

@app.post("/analyze")
def analyze_marks(request: MarksRequest):
    marks = request.marks
    passing_threshold = request.passing_threshold

    # Basic statistics
    stats = calculate_statistics(marks)
    grade, grade_points = determine_grade(stats["average"], request.grade_scheme)

    # Performance metrics
    passed = sum(1 for m in marks if m >= passing_threshold)
    failed = len(marks) - passed

    # Subject-wise analysis
    subject_wise = []
    for i, mark in enumerate(marks):
        subject_name = request.subject_names[i] if request.subject_names and i < len(request.subject_names) else f"Subject {i+1}"
        subject_wise.append({
            "subject": subject_name,
            "marks": mark,
            "status": "Pass" if mark >= passing_threshold else "Fail",
            "performance": "Excellent" if mark >= 80 else "Good" if mark >= 60 else "Average" if mark >= 40 else "Needs Improvement"
        })

    # Performance summary
    performance_summary = {
        "performance_level": "Excellent" if stats["average"] >= 80 else "Good" if stats["average"] >= 60 else "Average" if stats["average"] >= 40 else "Poor",
        "consistency": "High" if stats["std_deviation"] < 15 else "Medium" if stats["std_deviation"] < 30 else "Low",
        "variance": stats["variance"],
        "quartiles": stats["quartiles"]
    }

    # AI-powered insights
    ai_insights = generate_ai_insights(marks, stats["average"], request.subject_names or [])

    # Anomaly detection
    anomalies = detect_anomalies(marks)

    # Performance index
    performance_index = calculate_performance_index(marks)

    # Recommendations
    recommendations = generate_recommendations(marks, stats["average"])

    return {
        "student_name": request.student_name or "Unnamed Student",
        "semester": request.semester,
        "batch_year": request.batch_year,
        "department": request.department,
        "total_marks": stats["total"],
        "average": stats["average"],
        "highest": stats["highest"],
        "lowest": stats["lowest"],
        "median": stats["median"],
        "std_deviation": stats["std_deviation"],
        "variance": stats["variance"],
        "quartiles": stats["quartiles"],
        "passed": passed,
        "failed": failed,
        "pass_percentage": (passed / len(marks)) * 100,
        "grade": grade,
        "grade_points": grade_points,
        "subject_wise": subject_wise,
        "performance_summary": performance_summary,
        "ai_insights": ai_insights,
        "anomalies": anomalies,
        "performance_index": performance_index,
        "recommendations": recommendations,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/analyze/batch")
def analyze_batch(students: List[MarksRequest]):
    """Analyze multiple students at once"""
    results = []
    for student in students:
        result = analyze_marks(student)
        results.append(result)

    # Aggregate statistics
    averages = [r["average"] for r in results]
    grades = [r["grade"] for r in results]

    return {
        "total_students": len(results),
        "average_score": np.mean(averages),
        "highest_score": max(averages),
        "lowest_score": min(averages),
        "grade_distribution": {grade: grades.count(grade) for grade in set(grades)},
        "students": results
    }

@app.post("/students/save")
def save_student(student: StudentRecord):
    try:
        total_marks = student.total_marks if student.total_marks is not None else sum(student.marks)

        with get_db_connection() as conn:
            cursor = conn.cursor()

            marks_json = json.dumps(student.marks)
            subjects_json = json.dumps(student.subjects)

            cursor.execute("""
                INSERT INTO students (name, marks, subjects, grade, average, total_marks, timestamp, semester, batch_year, department)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                student.name,
                marks_json,
                subjects_json,
                student.grade,
                student.average,
                total_marks,
                student.timestamp or datetime.now().isoformat(),
                student.semester,
                student.batch_year,
                student.department
            ))

            student_id = cursor.lastrowid

            # Create achievement notification if grade is A or A+
            if student.grade in ["A", "A+"]:
                cursor.execute("""
                    INSERT INTO notifications (student_id, message, type)
                    VALUES (?, ?, ?)
                """, (
                    student_id,
                    f"🎉 Congratulations! You achieved grade {student.grade} with an average of {student.average:.2f}!",
                    "Achievement"
                ))

            conn.commit()

            return {
                "message": "Student record saved successfully",
                "id": student_id,
                "student": {
                    "id": student_id,
                    "name": student.name,
                    "marks": student.marks,
                    "subjects": student.subjects,
                    "grade": student.grade,
                    "average": student.average,
                    "total_marks": total_marks,
                    "timestamp": student.timestamp,
                    "semester": student.semester,
                    "batch_year": student.batch_year,
                    "department": student.department
                }
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.put("/students/update/{student_id}")
def update_student(student_id: int, student: StudentRecord):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Check if student exists
            cursor.execute("SELECT id FROM students WHERE id = ?", (student_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Student not found")

            total_marks = student.total_marks if student.total_marks is not None else sum(student.marks)
            marks_json = json.dumps(student.marks)
            subjects_json = json.dumps(student.subjects)

            cursor.execute("""
                UPDATE students
                SET name = ?, marks = ?, subjects = ?, grade = ?, average = ?,
                    total_marks = ?, timestamp = ?, semester = ?, batch_year = ?, department = ?
                WHERE id = ?
            """, (
                student.name,
                marks_json,
                subjects_json,
                student.grade,
                student.average,
                total_marks,
                student.timestamp or datetime.now().isoformat(),
                student.semester,
                student.batch_year,
                student.department,
                student_id
            ))

            conn.commit()

            return {
                "message": "Student record updated successfully",
                "id": student_id
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/attendance")
def record_attendance(attendance: AttendanceRecord):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO attendance (student_id, date, status, subject)
                VALUES (?, ?, ?, ?)
            """, (
                attendance.student_id,
                attendance.date,
                attendance.status,
                attendance.subject
            ))

            # Create notification for absence
            if attendance.status in ["Absent", "Late"]:
                cursor.execute("""
                    INSERT INTO notifications (student_id, message, type)
                    VALUES (?, ?, ?)
                """, (
                    attendance.student_id,
                    f"⚠️ You were marked {attendance.status} on {attendance.date}",
                    "Warning"
                ))

            conn.commit()

            return {
                "message": "Attendance recorded successfully",
                "id": cursor.lastrowid
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/attendance/{student_id}")
def get_attendance(student_id: int, start_date: Optional[str] = None, end_date: Optional[str] = None):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM attendance WHERE student_id = ?"
            params = [student_id]

            if start_date:
                query += " AND date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND date <= ?"
                params.append(end_date)

            query += " ORDER BY date DESC"

            cursor.execute(query, params)
            records = [dict(row) for row in cursor.fetchall()]

            # Calculate attendance statistics
            if records:
                total = len(records)
                present = sum(1 for r in records if r["status"] == "Present")
                absent = sum(1 for r in records if r["status"] == "Absent")
                late = sum(1 for r in records if r["status"] == "Late")
                excused = sum(1 for r in records if r["status"] == "Excused")

                attendance_rate = (present / total) * 100 if total > 0 else 0

                return {
                    "student_id": student_id,
                    "total_records": total,
                    "attendance_rate": attendance_rate,
                    "present": present,
                    "absent": absent,
                    "late": late,
                    "excused": excused,
                    "records": records
                }

            return {
                "student_id": student_id,
                "total_records": 0,
                "attendance_rate": 0,
                "records": []
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/notifications")
def get_notifications(student_id: Optional[int] = None, unread_only: bool = False):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM notifications"
            params = []

            conditions = []
            if student_id:
                conditions.append("student_id = ?")
                params.append(student_id)
            if unread_only:
                conditions.append("is_read = 0")

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY created_at DESC"

            cursor.execute(query, params)
            notifications = [dict(row) for row in cursor.fetchall()]

            return {
                "count": len(notifications),
                "notifications": notifications
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.put("/notifications/mark-read/{notification_id}")
def mark_notification_read(notification_id: int):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("UPDATE notifications SET is_read = 1 WHERE id = ?", (notification_id,))
            conn.commit()

            return {
                "message": "Notification marked as read",
                "id": notification_id
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/students")
def get_all_students(limit: Optional[int] = 100, offset: Optional[int] = 0):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) as count FROM students")
            total_count = cursor.fetchone()["count"]

            cursor.execute("""
                SELECT * FROM students
                ORDER BY id DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))

            students = []
            for row in cursor.fetchall():
                student = dict(row)
                student["marks"] = json.loads(student["marks"])
                student["subjects"] = json.loads(student["subjects"])
                students.append(student)

            return {
                "count": total_count,
                "limit": limit,
                "offset": offset,
                "students": students
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/students/filter")
def filter_students(
    grade: Optional[str] = None,
    semester: Optional[str] = None,
    batch_year: Optional[str] = None,
    department: Optional[str] = None,
    min_average: Optional[float] = None,
    max_average: Optional[float] = None
):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM students WHERE 1=1"
            params = []

            if grade:
                query += " AND grade = ?"
                params.append(grade)
            if semester:
                query += " AND semester = ?"
                params.append(semester)
            if batch_year:
                query += " AND batch_year = ?"
                params.append(batch_year)
            if department:
                query += " AND department = ?"
                params.append(department)
            if min_average is not None:
                query += " AND average >= ?"
                params.append(min_average)
            if max_average is not None:
                query += " AND average <= ?"
                params.append(max_average)

            query += " ORDER BY average DESC"

            cursor.execute(query, params)
            students = []
            for row in cursor.fetchall():
                student = dict(row)
                student["marks"] = json.loads(student["marks"])
                student["subjects"] = json.loads(student["subjects"])
                students.append(student)

            return {
                "count": len(students),
                "filters": {
                    "grade": grade,
                    "semester": semester,
                    "batch_year": batch_year,
                    "department": department,
                    "min_average": min_average,
                    "max_average": max_average
                },
                "students": students
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/students/{student_id}")
def get_student_by_id(student_id: int):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
            row = cursor.fetchone()

            if not row:
                raise HTTPException(status_code=404, detail="Student not found")

            student = dict(row)
            student["marks"] = json.loads(student["marks"])
            student["subjects"] = json.loads(student["subjects"])
            return student
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.delete("/students/delete/{student_id}")
def delete_student(student_id: int):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM students WHERE id = ?", (student_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Student not found")

            # Delete related records
            cursor.execute("DELETE FROM attendance WHERE student_id = ?", (student_id,))
            cursor.execute("DELETE FROM notifications WHERE student_id = ?", (student_id,))
            cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))

            conn.commit()

            return {
                "message": "Student record and related data deleted successfully",
                "id": student_id
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/students/search")
def search_students(
    name: str,
    exact_match: bool = False,
    limit: int = 50
):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            if exact_match:
                query = "SELECT * FROM students WHERE name = ?"
                params = [name]
            else:
                query = "SELECT * FROM students WHERE name LIKE ?"
                params = [f"%{name}%"]

            query += " LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            students = []
            for row in cursor.fetchall():
                student = dict(row)
                student["marks"] = json.loads(student["marks"])
                student["subjects"] = json.loads(student["subjects"])
                students.append(student)

            return {
                "count": len(students),
                "search_term": name,
                "exact_match": exact_match,
                "students": students
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/stats/overall")
def overall_statistics():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM students")
            rows = cursor.fetchall()

            if not rows:
                return {"message": "No students data available"}

            students = []
            for row in rows:
                student = dict(row)
                student["marks"] = json.loads(student["marks"])
                students.append(student)

            averages = [s["average"] for s in students]
            grades = [s["grade"] for s in students]
            total_marks = [s["total_marks"] for s in students]

            grade_distribution = {}
            for grade in grades:
                grade_distribution[grade] = grade_distribution.get(grade, 0) + 1

            # Department statistics
            dept_stats = {}
            for student in students:
                dept = student.get("department", "Unknown")
                if dept not in dept_stats:
                    dept_stats[dept] = {"count": 0, "total_average": 0, "grades": []}
                dept_stats[dept]["count"] += 1
                dept_stats[dept]["total_average"] += student["average"]
                dept_stats[dept]["grades"].append(student["grade"])

            for dept in dept_stats:
                dept_stats[dept]["average"] = dept_stats[dept]["total_average"] / dept_stats[dept]["count"]
                dept_stats[dept]["grade_distribution"] = {
                    grade: dept_stats[dept]["grades"].count(grade)
                    for grade in set(dept_stats[dept]["grades"])
                }
                del dept_stats[dept]["total_average"]
                del dept_stats[dept]["grades"]

            # Subject statistics
            subject_stats = {}
            for student in students:
                for i, subject in enumerate(student["subjects"]):
                    if subject not in subject_stats:
                        subject_stats[subject] = {"marks": [], "count": 0}
                    subject_stats[subject]["marks"].append(student["marks"][i])
                    subject_stats[subject]["count"] += 1

            subject_averages = {}
            for subject, data in subject_stats.items():
                subject_averages[subject] = {
                    "average": np.mean(data["marks"]),
                    "highest": max(data["marks"]),
                    "lowest": min(data["marks"]),
                    "std_dev": np.std(data["marks"]),
                    "count": data["count"]
                }

            return {
                "total_students": len(students),
                "average_of_averages": float(np.mean(averages)),
                "median_average": float(np.median(averages)),
                "highest_average": float(max(averages)),
                "lowest_average": float(min(averages)),
                "std_dev_averages": float(np.std(averages)),
                "average_total_marks": float(np.mean(total_marks)),
                "grade_distribution": grade_distribution,
                "pass_rate": sum(1 for s in students if s["grade"] != "F") / len(students) * 100,
                "distinction_rate": sum(1 for s in students if s["grade"] in ["A", "A+"]) / len(students) * 100,
                "department_statistics": dept_stats,
                "subject_statistics": subject_averages,
                "top_performers": sorted(students, key=lambda x: x["average"], reverse=True)[:5]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/stats/grade-distribution")
def grade_distribution():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT grade, COUNT(*) as count, AVG(average) as avg_score,
                       MIN(average) as min_score, MAX(average) as max_score
                FROM students
                GROUP BY grade
                ORDER BY grade
            """)

            results = cursor.fetchall()
            return {
                "distribution": [dict(row) for row in results]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/stats/subject-analysis")
def subject_analysis():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT marks FROM students")
            rows = cursor.fetchall()

            if not rows:
                return {"message": "No data available"}

            all_marks = []
            for row in rows:
                marks = json.loads(row["marks"])
                all_marks.append(marks)

            if not all_marks:
                return {"message": "No marks data available"}

            # Analyze subject performance
            num_subjects = len(all_marks[0])
            subject_data = []

            for i in range(num_subjects):
                subject_marks = [marks[i] for marks in all_marks if i < len(marks)]
                subject_data.append({
                    "subject": f"Subject {i+1}",
                    "average": np.mean(subject_marks),
                    "highest": max(subject_marks),
                    "lowest": min(subject_marks),
                    "std_dev": np.std(subject_marks),
                    "pass_rate": sum(1 for m in subject_marks if m >= 40) / len(subject_marks) * 100
                })

            # Find hardest and easiest subjects
            hardest = min(subject_data, key=lambda x: x["average"])
            easiest = max(subject_data, key=lambda x: x["average"])

            return {
                "subject_analysis": subject_data,
                "hardest_subject": hardest,
                "easiest_subject": easiest,
                "overall_subject_average": np.mean([s["average"] for s in subject_data])
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/export/csv")
def export_csv():
    """Export all student data as CSV"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM students ORDER BY id")
            rows = cursor.fetchall()

            if not rows:
                return {"message": "No data to export"}

            data = []
            for row in rows:
                student = dict(row)
                student["marks"] = json.loads(student["marks"])
                student["subjects"] = json.loads(student["subjects"])
                # Flatten the data
                student["marks_str"] = ", ".join(map(str, student["marks"]))
                student["subjects_str"] = ", ".join(student["subjects"])
                del student["marks"]
                del student["subjects"]
                data.append(student)

            df = pd.DataFrame(data)
            csv_data = df.to_csv(index=False)

            return Response(
                content=csv_data,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=students_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export error: {str(e)}")

@app.get("/health")
def health_check():
    """Health check endpoint"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            db_status = "healthy"
    except:
        db_status = "unhealthy"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
