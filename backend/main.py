from fastapi import FastAPI, HTTPException, Query, Depends, status, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, FileResponse
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from jose import JWTError, jwt
from datetime import datetime, timedelta
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import bcrypt
import numpy as np
import pandas as pd
import json
import sqlite3
import os
import io
import re
import random
import string
import smtplib
import csv as csv_module
import secrets
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

try:
    from pdf_generator import generate_report_card
except ImportError:
    generate_report_card = None
    print("⚠️ pdf_generator.py not found — PDF disabled")

# ============================================================
# CONFIG
# ============================================================
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(48))
REFRESH_SECRET_KEY = os.getenv("REFRESH_SECRET_KEY", secrets.token_urlsafe(48))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
REFRESH_TOKEN_EXPIRE_DAYS = 7
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15

OTP_EXPIRE_MINUTES = int(os.getenv("OTP_EXPIRE_MINUTES", 10))
OTP_LENGTH = int(os.getenv("OTP_LENGTH", 6))

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")

DEV_MODE_SMS = os.getenv("DEV_MODE_SMS", "true").lower() == "true"
FAST2SMS_API_KEY = os.getenv("FAST2SMS_API_KEY", "")

# ============================================================
# APP
# ============================================================
app = FastAPI(
    title="Student Marks Analyzer API",
    description="Secure API with OTP verification (email + SMS), role-based access",
    version="6.0.0"
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

# ============================================================
# VALIDATION
# ============================================================
def validate_password_strength(password: str) -> tuple:
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r"[A-Z]", password):
        return False, "Must contain an uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Must contain a lowercase letter"
    if not re.search(r"\d", password):
        return False, "Must contain a digit"
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\\/;'`~]", password):
        return False, "Must contain a special character"
    return True, ""


def validate_subject_name(name: str) -> tuple:
    """No gibberish subject names."""
    if not name or not name.strip():
        return False, "Subject name cannot be empty"

    name = name.strip()

    if len(name) < 2:
        return False, "Subject name too short (min 2 chars)"
    if len(name) > 50:
        return False, "Subject name too long (max 50 chars)"
    if not name[0].isalpha():
        return False, "Subject name must start with a letter"
    if not re.search(r"[aeiouAEIOU]", name):
        return False, f"'{name}' doesn't look like a valid subject name"
    if not re.match(r"^[A-Za-z][A-Za-z0-9\s\-\.\(\)&,']*$", name):
        return False, "Subject name contains invalid characters"

    letters = re.sub(r"[^A-Za-z]", "", name).lower()
    if letters and len(set(letters)) <= 2:
        return False, "Subject name has no variety"

    return True, ""


def validate_email(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


def validate_phone(phone: str) -> tuple:
    if not phone:
        return False, "Phone required"
    cleaned = re.sub(r"[\s\-\(\)]", "", phone)
    if not re.match(r"^\+?[0-9]{10,15}$", cleaned):
        return False, "Invalid phone number"
    if not cleaned.startswith("+"):
        cleaned = "+91" + cleaned.lstrip("0") if len(cleaned) == 10 else "+" + cleaned
    return True, cleaned


def verify_password(plain: str, hashed: str) -> bool:
    try:
        pwd_bytes = plain.encode('utf-8')[:72]
        hash_bytes = hashed.encode('utf-8') if isinstance(hashed, str) else hashed
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode('utf-8')[:72]
    return bcrypt.hashpw(pwd_bytes, bcrypt.gensalt(rounds=12)).decode('utf-8')


# ============================================================
# TOKENS
# ============================================================
def create_access_token(data: dict) -> str:
    d = data.copy()
    d["type"] = "access"
    d["exp"] = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(d, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    d = data.copy()
    d["type"] = "refresh"
    d["exp"] = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    return jwt.encode(d, REFRESH_SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str, refresh: bool = False) -> Optional[dict]:
    try:
        key = REFRESH_SECRET_KEY if refresh else SECRET_KEY
        return jwt.decode(token, key, algorithms=[ALGORITHM])
    except JWTError:
        return None


# ============================================================
# OTP DELIVERY
# ============================================================
def generate_otp() -> str:
    return ''.join(random.choices(string.digits, k=OTP_LENGTH))


def send_email_otp(to_email: str, otp: str, purpose: str = "verification") -> bool:
    """Send OTP via Gmail SMTP"""
    if not SMTP_USER or not SMTP_PASS:
        print(f"\n{'='*60}")
        print(f"📧 EMAIL OTP (SMTP not configured) [{purpose}] → {to_email}")
        print(f"   Code: {otp}")
        print(f"   Expires in {OTP_EXPIRE_MINUTES} minutes")
        print(f"{'='*60}\n")
        return True

    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = to_email
        msg['Subject'] = f"Your verification code: {otp}"

        purpose_label = {
            "verification": "email verification",
            "reset_password": "password reset",
            "login": "login verification",
            "phone_verification": "phone verification",
        }.get(purpose, purpose)

        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5;">
            <div style="max-width: 500px; margin: 0 auto; background: white; border-radius: 12px;
                        padding: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
                <h2 style="color: #667eea; margin: 0 0 20px 0;">🎓 Student Marks Analyzer</h2>
                <p style="color: #333; font-size: 16px;">Your <b>{purpose_label}</b> code is:</p>
                <h1 style="background: linear-gradient(135deg, #667eea, #764ba2); color: white;
                           padding: 20px; border-radius: 12px; letter-spacing: 8px;
                           text-align: center; font-size: 32px; margin: 20px 0;">
                    {otp}
                </h1>
                <p style="color: #666; font-size: 14px;">
                    This code expires in <b>{OTP_EXPIRE_MINUTES} minutes</b>.
                </p>
                <p style="color: #999; font-size: 12px; margin-top: 30px;
                          border-top: 1px solid #eee; padding-top: 15px;">
                    If you didn't request this code, please ignore this email.
                </p>
            </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(body, 'html'))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)

        print(f"✅ Email OTP sent to {to_email}")
        return True
    except Exception as e:
        print(f"❌ Email send error: {e}")
        # Fallback: print OTP so dev can still test
        print(f"\n{'='*60}")
        print(f"📧 EMAIL OTP (fallback) [{purpose}] → {to_email}")
        print(f"   Code: {otp}")
        print(f"{'='*60}\n")
        return False


def send_sms_otp(phone: str, otp: str) -> bool:
    """
    SMS OTP delivery.
    Fast2SMS integration is stubbed — plug in later.
    Currently: console print only.
    """
    # Dev / console mode
    if DEV_MODE_SMS or not FAST2SMS_API_KEY:
        print(f"\n{'='*60}")
        print(f"📱 SMS OTP → {phone}")
        print(f"   Code: {otp}")
        print(f"   Expires in {OTP_EXPIRE_MINUTES} minutes")
        print(f"{'='*60}\n")
        return True

    # TODO: Fast2SMS integration (paste your API key in .env later)
    try:
        import requests as req
        url = "https://www.fast2sms.com/dev/bulkV2"
        payload = {
            "route": "q",
            "message": f"Your Student Marks Analyzer OTP: {otp}. Valid for {OTP_EXPIRE_MINUTES} min.",
            "language": "english",
            "flash": 0,
            "numbers": phone.lstrip("+91"),
        }
        headers = {
            "authorization": FAST2SMS_API_KEY,
            "Content-Type": "application/json",
        }
        r = req.post(url, json=payload, headers=headers, timeout=10)
        if r.status_code == 200:
            print(f"✅ SMS OTP sent to {phone}")
            return True
        else:
            print(f"❌ Fast2SMS error: {r.text}")
    except Exception as e:
        print(f"❌ SMS error: {e}")

    # Fallback to console
    print(f"\n{'='*60}")
    print(f"📱 SMS OTP (fallback) → {phone}")
    print(f"   Code: {otp}")
    print(f"{'='*60}\n")
    return False


