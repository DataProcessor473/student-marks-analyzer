param(
    [int]$AssignmentId = 3,
    [string]$FilePath = "D:\sub.pdf",
    [string]$BaseUrl = "https://student-marks-analyzer-vju7.onrender.com"
)

$ErrorActionPreference = "Stop"

function Section($title) {
    Write-Host ""
    Write-Host ("=" * 72) -ForegroundColor Cyan
    Write-Host ("  " + $title) -ForegroundColor Cyan
    Write-Host ("=" * 72) -ForegroundColor Cyan
}

function Ok($msg)   { Write-Host ("  [OK]   " + $msg) -ForegroundColor Green }
function Fail($msg) { Write-Host ("  [FAIL] " + $msg) -ForegroundColor Red }
function Info($msg) { Write-Host ("  [INFO] " + $msg) -ForegroundColor Yellow }

# ------------------------------------------------------------------
# 0. Sanity check
# ------------------------------------------------------------------
Section "0. SANITY CHECK"

if (-not (Test-Path $FilePath)) {
    Fail ("File not found: " + $FilePath)
    exit 1
}
$fileInfo = Get-Item $FilePath
Ok ("Test file: " + $fileInfo.FullName + "  (" + $fileInfo.Length + " bytes)")
Ok ("Base URL:  " + $BaseUrl)
Ok ("Assignment ID: " + $AssignmentId)

# ------------------------------------------------------------------
# 1. Health
# ------------------------------------------------------------------
Section "1. HEALTH CHECK"

try {
    $health = Invoke-RestMethod -Uri ($BaseUrl + "/health") -Method GET
    Ok ("Backend reachable")
} catch {
    Fail ("Backend unreachable: " + $_)
    exit 1
}

# ------------------------------------------------------------------
# 2. Student login
# ------------------------------------------------------------------
Section "2. STUDENT LOGIN (student1)"

try {
    $sUrl = $BaseUrl + "/auth/login?username=student1&password=Student@123"
    $studentLogin = Invoke-RestMethod -Uri $sUrl -Method POST
    $studentToken = $studentLogin.access_token
    $studentId    = $studentLogin.user.id
    Ok ("Logged in as student1 (user id " + $studentId + ")")
} catch {
    Fail ("Student login failed: " + $_)
    exit 1
}

# ------------------------------------------------------------------
# 3. Admin login
# ------------------------------------------------------------------
Section "3. ADMIN LOGIN (admin)"

try {
    $aUrl = $BaseUrl + "/auth/login?username=admin&password=Admin@123"
    $adminLogin = Invoke-RestMethod -Uri $aUrl -Method POST
    $adminToken = $adminLogin.access_token
    Ok "Logged in as admin"
} catch {
    Fail ("Admin login failed: " + $_)
    exit 1
}

$adminHeaders = @{ Authorization = "Bearer " + $adminToken }

# ------------------------------------------------------------------
# 4. Verify assignment exists
# ------------------------------------------------------------------
Section ("4. VERIFY ASSIGNMENT " + $AssignmentId + " EXISTS")

try {
    $assignments = Invoke-RestMethod -Uri ($BaseUrl + "/assignments") -Headers $adminHeaders -Method GET
    $target = $assignments.assignments | Where-Object { $_.id -eq $AssignmentId }
    if ($null -eq $target) {
        Fail ("Assignment " + $AssignmentId + " not found")
        Write-Host "  Available assignments:"
        $assignments.assignments | ForEach-Object { Write-Host ("    id=" + $_.id + "  " + $_.title) }
        exit 1
    }
    Ok ("Assignment " + $AssignmentId + " = " + $target.title)
} catch {
    Fail ("Could not fetch assignments: " + $_)
    exit 1
}

# ------------------------------------------------------------------
# 5. Submit the file
# ------------------------------------------------------------------
Section "5. SUBMIT FILE AS STUDENT"

