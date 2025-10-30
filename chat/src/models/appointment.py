"""Appointment booking models for internal scheduling system."""

from datetime import date, time
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Date, ForeignKey, String, Text, Time, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class AppointmentStatus(str, Enum):
    """Appointment status."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


class AppointmentType(str, Enum):
    """Type of appointment."""

    EMERGENCY = "emergency"  # Same day
    URGENT = "urgent"  # Within 24-48 hours
    ROUTINE = "routine"  # Scheduled 1-2 weeks out
    FOLLOW_UP = "follow_up"


class Doctor(Base, TimestampMixin):
    """Doctor/ophthalmologist profile."""

    __tablename__ = "doctors"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Doctor information
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    specialization: Mapped[str] = mapped_column(String(255), nullable=False)
    license_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Availability
    is_active: Mapped[bool] = mapped_column(default=True)
    accepts_emergency: Mapped[bool] = mapped_column(default=False)

    # Relationships
    availability: Mapped[list["DoctorAvailability"]] = relationship(
        "DoctorAvailability", back_populates="doctor", cascade="all, delete-orphan"
    )
    appointments: Mapped[list["Appointment"]] = relationship(
        "Appointment", back_populates="doctor"
    )

    def __repr__(self) -> str:
        return f"<Doctor(id={self.id}, name={self.full_name})>"


class DoctorAvailability(Base, TimestampMixin):
    """Doctor availability schedule."""

    __tablename__ = "doctor_availability"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    doctor_id: Mapped[UUID] = mapped_column(
        ForeignKey("doctors.id", ondelete="CASCADE"), index=True
    )

    # Schedule
    day_of_week: Mapped[int] = mapped_column(nullable=False)  # 0=Monday, 6=Sunday
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)

    # Slot configuration
    slot_duration_minutes: Mapped[int] = mapped_column(default=30)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Relationships
    doctor: Mapped["Doctor"] = relationship("Doctor", back_populates="availability")

    def __repr__(self) -> str:
        return f"<DoctorAvailability(doctor={self.doctor_id}, day={self.day_of_week})>"


class Appointment(Base, TimestampMixin):
    """Patient appointment."""

    __tablename__ = "appointments"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    doctor_id: Mapped[UUID] = mapped_column(
        ForeignKey("doctors.id", ondelete="RESTRICT"), index=True
    )
    conversation_id: Mapped[UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )

    # Appointment details
    appointment_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    appointment_time: Mapped[time] = mapped_column(Time, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(default=30)

    # Classification
    appointment_type: Mapped[AppointmentType] = mapped_column(
        nullable=False, default=AppointmentType.ROUTINE
    )
    status: Mapped[AppointmentStatus] = mapped_column(
        nullable=False, default=AppointmentStatus.PENDING, index=True
    )

    # Patient information
    patient_name: Mapped[str] = mapped_column(String(255), nullable=False)
    patient_phone: Mapped[str] = mapped_column(String(50), nullable=False)
    patient_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Chief complaint from triage
    chief_complaint: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    urgency_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Cancellation
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    doctor: Mapped["Doctor"] = relationship("Doctor", back_populates="appointments")

    def __repr__(self) -> str:
        return f"<Appointment(id={self.id}, date={self.appointment_date}, status={self.status})>"


class AppointmentSlot(Base, TimestampMixin):
    """Pre-generated time slots for appointment booking."""

    __tablename__ = "appointment_slots"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    doctor_id: Mapped[UUID] = mapped_column(
        ForeignKey("doctors.id", ondelete="CASCADE"), index=True
    )

    # Slot details
    slot_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    slot_time: Mapped[time] = mapped_column(Time, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(default=30)

    # Availability
    is_available: Mapped[bool] = mapped_column(default=True, index=True)
    is_emergency_only: Mapped[bool] = mapped_column(default=False)

    # Booking
    appointment_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("appointments.id", ondelete="SET NULL"), nullable=True
    )

    def __repr__(self) -> str:
        return f"<AppointmentSlot(date={self.slot_date}, time={self.slot_time}, available={self.is_available})>"
