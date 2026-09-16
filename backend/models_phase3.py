"""
Phase 3 Pydantic Models
All new models for Phase 3 features.
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any


# ============================================================
# STUDENT PHOTO / PROFILE
# ============================================================
class StudentProfileUpdate(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    address: Optional[str] = None


# ============================================================
# EXAMS / TIMETABLE
# ============================================================
class ExamCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    class_name: Optional[str] = None
    subject: Optional[str] = None
    exam_date: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    total_marks: int = 100
    room: Optional[str] = None
    notes: Optional[str] = None


class TimetableCreate(BaseModel):
    class_name: str
    day_of_week: str  # Monday, Tuesday...
    period: Optional[int] = None
    subject: str
    teacher_name: Optional[str] = None
    room: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None


# ============================================================
# ASSIGNMENTS
# ============================================================
class AssignmentCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    class_name: Optional[str] = None
    subject: Optional[str] = None
    due_date: str
    total_marks: int = 100


class SubmissionUpdate(BaseModel):
    status: Optional[str] = None  # pending, submitted, graded
    marks_obtained: Optional[float] = None
    feedback: Optional[str] = None
    file_url: Optional[str] = None


# ============================================================
# FEES
# ============================================================
class FeeStructureCreate(BaseModel):
    class_name: str
    fee_type: str
    amount: float = Field(..., gt=0)
    frequency: str = "monthly"
    academic_year: Optional[str] = None


class FeePaymentCreate(BaseModel):
    student_id: int
    fee_type: str
    amount: float = Field(..., gt=0)
    payment_date: str
    payment_method: str = "cash"
    transaction_id: Optional[str] = None
    status: str = "paid"
    due_date: Optional[str] = None
    notes: Optional[str] = None


# ============================================================
# SAVED FILTERS
# ============================================================
class SavedFilterCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    entity: str  # students, users, etc.
    filter_json: str
    is_shared: bool = False


# ============================================================
# SCHEDULED REPORTS
# ============================================================
class ScheduledReportCreate(BaseModel):
    report_type: str
    recipients: str  # comma-separated emails
    schedule: str  # daily, weekly, monthly
    enabled: bool = True


# ============================================================
# WHATSAPP OTP
# ============================================================
class WhatsAppOTPRequest(BaseModel):
    phone: str
    purpose: str = "verification"


# ============================================================
# BACKUP
# ============================================================
class BackupRestoreRequest(BaseModel):
    filename: str
    confirm: bool = False
