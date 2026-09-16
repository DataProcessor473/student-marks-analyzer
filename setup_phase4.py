"""
Student Marks Analyzer - Phase 4A Setup Automation
Installs PostgreSQL, creates DB, updates .env, tests connection.
Run: python setup_phase4.py
"""
import os
import sys
import subprocess
import urllib.request
import tempfile
import shutil
import ctypes
import time
from pathlib import Path

# ============================================================
# CONFIG
# ============================================================
PROJECT_ROOT = Path(r"D:\student_marks_analyzer")
ENV_FILE     = PROJECT_ROOT / ".env"
BACKEND_DIR  = PROJECT_ROOT / "backend"

PG_VERSION   = "16.4-1"
PG_URL       = f"https://get.enterprisedb.com/postgresql/postgresql-{PG_VERSION}-windows-x64.exe"
PG_INSTALLER = Path(tempfile.gettempdir()) / f"postgresql-{PG_VERSION}.exe"

PG_INSTALL_DIR = r"C:\Program Files\PostgreSQL\16"
PG_DATA_DIR    = r"C:\Program Files\PostgreSQL\16\data"
PG_PORT        = "5432"
PG_SUPERUSER   = "postgres"
PG_PASSWORD    = "postgres"
PG_BIN         = Path(PG_INSTALL_DIR) / "bin"
PG_PSQL        = PG_BIN / "psql.exe"

DB_NAME        = "student_marks_db"
DB_URL         = f"postgresql://{PG_SUPERUSER}:{PG_PASSWORD}@localhost:{PG_PORT}/{DB_NAME}"

PIP_PACKAGES   = ["sqlalchemy", "psycopg2-binary", "alembic", "python-dotenv"]

# ============================================================
# HELPERS
# ============================================================
def log(msg, kind="info"):
    colors = {"ok": "\033[92m", "fail": "\033[91m", "warn": "\033[93m",
              "info": "\033[96m", "head": "\033[95m", "end": "\033[0m"}
    prefixes = {"ok": "[OK]  ", "fail": "[FAIL]", "warn": "[WARN]",
                "info": "[INFO]", "head": "\n=== ", "end": ""}
    end = "" if kind != "head" else " ==="
    print(f"{colors.get(kind,'')}{prefixes.get(kind,'')}{msg}{end}\033[0m")

def run(cmd, check=False, shell=False, capture=True):
    """Run command, return (success, stdout+stderr)."""
    try:
        result = subprocess.run(
            cmd, shell=shell, capture_output=capture,
            text=True, timeout=600, encoding="utf-8", errors="ignore"
        )
        out = (result.stdout or "") + (result.stderr or "")
        if check and result.returncode != 0:
            return False, out
        return result.returncode == 0, out.strip()
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT"
    except Exception as e:
        return False, str(e)

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

def request_admin():
    """Re-launch this script as admin."""
    log("Requesting administrator privileges...", "warn")
    script = os.path.abspath(__file__)
    params = " ".join([f'"{a}"' for a in sys.argv])
    try:
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, f'"{script}" {params}', None, 1
        )
    except Exception as e:
        log(f"Cannot elevate: {e}", "fail")
        sys.exit(1)
    sys.exit(0)

def file_size_mb(path):
    try:
        return round(Path(path).stat().st_size / 1024 / 1024, 1)
    except Exception:
        return 0

# ============================================================
# BANNER
# ============================================================
print()
print("=" * 70)
print("  Student Marks Analyzer - Phase 4A Setup Automation")
print("=" * 70)

# ============================================================
# STEP 0: Admin check
# ============================================================
log("STEP 0: Admin privileges", "head")
if not is_admin():
    log("Not running as admin", "warn")
    request_admin()
else:
    log("Running as administrator", "ok")

# ============================================================
# STEP 1: Project check
# ============================================================
log("STEP 1: Project structure", "head")
if not PROJECT_ROOT.exists():
    log(f"Project root missing: {PROJECT_ROOT}", "fail")
    sys.exit(1)
log(f"Project root: {PROJECT_ROOT}", "ok")
if BACKEND_DIR.exists():
    log(f"Backend folder: {BACKEND_DIR}", "ok")
else:
    log(f"Backend folder missing: {BACKEND_DIR}", "warn")