# ============================================================
# DATABASE
# ============================================================
DB_PATH = os.path.join(os.path.dirname(__file__), "student_marks.db")


@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_database():
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT,
                hashed_password TEXT NOT NULL,
                full_name TEXT,
                role TEXT DEFAULT 'teacher',
                is_active INTEGER DEFAULT 1,
                email_verified INTEGER DEFAULT 0,
                phone_verified INTEGER DEFAULT 0,
                failed_login_attempts INTEGER DEFAULT 0,
                locked_until TIMESTAMP,
                last_login TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS otp_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                identifier TEXT NOT NULL,
                otp_code TEXT NOT NULL,
                purpose TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                used INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT NOT NULL,
                marks TEXT NOT NULL,
                subjects TEXT NOT NULL,
                grade TEXT NOT NULL,
                average REAL NOT NULL,
                total_marks REAL NOT NULL,
                timestamp TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                semester TEXT,
                batch_year TEXT,
                department TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                date TEXT NOT NULL,
                status TEXT NOT NULL,
                subject TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_trends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                semester TEXT,
                average REAL,
                grade TEXT,
                total_marks REAL,
                timestamp TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                message TEXT,
                type TEXT,
                is_read INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parent_children (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_user_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                relationship TEXT DEFAULT 'parent',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(parent_user_id, student_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS token_blacklist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token_hash TEXT UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                ip_address TEXT,
                user_agent TEXT,
                success INTEGER,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                action TEXT NOT NULL,
                resource TEXT,
                details TEXT,
                ip_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS role_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                old_role TEXT NOT NULL,
                new_role TEXT NOT NULL,
                changed_by INTEGER,
                changed_by_username TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Migrations
        for table, cols in {
            "users": [
                ("phone", "TEXT"),
                ("email_verified", "INTEGER DEFAULT 0"),
                ("phone_verified", "INTEGER DEFAULT 0"),
                ("failed_login_attempts", "INTEGER DEFAULT 0"),
                ("locked_until", "TIMESTAMP"),
                ("last_login", "TIMESTAMP"),
            ],
        }.items():
            cursor.execute(f"PRAGMA table_info({table})")
            existing = [c[1] for c in cursor.fetchall()]
            for col, ctype in cols:
                if col not in existing:
                    try:
                        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {ctype}")
                    except sqlite3.OperationalError:
                        pass

        # Default admin
        cursor.execute("SELECT COUNT(*) as count FROM users")
        if cursor.fetchone()["count"] == 0:
            default_hash = get_password_hash("Admin@123")
            cursor.execute("""
                INSERT INTO users (username, email, hashed_password, full_name, role,
                                   email_verified, phone_verified)
                VALUES (?, ?, ?, ?, ?, 1, 1)
            """, ("admin", "admin@example.com", default_hash, "Default Admin", "admin"))
            print("✅ Created default admin — admin / Admin@123")

        for idx in [
            "CREATE INDEX IF NOT EXISTS idx_user_username ON users(username)",
            "CREATE INDEX IF NOT EXISTS idx_user_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS idx_otp_identifier ON otp_codes(identifier)",
            "CREATE INDEX IF NOT EXISTS idx_otp_expires ON otp_codes(expires_at)",
        ]:
            try:
                cursor.execute(idx)
            except sqlite3.OperationalError:
                pass

        conn.commit()
        print("✅ Database initialized successfully")


init_database()


# ============================================================
# MODELS
# ============================================================
class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=30)
    email: str
    phone: Optional[str] = None
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = Field(None, max_length=100)
    role: str = "teacher"

    @validator('username')
    def v_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError("Username: letters, numbers, underscores only")
        return v.lower()

    @validator('role')
    def v_role(cls, v):
        if v not in ["admin", "teacher", "student", "parent"]:
            raise ValueError("Invalid role")
        return v


class OTPRequest(BaseModel):
    identifier: str
    purpose: str = "verification"


class OTPVerify(BaseModel):
    identifier: str
    otp_code: str
    purpose: str = "verification"


class PasswordResetOTP(BaseModel):
    identifier: str
    otp_code: str
    new_password: str


class PasswordChange(BaseModel):
    old_password: str
    new_password: str


class MarksRequest(BaseModel):
    marks: List[float]
    student_name: Optional[str] = None
    subject_names: Optional[List[str]] = None
    passing_threshold: float = 40
    grade_scheme: str = "standard"
    semester: Optional[str] = None
    batch_year: Optional[str] = None
    department: Optional[str] = None

    @validator('marks')
    def v_marks(cls, v):
        if not v:
            raise ValueError("Marks cannot be empty")
        if any(m < 0 or m > 100 for m in v):
            raise ValueError("Marks must be 0–100")
        return v

    @validator('subject_names')
    def v_subjects(cls, v):
        if v:
            for name in v:
                ok, err = validate_subject_name(name)
                if not ok:
                    raise ValueError(f"Invalid subject '{name}': {err}")
        return v


class StudentRecord(BaseModel):
    name: str
    marks: List[float]
    subjects: List[str]
    grade: str
    average: float
    total_marks: Optional[float] = None
    timestamp: str
    semester: Optional[str] = None
    batch_year: Optional[str] = None
    department: Optional[str] = None

    @validator('subjects')
    def v_sub(cls, v):
        for name in v:
            ok, err = validate_subject_name(name)
            if not ok:
                raise ValueError(f"Invalid subject '{name}': {err}")
        return v


class AttendanceRecord(BaseModel):
    student_id: int
    date: str
    status: str
    subject: Optional[str] = None
    notes: Optional[str] = None


class BulkAttendanceRecord(BaseModel):
    date: str
    subject: Optional[str] = None
    records: List[Dict[str, Any]]


class NotificationCreate(BaseModel):
    student_id: int
    message: str
    type: str = "Info"


class CompareRequest(BaseModel):
    student_ids: List[int]


class LinkChildRequest(BaseModel):
    student_id: int
    relationship: Optional[str] = "parent"


# ============================================================
# HELPERS
# ============================================================
def hash_token(token: str) -> str:
    import hashlib
    return hashlib.sha256(token.encode()).hexdigest()


def blacklist_token(token: str, expires_at: datetime):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO token_blacklist (token_hash, expires_at) VALUES (?, ?)",
                (hash_token(token), expires_at.isoformat())
            )
            conn.commit()
    except Exception:
        pass


def is_token_blacklisted(token: str) -> bool:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM token_blacklist WHERE token_hash=?", (hash_token(token),))
            return cursor.fetchone() is not None
    except Exception:
        return False


