import sqlite3
import json

DB_PATH = "student_marks.db"

def migrate_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if columns exist and add them
    cursor.execute("PRAGMA table_info(students)")
    columns = [column[1] for column in cursor.fetchall()]

    if 'semester' not in columns:
        cursor.execute("ALTER TABLE students ADD COLUMN semester TEXT")
    if 'batch_year' not in columns:
        cursor.execute("ALTER TABLE students ADD COLUMN batch_year TEXT")
    if 'department' not in columns:
        cursor.execute("ALTER TABLE students ADD COLUMN department TEXT")

    conn.commit()
    conn.close()
    print("Database migration completed successfully!")

if __name__ == "__main__":
    migrate_database()
