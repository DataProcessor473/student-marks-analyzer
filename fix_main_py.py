"""
Fix all 3 problems in main.py:
1. Remove duplicated validation functions
2. Add missing Phase 5 helpers
3. Add missing Phase 5 endpoints
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

# Backup
backup = MAIN_PY.with_suffix(f".py.fixbackup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
shutil.copy(MAIN_PY, backup)
print(f"✅ Backup: {backup.name}\n")

content = MAIN_PY.read_text(encoding="utf-8")
original = content

# ============================================================
# FIX 1: Remove duplicated validation functions
# ============================================================
print("=== FIX 1: Deduplicate validation block ===")

# Find start: "# VALIDATION" header
# Find end: "def validate_subject_name"

start_marker = "# VALIDATION"
end_marker = "def validate_subject_name"

# Find the LAST occurrence of the "# VALIDATION" header before validate_subject_name
idx_subject = content.find(end_marker)
if idx_subject == -1:
    print("  ❌ Cannot find validate_subject_name")
    sys.exit(1)

# Find "# ====" header before "# VALIDATION" for proper boundary
idx_validation = content.rfind("# VALIDATION", 0, idx_subject)
if idx_validation == -1:
    print("  ❌ Cannot find # VALIDATION header")
    sys.exit(1)

# Walk back to find the "# ====" line
idx_start = content.rfind("# ==", 0, idx_validation)
if idx_start == -1:
    idx_start = idx_validation

# Replace entire block
clean_block = '''# ============================================================
# VALIDATION
# ============================================================
def validate_password_strength(password: str) -> tuple:
    if len(password) < PASSWORD_MIN_LENGTH:
        return False, f"Password must be at least {PASSWORD_MIN_LENGTH} characters"
    if not re.search(r"[A-Z]", password):
        return False, "Must contain an uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Must contain a lowercase letter"
    if not re.search(r"\\d", password):
        return False, "Must contain a digit"
    if not re.search(r"[!@#$%^&*(),.?\\":{}|<>_\\-+=\\[\\]\\\\\\/;'`~]", password):
        return False, "Must contain a special character"
    weak = ["password", "admin", "12345", "qwerty", "letmein", "welcome"]
    if any(w in password.lower() for w in weak):
        return False, "Password contains a common weak pattern"
    return True, ""


def is_password_reused(user_id: int, new_password: str) -> bool:
    """Check last N password hashes."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(_q("""
                SELECT password_hash FROM password_history
                WHERE user_id=? ORDER BY created_at DESC LIMIT ?
            """), (user_id, PASSWORD_HISTORY_CHECK))
            for row in cursor.fetchall():
                if verify_password(new_password, row["password_hash"]):
                    return True
    except Exception:
        pass
    return False


def store_password_history(user_id: int, password_hash: str):
    """Store password hash in history (keep last N+5)."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(_q("""
                INSERT INTO password_history (user_id, password_hash)
                VALUES (?, ?)
            """), (user_id, password_hash))
            cursor.execute(_q("""
                DELETE FROM password_history
                WHERE id NOT IN (
                    SELECT id FROM password_history
                    WHERE user_id=? ORDER BY created_at DESC LIMIT ?
                )
            """), (user_id, PASSWORD_HISTORY_CHECK + 5))
            conn.commit()
    except Exception:
        pass


'''

# Find end of block (start of validate_subject_name)
content = content[:idx_start] + clean_block + content[idx_subject:]
print("  ✅ Validation block cleaned")

# ============================================================
# FIX 2: Add Phase 5 helpers after decode_token
# ============================================================
print("\n=== FIX 2: Add Phase 5 helpers ===")

if "def log_security_event" in content:
    print("  ℹ️  Helpers already present — skipping")
else:
    # Find end of decode_token
    idx = content.find("def decode_token")
    if idx == -1:
        print("  ❌ Cannot find decode_token")
        sys.exit(1)

    # Find end: next "\n\n\n" after decode_token
    after = content.find("\n\n\n", idx)
    if after == -1:
        print("  ❌ Cannot find end of decode_token")
        sys.exit(1)

    helpers = '''

# ============================================================
# SECURITY HELPERS (Phase 5)
# ============================================================
def log_security_event(user_id, username, event_type, details=None,
                       ip=None, ua=None, severity="info"):
    """Log a security event."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(_q("""
                INSERT INTO security_events
                (user_id, username, event_type, details, ip_address, user_agent, severity)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """), (user_id, username, event_type, details,
                   ip, (ua or "")[:200], severity))
            conn.commit()
    except Exception as e:
        print(f"[SECURITY LOG] {event_type}: {e}")


def register_session(user_id, token, ip, ua):
    """Track active session."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(_q("""
                INSERT INTO sessions (user_id, token_hash, device_info, ip_address)
                VALUES (?, ?, ?, ?)
            """), (user_id, hash_token(token), (ua or "")[:200], ip))
            conn.commit()
    except Exception as e:
        print(f"[SESSION] {e}")


def revoke_all_sessions(user_id):
    """Mark all sessions revoked."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(_q("""
                UPDATE sessions SET revoked=1 WHERE user_id=?
            """), (user_id,))
            conn.commit()
    except Exception:
        pass


def is_session_valid(user_id, token):
    """Check if session is still valid."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(_q("""
                SELECT revoked FROM sessions
                WHERE user_id=? AND token_hash=?
                ORDER BY id DESC LIMIT 1
            """), (user_id, hash_token(token)))
            row = cursor.fetchone()
            if row and row["revoked"]:
                return False
    except Exception:
        pass
    return True


def increment_token_version(user_id):
    """Bump token version (invalidates all tokens)."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(_q("""
                UPDATE users SET token_version = COALESCE(token_version, 1) + 1
                WHERE id=?
            """), (user_id,))
            conn.commit()
    except Exception:
        pass


def verify_turnstile(token: str, ip: str = None) -> bool:
    """Verify Cloudflare Turnstile CAPTCHA token (no-op if disabled)."""
    if not TURNSTILE_ENABLED:
        return True
    if not token:
        return False
    try:
        import requests as req
        r = req.post(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            data={"secret": TURNSTILE_SECRET_KEY, "response": token, "remoteip": ip},
            timeout=10,
        )
        return r.json().get("success", False)
    except Exception as e:
        print(f"[TURNSTILE] {e}")
        return False

'''
    content = content[:after] + helpers + content[after:]
    print("  ✅ Helpers inserted")

# ============================================================
# FIX 3: Add Phase 5 endpoints after check_strength
# ============================================================
print("\n=== FIX 3: Add Phase 5 endpoints ===")

if '@app.get("/auth/sessions")' in content:
    print("  ℹ️  Endpoints already present — skipping")
else:
    # Find end of check_strength — the next @app.put("/auth/theme")
    idx = content.find('@app.post("/auth/check-strength")')
    if idx == -1:
        print("  ❌ Cannot find check-strength")
        sys.exit(1)

    idx_next = content.find('@app.put("/auth/theme")', idx)
    if idx_next == -1:
        print("  ❌ Cannot find auth/theme after check-strength")
        sys.exit(1)

    endpoints = '''

# ============================================================
# SECURITY MANAGEMENT (Phase 5)
# ============================================================
@app.get("/auth/sessions")
def list_sessions(request: Request, user=Depends(require_user)):
    """List active sessions for current user."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(_q("""
                SELECT id, device_info, ip_address, created_at, last_active, revoked
                FROM sessions
                WHERE user_id=? AND revoked=0
                ORDER BY last_active DESC
            """), (user["id"],))
            rows = [dict(r) for r in cursor.fetchall()]
            for r in rows:
                if r.get("created_at"):
                    r["created_at"] = str(r["created_at"])[:19]
                if r.get("last_active"):
                    r["last_active"] = str(r["last_active"])[:19]
            return {"sessions": rows, "count": len(rows)}
    except Exception as e:
        raise HTTPException(500, f"Failed: {e}")


@app.delete("/auth/sessions/{session_id}")
def revoke_session(session_id: int, user=Depends(require_user)):
    """Revoke a specific session."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(_q("""
            UPDATE sessions SET revoked=1 WHERE id=? AND user_id=?
        """), (session_id, user["id"]))
        conn.commit()
    log_security_event(user["id"], user["username"], "session_revoked",
                      f"session_id={session_id}")
    return {"message": "Session revoked"}


@app.post("/auth/sessions/revoke-all")
def revoke_all_my_sessions(request: Request, user=Depends(require_user)):
    """Revoke ALL sessions (forces re-login everywhere)."""
    revoke_all_sessions(user["id"])
    increment_token_version(user["id"])
    ip = request.client.host if request.client else None
    log_security_event(user["id"], user["username"], "all_sessions_revoked",
                      None, ip, None, "warning")
    return {"message": "All sessions revoked. Re-login required.",
            "reauthentication_required": True}


@app.get("/auth/security-events")
def get_security_events(request: Request, limit: int = 50,
                        user=Depends(require_user)):
    """Get security events for current user (or all if admin)."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if user["role"] == "admin":
            cursor.execute(_q("""
                SELECT * FROM security_events
                ORDER BY created_at DESC LIMIT ?
            """), (limit,))
        else:
            cursor.execute(_q("""
                SELECT * FROM security_events
                WHERE user_id=?
                ORDER BY created_at DESC LIMIT ?
            """), (user["id"], limit))
        rows = [dict(r) for r in cursor.fetchall()]
        for r in rows:
            if r.get("created_at"):
                r["created_at"] = str(r["created_at"])[:19]
        return {"events": rows, "count": len(rows)}