def log_audit(uid, username, action, resource=None, details=None, ip=None):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO audit_log (user_id, username, action, resource, details, ip_address)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (uid, username, action, resource, details, ip))
            conn.commit()
    except Exception:
        pass


def log_login_attempt(username, ip, ua, success, reason=""):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO login_attempts (username, ip_address, user_agent, success, reason)
                VALUES (?, ?, ?, ?, ?)
            """, (username, ip, (ua or "")[:200], 1 if success else 0, reason))
            conn.commit()
    except Exception:
        pass


def check_account_locked(username):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT locked_until FROM users WHERE username=?", (username,))
        row = cursor.fetchone()
        if row and row["locked_until"]:
            try:
                lu = datetime.fromisoformat(row["locked_until"])
                if datetime.utcnow() < lu:
                    mins = int((lu - datetime.utcnow()).total_seconds() / 60) + 1
                    return f"Account locked. Try again in {mins} minute(s)."
            except ValueError:
                pass
    return None


def increment_failed_attempts(username):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT failed_login_attempts FROM users WHERE username=?", (username,))
        row = cursor.fetchone()
        if not row:
            return
        attempts = (row["failed_login_attempts"] or 0) + 1
        if attempts >= MAX_FAILED_ATTEMPTS:
            lu = (datetime.utcnow() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)).isoformat()
            cursor.execute("UPDATE users SET failed_login_attempts=?, locked_until=? WHERE username=?",
                           (attempts, lu, username))
        else:
            cursor.execute("UPDATE users SET failed_login_attempts=? WHERE username=?",
                           (attempts, username))
        conn.commit()


def reset_failed_attempts(username):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users SET failed_login_attempts=0, locked_until=NULL, last_login=?
            WHERE username=?
        """, (datetime.utcnow().isoformat(), username))
        conn.commit()


def save_otp(identifier, otp, purpose):
    expires = (datetime.utcnow() + timedelta(minutes=OTP_EXPIRE_MINUTES)).isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE otp_codes SET used=1
            WHERE identifier=? AND purpose=? AND used=0
        """, (identifier, purpose))
        cursor.execute("""
            INSERT INTO otp_codes (identifier, otp_code, purpose, expires_at)
            VALUES (?, ?, ?, ?)
        """, (identifier, otp, purpose, expires))
        conn.commit()


def verify_otp(identifier, otp, purpose):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM otp_codes
            WHERE identifier=? AND purpose=? AND used=0
            ORDER BY created_at DESC LIMIT 1
        """, (identifier, purpose))
        row = cursor.fetchone()
        if not row:
            return False, "No OTP found. Request a new one."
        if row["otp_code"] != otp:
            return False, "Incorrect OTP"
        try:
            exp = datetime.fromisoformat(row["expires_at"])
            if datetime.utcnow() > exp:
                return False, "OTP expired. Request a new one."
        except ValueError:
            pass
        cursor.execute("UPDATE otp_codes SET used=1 WHERE id=?", (row["id"],))
        conn.commit()
        return True, "OK"


# ============================================================
# ANALYTICS HELPERS
# ============================================================
def calculate_statistics(marks):
    arr = np.array(marks)
    return {
        "total": float(np.sum(arr)),
        "average": float(np.mean(arr)),
        "highest": float(np.max(arr)),
        "lowest": float(np.min(arr)),
        "median": float(np.median(arr)),
        "std_deviation": float(np.std(arr)),
        "range": float(np.max(arr) - np.min(arr)),
        "variance": float(np.var(arr)),
        "quartiles": {
            "q1": float(np.percentile(arr, 25)),
            "q2": float(np.percentile(arr, 50)),
            "q3": float(np.percentile(arr, 75)),
        },
    }


def determine_grade(avg, scheme="standard"):
    schemes = {
        "standard": {(90, 100): ("A+", 10), (80, 89.99): ("A", 9), (70, 79.99): ("B", 8),
                     (60, 69.99): ("C", 7), (50, 59.99): ("D", 6), (40, 49.99): ("E", 5),
                     (0, 39.99): ("F", 0)},
        "strict": {(93, 100): ("A+", 10), (85, 92.99): ("A", 9), (75, 84.99): ("B", 8),
                   (65, 74.99): ("C", 7), (55, 64.99): ("D", 6), (45, 54.99): ("E", 5),
                   (0, 44.99): ("F", 0)},
        "lenient": {(85, 100): ("A+", 10), (70, 84.99): ("A", 9), (60, 69.99): ("B", 8),
                    (50, 59.99): ("C", 7), (40, 49.99): ("D", 6), (30, 39.99): ("E", 5),
                    (0, 29.99): ("F", 0)},
    }
    for (lo, hi), (g, p) in schemes.get(scheme, schemes["standard"]).items():
        if lo <= avg <= hi:
            return g, p
    return "F", 0


def generate_ai_insights(marks, avg, subjects):
    ins = {"strengths": [], "weaknesses": [], "recommendations": [],
           "predictions": [], "study_tips": [], "improvement_potential": 0}
    for i, m in enumerate(marks):
        s = subjects[i] if i < len(subjects) else f"Subject {i+1}"
        if m >= 80:
            ins["strengths"].append({"subject": s, "marks": m, "level": "Excellent"})
        elif m < 40:
            ins["weaknesses"].append({"subject": s, "marks": m, "level": "Needs Improvement"})
    if avg < 40:
        ins["recommendations"].append({"priority": "High", "action": "Immediate intervention",
                                       "details": "Consider tutoring"})
        ins["study_tips"] = ["Focus on fundamentals", "Practice daily"]
    elif avg < 60:
        ins["recommendations"].append({"priority": "Medium", "action": "Structured plan",
                                       "details": "Create schedule"})
        ins["study_tips"] = ["Join study groups", "Use online resources"]
    elif avg < 75:
        ins["recommendations"].append({"priority": "Low", "action": "Enhance performance",
                                       "details": "Focus on weak areas"})
        ins["study_tips"] = ["Advanced problems", "Teach peers"]
    else:
        ins["recommendations"].append({"priority": "Optional", "action": "Excellence program",
                                       "details": "Advanced topics"})
        ins["study_tips"] = ["Peer tutoring", "Competitions"]
    if len(marks) >= 5:
        trend = np.polyfit(range(len(marks)), marks, 1)[0]
        ins["predictions"].append("📈 Positive trend" if trend > 0
                                   else "📉 Declining" if trend < 0 else "➡️ Stable")
    max_total = len(marks) * 100
    ins["improvement_potential"] = round(((max_total - sum(marks)) / max_total) * 100, 2)
    return ins


def detect_anomalies(marks):
    anomalies = []
    arr = np.array(marks)
    if len(arr) < 3:
        return anomalies
    mean, std = np.mean(arr), np.std(arr)
    for i, m in enumerate(marks):
        z = (m - mean) / std if std > 0 else 0
        if abs(z) > 2:
            anomalies.append({"subject": f"Subject {i+1}", "marks": m, "z_score": round(z, 2),
                              "type": "Exceptionally High" if m > mean else "Exceptionally Low",
                              "suggestion": "Review"})
    return anomalies


