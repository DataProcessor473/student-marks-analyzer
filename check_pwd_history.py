"""Check/create password_history table."""
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()
conn = psycopg2.connect(os.getenv("DATABASE_URL"), cursor_factory=RealDictCursor)
cur = conn.cursor()

cur.execute("SELECT table_name FROM information_schema.tables WHERE table_name='password_history'")
row = cur.fetchone()

if row:
    print("✅ password_history EXISTS")
    cur.execute("SELECT COUNT(*) as c FROM password_history")
    print(f"   Records: {cur.fetchone()['c']}")
else:
    print("❌ password_history MISSING — creating...")
    cur.execute("""
        CREATE TABLE password_history (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("CREATE INDEX idx_pwd_history_user ON password_history(user_id)")
    conn.commit()
    print("✅ Created table")

    cur.execute("SELECT id, hashed_password FROM users")
    users = cur.fetchall()
    for u in users:
        cur.execute(
            "INSERT INTO password_history (user_id, password_hash) VALUES (%s, %s)",
            (u["id"], u["hashed_password"])
        )
    conn.commit()
    print(f"✅ Backfilled {len(users)} hashes")

cur.close()
conn.close()
