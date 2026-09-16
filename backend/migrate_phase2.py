import sqlite3

conn = sqlite3.connect("student_marks.db")
cur = conn.cursor()

print("=== Adding missing columns ===")

# Users table
cur.execute("PRAGMA table_info(users)")
cols = [c[1] for c in cur.fetchall()]

user_migrations = {
    "twofa_enabled": "INTEGER DEFAULT 0",
    "twofa_secret": "TEXT",
    "language": "TEXT DEFAULT 'en'",
}
for col, ctype in user_migrations.items():
    if col not in cols:
        cur.execute(f"ALTER TABLE users ADD COLUMN {col} {ctype}")
        print(f"  ✅ Added users.{col}")
    else:
        print(f"  ℹ️  users.{col} already exists")

# Students table
cur.execute("PRAGMA table_info(students)")
cols = [c[1] for c in cur.fetchall()]

if "class_name" not in cols:
    cur.execute("ALTER TABLE students ADD COLUMN class_name TEXT")
    print("  ✅ Added students.class_name")
else:
    print("  ℹ️  students.class_name already exists")

# Create new tables
cur.execute("""
    CREATE TABLE IF NOT EXISTS classes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        department TEXT,
        teacher_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
print("  ✅ classes table ready")

cur.execute("""
    CREATE TABLE IF NOT EXISTS email_queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        to_email TEXT NOT NULL,
        subject TEXT NOT NULL,
        html_body TEXT NOT NULL,
        sent INTEGER DEFAULT 0,
        attempts INTEGER DEFAULT 0,
        error TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
print("  ✅ email_queue table ready")

# Add email_sent to notifications
cur.execute("PRAGMA table_info(notifications)")
cols = [c[1] for c in cur.fetchall()]
if "email_sent" not in cols:
    cur.execute("ALTER TABLE notifications ADD COLUMN email_sent INTEGER DEFAULT 0")
    print("  ✅ Added notifications.email_sent")
if "user_id" not in cols:
    cur.execute("ALTER TABLE notifications ADD COLUMN user_id INTEGER")
    print("  ✅ Added notifications.user_id")

# Indexes
for idx in [
    "CREATE INDEX IF NOT EXISTS idx_student_class ON students(class_name)",
    "CREATE INDEX IF NOT EXISTS idx_notif_user ON notifications(user_id)",
]:
    try:
        cur.execute(idx)
    except sqlite3.OperationalError:
        pass

conn.commit()
conn.close()
print("\n✅ Migration complete!")