"""Add theme column to users table."""
import sqlite3

conn = sqlite3.connect('student_marks.db')
cur = conn.cursor()

cur.execute('PRAGMA table_info(users)')
cols = [c[1] for c in cur.fetchall()]

if 'theme' not in cols:
    cur.execute("ALTER TABLE users ADD COLUMN theme TEXT DEFAULT 'light'")
    print('✅ Added users.theme')
else:
    print('ℹ️  users.theme already exists')

conn.commit()
conn.close()
