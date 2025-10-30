"""State definition for the triage workflow."""

from typing import Annotated, Literal
from uuid import UUID

from langgraph.graph import MessagesState
from pydantic import BaseModel, Field


class TriageState(MessagesState):
    """State for the triage workflow.

    Extends MessagesState to include message history plus triage-specific state.
    """

    # Session identifiers
    conversation_id: UUID | None = None
    triage_session_id: UUID | None = None

    # Current workflow phase
    phase: Literal[
        "consent",
        "red_flag_check",
        "chief_complaint",
        "systematic_questions",
        "risk_stratification",
        "recommendation",
        "appointment_booking",
        "completed"
    ] = "consent"

    # Consent
    consent_given: bool = False

    # Red flag detection
    has_red_flags: bool = False
    red_flag_details: dict | None = None

    # Chief complaint
    chief_complaint: str | None = None
    standardized_complaint: str | None = None

    # Differential diagnoses from GraphRAG
    differential_diagnoses: list[dict] | None = None

    # Risk assessment
    urgency_level: Literal["emergent", "urgent", "non_urgent", "unknown"] = "unknown"

    # Questions and answers
    systematic_questions: list[dict] | None = None
    patient_responses: dict = Field(default_factory=dict)

    # Virtual exam
    virtual_exam_results: dict | None = None

    # Final recommendation
    recommendation: str | None = None
    recommended_action: str | None = None

    # Appointment
    appointment_requested: bool = False
    appointment_id: UUID | None = None

    # Metadata
    model_used: str | None = None
    total_tokens: int = 0


class PhaseTransition(BaseModel):
    """Result of a phase execution."""

    next_phase: str
    should_continue: bool = True
    message: str | None = None
    metadata: dict = Field(default_factory=dict)
