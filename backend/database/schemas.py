"""
Pydantic Schemas for NEXUS Platform
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


# ─── Meeting Schemas ────────────────────────────────────────────────────────

class MeetingCreate(BaseModel):
    title: str
    raw_transcript: str
    participants: List[str] = []
    duration_minutes: int = 0


class MeetingResponse(BaseModel):
    id: str
    title: str
    raw_transcript: str
    uploaded_at: datetime
    status: str
    participants: List[str] = []
    duration_minutes: int = 0
    crew_run_id: Optional[str] = None
    summary: Optional[str] = None

    class Config:
        from_attributes = True


# ─── Decision Schemas ────────────────────────────────────────────────────────

class DecisionResponse(BaseModel):
    id: str
    meeting_id: str
    decision_text: str
    context: Optional[str] = None
    confidence_score: float = 0.8
    extracted_by: str
    extracted_at: datetime

    class Config:
        from_attributes = True


# ─── Task Schemas ────────────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    meeting_id: str
    decision_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    assigned_to: Optional[str] = None
    priority: str = "medium"
    due_date: Optional[datetime] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assigned_to: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[datetime] = None
    is_human_override: bool = True


class TaskResponse(BaseModel):
    id: str
    meeting_id: str
    decision_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    assigned_to: Optional[str] = None
    assigned_by: str
    priority: str
    status: str
    due_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    escalation_count: int = 0
    stall_detected_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    assignment_rationale: Optional[str] = None
    context_quote: Optional[str] = None
    is_human_override: bool = False

    class Config:
        from_attributes = True


# ─── Agent Event Schemas ─────────────────────────────────────────────────────

class AgentEventResponse(BaseModel):
    id: str
    meeting_id: str
    agent_name: str
    agent_role: Optional[str] = None
    event_type: str
    input_context: Dict[str, Any] = {}
    output_result: Dict[str, Any] = {}
    tool_used: Optional[str] = None
    duration_ms: int = 0
    timestamp: datetime
    sequence_number: int = 0

    class Config:
        from_attributes = True


# ─── Audit Schemas ───────────────────────────────────────────────────────────

class AuditLogResponse(BaseModel):
    id: str
    meeting_id: Optional[str] = None
    action: str
    actor: str
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None
    decision_rationale: Optional[str] = None
    timestamp: datetime
    is_human_override: bool = False
    checksum: Optional[str] = None
    checksum_valid: bool = True

    class Config:
        from_attributes = True


# ─── Notification Schemas ────────────────────────────────────────────────────

class NotificationResponse(BaseModel):
    id: str
    task_id: str
    recipient: str
    channel: str
    message: str
    sent_at: datetime
    notification_type: str
    email_sent: bool = False
    email_sent_at: Optional[datetime] = None
    email_error: Optional[str] = None

    class Config:
        from_attributes = True


# ─── Participant Email Schemas ───────────────────────────────────────────────

class ParticipantEmailBase(BaseModel):
    participant_name: str
    email_address: str


class ParticipantEmailCreate(BaseModel):
    meeting_id: str
    participants: List[ParticipantEmailBase]


class ParticipantEmailResponse(BaseModel):
    id: str
    meeting_id: str
    participant_name: str
    email_address: str
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Dashboard Stats Schema ──────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_meetings: int
    total_tasks: int
    completed_tasks: int
    escalated_tasks: int
    stalled_tasks: int
    autonomy_score: float
    active_workflows: int
    total_decisions: int


# ─── WebSocket Message Schema ────────────────────────────────────────────────

class WSMessage(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    meeting_id: str
    event_type: str
    agent_name: str
    agent_role: str
    message: str
    data: Dict[str, Any] = {}


# ─── Agent Output Pydantic Models ────────────────────────────────────────────

class MeetingContext(BaseModel):
    participants: List[str]
    topics: List[str]
    summary: str
    duration_minutes: int
    key_themes: List[str] = []


class ExtractedDecision(BaseModel):
    decision_text: str
    context_quote: str
    confidence_score: float
    speaker: str
    action_required: bool = True


class CreatedTask(BaseModel):
    title: str
    description: str
    priority: str
    suggested_due_date: str
    decision_ref: str


class AssignedTask(BaseModel):
    task_id: str
    assigned_to: str
    assignment_rationale: str
    notification_sent: bool


class WorkflowHealthReport(BaseModel):
    stalled_tasks: List[str]
    at_risk_tasks: List[str]
    health_score: float
    recommendations: List[str]


class EscalationReport(BaseModel):
    actions_taken: List[str]
    escalated_to_human: bool
    reason: str
    task_ids_affected: List[str]
