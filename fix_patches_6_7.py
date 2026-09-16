"""
Apply Patches 6 & 7 to backend/main.py.
- Patch 6: Login returns must_change_password, registers session, logs security event
- Patch 7: Change-password revokes sessions, stores history, bumps token version
Auto-backup + syntax check + auto-restore on failure.
"""
import re
import sys
import shutil
from pathlib import Path
from datetime import datetime

MAIN_PY = Path(r"D:\student_marks_analyzer\backend\main.py")

if not MAIN_PY.exists():
    print(f"❌ Not found: {MAIN_PY}")
    sys.exit(1)

backup = MAIN_PY.with_suffix(f".py.p67backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
shutil.copy(MAIN_PY, backup)
print(f"✅ Backup: {backup.name}\n")

content = MAIN_PY.read_text(encoding="utf-8")
original = content

# ============================================================
# PATCH 6: Login response + session registration
# ============================================================
print("=== Patch 6: Login response ===")

if 'must_change_password": bool(user.get("must_change_password' in content:
    print("  ℹ️  Already applied")
else:
    # Find the login function's return block
    # Old pattern: return with access_token, refresh_token
    pattern = re.compile(
        r'(    access_token = create_access_token\(\{\n'
        r'        "sub": user\["username"\], "role": user\["role"\], "user_id": user\["id"\],\n'
        r'    \}\)\n'
        r'    refresh = create_refresh_token\(\{"sub": user\["username"\], "user_id": user\["id"\]\}\)\n'
        r'\n'
        r')(    return \{\n'
        r'        "access_token": access_token,\n'
        r'        "refresh_token": refresh,\n'
        r'        "token_type": "bearer",\n'
        r'        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES \* 60,\n'
        r'        "user": \{\n'
        r'(?:.*\n)*?'
        r'        \},\n'
        r'    \})',
        re.MULTILINE
    )

    match = pattern.search(content)
    if match:
        # Replace the return block with our new one
        new_block = '''    # Register session for tracking
    register_session(user["id"], access_token, ip, ua)

    # Log security event
    log_security_event(user["id"], user["username"], "login_success",
                      None, ip, ua, "info")

    return {
        "access_token": access_token,
        "refresh_token": refresh,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "must_change_password": bool(user.get("must_change_password", 0)),
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "phone": user.get("phone"),
            "full_name": user.get("full_name"),
            "role": user["role"],
            "language": user.get("language", "en"),
            "theme": user.get("theme", "light"),
            "email_verified": bool(user.get("email_verified")),
            "phone_verified": bool(user.get("phone_verified")),
            "twofa_enabled": bool(user.get("twofa_enabled")),
            "must_change_password": bool(user.get("must_change_password", 0)),
        },
    }'''

        # Get the exact span of the return block
        content = content[:match.start(2)] + new_block + content[match.end(2):]
        print("  ✅ Patch 6 applied")
    else:
        # Alternative: find the return block by simpler pattern
        pattern2 = re.compile(
            r'(    access_token = create_access_token\(.*?\)\n'
            r'    refresh = create_refresh_token\(.*?\)\n'
            r'\n)'
            r'(    return \{\n'
            r'        "access_token": access_token,.*?\n    \})',
            re.DOTALL
        )
        match2 = pattern2.search(content)
        if match2:
            new_block = '''    # Register session for tracking
    register_session(user["id"], access_token, ip, ua)
    log_security_event(user["id"], user["username"], "login_success",
                      None, ip, ua, "info")

    return {
        "access_token": access_token,
        "refresh_token": refresh,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "must_change_password": bool(user.get("must_change_password", 0)),
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "phone": user.get("phone"),
            "full_name": user.get("full_name"),
            "role": user["role"],
            "language": user.get("language", "en"),
            "theme": user.get("theme", "light"),
            "email_verified": bool(user.get("email_verified")),
            "phone_verified": bool(user.get("phone_verified")),
            "twofa_enabled": bool(user.get("twofa_enabled")),
            "must_change_password": bool(user.get("must_change_password", 0)),
        },
    }'''
            content = content[:match2.start(2)] + new_block + content[match2.end(2):]
            print("  ✅ Patch 6 applied (alt pattern)")
        else:
            print("  ❌ Cannot find login return block — patch manually")
            sys.exit(1)

# ============================================================
# PATCH 7: Change password hardening
# ============================================================
print("\n=== Patch 7: Change password ===")

if 'is_password_reused(user["id"], data.new_password)' in content:
    print("  ℹ️  Already applied")
else:
    # Find the change_password function
    pattern = re.compile(
        r'(@app\.post\("/auth/change-password"\)\n'
        r'def change_password\(data: PasswordChange, user=Depends\(require_user\)\):\n)'
        r'((?:    .*\n)+?)(?=\n\n@app\.|\n\n#|\Z)',
        re.MULTILINE
    )

    match = pattern.search(content)
    if match:
        new_func = '''@app.post("/auth/change-password")
def change_password(data: PasswordChange, request: Request, user=Depends(require_user)):
    ip = request.client.host if request.client else "unknown"

    if not verify_password(data.old_password, user["hashed_password"]):
        log_security_event(user["id"], user["username"], "password_change_failed",
                          "wrong_old_password", ip, None, "warning")
        raise HTTPException(400, "Current password is incorrect")

    is_valid, error = validate_password_strength(data.new_password)
    if not is_valid:
        raise HTTPException(400, error)

    if is_password_reused(user["id"], data.new_password):
        raise HTTPException(400,
            f"Cannot reuse your last {PASSWORD_HISTORY_CHECK} passwords")

    new_hash = get_password_hash(data.new_password)

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Store current hash in history
        cursor.execute(_q("""
            INSERT INTO password_history (user_id, password_hash)
            VALUES (?, ?)
        """), (user["id"], user["hashed_password"]))

        # Update password + flag + timestamp + bump version
        cursor.execute(_q("""
            UPDATE users SET
                hashed_password=?,
                must_change_password=0,
                password_changed_at=?,
                token_version=COALESCE(token_version, 1) + 1
            WHERE id=?
        """), (new_hash, datetime.utcnow().isoformat(), user["id"]))

        conn.commit()

    # Revoke all existing sessions
    revoke_all_sessions(user["id"])

    log_security_event(user["id"], user["username"], "password_changed",
                      None, ip, None, "info")
    log_audit(user["id"], user["username"], "change_password", "user",
             None, ip)

    return {
        "message": "Password changed successfully. Please log in again.",
        "reauthentication_required": True,
    }

'''
        content = content[:match.start(1)] + new_func + content[match.end(2):]
        print("  ✅ Patch 7 applied")
    else:
        print("  ❌ Cannot find change_password function — patch manually")
        sys.exit(1)

# ============================================================
# SAVE & VERIFY
# ============================================================
if content != original:
    MAIN_PY.write_text(content, encoding="utf-8")
    print("\n✅ main.py updated")
else:
    print("\nℹ️  No changes made")

print("\n=== Syntax check ===")
import ast
try:
    ast.parse(content)
    print("  ✅ Syntax OK")
except SyntaxError as e:
    print(f"  ❌ Syntax error: {e}")
    print(f"  Restoring from {backup.name}")
    shutil.copy(backup, MAIN_PY)
    sys.exit(1)

# Count markers
print("\n=== Verify ===")
verify = {
    "Patch 6 - must_change_password": 'must_change_password": bool' in content,
    "Patch 6 - register_session call": 'register_session(user["id"], access_token, ip, ua)' in content,
    "Patch 6 - log_security_event call": 'log_security_event(user["id"], user["username"], "login_success"' in content,
    "Patch 7 - is_password_reused call": 'is_password_reused(user["id"], data.new_password)' in content,
    "Patch 7 - revoke_all_sessions call": 'revoke_all_sessions(user["id"])' in content,
    "Patch 7 - token_version bump": 'token_version=COALESCE(token_version, 1) + 1' in content,
}
all_ok = True
for k, v in verify.items():
    symbol = "✅" if v else "❌"
    print(f"  {symbol} {k}")
    if not v:
        all_ok = False

lines = content.count("\n") + 1
print(f"\n📊 Total lines: {lines}")
print(f"🔒 Backup: {backup.name}")

if all_ok:
    print("\n🎉 Patches 6 & 7 applied successfully!")
else:
    print("\n⚠️  Some markers missing — check above.")

sys.exit(0 if all_ok else 1)
