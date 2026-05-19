from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SAEnum
from sqlalchemy.sql import func
from sqlalchemy import event
import enum
from app.database import Base


class MessageStatus(str, enum.Enum):
    unread = "unread"
    read = "read"
    replied = "replied"
    archived = "archived"
    spam = "spam"


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    reference_id = Column(String(20), nullable=True, unique=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    budget = Column(String(100), nullable=True)
    message = Column(Text, nullable=False)
    status = Column(
        SAEnum(MessageStatus),
        default=MessageStatus.unread,
        nullable=False,
        index=True,
    )
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    notes = Column(Text, nullable=True)


@event.listens_for(Message, "after_insert")
def set_reference_id(mapper, connection, target):
    connection.execute(
        Message.__table__.update()
        .where(Message.__table__.c.id == target.id)
        .values(reference_id=f"FP{target.id:03d}")
    )