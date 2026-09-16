"""
Minimal deployment prep — creates all essential config files.
Unpinned requirements for maximum compatibility.
"""
import secrets
from pathlib import Path

ROOT = Path(__file__).parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"


def w(path, content, skip=True):
    path.parent.mkdir(parents=True, exist_ok=True)
    if skip and path.exists():
        print(f"  [SKIP] {path.relative_to(ROOT)}")
        return
    path.write_text(content, encoding="utf-8")
    print(f"  [OK]   {path.relative_to(ROOT)}")


print("=" * 70)
print("  DEPLOYMENT PREPARATION — Unpinned Requirements")
print("=" * 70)
print()

# ============================================================
# Backend requirements (unpinned)
# ============================================================
w(BACKEND / "requirements.txt", """fastapi
uvicorn[standard]
python-multipart
psycopg2-binary
sqlalchemy
alembic
python-dotenv
passlib[bcrypt]
python-jose[cryptography]
pyotp
qrcode[pil]
apscheduler
requests
pandas
numpy
scikit-learn
joblib
openpyxl
pillow
websockets
fpdf2
slowapi
bcrypt
twilio
""", skip=False)

# ============================================================
# Frontend requirements (unpinned)
# ============================================================
w(FRONTEND / "requirements.txt", """streamlit
streamlit-option-menu
requests
pandas
plotly
websockets
""", skip=False)

# ============================================================
# Procfile
# ============================================================
w(BACKEND / "Procfile", "web: uvicorn main:app --host 0.0.0.0 --port $PORT\n", skip=False)

# ============================================================
# runtime.txt
# ============================================================
w(BACKEND / "runtime.txt", "python-3.11.10\n", skip=False)

# ============================================================
# render.yaml
# ============================================================
w(ROOT / "render.yaml", """services:
  - type: web
    name: student-marks-api
    runtime: python
    plan: free
    region: singapore
    rootDir: backend
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /health
    autoDeploy: true
    envVars:
      - key: SECRET_KEY
        generateValue: true
      - key: REFRESH_SECRET_KEY
        generateValue: true
      - key: ALGORITHM
        value: HS256
      - key: ACCESS_TOKEN_EXPIRE_MINUTES
        value: "30"
      - key: DATABASE_URL
        sync: false
      - key: CORS_ORIGINS
        sync: false
      - key: PASSWORD_MIN_LENGTH
        value: "10"
      - key: SMTP_HOST
        sync: false
      - key: SMTP_PORT
        value: "587"
      - key: SMTP_USER
        sync: false
      - key: SMTP_PASS
        sync: false
      - key: SMTP_FROM
        sync: false
      - key: DEV_MODE_SMS
        value: "true"
      - key: PYTHON_VERSION
        value: "3.11.10"
""", skip=False)

# ============================================================
# Streamlit secrets
# ============================================================
w(FRONTEND / ".streamlit" / "secrets.toml",
  'API_URL = "https://your-render-api.onrender.com"\n', skip=False)

# ============================================================
# Streamlit config
# ============================================================
w(FRONTEND / ".streamlit" / "config.toml", """[theme]
primaryColor = "#667eea"

[server]
headless = true
enableXsrfProtection = true
maxUploadSize = 10

[browser]
gatherUsageStats = false
""", skip=False)

# ============================================================
# .env.example
# ============================================================
w(ROOT / ".env.example", """# Student Marks Analyzer — Environment Template
# Copy to .env for local dev. For production, use Render env vars.

# Security
SECRET_KEY=change-me-64-char-random
REFRESH_SECRET_KEY=change-me-different-64-char-random
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
# Local: leave empty (uses SQLite)
# Production: Neon PostgreSQL URL
DATABASE_URL=

# CORS
CORS_ORIGINS=http://localhost:8501

# Password Policy
PASSWORD_MIN_LENGTH=10
PASSWORD_HISTORY_CHECK=3

# Email (Brevo)
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASS=
SMTP_FROM=noreply@yourdomain.com

# SMS (Fast2SMS)
DEV_MODE_SMS=true
FAST2SMS_API_KEY=

# WhatsApp (Twilio — optional)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886

# CAPTCHA (Cloudflare Turnstile — optional)
TURNSTILE_SECRET_KEY=

# Files
UPLOAD_DIR=uploads
MAX_UPLOAD_SIZE_MB=5
BACKUP_DIR=backups
AUTO_BACKUP_HOURS=24

# Misc
WEBSOCKET_ENABLED=true
OTP_EXPIRE_MINUTES=10
OTP_LENGTH=6
""", skip=False)

# ============================================================
# Verify
# ============================================================
print()
print("=" * 70)
print("  VERIFY FILES")
print("=" * 70)

files = [
    BACKEND / "requirements.txt",
    BACKEND / "Procfile",
    BACKEND / "runtime.txt",
    FRONTEND / "requirements.txt",
    FRONTEND / ".streamlit" / "secrets.toml",
    FRONTEND / ".streamlit" / "config.toml",
    ROOT / "render.yaml",
    ROOT / ".env.example",
]

all_ok = True
for f in files:
    if f.exists():
        print(f"  ✅ {f.relative_to(ROOT)} ({f.stat().st_size} bytes)")
    else:
        print(f"  ❌ {f.relative_to(ROOT)} MISSING")
        all_ok = False

# ============================================================
# Generate keys
# ============================================================
print()
print("=" * 70)
print("  🔐 RANDOM KEYS — COPY THESE NOW (shown once)")
print("=" * 70)
print()
print(f"  SECRET_KEY          = {secrets.token_urlsafe(48)}")
print(f"  REFRESH_SECRET_KEY  = {secrets.token_urlsafe(48)}")
print()

if all_ok:
    print("=" * 70)
    print("  ✅ READY TO DEPLOY")
    print("=" * 70)
    print()
    print("Next: commit + push, then deploy to Render + Streamlit Cloud")
else:
    print("⚠️  Some files missing — check above.")