def generate_recommendations(marks, avg):
    recs = []
    if avg < 40:
        recs += ["🔴 Urgent: Consider additional tutoring", "📚 Focus on foundational concepts"]
    elif avg < 60:
        recs += ["🟡 Need improvement: Study groups recommended", "📝 Create structured schedule"]
    elif avg < 75:
        recs += ["🟢 Good performance: Focus on weak areas", "🎯 Set higher targets"]
    else:
        recs += ["🌟 Excellent! Help peers", "🏆 Aim for top performance"]
    weak = [i for i, m in enumerate(marks) if m < 40]
    if weak:
        recs.append(f"⚠️ Focus on subjects {', '.join(str(i+1) for i in weak)}")
    strong = [i for i, m in enumerate(marks) if m >= 80]
    if strong:
        recs.append(f"💪 Strong in subjects {', '.join(str(i+1) for i in strong)}")
    return recs


def analyze_trends(student_id):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM performance_trends
                WHERE student_id=? ORDER BY created_at ASC
            """, (student_id,))
            trends = [dict(r) for r in cursor.fetchall()]
            if len(trends) < 2:
                return {"message": "Not enough data for trend analysis", "trends": trends}
            avgs = [t["average"] for t in trends]
            imp = avgs[-1] - avgs[0]
            d = "📈 Improving" if imp > 5 else "📉 Declining" if imp < -5 else "➡️ Stable"
            return {"student_id": student_id, "total_records": len(trends),
                    "first_average": avgs[0], "current_average": avgs[-1],
                    "improvement": round(imp, 2), "trend_direction": d, "trends": trends}
    except Exception as e:
        return {"error": str(e)}


# ============================================================
# AUTH DEPENDENCIES
# ============================================================
async def get_current_user(token: str = Depends(oauth2_scheme)):
    if not token:
        return None
    if is_token_blacklisted(token):
        return None
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        return None
    username = payload.get("sub")
    if not username:
        return None
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND is_active=1", (username,))
        row = cursor.fetchone()
        return dict(row) if row else None


async def require_user(user=Depends(get_current_user)):
    if user is None:
        raise HTTPException(401, "Authentication required", headers={"WWW-Authenticate": "Bearer"})
    return user


async def require_admin(user=Depends(require_user)):
    if user.get("role") != "admin":
        raise HTTPException(403, "Admin access required")
    return user


def require_role(*roles):
    async def checker(user=Depends(require_user)):
        if user.get("role") not in roles:
            raise HTTPException(403, f"Requires role: {', '.join(roles)}")
        return user
    return checker


# ============================================================
# AUTH ENDPOINTS
# ============================================================
@app.post("/auth/register")
@limiter.limit("10/minute")
def register_user(request: Request, user: UserRegister):
    is_valid, error = validate_password_strength(user.password)
    if not is_valid:
        raise HTTPException(400, error)

    if not validate_email(user.email):
        raise HTTPException(400, "Invalid email format")

    phone_clean = None
    if user.phone:
        ok, result = validate_phone(user.phone)
        if not ok:
            raise HTTPException(400, result)
        phone_clean = result

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username=? OR email=?",
                       (user.username, user.email.lower()))
        if cursor.fetchone():
            raise HTTPException(400, "Username or email already exists")

        hashed = get_password_hash(user.password)
        cursor.execute("""
            INSERT INTO users (username, email, phone, hashed_password, full_name,
                               role, email_verified, phone_verified)
            VALUES (?, ?, ?, ?, ?, ?, 0, 0)
        """, (user.username, user.email.lower(), phone_clean, hashed,
              user.full_name or user.username, user.role))
        user_id = cursor.lastrowid
        conn.commit()

    # Send email OTP
    otp = generate_otp()
    save_otp(user.email.lower(), otp, "verification")
    send_email_otp(user.email, otp, "verification")

    # Send phone OTP if provided
    if phone_clean:
        phone_otp = generate_otp()
        save_otp(phone_clean, phone_otp, "phone_verification")
        send_sms_otp(phone_clean, phone_otp)

    log_audit(user_id, user.username, "register", "user",
              f"Role: {user.role}", request.client.host if request.client else None)

    return {
        "message": "Registration successful. Check your email for the verification code.",
        "user_id": user_id,
        "username": user.username,
        "email": user.email.lower(),
        "phone": phone_clean,
        "email_verification_required": True,
        "phone_verification_required": bool(phone_clean),
    }


@app.post("/auth/login")
@limiter.limit("10/minute")
def login(request: Request, username: str = "", password: str = "",
          email: str = "", pwd: str = ""):
    """
    Login with username OR email.
    Accepts: username+password OR email+pwd
    """
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "")

    identifier = (username or email or "").strip().lower()
    pwd_value = password or pwd or ""

    if not identifier or not pwd_value:
        raise HTTPException(400, "Username/email and password required")

    lock_msg = check_account_locked(identifier)
    if lock_msg:
        log_login_attempt(identifier, ip, ua, False, "account_locked")
        raise HTTPException(423, lock_msg)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? OR email=?",
                       (identifier, identifier))
        user = cursor.fetchone()

    if not user:
        log_login_attempt(identifier, ip, ua, False, "user_not_found")
        raise HTTPException(401, "Invalid credentials")

    user = dict(user)

    if not user.get("is_active", 1):
        log_login_attempt(identifier, ip, ua, False, "account_disabled")
        raise HTTPException(403, "Account disabled")

    if not verify_password(pwd_value, user["hashed_password"]):
        increment_failed_attempts(user["username"])
        log_login_attempt(identifier, ip, ua, False, "wrong_password")
        raise HTTPException(401, "Invalid credentials")

    reset_failed_attempts(user["username"])
    log_login_attempt(identifier, ip, ua, True, "success")
    log_audit(user["id"], user["username"], "login", "user", None, ip)

    access_token = create_access_token({
        "sub": user["username"], "role": user["role"], "user_id": user["id"]
    })
    refresh = create_refresh_token({"sub": user["username"], "user_id": user["id"]})

    return {
        "access_token": access_token,
        "refresh_token": refresh,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "phone": user.get("phone"),
            "full_name": user.get("full_name"),
            "role": user["role"],
            "email_verified": bool(user.get("email_verified")),
            "phone_verified": bool(user.get("phone_verified")),
        }
    }


@app.post("/auth/send-otp")
@limiter.limit("5/minute")
def send_otp(request: Request, data: OTPRequest):
    """Send OTP for verification or password reset"""
    identifier = data.identifier.strip().lower()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email=? OR phone=?",
                       (identifier, data.identifier.strip()))
        user = cursor.fetchone()

    if not user and data.purpose == "reset_password":
        raise HTTPException(404, "No account found with that email/phone")

    otp = generate_otp()

    if "@" in identifier:
        save_otp(identifier, otp, data.purpose)
        sent = send_email_otp(identifier, otp, data.purpose)
        return {
            "message": "OTP sent to your email" if sent else "OTP sent (check console)",
            "delivery": "email" if sent else "console"
        }
    else:
        ok, phone = validate_phone(identifier)
        if not ok:
            raise HTTPException(400, phone)
        save_otp(phone, otp, data.purpose)
        sent = send_sms_otp(phone, otp)
        return {
            "message": "OTP sent to your phone" if sent else "OTP sent (check console)",
            "delivery": "sms" if sent else "console"
        }


@app.post("/auth/verify-otp")
def verify_otp_endpoint(data: OTPVerify):
    """Verify OTP for email/phone verification"""
    ok, msg = verify_otp(data.identifier.strip().lower(), data.otp_code, data.purpose)
    if not ok:
        raise HTTPException(400, msg)

    # Mark verified in users table
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if data.purpose == "verification":
            cursor.execute("UPDATE users SET email_verified=1 WHERE email=?",
                           (data.identifier.strip().lower(),))
        elif data.purpose == "phone_verification":
            ok_p, phone = validate_phone(data.identifier)
            if ok_p:
                cursor.execute("UPDATE users SET phone_verified=1 WHERE phone=?", (phone,))
        conn.commit()

    return {"message": "Verification successful", "verified": True}


@app.post("/auth/reset-password")
@limiter.limit("5/minute")
def reset_password(request: Request, data: PasswordResetOTP):
    """Reset password using OTP"""
    ok, msg = verify_otp(data.identifier.strip().lower(), data.otp_code, "reset_password")
    if not ok:
        raise HTTPException(400, msg)

    is_valid, error = validate_password_strength(data.new_password)
    if not is_valid:
        raise HTTPException(400, error)

    hashed = get_password_hash(data.new_password)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users SET hashed_password=?, failed_login_attempts=0, locked_until=NULL
            WHERE email=? OR phone=?
        """, (hashed, data.identifier.strip().lower(), data.identifier.strip()))
        if cursor.rowcount == 0:
            raise HTTPException(404, "User not found")
        conn.commit()

    log_audit(None, data.identifier, "reset_password", "user", None,
              request.client.host if request.client else None)

    return {"message": "Password reset successfully. Please log in."}


