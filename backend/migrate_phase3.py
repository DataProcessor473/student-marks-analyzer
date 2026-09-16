"""
Phase 3 Database Migration
Adds all new tables and columns for Phase 3 features.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "student_marks.db")


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    print("=" * 60)
    print("  Phase 3 Database Migration")
    print("=" * 60)

    # --------------------------------------------------------
    # 1. Student photos (add columns to students)
    # --------------------------------------------------------
    cur.execute("PRAGMA table_info(students)")
    cols = [c[1] for c in cur.fetchall()]

    if "photo_url" not in cols:
        cur.execute("ALTER TABLE students ADD COLUMN photo_url TEXT")
        print("✅ Added students.photo_url")

    if "email" not in cols:
        cur.execute("ALTER TABLE students ADD COLUMN email TEXT")
        print("✅ Added students.email")

    if "phone" not in cols:
        cur.execute("ALTER TABLE students ADD COLUMN phone TEXT")
        print("✅ Added students.phone")

    if "date_of_birth" not in cols:
        cur.execute("ALTER TABLE students ADD COLUMN date_of_birth TEXT")
        print("✅ Added students.date_of_birth")

    if "address" not in cols:
        cur.execute("ALTER TABLE students ADD COLUMN address TEXT")
        print("✅ Added students.address")

    # --------------------------------------------------------
    # 2. Exams / Timetable
    # --------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            class_name TEXT,
            subject TEXT,
            exam_date TEXT NOT NULL,
            start_time TEXT,
            end_time TEXT,
            total_marks INTEGER DEFAULT 100,
            room TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✅ exams table ready")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS timetable (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_name TEXT NOT NULL,
            day_of_week TEXT NOT NULL,
            period INTEGER,
            subject TEXT NOT NULL,
            teacher_name TEXT,
            room TEXT,
            start_time TEXT,
            end_time TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✅ timetable table ready")

    # --------------------------------------------------------
    # 3. Assignments
    # --------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            class_name TEXT,
            subject TEXT,
            due_date TEXT NOT NULL,
            total_marks INTEGER DEFAULT 100,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✅ assignments table ready")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS assignment_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assignment_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            submitted_at TEXT,
            status TEXT DEFAULT 'pending',
            marks_obtained REAL,
            feedback TEXT,
            file_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(assignment_id, student_id),
            FOREIGN KEY (assignment_id) REFERENCES assignments(id) ON DELETE CASCADE,
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
        )
    """)
    print("✅ assignment_submissions table ready")

    # --------------------------------------------------------
    # 4. Fee Management
    # --------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS fee_structures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_name TEXT NOT NULL,
            fee_type TEXT NOT NULL,
            amount REAL NOT NULL,
            frequency TEXT DEFAULT 'monthly',
            academic_year TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✅ fee_structures table ready")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS fee_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            fee_type TEXT NOT NULL,
            amount REAL NOT NULL,
            payment_date TEXT NOT NULL,
            payment_method TEXT DEFAULT 'cash',
            transaction_id TEXT,
            status TEXT DEFAULT 'paid',
            due_date TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
        )
    """)
    print("✅ fee_payments table ready")

    # --------------------------------------------------------
    # 5. Saved Filters
    # --------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS saved_filters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            entity TEXT NOT NULL,
            filter_json TEXT NOT NULL,
            is_shared INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    print("✅ saved_filters table ready")

    # --------------------------------------------------------
    # 6. Backup logs
    # --------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS backup_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            size_bytes INTEGER,
            backup_type TEXT DEFAULT 'manual',
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✅ backup_logs table ready")

    # --------------------------------------------------------
    # 7. Scheduled report logs
    # --------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS scheduled_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_type TEXT NOT NULL,
            recipients TEXT NOT NULL,
            schedule TEXT NOT NULL,
            last_sent TIMESTAMP,
            enabled INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✅ scheduled_reports table ready")

    # --------------------------------------------------------
    # 8. Real-time notifications (for websocket)
    # --------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS live_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            event_type TEXT NOT NULL,
            payload TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✅ live_events table ready")

    # --------------------------------------------------------
    # 9. Create indexes
    # --------------------------------------------------------
    for idx in [
        "CREATE INDEX IF NOT EXISTS idx_exams_date ON exams(exam_date)",
        "CREATE INDEX IF NOT EXISTS idx_exams_class ON exams(class_name)",
        "CREATE INDEX IF NOT EXISTS idx_timetable_class ON timetable(class_name)",
        "CREATE INDEX IF NOT EXISTS idx_assignments_due ON assignments(due_date)",
        "CREATE INDEX IF NOT EXISTS idx_submissions_student ON assignment_submissions(student_id)",
        "CREATE INDEX IF NOT EXISTS idx_fee_payments_student ON fee_payments(student_id)",
        "CREATE INDEX IF NOT EXISTS idx_saved_filters_user ON saved_filters(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_live_events_user ON live_events(user_id)",
    ]:
        try:
            cur.execute(idx)
        except sqlite3.OperationalError:
            pass

    print("✅ Indexes created")

    conn.commit()
    conn.close()
    print("=" * 60)
    print("  ✅ Phase 3 migration complete!")
    print("=" * 60)


if __name__ == "__main__":
    migrate()