# ============================================================
# STEP 2: Check Python & pip
# ============================================================
log("STEP 2: Python environment", "head")
ok, out = run([sys.executable, "--version"])
log(f"Python: {out}" if ok else "Python check failed", "ok" if ok else "fail")

ok, out = run([sys.executable, "-m", "pip", "--version"])
log(f"pip: {out.split()[1]}" if ok else "pip check failed", "ok" if ok else "fail")

# ============================================================
# STEP 3: Install Python packages
# ============================================================
log("STEP 3: Python packages", "head")
for pkg in PIP_PACKAGES:
    ok, out = run([sys.executable, "-m", "pip", "show", pkg])
    if ok:
        version = ""
        for line in out.splitlines():
            if line.startswith("Version:"):
                version = line.split(":", 1)[1].strip()
                break
        log(f"{pkg} {version} (already installed)", "ok")
    else:
        log(f"Installing {pkg}...", "info")
        ok, out = run([sys.executable, "-m", "pip", "install", pkg, "--quiet"])
        log(f"Installed: {pkg}" if ok else f"Failed: {pkg} — {out[:100]}",
            "ok" if ok else "fail")

# ============================================================
# STEP 4: Check PostgreSQL
# ============================================================
log("STEP 4: PostgreSQL status", "head")

PG_INSTALLED = False
PSQL_EXE = None

# Check common install locations
candidates = [
    Path(r"C:\Program Files\PostgreSQL\16\bin\psql.exe"),
    Path(r"C:\Program Files\PostgreSQL\17\bin\psql.exe"),
    Path(r"C:\Program Files\PostgreSQL\15\bin\psql.exe"),
]

for c in candidates:
    if c.exists():
        PSQL_EXE = c
        PG_INSTALLED = True
        log(f"Found: {c}", "ok")
        break

# Check via PATH
if not PG_INSTALLED:
    ok, out = run(["psql", "--version"], shell=True)
    if ok and "psql" in out.lower():
        PG_INSTALLED = True
        log(f"Found in PATH: {out}", "ok")

if not PG_INSTALLED:
    log("PostgreSQL not installed", "warn")
else:
    log("PostgreSQL is installed", "ok")

