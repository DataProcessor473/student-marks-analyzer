"""Sync SQLite data → PostgreSQL. Safe to re-run."""
import os
import sqlite3
from pathlib import Path
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

SQLITE_DB = Path(__file__).parent / "backend" / "student_marks.db"
DATABASE_URL = os.getenv("DATABASE_URL", "")

if not DATABASE_URL.startswith("postgresql"):
    print("❌ DATABASE_URL not PostgreSQL")
    exit(1)

print(f"SQLite:     {SQLITE_DB}")
print(f"PostgreSQL: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'ok'}")
print()

pg = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
pg_cur = pg.cursor()

sq = sqlite3.connect(str(SQLITE_DB))
sq.row_factory = sqlite3.Row
sq_cur = sq.cursor()

sq_cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
tables = [r["name"] for r in sq_cur.fetchall()]

print(f"=== Syncing {len(tables)} tables ===\n")

for table in tables:
    try:
        sq_cur.execute(f"SELECT * FROM {table}")
        rows = [dict(r) for r in sq_cur.fetchall()]
        if not rows:
            print(f"  ⏭️  {table}: empty in SQLite")
            continue

        pg_cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name=%s
        """, (table,))
        pg_cols = {r["column_name"] for r in pg_cur.fetchall()}
        if not pg_cols:
            print(f"  ⚠️  {table}: not in PostgreSQL")
            continue

        common = [c for c in rows[0].keys() if c in pg_cols]
        if not common:
            continue

        pg_cur.execute(f'SELECT COUNT(*) as c FROM "{table}"')
        existing = pg_cur.fetchone()["c"]

        if existing >= len(rows):
            print(f"  ℹ️  {table}: PG has {existing} >= SQLite {len(rows)} (skip)")
            continue

        cols_q = ", ".join(f'"{c}"' for c in common)
        ph = ", ".join(["%s"] * len(common))
        insert_sql = f'INSERT INTO "{table}" ({cols_q}) VALUES ({ph}) ON CONFLICT DO NOTHING'

        inserted = 0
        failed = 0
        for row in rows:
            try:
                pg_cur.execute(insert_sql, tuple(row[c] for c in common))
                inserted += 1
            except Exception:
                failed += 1

        pg.commit()
        print(f"  ✅ {table}: {existing} → {existing + inserted}" + (f" ({failed} failed)" if failed else ""))
    except Exception as e:
        pg.rollback()
        print(f"  ❌ {table}: {str(e)[:80]}")

# Verify
print("\n=== Final counts ===")
print(f"  {'Table':<28} {'SQLite':>8} {'PG':>8}")
print(f"  {'-'*28} {'-'*8} {'-'*8}")
for table in tables:
    try:
        sq_cur.execute(f"SELECT COUNT(*) as c FROM {table}")
        sq_c = sq_cur.fetchone()["c"]
        pg_cur.execute(f'SELECT COUNT(*) as c FROM "{table}"')
        pg_c = pg_cur.fetchone()["c"]
        mark = "✅" if pg_c >= sq_c else "⚠️"
        print(f"  {mark} {table:<26} {sq_c:>8} {pg_c:>8}")
    except Exception:
        pass

pg_cur.close(); pg.close()
sq_cur.close(); sq.close()
print("\n🎉 Sync done!")
