from fastapi import APIRouter, Request, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, cast, Date
from datetime import datetime, timedelta, timezone
from slowapi import Limiter
from slowapi.util import get_remote_address
import jwt

from app.database import get_db
from app.models import Message, MessageStatus
from app.schemas import (
    AdminLoginRequest, AdminLoginResponse,
    MessageRecord, MessageListResponse, MessageStatusUpdate,
    DashboardStats,
)
from app.config import settings

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
bearer = HTTPBearer()


# ── JWT helpers ──────────────────────────────────────────────────────────
def create_token(username: str) -> str:
    payload = {
        "sub": username,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> str:
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ── Auth ─────────────────────────────────────────────────────────────────
@router.post("/login", response_model=AdminLoginResponse, summary="Admin login")
@limiter.limit("10/minute")
async def login(request: Request, body: AdminLoginRequest):
    if body.username != settings.ADMIN_USERNAME or body.password != settings.ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return AdminLoginResponse(access_token=create_token(body.username))


# ── Dashboard stats ───────────────────────────────────────────────────────
@router.get("/dashboard", response_model=DashboardStats, summary="Dashboard stats")
@limiter.limit(settings.ADMIN_RATE_LIMIT)
async def dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_token),
):
    now = datetime.now(timezone.utc)
    today = now.date()
    week_ago = now - timedelta(days=7)

    total = (await db.execute(select(func.count()).select_from(Message))).scalar()

    counts = {}
    for s in MessageStatus:
        c = (await db.execute(
            select(func.count()).select_from(Message).where(Message.status == s)
        )).scalar()
        counts[s.value] = c

    today_count = (await db.execute(
        select(func.count()).select_from(Message).where(
            cast(Message.created_at, Date) == today
        )
    )).scalar()

    week_count = (await db.execute(
        select(func.count()).select_from(Message).where(Message.created_at >= week_ago)
    )).scalar()

    return DashboardStats(
        total=total,
        unread=counts.get("unread", 0),
        read=counts.get("read", 0),
        replied=counts.get("replied", 0),
        archived=counts.get("archived", 0),
        spam=counts.get("spam", 0),
        today=today_count,
        this_week=week_count,
    )


# ── List messages ─────────────────────────────────────────────────────────
@router.get("/messages", response_model=MessageListResponse, summary="List messages")
@limiter.limit(settings.ADMIN_RATE_LIMIT)
async def list_messages(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: MessageStatus | None = Query(None),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_token),
):
    offset = (page - 1) * limit
    base = select(Message)

    if status:
        base = base.where(Message.status == status)
    if search:
        term = f"%{search}%"
        base = base.where(
            Message.name.ilike(term) |
            Message.email.ilike(term) |
            Message.message.ilike(term)
        )

    total = (await db.execute(
        select(func.count()).select_from(base.subquery())
    )).scalar()

    rows = (await db.execute(
        base.order_by(Message.created_at.desc()).offset(offset).limit(limit)
    )).scalars().all()

    return MessageListResponse(
        total=total, page=page, limit=limit,
        messages=[MessageRecord.model_validate(r) for r in rows],
    )


# ── Single message ────────────────────────────────────────────────────────
@router.get("/messages/{msg_id}", response_model=MessageRecord, summary="Get message")
@limiter.limit(settings.ADMIN_RATE_LIMIT)
async def get_message(
    request: Request,
    msg_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_token),
):
    msg = await db.get(Message, msg_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    # Auto-mark as read when opened
    if msg.status == MessageStatus.unread:
        msg.status = MessageStatus.read
        await db.flush()

    return MessageRecord.model_validate(msg)


# ── Update status / notes ─────────────────────────────────────────────────
@router.patch("/messages/{msg_id}", response_model=MessageRecord, summary="Update message status")
@limiter.limit(settings.ADMIN_RATE_LIMIT)
async def update_message(
    request: Request,
    msg_id: int,
    body: MessageStatusUpdate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_token),
):
    msg = await db.get(Message, msg_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    msg.status = body.status
    if body.notes is not None:
        msg.notes = body.notes
    await db.flush()
    await db.refresh(msg)

    return MessageRecord.model_validate(msg)


# ── Delete message ────────────────────────────────────────────────────────
@router.delete("/messages/{msg_id}", summary="Delete message")
@limiter.limit(settings.ADMIN_RATE_LIMIT)
async def delete_message(
    request: Request,
    msg_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_token),
):
    msg = await db.get(Message, msg_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    await db.delete(msg)
    return {"success": True, "id": msg_id}
