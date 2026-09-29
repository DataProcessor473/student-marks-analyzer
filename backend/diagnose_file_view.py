"""
diagnose_file_view.py - Trace why submitted files don't show in the admin view.

Checks:
  1. Does assignment_submissions have file-related columns?
  2. Do any rows actually have a file URL stored?
  3. What does the submissions API return for a submission?
  4. Does the frontend have the file-display block in the grading expander?
"""
import sqlite3
import json
from pathlib import Path

BACKEND = Path(__file__).parent.resolve()
DB = BACKEND / "student_marks.db"
APP = BACKEND.parent / "frontend" / "app.py"


def banner(t):
    print()
    print("=" * 72)
    print("  " + t)
    print("=" * 72)


# ------------------------------------------------------------------
# 1. Schema of assignment_submissions
# ------------------------------------------------------------------

banner("1. assignment_submissions SCHEMA")

conn = sqlite3.connect(str(DB))
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='assignment_submissions'")
row = cur.fetchone()
if row:
    print(row["sql"])
else:
    print("  [ERROR] table does not exist")

print()
cur.execute("PRAGMA table_info(assignment_submissions)")
cols = [r["name"] for r in cur.fetchall()]
print("  Columns (" + str(len(cols)) + "): " + ", ".join(cols))

# Which columns look file-related?
file_cols = [c for c in cols if "file" in c.lower() or "url" in c.lower() or "path" in c.lower()]
print()
print("  File-related columns: " + (", ".join(file_cols) if file_cols else "(NONE!)"))


# ------------------------------------------------------------------
# 2. Sample rows
# ------------------------------------------------------------------

banner("2. SAMPLE SUBMISSIONS")

cur.execute("SELECT * FROM assignment_submissions ORDER BY id DESC LIMIT 5")
rows = [dict(r) for r in cur.fetchall()]

if not rows:
    print("  No submissions in DB")
else:
    for r in rows:
        print("  --- id " + str(r.get("id")) + " ---")
        for k, v in r.items():
            if v is None or v == "":
                continue
            s = str(v)
            if len(s) > 80:
                s = s[:77] + "..."
            print("    " + k + ": " + s)
        print()


# ------------------------------------------------------------------
# 3. Check for a real submission with a file
# ------------------------------------------------------------------

banner("3. SUBMISSIONS WITH FILE URL")

if not file_cols:
    print("  [CRITICAL] No file-related column exists in the table.")
    print("  The upload endpoint cannot store a file location.")
    print("  -> Fix: add a column like file_url or file_path.")
else:
    # Try each file col
    for col in file_cols:
        cur.execute(
            "SELECT id, " + col + " FROM assignment_submissions "
            "WHERE " + col + " IS NOT NULL AND " + col + " != '' "
            "ORDER BY id DESC LIMIT 5"
        )
        hits = cur.fetchall()
        print("  Column " + col + ": " + str(len(hits)) + " row(s) with a value")
        for h in hits:
            print("    id=" + str(h["id"]) + "  " + col + "=" + str(h[col]))


# ------------------------------------------------------------------
# 4. Frontend - does the file-display block exist?
# ------------------------------------------------------------------

banner("4. FRONTEND FILE-DISPLAY BLOCK")

if not APP.exists():
    print("  [ERROR] app.py not found at " + str(APP))
else:
    text = APP.read_text(encoding="utf-8")

    checks = [
        ("Uploaded file: link",        "Uploaded file:"),
        ("file_url reference",         "file_url"),
        ("file_path reference",        "file_path"),
        ("st.image inline preview",    "st.image("),
        ("API_URL concatenation",      "API_URL.rstrip"),
    ]
    for label, needle in checks:
        count = text.count(needle)
        mark = "[OK]  " if count > 0 else "[MISS]"
        print("  " + mark + " " + label + "  (occurrences: " + str(count) + ")")

    # Show the actual grading expander block
    print()
    print("  --- Grading expander source ---")
    for marker in ["with st.expander(_name", "with st.expander(name"]:
        i = text.find(marker)
        if i >= 0:
            print(text[i:i+900])
            break
    else:
        print("  (grading expander not found)")


# ------------------------------------------------------------------
# 5. Backend upload endpoint - does it save the file path?
# ------------------------------------------------------------------

banner("5. BACKEND UPLOAD ENDPOINT")

MAIN = BACKEND / "main.py"
if not MAIN.exists():
    print("  [ERROR] main.py not found")
else:
    t = MAIN.read_text(encoding="utf-8")

    # Find the submission upload handler
    for marker in ["def submit_assignment", "@app.post(\"/assignments/", "async def submit_"]:
        i = t.find(marker)
        if i >= 0:
            print("  Found marker: " + repr(marker) + " at offset " + str(i))
            print()
            print(t[i:i+1500])
            break
    else:
        print("  No upload/submit endpoint found by common names")

    # What columns does the INSERT write to?
    print()
    print("  --- INSERT INTO assignment_submissions statements ---")
    offset = 0
    while True:
        i = t.find("INSERT INTO assignment_submissions", offset)
        if i < 0:
            break
        snippet = t[i:i+300].split(")")[0] + ")"
        print(snippet)
        print()
        offset = i + 40


conn.close()
print()
print("=" * 72)
print("  DONE - paste this whole output")
print("=" * 72)