@app.post("/auth/2fa/recovery-codes/generate")
def generate_recovery_codes(request: Request, user=Depends(require_user)):
    """Generate 10 one-time recovery codes."""
    if not user.get("twofa_enabled"):
        raise HTTPException(400, "Enable 2FA first")

    codes = []
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(_q("""
            DELETE FROM recovery_codes WHERE user_id=? AND used=0
        """), (user["id"],))
        for _ in range(10):
            code = f"{secrets.token_hex(2).upper()}-{secrets.token_hex(2).upper()}-{secrets.token_hex(2).upper()}"
            codes.append(code)
            cursor.execute(_q("""
                INSERT INTO recovery_codes (user_id, code_hash)
                VALUES (?, ?)
            """), (user["id"], hash_token(code)))
        conn.commit()

    log_security_event(user["id"], user["username"], "recovery_codes_generated",
                      "10 codes", request.client.host if request.client else None)
    return {"codes": codes, "message": "Save these codes!"}


@app.post("/auth/2fa/recovery-codes/verify")
def verify_recovery_code(data: TOTPVerify, request: Request):
    """Use a recovery code (bypasses 2FA)."""
    code = data.code.strip().upper()
    code_hash = hash_token(code)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(_q("""
            SELECT id, user_id FROM recovery_codes
            WHERE code_hash=? AND used=0
        """), (code_hash,))
        row = cursor.fetchone()

        if not row:
            log_security_event(None, None, "recovery_code_invalid",
                              None, request.client.host if request.client else None,
                              severity="warning")
            raise HTTPException(401, "Invalid or already-used recovery code")

        cursor.execute(_q("""
            UPDATE recovery_codes SET used=1, used_at=? WHERE id=?
        """), (datetime.utcnow().isoformat(), row["id"]))
        conn.commit()

        cursor.execute(_q("SELECT * FROM users WHERE id=?"), (row["user_id"],))
        u = cursor.fetchone()
        if not u:
            raise HTTPException(404, "User not found")
        u = dict(u)

    token_version = u.get("token_version", 1) or 1
    access_token = create_access_token({
        "sub": u["username"], "role": u["role"],
        "user_id": u["id"], "token_version": token_version,
    })
    refresh = create_refresh_token({"sub": u["username"], "user_id": u["id"]})

    log_security_event(u["id"], u["username"], "recovery_code_used",
                      None, request.client.host if request.client else None,
                      severity="warning")

    return {
        "access_token": access_token,
        "refresh_token": refresh,
        "token_type": "bearer",
        "user": {
            "id": u["id"], "username": u["username"], "email": u["email"],
            "role": u["role"], "language": u.get("language", "en"),
            "theme": u.get("theme", "light"),
        },
    }

'''
    content = content[:idx_next] + endpoints + "\n" + content[idx_next:]
    print("  ✅ Endpoints inserted")

# ============================================================
# SAVE
# ============================================================
if content != original:
    MAIN_PY.write_text(content, encoding="utf-8")
    print("\n✅ main.py updated")
else:
    print("\nℹ️  No changes made")

# ============================================================
# VERIFY SYNTAX
# ============================================================
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

# Count
lines = content.count("\n") + 1
print(f"\n📊 Total lines: {lines}")
print(f"🔒 Backup kept: {backup.name}")
print("\n🎉 Done!")
