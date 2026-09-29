"""
fix_submit_endpoint.py - Rewrite the /assignments/{id}/submit endpoint
so it correctly stores file_url + text answer from student submissions.

Idempotent. Backs up main.py. Syntax-checks before writing.
"""
import ast
import re
import sys
from pathlib import Path

BACKEND = Path(__file__).parent.resolve()
MAIN = BACKEND / "main.py"
UPLOADS = BACKEND / "uploads"


def banner(t):
    print()
    print("=" * 72)
    print("  " + t)
    print("=" * 72)


NEW_ENDPOINT = '''
@app.post("/assignments/{assignment_id}/submit")
async def submit_assignment(
    assignment_id: int,
    file: UploadFile = File(None),
    text_answer: str = Form(""),
    user=Depends(require_role("student", "admin", "teacher")),
):
    """Student submits an assignment (file and/or text answer)."""
    # --- 1. Verify assignment exists ---
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(_q("SELECT id FROM assignments WHERE id=?"), (assignment_id,))
        if not cursor.fetchone():
            raise HTTPException(404, "Assignment not found")

    # --- 2. Find the student id for this user ---
    student_id = None
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(_q("SELECT id FROM students WHERE user_id=?"), (user["id"],))
        row = cursor.fetchone()
        if row:
            student_id = row["id"] if isinstance(row, dict) else row[0]

    # Admin/teacher without a linked student → pick first student (dev convenience)
    if not student_id and user["role"] in ("admin", "teacher"):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM students ORDER BY id LIMIT 1")
            row = cursor.fetchone()
            if row:
                student_id = row["id"] if isinstance(row, dict) else row[0]

    if not student_id:
        raise HTTPException(400, "Your account is not linked to a student record")

    # --- 3. Save uploaded file (if any) ---
    stored_file_url = None
    if file is not None and getattr(file, "filename", None):
        UPLOADS.mkdir(parents=True, exist_ok=True)
        # Sanitize filename
        safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", file.filename)
        # Prefix with assignment + student + timestamp to avoid collisions
        import uuid
        stamp = uuid.uuid4().hex[:8]
        final_name = "a" + str(assignment_id) + "_s" + str(student_id) + "_" + stamp + "_" + safe_name
        dest = UPLOADS / final_name
        contents = await file.read()
        dest.write_bytes(contents)
        # Public URL served by /uploads static mount
        stored_file_url = "/uploads/" + final_name
        print("[SUBMIT] Saved file " + str(dest) + " (" + str(len(contents)) + " bytes)")

    # --- 4. Upsert submission row ---
    now = datetime.now().isoformat()
    status_value = "submitted" if (text_answer or stored_file_url) else "pending"

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Fetch existing submission
        cursor.execute(_q(
            "SELECT id, file_url FROM assignment_submissions "
            "WHERE assignment_id=? AND student_id=?"
        ), (assignment_id, student_id))
        existing = cursor.fetchone()

        if existing:
            # Keep prior file_url if the new submit has no file
            existing_file = existing["file_url"] if isinstance(existing, dict) else existing[1]
            effective_file = stored_file_url if stored_file_url else existing_file
            cursor.execute(_q(
                "UPDATE assignment_submissions "
                "SET status=?, submitted_at=?, feedback=?, file_url=? "
                "WHERE assignment_id=? AND student_id=?"
            ), (status_value, now, text_answer, effective_file, assignment_id, student_id))
        else:
            cursor.execute(_q(
                "INSERT INTO assignment_submissions "
                "(assignment_id, student_id, status, submitted_at, feedback, file_url) "
                "VALUES (?, ?, ?, ?, ?, ?)"
            ), (assignment_id, student_id, status_value, now, text_answer, stored_file_url))

        conn.commit()

    return {
        "message": "Submission saved",
        "student_id": student_id,
        "status": status_value,
        "file_url": stored_file_url,
        "has_text": bool(text_answer),
    }
'''


def find_endpoint_bounds(text):
    """Return (start, end) of the OLD /assignments/{id}/submit endpoint."""
    # Find the decorator line
    deco = '@app.post("/assignments/{assignment_id}/submit")'
    start = text.find(deco)
    if start < 0:
        return None, None

    # The older route /submit/{student_id} also contains this substring? No - it has /submit/{student_id}
    # Confirm we hit the right one: the next non-space chars should be 'async def submit_assignment('
    after = text[start:start + 400]
    if "async def submit_assignment(" not in after:
        return None, None

    # Find the NEXT @app. or def at column 0 (end of this function)
    lines = text.split("\n")
    line_no = text[:start].count("\n")

    end_line = None
    for i in range(line_no + 1, len(lines)):
        s = lines[i]
        # End when another @app decorator or top-level def appears
        if re.match(r"^@app\.", s) or re.match(r"^def ", s):
            end_line = i
            break

    if end_line is None:
        return None, None

    end_offset = sum(len(lines[j]) + 1 for j in range(end_line))
    return start, end_offset


def main():
    print()
    print("#" * 72)
    print("#  FIX /assignments/{id}/submit ENDPOINT")
    print("#  Project: " + str(BACKEND))
    print("#" * 72)

    if not MAIN.exists():
        print("  [ERROR] main.py not found")
        return 1

    text = MAIN.read_text(encoding="utf-8")

    # Idempotency check
    if "Save uploaded file (if any)" in text and "stored_file_url" in text:
        print("  [OK] Endpoint already patched — nothing to do")
        return 0

    start, end = find_endpoint_bounds(text)
    if start is None:
        print("  [ERROR] Could not locate the old submit_assignment endpoint")
        print("  Searching for the decorator...")
        i = text.find('@app.post("/assignments/{assignment_id}/submit")')
        if i >= 0:
            print("  Found at offset " + str(i))
            print(text[i:i+500])
        return 1

    print("  Found old endpoint: offsets " + str(start) + ".." + str(end))
    print("  Replacing with new implementation...")

    new_text = text[:start] + NEW_ENDPOINT.strip() + "\n\n\n" + text[end:]

    # Syntax check
    try:
        ast.parse(new_text)
        print("  [OK] New main.py parses cleanly")
    except SyntaxError as e:
        print("  [FAIL] Syntax error: " + str(e))
        return 1

    # Backup + write
    bak = MAIN.with_suffix(".py.bak")
    bak.write_text(text, encoding="utf-8")
    MAIN.write_text(new_text, encoding="utf-8")
    print("  [OK] main.py updated (backup at " + bak.name + ")")

    # Check imports
    banner("CHECKING IMPORTS")
    needed = [
        ("UploadFile", "from fastapi import"),
        ("File",       "from fastapi import"),
        ("Form",       "from fastapi import"),
    ]
    missing = []
    for name, _ in needed:
        # Look for it in the imports block
        pattern = re.compile(r"from fastapi import[^\n]*\b" + name + r"\b")
        if pattern.search(new_text):
            print("  [OK] " + name + " is imported")
        else:
            print("  [MISSING] " + name)
            missing.append(name)

    if missing:
        print()
        print("  ACTION REQUIRED:")
        print("  Add these to the 'from fastapi import ...' line at the top of main.py:")
        for m in missing:
            print("    " + m)
        print()
        print("  Example:")
        print("    from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form")
    else:
        print("  All required imports present.")

    banner("DONE")
    print()
    print("  Next steps:")
    print("    1. Restart the backend (uvicorn main:app --reload)")
    print("    2. Test: as a student, upload a file to an assignment")
    print("    3. In the admin view, the 'Uploaded file:' link should appear")
    print()
    print("  To rollback: copy main.py.bak over main.py")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())