"""
cleanup_submit.py - Remove duplicate submit endpoints, keep only the new one,
add missing 'Form' import, syntax-check.
"""
import ast
import re
import sys
from pathlib import Path

BACKEND = Path(__file__).parent.resolve()
MAIN = BACKEND / "main.py"


def banner(t):
    print()
    print("=" * 72)
    print("  " + t)
    print("=" * 72)


def find_all_endpoints(text):
    """Return list of (start, end) for every submit_assignment definition."""
    results = []
    pattern = re.compile(
        r'@app\.post\(\s*"/assignments/\{assignment_id\}/submit"\s*\)\s*\n'
        r'async def submit_assignment\s*\(',
        re.MULTILINE,
    )
    for m in pattern.finditer(text):
        start = m.start()
        # Find the end: next top-level @app. or def after the function body
        lines = text.split("\n")
        start_line = text[:start].count("\n")
        end_line = None
        for i in range(start_line + 1, len(lines)):
            if re.match(r"^@app\.", lines[i]) or re.match(r"^def ", lines[i]):
                end_line = i
                break
        if end_line is None:
            end_line = len(lines)
        end_offset = sum(len(lines[j]) + 1 for j in range(end_line))
        results.append((start, end_offset, start_line + 1, end_line + 1))
    return results


def main():
    print()
    print("#" * 72)
    print("#  CLEANUP DUPLICATE SUBMIT ENDPOINTS")
    print("#  Project: " + str(BACKEND))
    print("#" * 72)

    if not MAIN.exists():
        print("  [ERROR] main.py not found")
        return 1

    text = MAIN.read_text(encoding="utf-8")
    original = text

    # -----------------------------------------------------------------
    # 1. Add missing Form import
    # -----------------------------------------------------------------
    banner("1. ADD MISSING 'Form' IMPORT")

    if re.search(r"from fastapi import[^\n]*\bForm\b", text):
        print("  [OK] Form already imported")
    else:
        # Append Form to the existing fastapi import line
        def add_form(m):
            line = m.group(0)
            if line.rstrip().endswith(")"):
                # unexpected
                return line
            return line.rstrip() + ", Form"
        new_text, n = re.subn(r"^from fastapi import [^\n]+$", add_form, text, count=1, flags=re.MULTILINE)
        if n == 0:
            print("  [FAIL] Could not find 'from fastapi import ...' line")
            return 1
        text = new_text
        print("  [OK] Added 'Form' to fastapi import")

    # -----------------------------------------------------------------
    # 2. Find all submit_assignment endpoints
    # -----------------------------------------------------------------
    banner("2. LOCATE submit_assignment ENDPOINTS")

    endpoints = find_all_endpoints(text)
    print("  Found " + str(len(endpoints)) + " definition(s):")
    for i, (s, e, ls, le) in enumerate(endpoints):
        print("    [" + str(i) + "] lines " + str(ls) + ".." + str(le) + "  (chars " + str(s) + ".." + str(e) + ")")

    if len(endpoints) < 2:
        print()
        print("  [INFO] Only one endpoint — nothing to dedupe.")
        print("  But we should still verify it's the NEW version.")
    else:
        # Keep the last one (should be the new patched version)
        # Strategy: check which one contains 'Save uploaded file'
        new_ones = [i for i, (s, e, _, _) in enumerate(endpoints) if "Save uploaded file" in text[s:e]]
        old_ones = [i for i, (s, e, _, _) in enumerate(endpoints) if "request.query_param" in text[s:e]]

        print()
        print("  Looks like:")
        print("    NEW versions (contain 'Save uploaded file'): " + str(new_ones))
        print("    OLD versions (contain 'request.query_param'): " + str(old_ones))

        # Delete all but the last endpoint that is "new"
        to_keep = new_ones[-1] if new_ones else len(endpoints) - 1
        print()
        print("  Keeping endpoint [" + str(to_keep) + "]")

        # Delete endpoints in reverse order
        for idx in sorted(range(len(endpoints)), reverse=True):
            if idx == to_keep:
                continue
            s, e, ls, le = endpoints[idx]
            print("  Removing endpoint [" + str(idx) + "] at lines " + str(ls) + ".." + str(le))
            text = text[:s] + text[e:]

    # -----------------------------------------------------------------
    # 3. Verify no leftover typo
    # -----------------------------------------------------------------
    banner("3. VERIFY")

    has_typo = "request.query_param" in text and "request.query_params" not in text
    # Note: if BOTH are present, we need to look more carefully
    typo_count = text.count("request.query_param") - text.count("request.query_params")
    print("  'request.query_param' (bad) count: " + str(typo_count))
    print("  'stored_file_url' (new) present: " + str("stored_file_url" in text))
    print("  'Save uploaded file' (new) present: " + str("Save uploaded file" in text))

    # Count decorators
    deco_count = text.count('@app.post("/assignments/{assignment_id}/submit")')
    print("  submit endpoint decorator count: " + str(deco_count))

    # -----------------------------------------------------------------
    # 4. Syntax check + write
    # -----------------------------------------------------------------
    banner("4. WRITE FILE")

    if text == original:
        print("  [INFO] No changes needed")
        return 0

    try:
        ast.parse(text)
        print("  [OK] Syntax valid")
    except SyntaxError as e:
        print("  [FAIL] Syntax error: " + str(e))
        return 1

    bak = MAIN.with_suffix(".py.bak2")
    bak.write_text(original, encoding="utf-8")
    MAIN.write_text(text, encoding="utf-8")
    print("  [OK] main.py updated (backup at " + bak.name + ")")

    banner("DONE - NEXT STEPS")
    print()
    print("  1. Verify imports:")
    print("       python -c \"import re; t=open('main.py',encoding='utf-8').read(); print(re.search(r'from fastapi import [^\\n]+', t).group(0))\"")
    print()
    print("  2. Restart backend if running:")
    print("       uvicorn main:app --reload --port 8000")
    print()
    print("  3. Test submission in the Streamlit app as student1")
    print()
    print("  4. Re-check DB:")
    print("       python -c \"import sqlite3; c=sqlite3.connect('student_marks.db'); c.row_factory=sqlite3.Row; [print(dict(r)) for r in c.execute('SELECT id, assignment_id, student_id, status, file_url FROM assignment_submissions ORDER BY id DESC LIMIT 3')]\"")
    print()
    print("  Rollback: copy main.py.bak2 over main.py")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())