$textAnswer = "automated test at " + (Get-Date -Format "HH:mm:ss")

$submitRaw = & curl.exe -s -X POST ($BaseUrl + "/assignments/" + $AssignmentId + "/submit") `
    -H ("Authorization: Bearer " + $studentToken) `
    -F ("text_answer=" + $textAnswer) `
    -F ("file=@" + $FilePath)

Info ("Raw response: " + $submitRaw)

try {
    $submit = $submitRaw | ConvertFrom-Json
} catch {
    Fail "Could not parse submit response as JSON"
    exit 1
}

if ($submit.file_url) {
    Ok "Submit succeeded"
    Ok ("  file_url:   " + $submit.file_url)
    Ok ("  student_id: " + $submit.student_id)
    Ok ("  status:     " + $submit.status)
    Ok ("  has_text:   " + $submit.has_text)
} else {
    Fail "Submit response missing file_url"
    Write-Host ($submit | ConvertTo-Json)
    exit 1
}

# ------------------------------------------------------------------
# 6. Fetch the uploaded file
# ------------------------------------------------------------------
Section "6. FETCH THE UPLOADED FILE"

$fileUrl = $BaseUrl + $submit.file_url
Info ("GET " + $fileUrl)

$httpCode = & curl.exe -s -o NUL -w "%{http_code}" -I $fileUrl
if ($httpCode -eq "200") {
    Ok "File is served by the backend (HTTP 200)"
    $tmp = [System.IO.Path]::GetTempFileName()
    & curl.exe -s -o $tmp $fileUrl
    $downloadedSize = (Get-Item $tmp).Length
    if ($downloadedSize -eq $fileInfo.Length) {
        Ok ("Downloaded file matches original size (" + $downloadedSize + " bytes)")
    } else {
        Fail ("Size mismatch: original=" + $fileInfo.Length + "  downloaded=" + $downloadedSize)
    }
    Remove-Item $tmp -ErrorAction SilentlyContinue
} elseif ($httpCode -eq "404") {
    Fail "File returned 404"
    Info "On Render free tier, files are wiped on every deploy."
} else {
    Fail ("Unexpected HTTP status: " + $httpCode)
}

# ------------------------------------------------------------------
# 7. Admin list submissions
# ------------------------------------------------------------------
Section "7. ADMIN LIST SUBMISSIONS"

try {
    $subsUrl = $BaseUrl + "/assignments/" + $AssignmentId + "/submissions"
    $subs = Invoke-RestMethod -Uri $subsUrl -Headers $adminHeaders -Method GET
    $mine = $subs.submissions | Where-Object { $_.student_id -eq $submit.student_id }
    if ($mine) {
        Ok ("Admin sees submission for student " + $mine.student_id)
        Ok ("  submission_id: " + $mine.submission_id)
        Ok ("  status:        " + $mine.status)
        Ok ("  feedback:      " + $mine.feedback)
        Ok ("  file_url:      " + $mine.file_url)
        if ($mine.file_url) {
            Ok "Admin list INCLUDES file_url"
        } else {
            Fail "Admin list is MISSING file_url"
        }
    } else {
        Fail "Admin list does not include this student's submission"
    }
} catch {
    Fail ("Could not list submissions: " + $_)
}

# ------------------------------------------------------------------
# 8. Summary
# ------------------------------------------------------------------
Section "TEST COMPLETE"

Write-Host ("  Submitted file: " + $FilePath)
Write-Host ("  Returned URL:   " + $fileUrl)
Write-Host ""
Write-Host "  Manual check:" -ForegroundColor Yellow
Write-Host "    1. Open https://student-marks-analyzer-faysmbfnqzde8wyr7tgdxy.streamlit.app"
Write-Host "    2. Log in as admin / Admin@123"
Write-Host ("    3. Go to Submissions for assignment " + $AssignmentId)
Write-Host "    4. Expand the student row"
Write-Host "    5. Look for the Uploaded file link"
Write-Host ""