@app.get("/auth/me")
def get_me(user=Depends(require_user)):
    return {
        "id": user["id"], "username": user["username"], "email": user["email"],
        "phone": user.get("phone"), "full_name": user.get("full_name"),
        "role": user["role"],
        "email_verified": bool(user.get("email_verified")),
        "phone_verified": bool(user.get("phone_verified")),
        "last_login": user.get("last_login"),
        "created_at": user.get("created_at"),
    }


@app.post("/auth/change-password")
def change_password(data: PasswordChange, user=Depends(require_user)):
    if not verify_password(data.old_password, user["hashed_password"]):
        raise HTTPException(400, "Current password is incorrect")
    is_valid, error = validate_password_strength(data.new_password)
    if not is_valid:
        raise HTTPException(400, error)
    new_hash = get_password_hash(data.new_password)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET hashed_password=? WHERE id=?", (new_hash, user["id"]))
        conn.commit()
    return {"message": "Password changed successfully"}


@app.post("/auth/logout")
def logout(token: str = Depends(oauth2_scheme), user=Depends(require_user)):
    if token:
        payload = decode_token(token)
        if payload and payload.get("exp"):
            blacklist_token(token, datetime.utcfromtimestamp(payload["exp"]))
    return {"message": "Logged out"}


@app.post("/auth/check-strength")
def check_strength(password: str = Query(..., min_length=1)):
    score = 0
    if len(password) >= 8: score += 20
    if len(password) >= 12: score += 10
    if re.search(r"[A-Z]", password): score += 15
    if re.search(r"[a-z]", password): score += 15
    if re.search(r"\d", password): score += 15
    if re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\\/;'`~]", password): score += 15
    if len(set(password)) > 6: score += 10
    score = min(score, 100)
    label = "Weak" if score < 40 else "Fair" if score < 60 else "Good" if score < 80 else "Strong"
    valid, err = validate_password_strength(password)
    return {"score": score, "label": label, "valid": valid, "error": err}


# ============================================================
# USER MANAGEMENT (ADMIN)
# ============================================================
@app.get("/auth/users")
def list_users(admin=Depends(require_admin)):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username, email, phone, full_name, role, is_active,
                   email_verified, phone_verified, last_login, created_at
            FROM users ORDER BY id
        """)
        return {"users": [dict(r) for r in cursor.fetchall()]}


@app.put("/auth/users/{user_id}/toggle")
def toggle_user(request: Request, user_id: int, admin=Depends(require_admin)):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT is_active, username FROM users WHERE id=?", (user_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(404, "User not found")
        if row["username"] == admin["username"]:
            raise HTTPException(400, "Cannot disable your own account")
        new_status = 0 if row["is_active"] else 1
        cursor.execute("UPDATE users SET is_active=? WHERE id=?", (new_status, user_id))
        conn.commit()
    log_audit(admin["id"], admin["username"], "toggle_user", f"user:{user_id}",
              f"new_status={new_status}", request.client.host if request.client else None)
    return {"message": "Toggled", "user_id": user_id, "is_active": new_status}


@app.put("/auth/users/{user_id}/role")
def change_role(request: Request, user_id: int, role: str, admin=Depends(require_admin)):
    if role not in ["admin", "teacher", "student", "parent"]:
        raise HTTPException(400, "Invalid role")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username, role FROM users WHERE id=?", (user_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(404, "User not found")

        old_role = row["role"]
        username = row["username"]
        if old_role == role:
            raise HTTPException(400, f"Already has role '{role}'")

        cursor.execute("UPDATE users SET role=? WHERE id=?", (role, user_id))
        cursor.execute("""
            INSERT INTO role_history (user_id, username, old_role, new_role, changed_by, changed_by_username)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, username, old_role, role, admin["id"], admin["username"]))
        conn.commit()

    log_audit(admin["id"], admin["username"], "change_role", f"user:{user_id}",
              f"{old_role} -> {role}", request.client.host if request.client else None)
    return {"message": f"Role changed: {old_role} → {role}",
            "user_id": user_id, "old_role": old_role, "new_role": role}


