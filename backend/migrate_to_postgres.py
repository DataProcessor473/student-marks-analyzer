"""
Ensure PostgreSQL has all required columns and tables.
Run: python migrate_postgres.py
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")
if not DATABASE_URL.startswith("postgresql"):
    print("⚠️  DATABASE_URL is not PostgreSQL. Nothing to do.")
    exit(0)

print(f"Connecting to PostgreSQL...")
conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
cur = conn.cursor()

# ============================================================
# 1. USERS table: add theme column
# ============================================================
cur.execute("""
    SELECT column_name FROM information_schema.columns
    WHERE table_name='users' AND column_name='theme'
""")
if not cur.fetchone():
    cur.execute("ALTER TABLE users ADD COLUMN theme TEXT DEFAULT 'light'")
    print("✅ Added users.theme")
else:
    print("ℹ️  users.theme already exists")

# ============================================================
# 2. NOTIFICATION_PREFERENCES table
# ============================================================
cur.execute("""
    SELECT table_name FROM information_schema.tables
    WHERE table_name='notification_preferences'
""")
if not cur.fetchone():
    cur.execute("""
        CREATE TABLE notification_preferences (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL UNIQUE,
            email_on_grade INTEGER DEFAULT 1,
            email_on_attendance INTEGER DEFAULT 1,
            email_on_fee INTEGER DEFAULT 1,
            email_on_assignment INTEGER DEFAULT 1,
            email_on_report INTEGER DEFAULT 0,
            inapp_on_all INTEGER DEFAULT 1,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✅ Created notification_preferences table")
else:
    print("ℹ️  notification_preferences already exists")

# ============================================================
# 3. VERIFY ALL TABLES
# ============================================================
required_tables = [
    "users", "otp_codes", "students", "attendance", "performance_trends",
    "notifications", "notification_preferences", "parent_children",
    "token_blacklist", "login_attempts", "audit_log", "role_history",
    "classes", "email_queue", "exams", "timetable", "assignments",
    "assignment_submissions", "fee_structures", "fee_payments",
    "saved_filters", "backup_logs", "scheduled_reports", "live_events",
]

print("\n=== Table check ===")
missing = []
for t in required_tables:
    cur.execute(f"SELECT table_name FROM information_schema.tables WHERE table_name=%s", (t,))
    if cur.fetchone():
        print(f"  ✅ {t}")
    else:
        print(f"  ❌ {t} (MISSING)")
        missing.append(t)

conn.commit()
cur.close()
conn.close()

if missing:
    print(f"\n⚠️  {len(missing)} tables missing: {missing}")
    print("Run the schema setup in main.py or use SQLAlchemy to create them.")
else:
    print("\n🎉 PostgreSQL schema is complete!")