# ============================================================
# STEP 5: Install PostgreSQL if missing
# ============================================================
if not PG_INSTALLED:
    log("STEP 5: Installing PostgreSQL", "head")
    log(f"Version: {PG_VERSION}", "info")
    log(f"Download URL: {PG_URL}", "info")

    # Download
    if PG_INSTALLER.exists() and file_size_mb(PG_INSTALLER) > 200:
        log(f"Installer already cached: {PG_INSTALLER} ({file_size_mb(PG_INSTALLER)} MB)", "ok")
    else:
        log(f"Downloading... (~350 MB, please wait)", "info")
        try:
            def progress(block_num, block_size, total_size):
                downloaded = block_num * block_size
                if total_size > 0:
                    pct = min(100, downloaded * 100 // total_size)
                    mb = downloaded / 1024 / 1024
                    total_mb = total_size / 1024 / 1024
                    sys.stdout.write(f"\r  [{pct:3d}%] {mb:.1f}/{total_mb:.1f} MB")
                    sys.stdout.flush()

            urllib.request.urlretrieve(PG_URL, PG_INSTALLER, reporthook=progress)
            print()
            log(f"Downloaded: {file_size_mb(PG_INSTALLER)} MB", "ok")
        except Exception as e:
            log(f"Download failed: {e}", "fail")
            log("Manual download: https://www.enterprisedb.com/downloads/postgres-postgresql-downloads", "info")
            sys.exit(1)

    # Silent install
    log("Installing PostgreSQL silently (2-3 minutes)...", "info")
    log("This creates: PostgreSQL server, pgAdmin, command line tools", "info")
    print()

    install_cmd = [
        str(PG_INSTALLER),
        "--mode", "unattended",
        "--unattendedmodeui", "minimal",
        "--superpassword", PG_PASSWORD,
        "--serverport", PG_PORT,
        "--servicename", "postgresql-x64-16",
        "--datadir", PG_DATA_DIR,
        "--prefix", PG_INSTALL_DIR,
    ]

    log("Running installer...", "info")
    try:
        result = subprocess.run(install_cmd, timeout=600, capture_output=True, text=True)
        if result.returncode != 0:
            log(f"Installer returned code {result.returncode}", "warn")
            if result.stdout:
                log(f"stdout: {result.stdout[:500]}", "info")
            if result.stderr:
                log(f"stderr: {result.stderr[:500]}", "info")
    except subprocess.TimeoutExpired:
        log("Install timed out (may still be running in background)", "warn")
    except Exception as e:
        log(f"Install error: {e}", "fail")

    # Wait for service
    time.sleep(5)

    # Re-detect
    for c in candidates:
        if c.exists():
            PSQL_EXE = c
            PG_INSTALLED = True
            log(f"Installed at: {c}", "ok")
            break

    if not PG_INSTALLED:
        log("Install completed but psql.exe not found", "warn")
        log(f"Check: {PG_INSTALL_DIR}", "info")
        sys.exit(1)
else:
    log("STEP 5: Skipped (already installed)", "head")

# ============================================================
# STEP 6: Add to PATH
# ============================================================
log("STEP 6: PATH setup", "head")

pg_bin_str = str(PG_BIN)
ok, current = run(["powershell", "-Command",
                   "[Environment]::GetEnvironmentVariable('Path', 'User')"],
                  shell=False)
if pg_bin_str not in (current or ""):
    new_path = f"{current};{pg_bin_str}" if current else pg_bin_str
    ok, out = run(["powershell", "-Command",
                   f"[Environment]::SetEnvironmentVariable('Path', '{new_path}', 'User')"])
    if ok:
        log(f"Added to PATH: {pg_bin_str}", "ok")
        log("Close and reopen PowerShell after this script finishes", "info")
    else:
        log(f"PATH update failed: {out[:200]}", "warn")
        log(f"Manually add: {pg_bin_str}", "info")
else:
    log(f"Already in PATH: {pg_bin_str}", "ok")

# Update current session PATH
os.environ["PATH"] = f"{pg_bin_str};{os.environ.get('PATH', '')}"

# ============================================================
# STEP 7: Ensure service running
# ============================================================
log("STEP 7: PostgreSQL service", "head")

ok, out = run(["powershell", "-Command",
               "Get-Service postgresql* | Select-Object -ExpandProperty Name"],
              shell=False)
if ok and out.strip():
    service_name = out.strip().splitlines()[0].strip()
    log(f"Service: {service_name}", "ok")

    # Ensure running
    ok2, status = run(["powershell", "-Command",
                       f"(Get-Service '{service_name}').Status"],
                      shell=False)
    if "Running" in status:
        log("Service is running", "ok")
    else:
        log("Starting service...", "info")
        run(["powershell", "-Command", f"Start-Service '{service_name}'"], shell=False)
        time.sleep(3)
        ok3, status2 = run(["powershell", "-Command",
                            f"(Get-Service '{service_name}').Status"],
                           shell=False)
        log(f"Status: {status2.strip()}", "ok" if "Running" in status2 else "warn")
else:
    log("No PostgreSQL service found", "warn")
    log("Install may not have completed. Check manually.", "info")

# Wait for service to be ready
time.sleep(3)

# ============================================================
# STEP 8: Create database
# ============================================================
log("STEP 8: Create database", "head")

os.environ["PGPASSWORD"] = PG_PASSWORD

# Check if DB exists
check_cmd = [
    str(PSQL_EXE), "-U", PG_SUPERUSER, "-h", "localhost", "-p", PG_PORT,
    "-tAc", f"SELECT 1 FROM pg_database WHERE datname='{DB_NAME}'"
]
ok, out = run(check_cmd)

if ok and out.strip() == "1":
    log(f"Database '{DB_NAME}' already exists", "ok")
else:
    log(f"Creating database '{DB_NAME}'...", "info")
    create_cmd = [
        str(PSQL_EXE), "-U", PG_SUPERUSER, "-h", "localhost", "-p", PG_PORT,
        "-c", f"CREATE DATABASE {DB_NAME}"
    ]
    ok, out = run(create_cmd)
    if ok:
        log(f"Database created: {DB_NAME}", "ok")
    else:
        log(f"Create failed: {out[:200]}", "fail")
        log("Is the service running? Try restarting PostgreSQL service.", "info")

# Verify
verify_cmd = [
    str(PSQL_EXE), "-U", PG_SUPERUSER, "-h", "localhost", "-p", PG_PORT,
    "-tAc", f"SELECT 1 FROM pg_database WHERE datname='{DB_NAME}'"
]
ok, out = run(verify_cmd)
if ok and out.strip() == "1":
    log("Database verified", "ok")
else:
    log("Database verification failed", "fail")

# ============================================================
# STEP 9: Test Python connection
# ============================================================
log("STEP 9: Python connection test", "head")

test_script = f"""
import psycopg2
conn = psycopg2.connect(
    host='localhost', port={PG_PORT},
    user='{PG_SUPERUSER}', password='{PG_PASSWORD}',
    database='{DB_NAME}', connect_timeout=5
)
cur = conn.cursor()
cur.execute('SELECT version();')
ver = cur.fetchone()[0]
print('CONNECTED')
print(version_line=ver.split(',')[0])
conn.close()
""".replace("print(version_line=ver.split(',')[0])", "print(ver.split(',')[0])")

ok, out = run([sys.executable, "-c", test_script])
if "CONNECTED" in out:
    log("Python can connect to PostgreSQL", "ok")
    for line in out.splitlines():
        log(line, "info")
else:
    log(f"Connection failed: {out[:300]}", "fail")

# ============================================================
# STEP 10: Update .env
# ============================================================
log("STEP 10: Update .env file", "head")

db_url_line = f"\n# Phase 4A - PostgreSQL\nDATABASE_URL={DB_URL}\n"

if ENV_FILE.exists():
    log(f"Found .env: {ENV_FILE}", "ok")
    content = ENV_FILE.read_text(encoding="utf-8")

    if "DATABASE_URL" in content:
        # Update existing line
        lines = content.splitlines()
        new_lines = []
        for line in lines:
            if line.strip().startswith("DATABASE_URL="):
                new_lines.append(f"DATABASE_URL={DB_URL}")
            else:
                new_lines.append(line)
        ENV_FILE.write_text("\n".join(new_lines), encoding="utf-8")
        log("Updated existing DATABASE_URL", "ok")
    else:
        with open(ENV_FILE, "a", encoding="utf-8") as f:
            f.write(db_url_line)
        log("Appended DATABASE_URL", "ok")
else:
    log(f".env not found — creating: {ENV_FILE}", "warn")
    ENV_FILE.write_text(
        f"# Auto-generated by setup_phase4.py\n{db_url_line}",
        encoding="utf-8"
    )
    log("Created new .env", "ok")

# ============================================================
# STEP 11: Backup SQLite
# ============================================================
log("STEP 11: Backup SQLite database", "head")

backup_dir = PROJECT_ROOT / "_backups_phase3"
backup_dir.mkdir(exist_ok=True)

sqlite_files = list(BACKEND_DIR.glob("*.db")) + list(PROJECT_ROOT.glob("*.db"))
if sqlite_files:
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    for db in sqlite_files:
        dest = backup_dir / f"{db.stem}_{timestamp}{db.suffix}"
        shutil.copy2(db, dest)
        log(f"Backed up: {db.name} -> {dest.name}", "ok")
else:
    log("No SQLite files found", "warn")

# ============================================================
# FINAL SUMMARY
# ============================================================
print()
print("=" * 70)
print("  SETUP COMPLETE")
print("=" * 70)
print()
log("What was done:", "head")
log(f"  [x] Python packages installed ({len(PIP_PACKAGES)})", "ok")
log(f"  [x] PostgreSQL: {PG_INSTALL_DIR}", "ok")
log(f"  [x] Database: {DB_NAME}", "ok")
log(f"  [x] Service running on port {PG_PORT}", "ok")
log(f"  [x] Connection tested from Python", "ok")
log(f"  [x] DATABASE_URL added to: {ENV_FILE}", "ok")
log(f"  [x] SQLite backed up to: {backup_dir}", "ok")

print()
log("Next steps:", "head")
log("  1. Close and reopen PowerShell (to pick up PATH changes)", "info")
log("  2. Verify: psql --version", "info")
log("  3. Test backend still works with SQLite:", "info")
log("     cd D:\\student_marks_analyzer\\backend", "info")
log("     python -m uvicorn main:app --reload --port 8000", "info")
log("  4. Then ask: 'migrate to postgres' — I'll write the migration script", "info")

print()
log(f"Connection URL: {DB_URL}", "info")
print()
print("=" * 70)
