from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class BudgetRange(str, Enum):
    under_25k = "Under ₹25,000"
    range_25_75k = "₹25,000 – ₹75,000"
    range_75k_2L = "₹75,000 – ₹2,00,000"
    above_2L = "₹2,00,000+"
    discuss = "Let's discuss"


class MessageStatus(str, Enum):
    unread = "unread"
    read = "read"
    replied = "replied"
    archived = "archived"
    spam = "spam"


# ── Contact Form (public) ──────────────────────────────────────────────────
class ContactFormRequest(BaseModel):
    name: str
    email: EmailStr
    budget: Optional[str] = None
    message: str

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v):
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Name must be at least 2 characters")
        if len(v) > 100:
            raise ValueError("Name must be under 100 characters")
        return v

    @field_validator("message")
    @classmethod
    def message_not_empty(cls, v):
        v = v.strip()
        if len(v) < 10:
            raise ValueError("Message must be at least 10 characters")
        if len(v) > 5000:
            raise ValueError("Message must be under 5000 characters")
        return v


class ContactFormResponse(BaseModel):
    success: bool
    message: str
    id: str                  # FP001, FP002, ...
    reference_id: str        # same value, exposed explicitly


# ── Admin ─────────────────────────────────────────────────────────────────
class MessageRecord(BaseModel):
    id: int
    reference_id: Optional[str]   # FP001, FP002, ...
    name: str
    email: str
    budget: Optional[str]
    message: str
    status: str
    ip_address: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    notes: Optional[str]

    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    total: int
    page: int
    limit: int
    messages: List[MessageRecord]


class MessageStatusUpdate(BaseModel):
    status: MessageStatus
    notes: Optional[str] = None


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class DashboardStats(BaseModel):
    total: int
    unread: int
    read: int
    replied: int
    archived: int
    spam: int
    today: int
    this_week: int


class SubmissionDetail(BaseModel):
    reference_id: str
    name: str
    email: str
    budget: Optional[str]
    message: str
    status: str
    submitted_at: datetime