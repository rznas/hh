"""Conversation and message models for chat persistence."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String, Text, JSON, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class TriagePhase(str, Enum):
    """Triage workflow phases."""

    CONSENT = "consent"
    RED_FLAG_CHECK = "red_flag_check"
    CHIEF_COMPLAINT = "chief_complaint"
    SYSTEMATIC_QUESTIONS = "systematic_questions"
    RISK_STRATIFICATION = "risk_stratification"
    RECOMMENDATION = "recommendation"
    COMPLETED = "completed"


class UrgencyLevel(str, Enum):
    """Medical urgency classification."""

    EMERGENT = "emergent"  # ER immediately
    URGENT = "urgent"  # Doctor within 24-48h
    NON_URGENT = "non_urgent"  # Schedule 1-2 weeks
    UNKNOWN = "unknown"


class MessageRole(str, Enum):
    """Message sender role."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Conversation(Base, TimestampMixin):
    """Conversation session tracking."""

    __tablename__ = "conversations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    chainlit_session_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)

    # Current state
    current_phase: Mapped[TriagePhase] = mapped_column(
        SQLEnum(TriagePhase), default=TriagePhase.CONSENT
    )
    is_active: Mapped[bool] = mapped_column(default=True)

    # Relationships
    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )
    triage_sessions: Mapped[list["TriageSession"]] = relationship(
        "TriageSession", back_populates="conversation", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, phase={self.current_phase})>"


class Message(Base, TimestampMixin):
    """Individual chat message."""

    __tablename__ = "messages"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    conversation_id: Mapped[UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )

    # Message content
    role: Mapped[MessageRole] = mapped_column(SQLEnum(MessageRole))
    content: Mapped[str] = mapped_column(Text)

    # Metadata
    phase: Mapped[Optional[TriagePhase]] = mapped_column(
        SQLEnum(TriagePhase), nullable=True
    )
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # LLM tracking
    model_used: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tokens_used: Mapped[Optional[int]] = mapped_column(nullable=True)
    langfuse_trace_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, role={self.role}, phase={self.phase})>"


class TriageSession(Base, TimestampMixin):
    """Medical triage session with results."""

    __tablename__ = "triage_sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    conversation_id: Mapped[UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )

    # Chief complaint
    chief_complaint: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    standardized_complaint: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Red flag detection
    has_red_flags: Mapped[bool] = mapped_column(default=False)
    red_flag_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Risk assessment
    urgency_level: Mapped[UrgencyLevel] = mapped_column(
        SQLEnum(UrgencyLevel), default=UrgencyLevel.UNKNOWN
    )
    differential_diagnoses: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Recommendations
    recommendation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    virtual_exam_results: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Appointment booking
    appointment_booked: Mapped[bool] = mapped_column(default=False)
    appointment_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Audit trail
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    consent_given: Mapped[bool] = mapped_column(default=False)
    consent_timestamp: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Relationships
    conversation: Mapped["Conversation"] = relationship(
        "Conversation", back_populates="triage_sessions"
    )

    def __repr__(self) -> str:
        return f"<TriageSession(id={self.id}, urgency={self.urgency_level})>"
