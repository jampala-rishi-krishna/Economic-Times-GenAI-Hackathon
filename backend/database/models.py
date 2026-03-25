"""
SQLAlchemy ORM Models for NEXUS Platform
"""
import uuid
import hashlib
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Float, Integer, Boolean,
    DateTime, Enum, ForeignKey, JSON, create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


def gen_uuid():
    return str(uuid.uuid4())


class MeetingStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"
    partial_completion = "partial_completion"


class TaskPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class TaskStatus(str, enum.Enum):
    created = "created"
    in_progress = "in_progress"
    at_risk = "at_risk"  # CHANGE 2: Predictive risk detection
    stalled = "stalled"
    split_into_subtasks = "split_into_subtasks"  # CHANGE 1&3: Task splitting result
    reopened = "reopened"  # CHANGE 3: Verification failed
    escalated = "escalated"
    completed = "completed"
    cancelled = "cancelled"


class AgentEventType(str, enum.Enum):
    started = "started"
    thinking = "thinking"
    tool_call = "tool_call"
    decision = "decision"
    handoff = "handoff"
    completed = "completed"
    error = "error"
    retry = "retry"


class NotificationChannel(str, enum.Enum):
    email = "email"
    slack = "slack"
    in_app = "in_app"


class NotificationType(str, enum.Enum):
    assignment = "assignment"
    reminder = "reminder"
    escalation = "escalation"
    completion = "completion"


class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(String, primary_key=True, default=gen_uuid)
    title = Column(String, nullable=False)
    raw_transcript = Column(Text, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="pending")
    participants = Column(JSON, default=list)
    duration_minutes = Column(Integer, default=0)
    crew_run_id = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
    workflow_type = Column(String, default="meeting")  # CHANGE 3: Multi-workflow support
    retry_count = Column(Integer, default=0)  # CHANGE 1: Closed-loop tracking

    decisions = relationship("Decision", back_populates="meeting", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="meeting", cascade="all, delete-orphan")
    agent_events = relationship("AgentEvent", back_populates="meeting", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="meeting", cascade="all, delete-orphan")
    participant_emails = relationship("ParticipantEmail", back_populates="meeting", cascade="all, delete-orphan")


class ParticipantEmail(Base):
    __tablename__ = "participant_emails"

    id = Column(String, primary_key=True, default=gen_uuid)
    meeting_id = Column(String, ForeignKey("meetings.id"), nullable=False)
    participant_name = Column(String, nullable=False)
    email_address = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    meeting = relationship("Meeting", back_populates="participant_emails")


class Decision(Base):
    __tablename__ = "decisions"

    id = Column(String, primary_key=True, default=gen_uuid)
    meeting_id = Column(String, ForeignKey("meetings.id"), nullable=False)
    decision_text = Column(Text, nullable=False)
    context = Column(Text, nullable=True)
    confidence_score = Column(Float, default=0.8)
    extracted_by = Column(String, default="Decision Extraction Agent")
    extracted_at = Column(DateTime, default=datetime.utcnow)

    meeting = relationship("Meeting", back_populates="decisions")
    tasks = relationship("Task", back_populates="decision")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=gen_uuid)
    meeting_id = Column(String, ForeignKey("meetings.id"), nullable=False)
    decision_id = Column(String, ForeignKey("decisions.id"), nullable=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    assigned_to = Column(String, nullable=True)
    assigned_by = Column(String, default="Assignor Agent")
    priority = Column(String, default="medium")
    status = Column(String, default="created")
    due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    escalation_count = Column(Integer, default=0)
    retry_count = Column(Integer, default=0)  # CHANGE 1: Closed-loop retry tracking
    risk_score = Column(Float, default=0.0)  # CHANGE 2: Predictive risk (0-1.0)
    stall_detected_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    assignment_rationale = Column(Text, nullable=True)
    context_quote = Column(Text, nullable=True)
    is_human_override = Column(Boolean, default=False)

    meeting = relationship("Meeting", back_populates="tasks")
    decision = relationship("Decision", back_populates="tasks")
    notifications = relationship("Notification", back_populates="task", cascade="all, delete-orphan")


class AgentEvent(Base):
    __tablename__ = "agent_events"

    id = Column(String, primary_key=True, default=gen_uuid)
    meeting_id = Column(String, ForeignKey("meetings.id"), nullable=False)
    agent_name = Column(String, nullable=False)
    agent_role = Column(String, nullable=True)
    event_type = Column(String, default="started")
    input_context = Column(JSON, default=dict)
    output_result = Column(JSON, default=dict)
    tool_used = Column(String, nullable=True)
    duration_ms = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.utcnow)
    sequence_number = Column(Integer, default=0)

    meeting = relationship("Meeting", back_populates="agent_events")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=gen_uuid)
    meeting_id = Column(String, ForeignKey("meetings.id"), nullable=True)
    action = Column(String, nullable=False)
    actor = Column(String, nullable=False)
    target_type = Column(String, nullable=True)
    target_id = Column(String, nullable=True)
    before_state = Column(JSON, nullable=True)
    after_state = Column(JSON, nullable=True)
    decision_rationale = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_human_override = Column(Boolean, default=False)
    checksum = Column(String, nullable=True)

    meeting = relationship("Meeting", back_populates="audit_logs")

    def generate_checksum(self):
        raw = f"{self.actor}{self.action}{self.timestamp.isoformat() if self.timestamp else ''}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def verify_checksum(self):
        expected = self.generate_checksum()
        return self.checksum == expected


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, default=gen_uuid)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False)
    recipient = Column(String, nullable=False)
    channel = Column(String, default="in_app")
    message = Column(Text, nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    notification_type = Column(String, default="assignment")
    
    # Real email tracking
    email_sent = Column(Boolean, default=False)
    email_sent_at = Column(DateTime, nullable=True)
    email_error = Column(String, nullable=True)

    task = relationship("Task", back_populates="notifications")