@app.get("/auth/users/{user_id}/role-history")
def get_role_history(user_id: int, admin=Depends(require_admin)):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM role_history WHERE user_id=?
            ORDER BY created_at DESC LIMIT 50
        """, (user_id,))
        return {"history": [dict(r) for r in cursor.fetchall()]}


@app.put("/auth/users/{user_id}/revert-role")
def revert_role(request: Request, user_id: int, admin=Depends(require_admin)):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT old_role FROM role_history WHERE user_id=?
            ORDER BY created_at DESC LIMIT 1
        """, (user_id,))
        last = cursor.fetchone()
        if not last:
            raise HTTPException(400, "No previous role change")

        cursor.execute("SELECT username, role FROM users WHERE id=?", (user_id,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(404, "User not found")

        current = user["role"]
        prev = last["old_role"]
        if current == prev:
            raise HTTPException(400, f"Already at '{prev}'")

        cursor.execute("UPDATE users SET role=? WHERE id=?", (prev, user_id))
        cursor.execute("""
            INSERT INTO role_history (user_id, username, old_role, new_role, changed_by, changed_by_username)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, user["username"], current, prev, admin["id"], admin["username"]))
        conn.commit()

    log_audit(admin["id"], admin["username"], "revert_role", f"user:{user_id}",
              f"{current} -> {prev}", request.client.host if request.client else None)
    return {"message": f"Reverted: {current} → {prev}",
            "user_id": user_id, "old_role": current, "new_role": prev}


@app.delete("/auth/users/{user_id}")
def delete_user(request: Request, user_id: int, admin=Depends(require_admin)):
    if user_id == admin["id"]:
        raise HTTPException(400, "Cannot delete your own account")
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE id=?", (user_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(404, "User not found")
        cursor.execute("DELETE FROM parent_children WHERE parent_user_id=?", (user_id,))
        cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
        conn.commit()
    log_audit(admin["id"], admin["username"], "delete_user", f"user:{user_id}",
              f"deleted:{row['username']}", request.client.host if request.client else None)
    return {"message": "User deleted"}


# ============================================================
# AUDIT
# ============================================================
@app.get("/audit/logs")
def audit_logs(admin=Depends(require_admin), limit: int = Query(100, ge=1, le=1000)):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM audit_log ORDER BY created_at DESC LIMIT ?", (limit,))
        return {"logs": [dict(r) for r in cursor.fetchall()]}


@app.get("/audit/login-attempts")
def login_attempts(admin=Depends(require_admin), limit: int = Query(100, ge=1, le=1000)):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM login_attempts ORDER BY created_at DESC LIMIT ?", (limit,))
        return {"attempts": [dict(r) for r in cursor.fetchall()]}


# ============================================================
# ROLE-BASED DATA ACCESS
# ============================================================
def get_accessible_students(user):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if user["role"] in ["admin", "teacher"]:
            cursor.execute("SELECT * FROM students ORDER BY id DESC")
        elif user["role"] == "parent":
            cursor.execute("""
                SELECT s.* FROM students s
                JOIN parent_children pc ON s.id = pc.student_id
                WHERE pc.parent_user_id = ? ORDER BY s.id DESC
            """, (user["id"],))
        elif user["role"] == "student":
            cursor.execute("SELECT * FROM students WHERE user_id = ? ORDER BY id DESC",
                           (user["id"],))
        else:
            return []

        students = []
        for r in cursor.fetchall():
            s = dict(r)
            s["marks"] = json.loads(s["marks"])
            s["subjects"] = json.loads(s["subjects"])
            students.append(s)
        return students


# ============================================================
# STUDENTS
# ============================================================
@app.get("/students")
def get_all_students(user=Depends(require_user),
                     limit: int = Query(100, ge=1, le=1000),
                     offset: int = Query(0, ge=0)):
    try:
        all_students = get_accessible_students(user)
        total = len(all_students)
        return {
            "count": total, "limit": limit, "offset": offset,
            "page": (offset // limit) + 1 if limit > 0 else 1,
            "total_pages": (total + limit - 1) // limit if limit > 0 else 1,
            "students": all_students[offset:offset + limit],
        }
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")


@app.get("/students/{student_id}")
def get_student_by_id(student_id: int, user=Depends(require_user)):
    for s in get_accessible_students(user):
        if s["id"] == student_id:
            return s
    raise HTTPException(404, "Not found or access denied")


@app.post("/students/save")
def save_student(student: StudentRecord, user=Depends(require_role("admin", "teacher"))):
    try:
        total = student.total_marks if student.total_marks is not None else sum(student.marks)
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO students (name, marks, subjects, grade, average, total_marks,
                                      timestamp, semester, batch_year, department)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (student.name, json.dumps(student.marks), json.dumps(student.subjects),
                  student.grade, student.average, total,
                  student.timestamp or datetime.now().isoformat(),
                  student.semester, student.batch_year, student.department))
            sid = cursor.lastrowid
            cursor.execute("""
                INSERT INTO performance_trends (student_id, semester, average, grade, total_marks, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (sid, student.semester, student.average, student.grade, total,
                  datetime.now().isoformat()))
            if student.grade in ["A", "A+"]:
                cursor.execute("INSERT INTO notifications (student_id, message, type) VALUES (?, ?, ?)",
                               (sid, f"🎉 Congratulations! Grade {student.grade}", "Achievement"))
            elif student.grade == "F":
                cursor.execute("INSERT INTO notifications (student_id, message, type) VALUES (?, ?, ?)",
                               (sid, "⚠️ Warning: Grade F. Seek support.", "Warning"))
            conn.commit()
        return {"message": "Saved", "id": sid}
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")


@app.delete("/students/delete/{student_id}")
def delete_student(student_id: int, user=Depends(require_role("admin", "teacher"))):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM students WHERE id=?", (student_id,))
            if not cursor.fetchone():
                raise HTTPException(404, "Not found")
            cursor.execute("DELETE FROM attendance WHERE student_id=?", (student_id,))
            cursor.execute("DELETE FROM notifications WHERE student_id=?", (student_id,))
            cursor.execute("DELETE FROM performance_trends WHERE student_id=?", (student_id,))
            cursor.execute("DELETE FROM parent_children WHERE student_id=?", (student_id,))
            cursor.execute("DELETE FROM students WHERE id=?", (student_id,))
            conn.commit()
        return {"message": "Deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")


@app.get("/students/search")
def search_students(name: str = Query(..., min_length=1), user=Depends(require_user), limit: int = 50):
    results = [s for s in get_accessible_students(user) if name.lower() in s["name"].lower()]
    return {"count": len(results), "students": results[:limit]}


@app.get("/students/import-template")
def get_import_template(user=Depends(require_role("admin", "teacher"))):
    template = """name,marks,subjects,semester,department,batch_year
John Doe,"85,92,78,88,91","Math,Science,English,History,Art",Fall 2024,Computer Science,2024
"""
    return Response(content=template, media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=template.csv"})


@app.post("/students/import-csv")
async def import_csv(user=Depends(require_role("admin", "teacher")),
                     file: UploadFile = File(...)):
    try:
        content = await file.read()
        text = None
        for enc in ["utf-8", "utf-8-sig", "latin-1"]:
            try:
                text = content.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        if text is None:
            raise HTTPException(400, "Cannot decode file")

        reader = csv_module.DictReader(io.StringIO(text))
        fmap = {f.lower().strip(): f for f in (reader.fieldnames or [])}
        missing = [r for r in ["name", "marks", "subjects"] if r not in fmap]
        if missing:
            raise HTTPException(400, f"Missing columns: {missing}")

        imported = 0
        failed = []
        row_num = 1
        with get_db_connection() as conn:
            cursor = conn.cursor()
            for row in reader:
                row_num += 1
                try:
                    name = str(row.get(fmap['name'], '')).strip()
                    if not name:
                        failed.append(f"Row {row_num}: empty name")
                        continue
                    marks_raw = str(row.get(fmap['marks'], '')).strip()
                    marks = []
                    for sep in [',', ';', '|']:
                        if sep in marks_raw:
                            marks = [float(m.strip()) for m in marks_raw.split(sep) if m.strip()]
                            break
                    if not marks:
                        marks = [float(marks_raw)]

                    subj_raw = str(row.get(fmap['subjects'], '')).strip()
                    subjects = []
                    for sep in [',', ';', '|']:
                        if sep in subj_raw:
                            subjects = [s.strip() for s in subj_raw.split(sep) if s.strip()]
                            break
                    if not subjects:
                        subjects = [subj_raw]

                    if len(marks) != len(subjects):
                        failed.append(f"Row {row_num}: marks/subjects mismatch")
                        continue
                    if any(m < 0 or m > 100 for m in marks):
                        failed.append(f"Row {row_num}: marks 0-100 only")
                        continue

                    for sname in subjects:
                        ok, err = validate_subject_name(sname)
                        if not ok:
                            failed.append(f"Row {row_num}: {err}")
                            break
                    else:
                        stats = calculate_statistics(marks)
                        grade, _ = determine_grade(stats["average"])
                        semester = str(row.get(fmap.get('semester', ''), '') or '').strip() or None
                        dept = str(row.get(fmap.get('department', ''), '') or '').strip() or None
                        by = str(row.get(fmap.get('batch_year', ''), '') or '').strip() or None

                        cursor.execute("""
                            INSERT INTO students (name, marks, subjects, grade, average, total_marks,
                                                  timestamp, semester, batch_year, department)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (name, json.dumps(marks), json.dumps(subjects), grade,
                              stats["average"], stats["total"], datetime.now().isoformat(),
                              semester, by, dept))
                        imported += 1
                except Exception as e:
                    failed.append(f"Row {row_num}: {str(e)}")
            conn.commit()
        return {"message": f"Imported {imported}", "imported": imported,
                "failed_count": len(failed), "failed": failed[:20]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")


@app.get("/export/csv")
def export_csv(user=Depends(require_user)):
    try:
        students = get_accessible_students(user)
        if not students:
            raise HTTPException(404, "No data")
        out = io.StringIO()
        out.write("id,name,marks,subjects,grade,average,total_marks,semester,department,batch_year\n")
        for s in students:
            marks_str = '"' + ",".join(str(m) for m in s["marks"]) + '"'
            subj_str = '"' + ",".join(s["subjects"]) + '"'
            out.write(f'{s["id"]},"{s["name"]}",{marks_str},{subj_str},{s["grade"]},'
                      f'{s["average"]},{s["total_marks"]},{s.get("semester") or ""},'
                      f'{s.get("department") or ""},{s.get("batch_year") or ""}\n')
        return Response(content=out.getvalue(), media_type="text/csv",
                        headers={"Content-Disposition":
                                 f"attachment; filename=students_{datetime.now().strftime('%Y%m%d')}.csv"})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")


@app.get("/export/json")
def export_json(user=Depends(require_user)):
    try:
        students = get_accessible_students(user)
        if not students:
            raise HTTPException(404, "No data")
        return {"export_date": datetime.now().isoformat(),
                "total_students": len(students), "students": students}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")


# ============================================================
# ANALYZE
# ============================================================
@app.post("/analyze")
def analyze_marks(request: MarksRequest, user=Depends(require_user)):
    marks = request.marks
    threshold = request.passing_threshold
    stats = calculate_statistics(marks)
    grade, gp = determine_grade(stats["average"], request.grade_scheme)
    passed = sum(1 for m in marks if m >= threshold)
    failed = len(marks) - passed

    subject_wise = []
    for i, mark in enumerate(marks):
        subj = (request.subject_names[i] if request.subject_names and i < len(request.subject_names)
                else f"Subject {i+1}")
        subject_wise.append({
            "subject": subj, "marks": mark,
            "status": "Pass" if mark >= threshold else "Fail",
            "performance": "Excellent" if mark >= 80 else "Good" if mark >= 60
                            else "Average" if mark >= 40 else "Needs Improvement",
        })

    return {
        "student_name": request.student_name or "Unnamed",
        "semester": request.semester, "batch_year": request.batch_year,
        "department": request.department,
        "total_marks": stats["total"], "average": stats["average"],
        "highest": stats["highest"], "lowest": stats["lowest"],
        "median": stats["median"], "std_deviation": stats["std_deviation"],
        "variance": stats["variance"], "quartiles": stats["quartiles"],
        "passed": passed, "failed": failed,
        "pass_percentage": (passed / len(marks)) * 100,
        "grade": grade, "grade_points": gp,
        "subject_wise": subject_wise,
        "performance_summary": {
            "performance_level": "Excellent" if stats["average"] >= 80 else "Good"
                                 if stats["average"] >= 60 else "Average"
                                 if stats["average"] >= 40 else "Poor",
            "consistency": "High" if stats["std_deviation"] < 15
                           else "Medium" if stats["std_deviation"] < 30 else "Low",
        },
        "ai_insights": generate_ai_insights(marks, stats["average"], request.subject_names or []),
        "anomalies": detect_anomalies(marks),
        "recommendations": generate_recommendations(marks, stats["average"]),
        "timestamp": datetime.now().isoformat(),
    }


# ============================================================
# ATTENDANCE
# ============================================================
@app.post("/attendance")
def record_attendance(att: AttendanceRecord, user=Depends(require_role("admin", "teacher"))):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM students WHERE id=?", (att.student_id,))
        s = cursor.fetchone()
        if not s:
            raise HTTPException(404, "Student not found")
        cursor.execute("""
            INSERT INTO attendance (student_id, date, status, subject, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (att.student_id, att.date, att.status, att.subject, att.notes))
        if att.status in ["Absent", "Late"]:
            cursor.execute("INSERT INTO notifications (student_id, message, type) VALUES (?, ?, ?)",
                           (att.student_id, f"⚠️ Marked {att.status} on {att.date}", "Warning"))
        conn.commit()
    return {"message": "Recorded", "id": cursor.lastrowid}


@app.get("/attendance/stats/overall")
def attendance_overall(user=Depends(require_user)):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as t FROM attendance")
        total = cursor.fetchone()["t"]
        if total == 0:
            return {"total_records": 0, "message": "No records"}
        cursor.execute("SELECT status, COUNT(*) as c FROM attendance GROUP BY status")
        counts = {r["status"]: r["c"] for r in cursor.fetchall()}
        return {
            "total_records": total,
            "present": counts.get("Present", 0),
            "absent": counts.get("Absent", 0),
            "late": counts.get("Late", 0),
            "excused": counts.get("Excused", 0),
            "overall_rate": round(counts.get("Present", 0) / total * 100, 2),
        }


@app.get("/attendance/{student_id}/stats")
def attendance_stats(student_id: int, user=Depends(require_user)):
    if not any(s["id"] == student_id for s in get_accessible_students(user)):
        raise HTTPException(403, "Access denied")
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM students WHERE id=?", (student_id,))
        s = cursor.fetchone()
        if not s:
            raise HTTPException(404, "Student not found")
        cursor.execute("SELECT status, COUNT(*) as c FROM attendance WHERE student_id=? GROUP BY status",
                       (student_id,))
        st = {r["status"]: r["c"] for r in cursor.fetchall()}
        total = sum(st.values())
        if total == 0:
            return {"student_id": student_id, "student_name": s["name"], "total_days": 0,
                    "attendance_rate": 0, "message": "No records"}
        present = st.get("Present", 0)
        return {
            "student_id": student_id, "student_name": s["name"],
            "total_days": total, "present": present,
            "absent": st.get("Absent", 0), "late": st.get("Late", 0),
            "excused": st.get("Excused", 0),
            "attendance_rate": round(present / total * 100, 2),
        }


# ============================================================
# NOTIFICATIONS
# ============================================================
@app.get("/notifications")
def get_notifications(user=Depends(require_user), limit: int = 50):
    accessible = get_accessible_students(user)
    ids = [s["id"] for s in accessible]
    if not ids:
        return {"count": 0, "unread_count": 0, "notifications": []}
    with get_db_connection() as conn:
        cursor = conn.cursor()
        ph = ",".join("?" * len(ids))
        cursor.execute(f"""
            SELECT * FROM notifications WHERE student_id IN ({ph})
            ORDER BY created_at DESC LIMIT ?
        """, ids + [limit])
        notifs = [dict(r) for r in cursor.fetchall()]
        cursor.execute(f"SELECT COUNT(*) as c FROM notifications WHERE student_id IN ({ph}) AND is_read=0", ids)
        unread = cursor.fetchone()["c"]
        return {"count": len(notifs), "unread_count": unread, "notifications": notifs}


@app.put("/notifications/mark-read/{notif_id}")
def mark_read(notif_id: int, user=Depends(require_user)):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE notifications SET is_read=1 WHERE id=?", (notif_id,))
        conn.commit()
    return {"message": "Read"}


@app.put("/notifications/mark-all-read")
def mark_all_read(user=Depends(require_user)):
    accessible = get_accessible_students(user)
    ids = [s["id"] for s in accessible]
    if not ids:
        return {"message": "No notifications"}
    with get_db_connection() as conn:
        cursor = conn.cursor()
        ph = ",".join("?" * len(ids))
        cursor.execute(f"UPDATE notifications SET is_read=1 WHERE student_id IN ({ph})", ids)
        conn.commit()
    return {"message": "All read"}


# ============================================================
# STATS
# ============================================================
@app.get("/stats/overall")
def overall_stats(user=Depends(require_user)):
    students = get_accessible_students(user)
    if not students:
        return {"message": "No data"}
    avgs = [s["average"] for s in students]
    grades = [s["grade"] for s in students]
    dist = {}
    for g in grades:
        dist[g] = dist.get(g, 0) + 1
    return {
        "total_students": len(students),
        "average_of_averages": round(float(np.mean(avgs)), 2),
        "median_average": round(float(np.median(avgs)), 2),
        "highest_average": round(float(max(avgs)), 2),
        "lowest_average": round(float(min(avgs)), 2),
        "grade_distribution": dist,
        "pass_rate": round(sum(1 for s in students if s["grade"] != "F") / len(students) * 100, 2),
        "distinction_rate": round(sum(1 for s in students if s["grade"] in ["A", "A+"]) / len(students) * 100, 2),
        "top_performers": sorted(students, key=lambda x: x["average"], reverse=True)[:5],
    }


@app.get("/analytics/dashboard")
def analytics_dashboard(user=Depends(require_user)):
    students = get_accessible_students(user)
    if not students:
        return {"has_data": False, "total_students": 0, "message": "No data"}
    avgs = [s["average"] for s in students]
    grades = [s["grade"] for s in students]
    dist = {}
    for g in grades:
        dist[g] = dist.get(g, 0) + 1
    ranges = {
        "90-100 (A+)": sum(1 for a in avgs if a >= 90),
        "80-89 (A)": sum(1 for a in avgs if 80 <= a < 90),
        "70-79 (B)": sum(1 for a in avgs if 70 <= a < 80),
        "60-69 (C)": sum(1 for a in avgs if 60 <= a < 70),
        "50-59 (D)": sum(1 for a in avgs if 50 <= a < 60),
        "40-49 (E)": sum(1 for a in avgs if 40 <= a < 50),
        "0-39 (F)": sum(1 for a in avgs if a < 40),
    }
    subj_data = {}
    for s in students:
        for i, subj in enumerate(s["subjects"]):
            subj_data.setdefault(subj, []).append(s["marks"][i] if i < len(s["marks"]) else 0)
    subj_analytics = []
    for subj, marks in subj_data.items():
        arr = np.array(marks)
        subj_analytics.append({
            "subject": subj,
            "average": round(float(np.mean(arr)), 2),
            "highest": float(np.max(arr)),
            "lowest": float(np.min(arr)),
            "pass_rate": round(sum(1 for m in marks if m >= 40) / len(marks) * 100, 2),
            "count": len(marks),
        })
    subj_analytics.sort(key=lambda x: x["average"], reverse=True)
    passed = sum(1 for g in grades if g != "F")
    return {
        "has_data": True,
        "total_students": len(students),
        "overall_average": round(float(np.mean(avgs)), 2),
        "overall_median": round(float(np.median(avgs)), 2),
        "overall_std": round(float(np.std(avgs)), 2),
        "highest_average": round(float(max(avgs)), 2),
        "lowest_average": round(float(min(avgs)), 2),
        "passed": passed, "failed": len(students) - passed,
        "pass_rate": round(passed / len(students) * 100, 2),
        "distinction_rate": round(sum(1 for g in grades if g in ["A", "A+"]) / len(students) * 100, 2),
        "grade_distribution": dist, "grade_ranges": ranges,
        "subject_analytics": subj_analytics,
        "top_performers": sorted([
            {"id": s["id"], "name": s["name"], "average": s["average"], "grade": s["grade"]}
            for s in students
        ], key=lambda x: x["average"], reverse=True)[:10],
        "hardest_subject": subj_analytics[-1] if subj_analytics else None,
        "easiest_subject": subj_analytics[0] if subj_analytics else None,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/trends/{student_id}")
def trends(student_id: int, user=Depends(require_user)):
    if not any(s["id"] == student_id for s in get_accessible_students(user)):
        raise HTTPException(403, "Access denied")
    return analyze_trends(student_id)


# ============================================================
# PDF
# ============================================================
@app.get("/students/{student_id}/report-card")
def report_card(student_id: int, user=Depends(require_user)):
    if generate_report_card is None:
        raise HTTPException(500, "PDF not available")
    student = next((s for s in get_accessible_students(user) if s["id"] == student_id), None)
    if not student:
        raise HTTPException(404, "Not found")
    student["recommendations"] = generate_recommendations(student["marks"], student["average"])
    fname = f"report_{student_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    rdir = os.path.join(os.path.dirname(__file__), "reports")
    os.makedirs(rdir, exist_ok=True)
    fpath = os.path.join(rdir, fname)
    generate_report_card(student, fpath)
    return FileResponse(fpath, media_type="application/pdf", filename=fname)


# ============================================================
# HEALTH & HOME
# ============================================================
@app.get("/")
def home():
    return {"message": "Student Marks Analyzer API", "version": "6.0.0",
            "features": ["username/email login", "email OTP", "phone OTP (dev)",
                         "password reset via OTP", "role-based access",
                         "audit logging", "CSV import/export", "PDF reports"]}


@app.get("/health")
def health():
    try:
        with get_db_connection() as conn:
            conn.execute("SELECT 1")
        db = "healthy"
    except Exception:
        db = "unhealthy"
    return {"status": "healthy" if db == "healthy" else "degraded",
            "database": db, "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
