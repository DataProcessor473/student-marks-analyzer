"""
fix_bootstrap_seed.py — Make _bootstrap_postgres() seed admin users if empty.
Idempotent. Writes without BOM.
"""
from pathlib import Path
import sys


MAIN = Path(__file__).parent / "backend" / "main.py"

OLD = '''def _bootstrap_postgres():
    """Call right after init_database() to ensure Postgres schema exists."""
    if USE_POSTGRES:
        _create_postgres_tables()'''

NEW = '''def _bootstrap_postgres():
    """Call right after init_database() to ensure Postgres schema exists and admins are seeded."""
    if not USE_POSTGRES:
        return
    _create_postgres_tables()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) AS count FROM users")
            row = cursor.fetchone()
            count = row["count"] if isinstance(row, dict) else row[0]
            if count == 0:
                default_hash = get_password_hash("Admin@123")
                cursor.execute("""
                    INSERT INTO users (username, email, hashed_password, full_name,
                                       role, email_verified, phone_verified, theme, is_active)
                    VALUES (%s, %s, %s, %s, 'admin', 1, 1, 'light', 1)
                """, ("admin", "admin@example.com", default_hash, "Default Admin"))
                backup_hash = get_password_hash("Admin2@123")
                cursor.execute("""
                    INSERT INTO users (username, email, hashed_password, full_name,
                                       role, email_verified, phone_verified, theme, is_active)
                    VALUES (%s, %s, %s, %s, 'admin', 1, 1, 'light', 1)
                """, ("admin2", "admin2@example.com", backup_hash, "Backup Admin"))
                conn.commit()
                print("[OK] Default admins seeded in Postgres")
            else:
                print(f"[OK] Postgres has {count} user(s) - skipping admin seed")
    except Exception as e:
        print(f"[WARN] Failed to seed admins: {e}")'''


def main() -> int:
    print("=" * 60)
    print("  FIX BOOTSTRAP SEED")
    print("=" * 60)

    if not MAIN.exists():
        print(f"  Not found: {MAIN}")
        return 1

    text = MAIN.read_text(encoding="utf-8")

    if "Default admins seeded in Postgres" in text:
        print("  Already applied.")
        return 0

    if OLD not in text:
        print("  ERROR: target block not found")
        return 1

    text = text.replace(OLD, NEW, 1)

    # Write UTF-8 without BOM
    MAIN.write_bytes(text.encode("utf-8"))
    print(f"  Patched {MAIN}")

    import ast
    try:
        ast.parse(text)
        print("  Syntax: OK")
    except SyntaxError as e:
        print(f"  Syntax FAIL: {e}")
        return 1

    print("\n  NEXT")
    print("  git add backend/main.py")
    print('  git commit -m "fix: seed admins in bootstrap_postgres"')
    print("  git push origin main")
    return 0


if __name__ == "__main__":
    sys.exit(main())
