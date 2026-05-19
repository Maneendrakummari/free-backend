from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.database import get_db
from app.models import Message, MessageStatus
from app.schemas import ContactFormRequest, ContactFormResponse, SubmissionDetail
from app.config import settings

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


def format_ref(numeric_id: int) -> str:
    return f"FP{numeric_id:03d}"


@router.post("/contact", response_model=ContactFormResponse, summary="Submit contact form")
@limiter.limit(settings.CONTACT_RATE_LIMIT)
async def submit_contact(
    request: Request,
    form: ContactFormRequest,
    db: AsyncSession = Depends(get_db),
):
    if len(form.message.strip()) < 10:
        raise HTTPException(status_code=422, detail="Message too short")

    ip = request.client.host if request.client else None

    msg = Message(
        name=form.name.strip(),
        email=str(form.email).lower().strip(),
        budget=form.budget,
        message=form.message.strip(),
        status=MessageStatus.unread,
        ip_address=ip,
    )
    db.add(msg)
    await db.flush()
    await db.refresh(msg)

    return ContactFormResponse(
        success=True,
        message="Thanks! I'll get back to you within 24 hours.",
        id=format_ref(msg.id),
        reference_id=format_ref(msg.id),
    )


@router.get("/contact/{reference_id}", response_model=SubmissionDetail, summary="Fetch submission by reference ID")
@limiter.limit("10/minute")
async def get_submission(
    request: Request,
    reference_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Public endpoint — fetch your own submission using reference ID (e.g. FP001).
    Only returns safe public fields, no IP address or admin notes.
    """
    from sqlalchemy import select
    reference_id = reference_id.upper().strip()

    result = await db.execute(
        select(Message).where(Message.reference_id == reference_id)
    )
    msg = result.scalar_one_or_none()

    if not msg:
        raise HTTPException(status_code=404, detail=f"No submission found with ID {reference_id}")

    return SubmissionDetail(
        reference_id=msg.reference_id,
        name=msg.name,
        email=msg.email,
        budget=msg.budget,
        message=msg.message,
        status=msg.status,
        submitted_at=msg.created_at,
    )