"""
Database CRUD operations for NEXUS Platform
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from typing import List, Optional
import hashlib

from database.models import Meeting, Decision, Task, AgentEvent, AuditLog, Notification, ParticipantEmail


# ─── Meeting CRUD ─────────────────────────────────────────────────────────────

def create_meeting(db: Session, title: str, raw_transcript: str,
                   participants: List[str] = None, duration_minutes: int = 0) -> Meeting:
    meeting = Meeting(
        title=title,
        raw_transcript=raw_transcript,
        participants=participants or [],
        duration_minutes=duration_minutes,
        status="pending"
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    return meeting


def get_meeting(db: Session, meeting_id: str) -> Optional[Meeting]:
    return db.query(Meeting).filter(Meeting.id == meeting_id).first()


def get_meetings(db: Session, skip: int = 0, limit: int = 100) -> List[Meeting]:
    return db.query(Meeting).order_by(Meeting.uploaded_at.desc()).offset(skip).limit(limit).all()


def update_meeting_status(db: Session, meeting_id: str, status: str,
                          summary: str = None, crew_run_id: str = None) -> Optional[Meeting]:
    meeting = get_meeting(db, meeting_id)
    if meeting:
        meeting.status = status
        if summary:
            meeting.summary = summary
        if crew_run_id:
            meeting.crew_run_id = crew_run_id
        db.commit()
        db.refresh(meeting)
    return meeting


def delete_meeting(db: Session, meeting_id: str) -> bool:
    meeting = get_meeting(db, meeting_id)
    if meeting:
        db.delete(meeting)
        db.commit()
        return True
    return False

# ─── Participant Email CRUD ────────────────────────────────────────────────
def save_participant_emails(db: Session, meeting_id: str, participants: list) -> List[ParticipantEmail]:
    # Delete existing if any for this meeting
    db.query(ParticipantEmail).filter(ParticipantEmail.meeting_id == meeting_id).delete()
    
    emails = []
    for p in participants:
        email = ParticipantEmail(
            meeting_id=meeting_id,
            participant_name=p['participant_name'],
            email_address=p['email_address']
        )
        db.add(email)
        emails.append(email)
    
    db.commit()
    return emails

def get_participant_email(db: Session, meeting_id: str, participant_name: str) -> Optional[str]:
    if not participant_name or not meeting_id:
        return None
    
    print(f"[EMAIL LOOKUP] Looking for: '{participant_name}' in meeting: {meeting_id}")
    
    # Normalize search input
    search_name = participant_name.strip().lower()
    
    all_stored = db.query(ParticipantEmail).filter(
        ParticipantEmail.meeting_id == meeting_id
    ).all()
    
    # Strategy 1: Exact match (case-insensitive, after stripping whitespace)
    for stored in all_stored:
        if stored.participant_name.strip().lower() == search_name:
            print(f"[EMAIL LOOKUP] ✅ Found (exact match): {stored.email_address}")
            return stored.email_address
    
    # Strategy 2: Substring match (case-insensitive)
    for stored in all_stored:
        stored_lower = stored.participant_name.strip().lower()
        if search_name in stored_lower or stored_lower in search_name:
            print(f"[EMAIL LOOKUP] ✅ Found (substring match): {stored.email_address}")
            return stored.email_address
    
    # Strategy 3: First name match
    search_first = search_name.split()[0]
    for stored in all_stored:
        stored_first = stored.participant_name.strip().lower().split()[0]
        if search_first and stored_first and search_first == stored_first:
            print(f"[EMAIL LOOKUP] ✅ Found (first name match): {stored.email_address}")
            return stored.email_address
    
    print(f"[EMAIL LOOKUP] ❌ Not found for '{participant_name}'")
    print(f"[EMAIL LOOKUP] All stored: {[(e.participant_name, e.email_address) for e in all_stored]}")
    return None

def get_notifications_for_meeting(db: Session, meeting_id: str) -> List[Notification]:
    return db.query(Notification).join(Task).filter(Task.meeting_id == meeting_id).all()

# ─── Decision CRUD ───────────────────────────────────────────────────────────

def create_decision(db: Session, meeting_id: str, decision_text: str,
                    context: str = None, confidence_score: float = 0.8,
                    extracted_by: str = "Decision Extraction Agent") -> Decision:
    decision = Decision(
        meeting_id=meeting_id,
        decision_text=decision_text,
        context=context,
        confidence_score=confidence_score,
        extracted_by=extracted_by
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)
    return decision


def get_decisions_for_meeting(db: Session, meeting_id: str) -> List[Decision]:
    return db.query(Decision).filter(Decision.meeting_id == meeting_id).all()


# ─── Task CRUD ───────────────────────────────────────────────────────────────

def create_task(db: Session, meeting_id: str, title: str, description: str = None,
                decision_id: str = None, assigned_to: str = None, priority: str = "medium",
                due_date: datetime = None, assigned_by: str = "Assignor Agent",
                assignment_rationale: str = None, context_quote: str = None) -> Task:
    task = Task(
        meeting_id=meeting_id,
        decision_id=decision_id,
        title=title,
        description=description,
        assigned_to=assigned_to,
        assigned_by=assigned_by,
        priority=priority,
        status="created",
        due_date=due_date,
        assignment_rationale=assignment_rationale,
        context_quote=context_quote
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_task(db: Session, task_id: str) -> Optional[Task]:
    return db.query(Task).filter(Task.id == task_id).first()


def get_tasks(db: Session, meeting_id: str = None, status: str = None,
              assignee: str = None, skip: int = 0, limit: int = 200) -> List[Task]:
    query = db.query(Task)
    if meeting_id:
        query = query.filter(Task.meeting_id == meeting_id)
    if status:
        query = query.filter(Task.status == status)
    if assignee:
        query = query.filter(Task.assigned_to == assignee)
    return query.order_by(Task.created_at.desc()).offset(skip).limit(limit).all()


def update_task(db: Session, task_id: str, **kwargs) -> Optional[Task]:
    task = get_task(db, task_id)
    if task:
        for key, value in kwargs.items():
            if hasattr(task, key) and value is not None:
                setattr(task, key, value)
        task.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(task)
    return task


def mark_task_stalled(db: Session, task_id: str) -> Optional[Task]:
    task = get_task(db, task_id)
    if task:
        task.status = "stalled"
        task.stall_detected_at = datetime.utcnow()
        task.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(task)
    return task


def escalate_task(db: Session, task_id: str) -> Optional[Task]:
    task = get_task(db, task_id)
    if task:
        task.status = "escalated"
        task.escalation_count = (task.escalation_count or 0) + 1
        task.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(task)
    return task


def complete_task(db: Session, task_id: str, is_human_override: bool = False) -> Optional[Task]:
    task = get_task(db, task_id)
    if task:
        task.status = "completed"
        task.completed_at = datetime.utcnow()
        task.updated_at = datetime.utcnow()
        task.is_human_override = is_human_override
        db.commit()
        db.refresh(task)
    return task


# ─── Agent Event CRUD ────────────────────────────────────────────────────────

def create_agent_event(db: Session, meeting_id: str, agent_name: str,
                       agent_role: str = None, event_type: str = "started",
                       input_context: dict = None, output_result: dict = None,
                       tool_used: str = None, duration_ms: int = 0,
                       sequence_number: int = 0) -> AgentEvent:
    event = AgentEvent(
        meeting_id=meeting_id,
        agent_name=agent_name,
        agent_role=agent_role,
        event_type=event_type,
        input_context=input_context or {},
        output_result=output_result or {},
        tool_used=tool_used,
        duration_ms=duration_ms,
        sequence_number=sequence_number
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def get_agent_events(db: Session, meeting_id: str) -> List[AgentEvent]:
    return db.query(AgentEvent).filter(
        AgentEvent.meeting_id == meeting_id
    ).order_by(AgentEvent.sequence_number).all()


# ─── Audit Log CRUD ──────────────────────────────────────────────────────────

def create_audit_log(db: Session, action: str, actor: str,
                     meeting_id: str = None, target_type: str = None,
                     target_id: str = None, before_state: dict = None,
                     after_state: dict = None, decision_rationale: str = None,
                     is_human_override: bool = False) -> AuditLog:
    now = datetime.utcnow()
    raw = f"{actor}{action}{now.isoformat()}"
    checksum = hashlib.sha256(raw.encode()).hexdigest()

    log = AuditLog(
        meeting_id=meeting_id,
        action=action,
        actor=actor,
        target_type=target_type,
        target_id=target_id,
        before_state=before_state,
        after_state=after_state,
        decision_rationale=decision_rationale,
        timestamp=now,
        is_human_override=is_human_override,
        checksum=checksum
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_audit_logs(db: Session, meeting_id: str = None, skip: int = 0,
                   limit: int = 500) -> List[AuditLog]:
    query = db.query(AuditLog)
    if meeting_id:
        query = query.filter(AuditLog.meeting_id == meeting_id)
    return query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()


def verify_audit_log(db: Session, log_id: str) -> dict:
    log = db.query(AuditLog).filter(AuditLog.id == log_id).first()
    if not log:
        return {"valid": False, "error": "Log not found"}
    raw = f"{log.actor}{log.action}{log.timestamp.isoformat()}"
    expected = hashlib.sha256(raw.encode()).hexdigest()
    return {
        "valid": log.checksum == expected,
        "stored_checksum": log.checksum,
        "computed_checksum": expected
    }


# ─── Notification CRUD ───────────────────────────────────────────────────────

def create_notification(db: Session, task_id: str, recipient: str,
                        channel: str, message: str,
                        notification_type: str = "assignment",
                        email_sent: bool = False,
                        email_sent_at: datetime = None,
                        email_error: str = None) -> Notification:
    notif = Notification(
        task_id=task_id,
        recipient=recipient,
        channel=channel,
        message=message,
        notification_type=notification_type,
        email_sent=email_sent,
        email_sent_at=email_sent_at,
        email_error=email_error
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif


def get_notification(db: Session, notif_id: str) -> Optional[Notification]:
    return db.query(Notification).filter(Notification.id == notif_id).first()


def update_notification(db: Session, notif_id: str, **kwargs) -> Optional[Notification]:
    notif = get_notification(db, notif_id)
    if notif:
        for key, value in kwargs.items():
            if hasattr(notif, key):
                setattr(notif, key, value)
        db.commit()
        db.refresh(notif)
    return notif


# ─── Dashboard Stats ─────────────────────────────────────────────────────────

def get_dashboard_stats(db: Session) -> dict:
    total_meetings = db.query(func.count(Meeting.id)).scalar() or 0
    total_tasks = db.query(func.count(Task.id)).scalar() or 0
    completed_tasks = db.query(func.count(Task.id)).filter(Task.status == "completed").scalar() or 0
    escalated_tasks = db.query(func.count(Task.id)).filter(Task.status == "escalated").scalar() or 0
    stalled_tasks = db.query(func.count(Task.id)).filter(Task.status == "stalled").scalar() or 0
    at_risk_tasks = db.query(func.count(Task.id)).filter(Task.status == "at_risk").scalar() or 0
    split_tasks = db.query(func.count(Task.id)).filter(Task.status == "split_into_subtasks").scalar() or 0
    reopened_tasks = db.query(func.count(Task.id)).filter(Task.status == "reopened").scalar() or 0
    
    total_decisions = db.query(func.count(Decision.id)).scalar() or 0
    active_workflows = db.query(func.count(Meeting.id)).filter(Meeting.status == "processing").scalar() or 0

    human_override_tasks = db.query(func.count(Task.id)).filter(
        Task.is_human_override == True
    ).scalar() or 0

    # CHANGE 5: Calculate autonomy and auto-fix metrics
    autonomy_score = 0.0
    auto_fix_rate = 0.0
    if total_tasks > 0:
        autonomy_score = round(((total_tasks - human_override_tasks) / total_tasks) * 100, 1)
        # Auto-fixed tasks: escalated but not escalated to human (fixed by agent)
        auto_fixed = escalated_tasks - db.query(func.count(Task.id)).filter(
            Task.status == "escalated", Task.escalation_count >= 3
        ).scalar() or 0
        auto_fix_rate = round((auto_fixed / total_tasks) * 100, 1) if auto_fixed > 0 else 0.0

    return {
        "total_meetings": total_meetings,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "escalated_tasks": escalated_tasks,
        "stalled_tasks": stalled_tasks,
        "at_risk_tasks": at_risk_tasks,
        "split_tasks": split_tasks,
        "reopened_tasks": reopened_tasks,
        "autonomy_score": autonomy_score,
        "auto_fix_rate": auto_fix_rate,
        "active_workflows": active_workflows,
        "total_decisions": total_decisions,
        "risk_avoided": at_risk_tasks + split_tasks  # Tasks that were fixed before becoming critical
    }
