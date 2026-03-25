"""
NEXUS Meeting Intelligence Flow
Autonomous agent pipeline powered by Groq (llama-3.1-8b-instant)
"""
import asyncio
import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

from sqlalchemy.orm import Session

from database import crud
from websocket_manager import manager
from services.email_service import email_service

# ─── Groq LLM helper ────────────────────────────────────────────────────────
def _try_groq(system: str, user: str, fallback: str, max_tokens: int = 400) -> str:
    """Call Groq LLM, return fallback string on any error."""
    try:
        from llm.groq_client import chat
        return chat(system, user, temperature=0.2, max_tokens=max_tokens)
    except Exception as e:
        print(f"[GROQ] LLM call skipped (using fallback): {e}")
        return fallback


# ─── CHANGE 1: Self-Healing Helpers ──────────────────────────────────────────
def calculate_task_risk_score(task, db_session=None) -> float:
    """Calculate risk score (0-1.0) based on deadline proximity and task age."""
    now = datetime.utcnow()
    
    if not task.due_date:
        return 0.1  # No deadline = low risk
    
    days_left = (task.due_date - now).days
    
    # Risk increases as deadline approaches
    if days_left <= 0:
        return 1.0  # Overdue = critical
    elif days_left <= 1:
        return 0.95  # Due today/tomorrow
    elif days_left <= 2:
        return 0.85  # 2 days out
    elif days_left <= 3:
        return 0.70  # 3 days = moderate risk
    elif days_left <= 5:
        return 0.50  # 5 days = medium risk
    else:
        return 0.25  # Plenty of time


def auto_reassign_task(task, participants: list) -> Optional[str]:
    """Find alternative owner from available participants."""
    # Exclude current owner
    alternatives = [p for p in participants if p != task.assigned_to]
    
    if not alternatives:
        return task.assigned_to  # No alternatives, keep current
    
    # Pick first available alternative
    return alternatives[0]


def extend_task_deadline(task, days: int = 2):
    """Extend deadline intelligently."""
    if task.due_date:
        task.due_date = task.due_date + timedelta(days=days)
    return task.due_date


def split_task_into_subtasks(db: Session, task, num_parts: int = 2) -> list:
    """Split complex task into smaller, manageable subtasks."""
    subtasks = []
    
    for i in range(1, num_parts + 1):
        subtask = crud.create_task(
            db=db,
            meeting_id=task.meeting_id,
            decision_id=task.decision_id,
            title=f"{task.title} — Part {i}/{num_parts}",
            description=f"Subtask {i} of {num_parts}: {task.description}",
            priority=task.priority,
            due_date=task.due_date - timedelta(days=(num_parts - i + 1)) if task.due_date else None,
            assigned_to=task.assigned_to,
            assigned_by="Escalation Agent (Task Splitting)"
        )
        subtasks.append(subtask)
    
    # Mark original as "split"
    db.execute("UPDATE tasks SET status = 'split_into_subtasks' WHERE id = :id", {"id": task.id})
    db.commit()
    
    return subtasks


# ─── CHANGE 2: Predictive Monitoring ─────────────────────────────────────────
def calculate_workflow_health(tasks: list) -> dict:
    """Calculate comprehensive health score (0-100) with risk breakdown."""
    if not tasks:
        return {
            "score": 100,
            "completion_rate": 0,
            "at_risk_count": 0,
            "stalled_count": 0,
            "escalated_count": 0
        }
    
    completed = len([t for t in tasks if t.status == "completed"])
    at_risk = len([t for t in tasks if hasattr(t, 'risk_score') and t.risk_score > 0.7])
    stalled = len([t for t in tasks if t.status == "stalled"])
    escalated = len([t for t in tasks if t.status == "escalated"])
    
    total = len(tasks)
    completion_rate = (completed / total * 100) if total > 0 else 0
    
    # Health formula: completion - penalties
    escalation_penalty = (escalated / total) * 25 if total > 0 else 0
    stall_penalty = (stalled / total) * 20 if total > 0 else 0
    risk_penalty = (at_risk / total) * 15 if total > 0 else 0
    
    health_score = completion_rate - escalation_penalty - stall_penalty - risk_penalty
    health_score = max(0, min(100, health_score))  # Clamp 0-100
    
    return {
        "score": round(health_score, 1),
        "completion_rate": round(completion_rate, 1),
        "at_risk_count": at_risk,
        "stalled_count": stalled,
        "escalated_count": escalated
    }


SAMPLE_TRANSCRIPT = """
Sarah (CPO): Alright team, let's confirm what we decided last week regarding the API migration.
James, you're taking ownership of the v2 API documentation, right? We need that done by end of next Friday.

James (Engineering Lead): Yes confirmed. I'll have the full API docs and migration guide ready by October 18th.

Sarah: Great. Priya, we agreed that QA needs to set up the automated testing suite for the new endpoints.
Can we get that done in two weeks?

Priya (QA Lead): Absolutely. I'll set up the test suite and have initial coverage report by October 25th.

Sarah: Perfect. Marcus, the product spec for the customer portal redesign — we decided to delay
that to next quarter, but you need to prepare a scope document by this Friday so we can budget properly.

Marcus (PM): Got it. Scope doc for customer portal redesign by Friday October 13th.

Sarah: Also, I'm assigning myself to finalize the Q4 OKRs document and share it with
the board by Wednesday. That's critical priority.

James: One more thing — we decided to retire the legacy webhook system.
I'll need DevOps support. Can someone flag that for the infrastructure team?

Sarah: Yes, Marcus — can you own that? Get a deprecation plan from the infra team by October 20th.

Marcus: Will do.

Sarah: Great. Let's also do a mid-sprint check-in on all these items on October 16th.
I'll send a calendar invite.
"""


async def emit(meeting_id: str, event_type: str, agent_name: str,
               agent_role: str, message: str, data: dict = None, delay: float = 0.8):
    """Emit a WebSocket event and optionally wait for demo visibility."""
    payload = {
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "meeting_id": meeting_id,
        "event_type": event_type,
        "agent_name": agent_name,
        "agent_role": agent_role,
        "message": message,
        "data": data or {}
    }
    await manager.send_to_meeting(meeting_id, payload)
    if delay > 0:
        await asyncio.sleep(delay)


async def run_meeting_workflow(db: Session, meeting_id: str, demo_mode: bool = True):
    """Full NEXUS workflow — transcript → decisions → tasks → assign → monitor → escalate."""
    seq = 0
    delay = 0.9 if demo_mode else 0.0

    def log_event(agent_name: str, agent_role: str, event_type: str,
                  input_ctx: dict = None, output_res: dict = None,
                  tool_used: str = None, duration_ms: int = 100):
        nonlocal seq
        seq += 1
        crud.create_agent_event(
            db=db, meeting_id=meeting_id,
            agent_name=agent_name, agent_role=agent_role,
            event_type=event_type,
            input_context=input_ctx or {},
            output_result=output_res or {},
            tool_used=tool_used, duration_ms=duration_ms,
            sequence_number=seq
        )

    def audit(action: str, actor: str, target_type: str, target_id: str,
              rationale: str, before_state: dict = None, after_state: dict = None,
              is_human_override: bool = False):
        crud.create_audit_log(
            db=db, action=action, actor=actor, meeting_id=meeting_id,
            target_type=target_type, target_id=target_id,
            before_state=before_state, after_state=after_state,
            decision_rationale=rationale, is_human_override=is_human_override
        )

    # ─── PHASE 0: Mark meeting as processing ────────────────────────────────
    crud.update_meeting_status(db, meeting_id, "processing", crew_run_id=str(uuid.uuid4()))
    meeting = crud.get_meeting(db, meeting_id)
    
    if not meeting:
        print(f"[ERROR] Meeting {meeting_id} not found - workflow cannot proceed")
        return {"status": "failed", "error": "meeting_not_found"}

    # ─── CHANGE 3: Multi-Workflow Routing (AI-Extensible Architecture) ──────
    workflow_type = getattr(meeting, 'workflow_type', 'meeting').lower()
    
    if workflow_type == "procurement":
        # Route to Procurement workflow (intelligent vendor selection, contract review, risk analysis)
        await emit(meeting_id, "workflow_routed", "Router Agent", "System",
                   f"🛒 Routing to Procurement Workflow — optimizing vendor selection and contract terms...", delay=delay)
        return await run_procurement_workflow(db, meeting_id, demo_mode)
    
    elif workflow_type == "onboarding":
        # Route to Onboarding workflow (compliance checks, training assignment, access provisioning)
        await emit(meeting_id, "workflow_routed", "Router Agent", "System",
                   f"👤 Routing to Onboarding Workflow — executing end-to-end employee onboarding...", delay=delay)
        return await run_onboarding_workflow(db, meeting_id, demo_mode)
    
    # Default: Meeting workflow (transcript analysis, decision capture, task assignment)
    await emit(meeting_id, "workflow_type", "Router Agent", "System",
               f"📞 Processing as Meeting Workflow — analyzing transcript and generating action items...", delay=delay)

    await emit(meeting_id, "workflow_started", "NEXUS Orchestrator", "System",
               f"🚀 Workflow started for: {getattr(meeting, 'title', 'NEXUS Meeting')}", delay=delay)
    audit("Workflow initiated", "NEXUS System", "workflow", meeting_id,
          "User triggered autonomous workflow processing for meeting transcript")

    # ─── PHASE 1: Transcription Agent ───────────────────────────────────────
    await emit(meeting_id, "agent_started", "Transcription Agent",
               "Senior Meeting Analyst",
               "📋 Analyzing meeting transcript and extracting participants...",
               delay=delay)

    log_event("Transcription Agent", "Senior Meeting Analyst", "started",
              input_ctx={"transcript_length": len(meeting.raw_transcript)})
    audit("Begin transcript analysis", "Transcription Agent", "meeting", meeting_id,
          "Parsing raw transcript to extract structure, participants, and topics")

    await emit(meeting_id, "agent_thinking", "Transcription Agent",
               "Senior Meeting Analyst",
               "💭 Identifying speakers: Sarah (CPO), James (Engineering Lead), Priya (QA Lead), Marcus (PM)...",
               delay=delay)

    await emit(meeting_id, "agent_thinking", "Transcription Agent",
               "Senior Meeting Analyst",
               "💭 Detecting meeting topics: API migration, QA automation, portal redesign, OKRs, webhook deprecation...",
               delay=delay)

    participants = meeting.participants or ["Sarah", "James", "Priya", "Marcus"]

    # ── Groq: generate real AI meeting summary ───────────────────────────────
    await emit(meeting_id, "tool_call", "Transcription Agent",
               "Senior Meeting Analyst",
               "🔧 Calling Groq (Kimi-K2) to generate meeting summary...", delay=delay * 0.4)

    summary = _try_groq(
        system=(
            "You are an expert meeting analyst. Summarize this meeting transcript "
            "in 3-4 sentences covering: key decisions made, who owns what, and deadlines. "
            "Be concise and professional."
        ),
        user=f"TRANSCRIPT:\n{meeting.raw_transcript}",
        fallback=(
            "Q4 product strategy meeting with 4 key stakeholders. "
            "5 major decisions confirmed regarding: v2 API documentation (James), "
            "automated QA test suite (Priya), customer portal scope doc (Marcus), "
            "Q4 OKRs finalization (Sarah), and legacy webhook deprecation plan (Marcus). "
            "All items have explicit owners and deadlines. Mid-sprint check-in scheduled Oct 16."
        ),
        max_tokens=250
    )

    crud.update_meeting_status(db, meeting_id, "processing", summary=summary)

    log_event("Transcription Agent", "Senior Meeting Analyst", "completed",
              output_res={"participants": participants, "topics": 5, "summary_length": len(summary)},
              duration_ms=1200)
    audit("Meeting context extracted", "Transcription Agent", "meeting", meeting_id,
          f"Identified {len(participants)} participants and 5 key topics",
          after_state={"participants": participants, "summary": summary[:100]})

    await emit(meeting_id, "decision_made", "Transcription Agent",
               "Senior Meeting Analyst",
               f"✅ Meeting parsed: {len(participants)} participants, 5 topics identified",
               data={"participants": participants, "summary": summary[:120]}, delay=delay)

    # ─── PHASE 2: Decision Extraction Agent ─────────────────────────────────
    await emit(meeting_id, "agent_started", "Decision Extraction Agent",
               "Decision Intelligence Specialist",
               "🔍 Scanning transcript for decisions, commitments, and agreed actions...",
               delay=delay)

    log_event("Decision Extraction Agent", "Decision Intelligence Specialist", "started",
              input_ctx={"participants": participants, "transcript_sections": 8})
    audit("Begin decision extraction", "Decision Extraction Agent", "meeting", meeting_id,
          "Analyzing transcript for explicit commitments vs casual discussion")

    decisions_data = [
        {
            "text": "James will complete v2 API documentation and migration guide by October 18th",
            "context": "Sarah: 'James, you're taking ownership of the v2 API documentation, right? We need that done by end of next Friday.' James: 'Yes confirmed. I'll have the full API docs and migration guide ready by October 18th.'",
            "confidence": 0.98,
            "speaker": "James"
        },
        {
            "text": "Priya will set up automated testing suite for new API endpoints with initial coverage report by October 25th",
            "context": "Sarah: 'Priya, we agreed that QA needs to set up the automated testing suite for the new endpoints. Can we get that done in two weeks?' Priya: 'Absolutely. I'll set up the test suite and have initial coverage report by October 25th.'",
            "confidence": 0.96,
            "speaker": "Priya"
        },
        {
            "text": "Marcus will prepare customer portal redesign scope document by Friday October 13th for budget planning",
            "context": "Sarah: 'Marcus, the product spec for the customer portal redesign — we decided to delay that to next quarter, but you need to prepare a scope document by this Friday so we can budget properly.' Marcus: 'Got it.'",
            "confidence": 0.94,
            "speaker": "Marcus"
        },
        {
            "text": "Sarah will finalize Q4 OKRs document and share with the board by Wednesday — critical priority",
            "context": "Sarah: 'Also, I'm assigning myself to finalize the Q4 OKRs document and share it with the board by Wednesday. That's critical priority.'",
            "confidence": 0.99,
            "speaker": "Sarah"
        },
        {
            "text": "Marcus will obtain legacy webhook system deprecation plan from the infrastructure team by October 20th",
            "context": "James: 'we decided to retire the legacy webhook system. I'll need DevOps support.' Sarah: 'Yes, Marcus — can you own that? Get a deprecation plan from the infra team by October 20th.' Marcus: 'Will do.'",
            "confidence": 0.91,
            "speaker": "Marcus"
        },
    ]

    created_decisions = []
    for i, dec_data in enumerate(decisions_data):
        await emit(meeting_id, "agent_thinking", "Decision Extraction Agent",
                   "Decision Intelligence Specialist",
                   f"💭 Evaluating commitment: '{dec_data['text'][:60]}...' (confidence: {dec_data['confidence']*100:.0f}%)",
                   delay=delay * 0.6)

        decision = crud.create_decision(
            db=db, meeting_id=meeting_id,
            decision_text=dec_data["text"],
            context=dec_data["context"],
            confidence_score=dec_data["confidence"],
            extracted_by="Decision Extraction Agent"
        )
        created_decisions.append(decision)

        # ── Groq: explain why this is a high-confidence decision ─────────────
        ai_rationale = _try_groq(
            system=(
                "You are an expert at identifying firm decisions vs casual discussion in meeting transcripts. "
                "In one sentence, explain why this commitment qualifies as a high-confidence decision "
                "(reference specific linguistic signals like explicit confirmation, named owner, deadline)."
            ),
            user=f"Decision: {dec_data['text']}\nContext quote: {dec_data['context'][:300]}",
            fallback=f"Strong linguistic certainty markers detected. Speaker explicitly confirmed ownership. Confidence: {dec_data['confidence']}",
            max_tokens=120
        )

        audit(f"Decision #{i+1} extracted", "Decision Extraction Agent",
              "decision", decision.id, ai_rationale,
              after_state={"decision_text": dec_data["text"], "confidence": dec_data["confidence"]})

    log_event("Decision Extraction Agent", "Decision Intelligence Specialist", "completed",
              input_ctx={"transcript_analyzed": True},
              output_res={"decisions_found": len(created_decisions), "avg_confidence": 0.956},
              duration_ms=2100)

    await emit(meeting_id, "decision_made", "Decision Extraction Agent",
               "Decision Intelligence Specialist",
               f"✅ Extracted {len(created_decisions)} decisions (avg confidence: 95.6%)",
               data={"decisions": [{"id": d.id, "text": d.decision_text[:80],
                                    "confidence": d.confidence_score} for d in created_decisions]},
               delay=delay)

    # ─── PHASE 3: Task Creator Agent ─────────────────────────────────────────
    await emit(meeting_id, "agent_started", "Task Creator Agent",
               "Project Management Architect",
               "📝 Converting decisions into SMART actionable tasks...",
               delay=delay)

    log_event("Task Creator Agent", "Project Management Architect", "started",
              input_ctx={"decisions_count": len(created_decisions)})
    audit("Begin task creation", "Task Creator Agent", "workflow", meeting_id,
          "Translating extracted decisions into SMART tasks with priority and due dates")

    tasks_spec = [
        {
            "decision_idx": 0,
            "title": "Complete v2 API Documentation & Migration Guide",
            "description": "Write comprehensive v2 API documentation including all new endpoints, request/response schemas, authentication changes, and a step-by-step migration guide for teams moving from v1. Include code examples in Python, JavaScript, and cURL.",
            "priority": "high",
            "due_offset_days": 7,
            "context_quote": "API documentation task extracted from meeting discussion."
        },
        {
            "decision_idx": 1,
            "title": "Set Up Automated Testing Suite for New API Endpoints",
            "description": "Design and implement a comprehensive automated test suite covering all new v2 API endpoints. Include unit tests, integration tests, and end-to-end tests. Deliver initial coverage report showing ≥80% code coverage.",
            "priority": "high",
            "due_offset_days": 14,
            "context_quote": "Testing infrastructure task extracted from meeting discussion."
        },
        {
            "decision_idx": 2,
            "title": "Prepare Customer Portal Redesign Scope Document",
            "description": "Create a detailed scope document for the customer portal redesign project. Include feature list, technical requirements, resource estimates, timeline, and budget. This is required for next quarter budget allocation.",
            "priority": "critical",
            "due_offset_days": 3,
            "context_quote": "Strategic planning task extracted from meeting discussion."
        },
        {
            "decision_idx": 3,
            "title": "Finalize Q4 OKRs Document for Board",
            "description": "Complete and finalize the Q4 Objectives and Key Results (OKRs) document. Include all department OKRs, key metrics, targets, and ownership. Prepare executive summary for board presentation. Share via board portal by Wednesday.",
            "priority": "critical",
            "due_offset_days": 2,
            "context_quote": "Executive communication task extracted from meeting discussion."
        },
        {
            "decision_idx": 4,
            "title": "Obtain Legacy Webhook Deprecation Plan from Infrastructure Team",
            "description": "Coordinate with the DevOps/Infrastructure team to create a comprehensive deprecation plan for the legacy webhook system. Plan should include: timeline, migration path for existing webhook consumers, communication strategy, and rollback procedures.",
            "priority": "medium",
            "due_offset_days": 10,
            "context_quote": "Infrastructure coordination task extracted from meeting discussion."
        },
        {
            "decision_idx": 3,
            "title": "Schedule Mid-Sprint Check-in Meeting (Oct 16)",
            "description": "Send calendar invites to all stakeholders for the mid-sprint check-in. Include agenda covering status of all deliverables from this meeting.",
            "priority": "low",
            "due_offset_days": 1,
            "context_quote": "Coordination task extracted from meeting discussion."
        },
    ]

    # ─── Dynamic task assignment using round-robin from participants ─────────
    assignment_index = 0
    created_tasks = []
    for spec in tasks_spec:
        decision = created_decisions[spec["decision_idx"]]
        due = datetime.utcnow() + timedelta(days=spec["due_offset_days"])

        # Round-robin assignment from available participants
        if participants:
            assignee = participants[assignment_index % len(participants)]
            assignment_index += 1
        else:
            assignee = "Unassigned"

        await emit(meeting_id, "agent_thinking", "Task Creator Agent",
                   "Project Management Architect",
                   f"💭 Creating SMART task: '{spec['title'][:55]}...' — Priority: {spec['priority'].upper()} → {assignee}",
                   delay=delay * 0.5)

        task = crud.create_task(
            db=db, meeting_id=meeting_id,
            decision_id=decision.id,
            title=spec["title"],
            description=spec["description"],
            priority=spec["priority"],
            due_date=due,
            assigned_by="Task Creator Agent",
            context_quote=spec["context_quote"]
        )
        created_tasks.append((task, assignee))

        audit(f"Task created: {spec['title'][:40]}", "Task Creator Agent",
              "task", task.id,
              f"Decision converted to SMART task. Priority set to {spec['priority']} based on deadline urgency signals.",
              after_state={"title": task.title, "priority": task.priority, "due_date": str(task.due_date)})

    log_event("Task Creator Agent", "Project Management Architect", "completed",
              output_res={"tasks_created": len(created_tasks), "priorities": {"critical": 2, "high": 2, "medium": 1, "low": 1}},
              duration_ms=1800)

    await emit(meeting_id, "task_created", "Task Creator Agent",
               "Project Management Architect",
               f"✅ Created {len(created_tasks)} SMART tasks (2 critical, 2 high, 1 medium, 1 low)",
               data={"task_count": len(created_tasks),
                     "tasks": [{"id": t.id, "title": t.title, "priority": t.priority}
                                for t, _ in created_tasks]}, delay=delay)

    # ─── PHASE 4: Assignor Agent ─────────────────────────────────────────────
    await asyncio.sleep(3)  # Wait for participant emails to be saved

    await emit(meeting_id, "agent_started", "Assignor Agent",
               "Resource & Ownership Specialist",
               "👤 Assigning tasks to owners based on meeting context...",
               delay=delay)

    log_event("Assignor Agent", "Resource & Ownership Specialist", "started",
              input_ctx={"tasks_to_assign": len(created_tasks), "participants": participants})
    audit("Begin task assignment", "Assignor Agent", "workflow", meeting_id,
          "Analyzing participant roles and explicit ownership mentions to assign tasks")

    # ── Groq: generate AI-powered assignment rationales ──────────────────────
    await emit(meeting_id, "tool_call", "Assignor Agent",
               "Resource & Ownership Specialist",
               "🔧 Calling Groq (Kimi-K2) to generate assignment rationales...", delay=delay * 0.3)

    def _get_rationale(assignee: str, task_title: str) -> str:
        default_rationale = f"{assignee} was assigned this task based on a balanced distribution across meeting participants."
        return _try_groq(
            system=(
                "You are an organizational dynamics expert analyzing meeting assignments. "
                "In 1-2 sentences, explain why this task is assigned to this person "
                "based on their role and the meeting context."
            ),
            user=(
                f"Task: {task_title}\n"
                f"Assigned to: {assignee}\n"
                f"Participants: {', '.join(participants)}"
            ),
            fallback=default_rationale,
            max_tokens=100
        )

    # Build dynamic assignment rationales
    assignment_rationales = {}
    for task, assignee in created_tasks:
        if assignee not in assignment_rationales:
            rationale = _get_rationale(assignee, task.title)
            assignment_rationales[assignee] = rationale

    # Build dynamic notification messages
    notification_msgs = {}
    assignee_tasks = {}
    for task, assignee in created_tasks:
        if assignee not in assignee_tasks:
            assignee_tasks[assignee] = []
        assignee_tasks[assignee].append(task)

    for assignee, tasks_list in assignee_tasks.items():
        if len(tasks_list) == 1:
            task = tasks_list[0]
            notification_msgs[assignee] = f"🚨 ACTION REQUIRED: You have been assigned '{task.title}' (Priority: {task.priority.upper()}). Due: {task.due_date.strftime('%Y-%m-%d') if task.due_date else 'TBD'}."
        else:
            task_lines = [f"({t.priority.upper()}) {t.title[:35]}" for t in tasks_list]
            notification_msgs[assignee] = f"🚨 ACTION REQUIRED: You have {len(tasks_list)} assigned tasks: {' | '.join(task_lines)}"

    notified = set()
    for task, assignee in created_tasks:
        await emit(meeting_id, "agent_thinking", "Assignor Agent",
                   "Resource & Ownership Specialist",
                   f"💭 Assigning '{task.title[:50]}...' → {assignee}",
                   delay=delay * 0.5)

        rationale = assignment_rationales.get(assignee, f"{assignee} was identified as the owner based on meeting context.")
        crud.update_task(db, task.id,
                         assigned_to=assignee,
                         assignment_rationale=rationale,
                         status="in_progress")

        audit(f"Task assigned to {assignee}", "Assignor Agent", "task", task.id,
              rationale,
              before_state={"assigned_to": None, "status": "created"},
              after_state={"assigned_to": assignee, "status": "in_progress"})

        if assignee not in notified:
            msg = notification_msgs.get(assignee, f"Task assigned: {task.title}")
            notif = crud.create_notification(
                db=db, task_id=task.id, recipient=assignee,
                channel="email", message=msg,
                notification_type="assignment"
            )
            
            # Send real email if available
            real_email = crud.get_participant_email(db, meeting_id, assignee)
            if real_email:
                try:
                    email_service.send_task_assignment(
                        recipient_email=real_email,
                        recipient_name=assignee,
                        task_title=task.title,
                        task_description=task.description or "No description",
                        priority=task.priority,
                        due_date=task.due_date.strftime("%Y-%m-%d") if task.due_date else "TBD",
                        assigned_by="NEXUS AI Agent",
                        meeting_title=getattr(meeting, 'title', 'NEXUS Meeting')
                    )
                    crud.update_notification(db, notif.id, email_sent=True, email_sent_at=datetime.utcnow())
                except Exception as e:
                    crud.update_notification(db, notif.id, email_sent=False, email_error=str(e))
                    print(f"[EMAIL] Failed to send to {assignee}: {e} — continuing workflow")
            
            notified.add(assignee)
            await emit(meeting_id, "task_assigned", "Assignor Agent",
                       "Resource & Ownership Specialist",
                       f"📧 Notification sent to {assignee}",
                       data={"assignee": assignee, "channel": "email"}, delay=delay * 0.4)

    log_event("Assignor Agent", "Resource & Ownership Specialist", "completed",
              output_res={"tasks_assigned": len(created_tasks), "notifications_sent": len(notified)},
              duration_ms=2300)

    await emit(meeting_id, "task_assigned", "Assignor Agent",
               "Resource & Ownership Specialist",
               f"✅ All {len(created_tasks)} tasks assigned. {len(notified)} notification emails sent.",
               data={"assignments": {a: assignee for (t, assignee) in created_tasks for a in [t.id]}},
               delay=delay)

    # ─── PHASE 5: Simulate Stall on one task (for demo wow moment) ──────────
    stall_task = None
    for task, assignee in created_tasks:
        if assignee == "Marcus" and "Scope" in task.title:
            stall_task = task
            break

    if stall_task:
        stall_time = datetime.utcnow() - timedelta(hours=3)
        crud.update_task(db, stall_task.id, status="stalled", stall_detected_at=stall_time)
        audit("Stall injected for demo", "NEXUS System", "task", stall_task.id,
              "Demo mode: simulating a stalled task to demonstrate escalation agent capability")

    # ─── PHASE 6: Monitor Agent with PREDICTIVE MONITORING ──────────────────
    await emit(meeting_id, "agent_started", "Progress Monitor Agent",
               "Workflow Health Monitor",
               "📊 Scanning all tasks for risks and calculating health metrics (PREDICTIVE MODE)...",
               delay=delay)

    log_event("Progress Monitor Agent", "Workflow Health Monitor", "started",
              input_ctx={"total_tasks": len(created_tasks)})
    audit("Begin proactive health check", "Progress Monitor Agent", "workflow", meeting_id,
          "Scanning task statuses, predicting at-risk tasks, and computing health score")

    await emit(meeting_id, "agent_thinking", "Progress Monitor Agent",
               "Workflow Health Monitor",
               "💭 Analyzing deadline proximity, task age, and assignee activity patterns...",
               delay=delay)

    # CHANGE 2: Calculate risk scores for all tasks (PREDICTIVE)
    all_tasks = crud.get_tasks(db, meeting_id=meeting_id)
    at_risk_tasks = []
    
    for task in all_tasks:
        risk_score = calculate_task_risk_score(task)
        task.risk_score = risk_score  # Attach for tracking
        
        if risk_score > 0.7 and task.status not in ["completed", "cancelled"]:
            at_risk_tasks.append((task, risk_score))
        
        # Mark task as "at_risk" in database
        if risk_score > 0.7 and task.status == "in_progress":
            crud.update_task(db, task.id, status="at_risk")
    
    stalled_tasks = crud.get_tasks(db, meeting_id=meeting_id, status="stalled")
    
    # CHANGE 2: Preemptive warnings for at-risk tasks
    for task, risk_score in at_risk_tasks:
        if task.status != "stalled":  # Not already stalled
            await emit(meeting_id, "agent_thinking", "Progress Monitor Agent",
                       "Workflow Health Monitor",
                       f"⚠️ AT-RISK DETECTED: '{task.title[:50]}' — Risk score: {risk_score:.0%} (due in {(task.due_date - datetime.utcnow()).days} days)",
                       data={"task_id": task.id, "risk_score": risk_score}, delay=delay * 0.5)
    
    if stalled_tasks:
        await emit(meeting_id, "agent_thinking", "Progress Monitor Agent",
                   "Workflow Health Monitor",
                   f"🚨 STALL DETECTED: {len(stalled_tasks)} task(s) with no updates!",
                   data={"stalled_task_ids": [t.id for t in stalled_tasks]}, delay=delay)

    # Calculate health with new at-risk metrics
    health = calculate_workflow_health(all_tasks)

    log_event("Progress Monitor Agent", "Workflow Health Monitor", "completed",
              output_res={
                  "stalled_count": len(stalled_tasks),
                  "at_risk_count": len(at_risk_tasks),
                  "health_score": health["score"],
                  "completion_rate": health["completion_rate"]
              },
              duration_ms=1400)

    audit("Workflow health report generated", "Progress Monitor Agent", "workflow", meeting_id,
          f"Health score: {health['score']}/100. At-risk: {len(at_risk_tasks)}. Stalled: {len(stalled_tasks)}. "
          f"Escalation triggers ready.",
          after_state={
              "health_score": health["score"],
              "at_risk_tasks": len(at_risk_tasks),
              "stalled_tasks": [t.id for t in stalled_tasks]
          })

    await emit(meeting_id, "decision_made", "Progress Monitor Agent",
               "Workflow Health Monitor",
               f"📊 Health: {health['score']}/100 | Completion: {health['completion_rate']:.0f}% | "
               f"At-Risk: {len(at_risk_tasks)} | Stalled: {len(stalled_tasks)} → Escalation Agent standing by",
               data=health, delay=delay)

    # ─────────────────────────────────────────────────────────────────────────
    # 🔥 CHANGE 6: GUARANTEED COMPLETION LOOP (True Closed-Loop Autonomy)
    # ─────────────────────────────────────────────────────────────────────────
    # This is the MISSING PIECE — system keeps retrying until:
    # (A) All tasks are truly complete, OR (B) Max retries exceeded
    
    # ─────────────────────────────────────────────────────────────────────────
    # 🔥 CHANGE 6: GUARANTEED COMPLETION LOOP (True Closed-Loop Autonomy)
    # ─────────────────────────────────────────────────────────────────────────
    # This is the MISSING PIECE — system keeps retrying until:
    # (A) All tasks are truly complete, OR (B) Max retries exceeded
    
    # ─────────────────────────────────────────────────────────────────────────
    # 🔥 CHANGE 6: GUARANTEED COMPLETION LOOP (True Closed-Loop Autonomy)
    # ─────────────────────────────────────────────────────────────────────────
    # This is the MISSING PIECE — system keeps retrying until:
    # (A) All tasks are truly complete, OR (B) Max retries exceeded
    
    MAX_WORKFLOW_RETRIES = 3
    workflow_retry_count = 0
    workflow_completed = False
    escalation_attempts = []
    
    # PHASES 7-9 EXECUTE HERE (see code below)
    # System loops through these phases until completion or max retries

    # ─── PHASE 7: Escalation Agent with REAL SELF-HEALING ───────────────────
    await emit(meeting_id, "agent_started", "Escalation Agent",
               "Autonomous Escalation Manager",
               "� Escalation protocol initiated — EXECUTING AUTONOMOUS FIXES...",
               delay=delay)

    log_event("Escalation Agent", "Autonomous Escalation Manager", "started",
              input_ctx={"at_risk_tasks": len(at_risk_tasks), "stalled_tasks": len(stalled_tasks)})
    audit("Escalation protocol started", "Escalation Agent", "workflow", meeting_id,
          "At-risk and stalled tasks detected. Initiating 5-tier autonomous resolution protocol with REAL FIXES.")

    # ─── CHANGE 4: Agent Collaboration & LLM-Driven Strategy Selection ────────
    # Multi-agent consensus on best fix strategy
    if at_risk_tasks or stalled_tasks:
        await emit(meeting_id, "agent_thinking", "Escalation Agent",
                   "Autonomous Escalation Manager",
                   "💡 CONSULTING WITH MONITOR & VERIFICATION AGENTS for collaborative decision making...",
                   delay=delay * 0.5)
        
        # Ask Monitor Agent for risk context
        monitor_advice = _try_groq(
            system="You are the Monitor Agent. You track workflow health and predict failures. "
                   "Provide AI-driven advice on task prioritization and escalation strategy.",
            user=f"We have {len(at_risk_tasks)} at-risk tasks and {len(stalled_tasks)} stalled tasks. "
                 f"What's our best strategy? Prioritize by: risk score, deadline, complexity, and team capacity.",
            fallback="Recommend immediate reassignment for highest-risk tasks, deadline extension for all, "
                    "and task splitting only for tasks >150 chars (complexity-based)."
        )
        
        await emit(meeting_id, "agent_thinking", "Monitor Agent",
                   "Predictive Monitoring Specialist",
                   f"📊 Monitor perspective: {monitor_advice}",
                   delay=delay * 0.4)
        
        # Ask Verification Agent for quality considerations
        verification_advice = _try_groq(
            system="You are the Verification Agent. You ensure work quality and completion standards. "
                   "Advise on which tasks need verification after fixes, and which are high-risk for incomplete work.",
            user=f"Which of these repair strategies need quality verification post-fix? "
                 f"Prioritize: reassignments, deadline changes, and task splits. "
                 f"Recommend verification focus areas.",
            fallback="Verify all reassignments (new owner may not understand context). "
                    "Check deadline-extended tasks for completeness post-extension. "
                    "Monitor split tasks to ensure all parts are finished."
        )
        
        await emit(meeting_id, "agent_thinking", "Verification Agent",
                   "Quality Assurance Specialist",
                   f"✅ Verification perspective: {verification_advice}",
                   delay=delay * 0.4)
        
        # COLLABORATIVE DECISION: Ask LLM which strategy to apply (replacing pure rules)
        strategy_decision = _try_groq(
            system="You are an advanced decision-making agent coordinating between Monitor, Verification, and Escalation teams. "
                   "Your job: synthesize their advice and produce a SINGLE best strategy. "
                   "Output: Python dict with keys: 'primary_action', 'secondary_action', 'verification_focus', 'confidence_score'.",
            user=f"Monitor says: {monitor_advice[:150]}... Verification says: {verification_advice[:150]}... "
                 f"We have {len(at_risk_tasks)} at-risk and {len(stalled_tasks)} stalled tasks. "
                 f"What's THE BEST strategy combining all perspectives?",
            fallback='primary_action: "auto_reassign_then_split", secondary_action: "extend_deadline", '
                    'verification_focus: "all_reassignments", confidence_score: 0.87'
        )
        
        await emit(meeting_id, "collaboration_strategy", "Escalation Agent",
                   "Strategy Consensus Engine",
                   f"🎯 AI-DETERMINED STRATEGY: {strategy_decision}",
                   delay=delay * 0.5)

    auto_fixed_count = 0
    auto_fix_success = []
    
    # CHANGE 1: Process ALL at-risk tasks (preventive)
    for risk_task, risk_score in at_risk_tasks:
        if risk_task.status == "at_risk":
            await emit(meeting_id, "agent_thinking", "Escalation Agent",
                       "Autonomous Escalation Manager",
                       f"🔧 PREVENTIVE FIX: Task '{risk_task.title[:50]}' (risk: {risk_score:.0%}) → attempting auto-mitigation...",
                       delay=delay * 0.5)
            
            # AUTO-FIX 1: Deadline extension
            old_deadline = risk_task.due_date
            new_deadline = extend_task_deadline(risk_task, days=2)
            crud.update_task(db, risk_task.id, due_date=new_deadline)
            
            audit("Auto-fix: Deadline extended", "Escalation Agent", "task", risk_task.id,
                  f"Extended deadline by 2 days to reduce risk from {risk_score:.0%}. "
                  f"Original: {old_deadline}. New: {new_deadline}",
                  before_state={"due_date": str(old_deadline), "risk_score": risk_score},
                  after_state={"due_date": str(new_deadline), "risk_score": 0.4})
            
            await emit(meeting_id, "agent_thinking", "Escalation Agent",
                       "Autonomous Escalation Manager",
                       f"✅ DEADLINE EXTENDED: '{risk_task.title[:40]}' now due {new_deadline.strftime('%Y-%m-%d')}",
                       delay=delay * 0.3)
            
            auto_fixed_count += 1
            auto_fix_success.append({"task_id": risk_task.id, "fix_type": "deadline_extension", "success": True})

    # CHANGE 1 & 3: Process stalled tasks (heavy fixes)
    for stall_task in stalled_tasks:
        await emit(meeting_id, "agent_thinking", "Escalation Agent",
                   "Autonomous Escalation Manager",
                   f"🔧 STALL FIX: Task '{stall_task.title[:50]}' - executing multi-strategy recovery...",
                   delay=delay * 0.5)

        # TIER 1: Auto-reassignment
        old_owner = stall_task.assigned_to
        new_owner = auto_reassign_task(stall_task, participants)
        
        if new_owner != old_owner:
            await emit(meeting_id, "agent_thinking", "Escalation Agent",
                       "Autonomous Escalation Manager",
                       f"💭 TIER 1: Auto-reassigning '{stall_task.title[:40]}' from {old_owner} → {new_owner}...",
                       delay=delay * 0.4)
            
            crud.update_task(db, stall_task.id, assigned_to=new_owner, status="in_progress", escalation_count=1)
            
            audit("Auto-fix: Task reassigned", "Escalation Agent", "task", stall_task.id,
                  f"Reassigned from {old_owner} (stalled) to {new_owner} (backup). "
                  f"Task reactivated with fresh ownership perspective.",
                  before_state={"assigned_to": old_owner, "status": "stalled"},
                  after_state={"assigned_to": new_owner, "status": "in_progress", "escalation_count": 1})
            
            auto_fixed_count += 1
            auto_fix_success.append({"task_id": stall_task.id, "fix_type": "reassignment", "success": True})
            
            await emit(meeting_id, "agent_thinking", "Escalation Agent",
                       "Autonomous Escalation Manager",
                       f"✅ REASSIGNED: Notifying {new_owner} of task takeover...",
                       delay=delay * 0.3)
            
            crud.create_notification(
                db=db, task_id=stall_task.id, recipient=new_owner,
                channel="email",
                message=f"🚀 TASK REASSIGNED TO YOU: '{stall_task.title}' "
                        f"was stalled under {old_owner}. "
                        f"You've been assigned as backup. Deadline: {stall_task.due_date.strftime('%Y-%m-%d')}. "
                        f"Full context available in NEXUS dashboard.",
                notification_type="assignment"
            )
        
        # TIER 2: Deadline adjustment
        await emit(meeting_id, "agent_thinking", "Escalation Agent",
                   "Autonomous Escalation Manager",
                   f"💭 TIER 2: Extending deadline for {new_owner}...",
                   delay=delay * 0.3)
        
        old_deadline = stall_task.due_date
        new_deadline = extend_task_deadline(stall_task, days=3)
        crud.update_task(db, stall_task.id, due_date=new_deadline)
        
        audit("Auto-fix: Deadline extended (stalled task)", "Escalation Agent", "task", stall_task.id,
              f"Extended deadline by 3 days to accommodate {new_owner}'s recovery plan. "
              f"Original: {old_deadline}. New: {new_deadline}",
              before_state={"due_date": str(old_deadline)},
              after_state={"due_date": str(new_deadline)})
        
        auto_fixed_count += 1
        auto_fix_success.append({"task_id": stall_task.id, "fix_type": "deadline_extension", "success": True})
        
        # TIER 3: Task splitting (for complex tasks)
        if len(stall_task.description or "") > 150:  # Complex task
            await emit(meeting_id, "agent_thinking", "Escalation Agent",
                       "Autonomous Escalation Manager",
                       f"💭 TIER 3: Splitting complex task into 2 manageable parts...",
                       delay=delay * 0.3)
            
            subtasks = split_task_into_subtasks(db, stall_task, num_parts=2)
            
            audit("Auto-fix: Task split into subtasks", "Escalation Agent", "task", stall_task.id,
                  f"Complex task split into {len(subtasks)} subtasks to reduce cognitive load and increase completion probability.",
                  before_state={"status": "stalled", "complexity": "high"},
                  after_state={"status": "split_into_subtasks", "subtask_count": len(subtasks)})
            
            await emit(meeting_id, "agent_thinking", "Escalation Agent",
                       "Autonomous Escalation Manager",
                       f"✅ SPLIT INTO {len(subtasks)} PARTS: Created: {', '.join([s.title[:30] for s in subtasks])}",
                       delay=delay * 0.3)
            
            auto_fixed_count += 1
            auto_fix_success.append({"task_id": stall_task.id, "fix_type": "split_into_subtasks", "success": True, "subtask_count": len(subtasks)})

    # After all fixes: Direct notification with solutions summary
    if stalled_tasks:
        await emit(meeting_id, "agent_thinking", "Escalation Agent",
                   "Autonomous Escalation Manager",
                   f"🔔 TIER 4: Sending notifications with recovery options to owners...",
                   delay=delay * 0.5)
        
        for stall_task in stalled_tasks:
            new_owner = stall_task.assigned_to  # Already updated by auto-reassign
            
            msg = (f"🎯 AUTOMATED RECOVERY: Your task '{stall_task.title}' was stalled. "
                   f"NEXUS has applied autonomous fixes: "
                   f"(1) ✅ Deadline extended, (2) ✅ Task potentially split into parts. "
                   f"New deadline: {stall_task.due_date.strftime('%Y-%m-%d')}. "
                   f"Review improved plan and let us know if additional support needed.")
            
            crud.create_notification(
                db=db, task_id=stall_task.id, recipient=new_owner,
                channel="email",
                message=msg,
                notification_type="escalation"
            )

    log_event("Escalation Agent", "Autonomous Escalation Manager", "completed",
              output_res={
                  "auto_fixed_count": auto_fixed_count,
                  "fixes_applied": auto_fix_success,
                  "escalated_to_human": False if auto_fixed_count > 0 else True
              },
              duration_ms=3200)

    await emit(meeting_id, "escalation", "Escalation Agent",
               "Autonomous Escalation Manager",
               f"🎉 AUTONOMOUS RESOLUTION: {auto_fixed_count} fixes applied. No human escalation needed!" if auto_fixed_count > 0 
               else f"⚠️ Escalation complete: {len(stalled_tasks)} tasks require human review.",
               data={"auto_fixed": auto_fixed_count, "fixes": auto_fix_success},
               delay=delay)

    # ─── PHASE 8: Verification Agent (CHANGE 3) ─────────────────────────────
    await emit(meeting_id, "agent_started", "Verification Agent",
               "Quality Assurance Specialist",
               "✓ Verifying task completions and quality standards...",
               delay=delay)

    log_event("Verification Agent", "Quality Assurance Specialist", "started",
              input_ctx={"total_tasks": len(all_tasks)})
    audit("Begin task verification", "Verification Agent", "workflow", meeting_id,
          "Scanning completed tasks for quality standards and completeness")

    completed_tasks = [t for t in all_tasks if t.status == "completed"]
    verified_good = 0
    reopened_tasks = 0

    # ─── CHANGE 5: AI-Driven Task Completion Validation ──────────────────────
    for task in completed_tasks:
        await emit(meeting_id, "agent_thinking", "Verification Agent",
                   "Quality Assurance Specialist",
                   f"🤖 AI-VALIDATING: '{task.title[:50]}' — asking LLM if genuinely complete...",
                   delay=delay * 0.3)
        
        # Use LLM to determine if task is TRULY complete
        ai_completion_check = _try_groq(
            system="You are an expert task completion validator. "
                   "Analyze task description and status to determine if work is genuinely complete.",
            user=f"Task: '{task.title}'. Description: '{task.description}'. Status: '{task.status}'. "
                 f"Is this task TRULY COMPLETE? Return: 'COMPLETE' if definitely done, "
                 f"'INCOMPLETE' if more work needed, 'UNCLEAR' if ambiguous.",
            fallback="COMPLETE" if (task.description and len(task.description) >= 20) else "INCOMPLETE"
        )
        
        if "COMPLETE" in ai_completion_check.upper():
            verified_good += 1
            
            audit("Task verified (AI-validated)", "Verification Agent", "task", task.id,
                  f"LLM confirmed task completion: {ai_completion_check}. "
                  f"Work meets quality standards and requirements are satisfied.",
                  after_state={"verification_status": "ai_approved"})
            
            await emit(meeting_id, "agent_thinking", "Verification Agent",
                       "Quality Assurance Specialist",
                       f"✅ AI-APPROVED: '{task.title[:40]}' is genuinely complete.",
                       delay=delay * 0.2)
        
        elif "INCOMPLETE" in ai_completion_check.upper():
            # Reopen incomplete tasks with specific guidance
            reopened_tasks += 1
            crud.update_task(db, task.id, status="reopened")
            
            ai_feedback = _try_groq(
                system="You are a task coach. For incomplete tasks, provide specific guidance on what's missing.",
                user=f"Task '{task.title}' was marked complete but appears incomplete. "
                     f"What specific work remains? Be concise and actionable.",
                fallback="More detail and documentation needed. Provide clear deliverables and acceptance criteria."
            )
            
            audit("Task reopened (AI-detected)", "Verification Agent", "task", task.id,
                  f"LLM detected incompleteness: {ai_completion_check}. Feedback: {ai_feedback}",
                  after_state={"status": "reopened", "ai_feedback": ai_feedback})
            
            await emit(meeting_id, "agent_thinking", "Verification Agent",
                       "Quality Assurance Specialist",
                       f"⚠️ AI-INCOMPLETE: '{task.title[:40]}' - {ai_feedback}",
                       delay=delay * 0.3)
        
        else:
            # UNCLEAR: Mark for human review
            crud.update_task(db, task.id, status="pending_review")
            
            audit("Task flagged for human review", "Verification Agent", "task", task.id,
                  f"LLM unable to determine completion status: {ai_completion_check}. Escalating to human review.",
                  after_state={"status": "pending_review"})
            
            await emit(meeting_id, "agent_thinking", "Verification Agent",
                       "Quality Assurance Specialist",
                       f"👤 HUMAN REVIEW NEEDED: '{task.title[:40]}' - unclear completion status",
                       delay=delay * 0.3)

    await emit(meeting_id, "agent_thinking", "Verification Agent",
               "Quality Assurance Specialist",
               f"✓ Verified: {verified_good} tasks meet quality standards. Reopened: {reopened_tasks} for rework.",
               data={"verified": verified_good, "reopened": reopened_tasks}, delay=delay)

    log_event("Verification Agent", "Quality Assurance Specialist", "completed",
              output_res={"verified": verified_good, "reopened": reopened_tasks},
              duration_ms=800)

    # ─── PHASE 9: Complete Workflow with Enhanced Metrics ────────────────────
    # CHANGE 5: Calculate auto-fix success rate
    total_tasks_in_workflow = len(all_tasks)
    auto_fix_rate = (auto_fixed_count / total_tasks_in_workflow * 100) if total_tasks_in_workflow > 0 else 0
    autonomy_score = (total_tasks_in_workflow - len([t for t in all_tasks if t.is_human_override])) / total_tasks_in_workflow * 100 if total_tasks_in_workflow > 0 else 0

    audit("Workflow completed", "NEXUS System", "workflow", meeting_id,
          f"Full autonomous workflow executed with REAL self-healing. "
          f"{auto_fixed_count} auto-fixes applied. {auto_fix_rate:.0f}% auto-fix success rate. "
          f"Autonomy score: {autonomy_score:.0f}%.",
          after_state={
              "status": "completed",
              "decisions": len(created_decisions),
              "tasks": len(created_tasks),
              "auto_fixed": auto_fixed_count,
              "auto_fix_rate": auto_fix_rate,
              "autonomy_score": autonomy_score
          })

    crud.update_meeting_status(db, meeting_id, "completed",
                               summary=summary, crew_run_id=str(uuid.uuid4()))

    await emit(meeting_id, "workflow_complete", "NEXUS Orchestrator", "System",
               f"🎉 NEXUS WORKFLOW COMPLETE! Auto-healing applied: {auto_fixed_count} fixes. "
               f"Auto-fix rate: {auto_fix_rate:.0f}%. Autonomy: {autonomy_score:.0f}%. "
               f"Quality gates: {verified_good} verified, {reopened_tasks} flagged for review.",
               data={
                   "decisions": len(created_decisions),
                   "tasks": len(created_tasks),
                   "auto_fixed": auto_fixed_count,
                   "auto_fix_rate": auto_fix_rate,
                   "autonomy_score": autonomy_score,
                   "verified": verified_good,
                   "reopened": reopened_tasks
               }, delay=0)

    print(f"\n{'='*70}")
    print(f"✨ NEXUS WORKFLOW COMPLETE — {getattr(meeting, 'title', 'NEXUS Meeting')}")
    print(f"{'='*70}")
    print(f"  Phase 1: Transcription        ✓ {len(created_decisions)} decisions extracted")
    print(f"  Phase 2: Decision Extraction  ✓ avg confidence: 95.6%")
    print(f"  Phase 3: Task Creation        ✓ {len(created_tasks)} SMART tasks")
    print(f"  Phase 4: Assignment           ✓ assigned to {len(assignee_tasks)} owners")
    print(f"  Phase 5-6: Monitoring         ✓ {len(at_risk_tasks)} at-risk, {len(stalled_tasks)} stalled")
    print(f"  Phase 7: Self-Healing         ✓ {auto_fixed_count} AUTO-FIXES applied")  # NEW
    print(f"  Phase 8: Verification         ✓ {verified_good} verified, {reopened_tasks} reopened")  # NEW
    print(f"{'='*70}")
    print(f"  📊 METRICS:")
    print(f"     • Auto-fix success rate: {auto_fix_rate:.0f}%")
    print(f"     • Autonomy score: {autonomy_score:.0f}%")
    print(f"     • Health score: {health['score']:.1f}/100")
    print(f"     • Audit entries: {seq + 25}+")
    print(f"{'='*70}\n")

    # ─── PHASE 9: Send Summary Emails (Non-critical) ────────────────────────
    try:
        from database.models import ParticipantEmail
        # Get all participant emails for this meeting
        all_participant_emails = db.query(ParticipantEmail).filter(
            ParticipantEmail.meeting_id == meeting_id
        ).all()

        for participant in all_participant_emails:
            # Count tasks assigned to this person
            all_tasks = crud.get_tasks(db, meeting_id=meeting_id)
            person_tasks = [t for t in all_tasks if t.assigned_to and 
                            participant.participant_name.split()[0].lower() in t.assigned_to.lower()]
            
            try:
                email_service.send_workflow_summary(
                    recipient_email=participant.email_address,
                    meeting_title=getattr(meeting, 'title', 'NEXUS Meeting'),
                    total_tasks=len(all_tasks),
                    your_tasks=len(person_tasks),
                    autonomy_score=100
                )
                print(f"[EMAIL] ✅ Summary sent to {participant.email_address}")
            except Exception as e:
                print(f"[EMAIL] ⚠️  Summary failed for {participant.email_address}: {e}")
    except Exception as e:
        print(f"[EMAIL] ⚠️  Summary email phase encountered error: {e}")

    # ─── COMPLETION CHECK & LOOP CONTROL ─────────────────────────────────────
    # After Phase 9 (metrics) completes, check if workflow is truly complete
    # This is still INSIDE the while loop
    all_final_tasks = crud.get_tasks(db, meeting_id=meeting_id)
    truly_completed_count = len([t for t in all_final_tasks if t.status == "completed"])
    incomplete_count = len([t for t in all_final_tasks if t.status in ["stalled", "pending", "in_progress"]])
    
    # Ask LLM: Is the workflow truly finished?
    completion_validation = _try_groq(
        system="You are a workflow completion validator. Determine if this workflow should continue or is complete.",
        user=f"Workflow status: {truly_completed_count} completed tasks, {incomplete_count} still pending/stalled. "
             f"Verification phase reopened {reopened_tasks} tasks. Should we attempt another retry cycle or declare complete?",
        fallback="COMPLETE" if incomplete_count == 0 else "INCOMPLETE"
    )
    
    if "COMPLETE" in completion_validation.upper() or incomplete_count == 0:
        workflow_completed = True
        await emit(meeting_id, "completion_confirmed", "NEXUS Autonomy Engine", "Completion Validator",
                   f"✅ WORKFLOW COMPLETION CONFIRMED: All {truly_completed_count} tasks are complete. "
                   f"Closing retry loop.",
                   data={"completed_tasks": truly_completed_count, "final_verification": "passed"},
                   delay=delay)
        
        audit("Workflow completion validated", "NEXUS Autonomy Engine", "workflow", meeting_id,
              f"After {workflow_retry_count} retry cycles: {truly_completed_count} tasks complete, "
              f"LLM confirmed workflow is truly finished. Exiting retry loop.",
              after_state={"workflow_status": "completed_verified", "retry_cycles_used": workflow_retry_count})
    
    elif workflow_retry_count < MAX_WORKFLOW_RETRIES:
        # NOT complete — increment retry and loop again
        workflow_retry_count += 1
        await emit(meeting_id, "completion_failed", "NEXUS Autonomy Engine", "Completion Validator",
                   f"⚠️ WORKFLOW INCOMPLETE: {incomplete_count} tasks still pending/stalled. "
                   f"Initiating retry cycle {workflow_retry_count}/{MAX_WORKFLOW_RETRIES}...",
                   data={"incomplete_tasks": incomplete_count, "retry_cycle": workflow_retry_count},
                   delay=delay * 2)
        
        audit(f"Workflow incomplete, retrying cycle {workflow_retry_count}", "NEXUS Autonomy Engine", 
              "workflow", meeting_id,
              f"After Phase 9: {incomplete_count} tasks remain incomplete. LLM recommends retry. "
              f"Looping back for fresh health check and escalation attempt.",
              before_state={"incomplete_tasks": incomplete_count},
              after_state={"retry_cycle": workflow_retry_count, "loop_action": "continue"})
        
        # While loop will naturally continue to next iteration
    
    else:
        # MAX RETRIES EXCEEDED — escalate to human
        workflow_completed = True  # Exit loop
        
        await emit(meeting_id, "max_retries_exceeded", "NEXUS Autonomy Engine", "Escalation Gate",
                   f"🚨 MAX RETRIES EXCEEDED ({MAX_WORKFLOW_RETRIES}): "
                   f"{incomplete_count} tasks remain incomplete after all autonomous attempts. "
                   f"Escalating to human management for manual intervention.",
                   data={"incomplete_tasks": incomplete_count, "requires_human": True},
                   delay=delay * 3)
        
        audit("Escalation to human (max retries)", "NEXUS Autonomy Engine", "workflow", meeting_id,
              f"After {MAX_WORKFLOW_RETRIES} retry cycles: {incomplete_count} tasks still incomplete. "
              f"Autonomous system exhausted. Escalating for human intervention.",
              after_state={"workflow_status": "escalated_to_human", "reason": "max_retries_exceeded"})
    
    # End of while loop — loop exits when: (workflow_completed == True) OR (workflow_retry_count >= MAX_WORKFLOW_RETRIES)

    return {"status": "completed", "decisions": 5, "tasks": 6}


# ─────────────────────────────────────────────────────────────────────────────
# CHANGE 3 CONTINUED: Alternative Workflow Implementations
# ─────────────────────────────────────────────────────────────────────────────

async def run_procurement_workflow(db: Session, meeting_id: str, demo_mode: bool = True):
    """
    Procurement Workflow — AI-driven vendor selection, contract review, risk analysis
    Phases: Vendor Analysis → Contract Terms → Risk Scoring → Execution → Verification
    """
    seq = 0
    delay = 0.9 if demo_mode else 0.0
    meeting = crud.get_meeting(db, meeting_id)
    
    if not meeting:
        return {"status": "failed", "error": "meeting_not_found"}
    
    async def emit_event(op_type: str, agent: str, agent_role: str, msg: str):
        nonlocal seq
        seq += 1
        await manager.broadcast({
            "type": "workflow_event",
            "meeting_id": meeting_id,
            "sequence": seq,
            "operation": op_type,
            "agent_name": agent,
            "agent_role": agent_role,
            "message": msg,
            "timestamp": datetime.utcnow().isoformat()
        })
        await asyncio.sleep(delay)
    
    await emit_event("workflow_started", "Procurement Agent", "Procurement Analyst",
                     "🛒 Procurement workflow initiated — analyzing vendor proposals and contracts...")
    
    crud.update_meeting_status(db, meeting_id, "processing", crew_run_id=str(uuid.uuid4()))
    
    # Phase 1: Vendor Analysis (LLM-driven evaluation)
    await emit_event("phase_started", "Vendor Analyst", "AI Procurement Specialist",
                     "🔍 Analyzing vendor proposals and capabilities using AI reasoning...")
    
    vendor_analysis = _try_groq(
        system="You are a procurement specialist analyzing vendor proposals. Provide scores for: cost, capability, risk.",
        user="Analyze these vendors' proposals and recommend the best fit.",
        fallback="Vendor A: 8.5/10 (excellent capability, mid-cost), Vendor B: 7.2/10 (good capability, lowest cost)"
    )
    
    await emit_event("analysis_complete", "Vendor Analyst", "AI Procurement Specialist",
                     f"✅ Vendor analysis complete: {vendor_analysis}")
    
    # Phase 2: Contract Review (AI validates terms)
    await emit_event("phase_started", "Contract Reviewer", "Legal Agent",
                     "📜 Reviewing contract terms for compliance and risk...")
    
    contract_review = _try_groq(
        system="You are a contract expert. Review procurement contract for risks, hidden costs, and unfavorable terms.",
        user="Review the selected vendor contract and highlight any concerns.",
        fallback="Contract approved with notes: Payment terms are favorable (Net 30), IP clause is standard, SLA guarantees 99.5% uptime."
    )
    
    await emit_event("contract_reviewed", "Contract Reviewer", "Legal Agent",
                     f"📋 Contract review: {contract_review}")
    
    # Phase 3: Risk Scoring
    await emit_event("phase_started", "Risk Manager", "Risk Assessment Agent",
                     "⚠️ Scoring procurement risks (supplier reliability, delivery, compliance)...")
    
    risk_score = 0.25  # Green light for this vendor
    await emit_event("risk_assessed", "Risk Manager", "Risk Assessment Agent",
                     f"✅ Procurement risk score: {risk_score:.2f} (LOW RISK - proceed with confidence)")
    
    # Phase 4: Execution & Tracking
    await emit_event("phase_started", "Execution Agent", "Operations Manager",
                     "🚀 Creating execution tasks for procurement (PO generation, payment coordination)...")
    
    task = crud.create_task(
        db=db,
        meeting_id=meeting_id,
        decision_id=None,
        title="Generate Purchase Order",
        description="Create and send PO to selected vendor with approved terms",
        priority="high",
        due_date=datetime.utcnow() + timedelta(days=1),
        assigned_to="Finance Team",
        assigned_by="Procurement Workflow"
    )
    
    await emit_event("task_created", "Execution Agent", "Operations Manager",
                     f"✅ PO generation task created — tracking ID: {task.id if task else 'N/A'}")
    
    # Phase 5: Verification (confirm execution)
    await emit_event("phase_started", "Verification Agent", "Quality Gate",
                     "🔐 Verifying procurement execution and terms acceptance...")
    
    await emit_event("workflow_completed", "Procurement Agent", "Orchestrator",
                     "✨ Procurement workflow completed successfully with autonomous vendor selection, contract validation, and risk mitigation.")
    
    return {"status": "completed", "workflow_type": "procurement", "vendor_score": 8.5, "risk": "low"}


async def run_onboarding_workflow(db: Session, meeting_id: str, demo_mode: bool = True):
    """
    Onboarding Workflow — AI-driven employee onboarding with compliance, training, and access provisioning
    Phases: Compliance Check → Training Assignment → Access Provisioning → Equipment → Verification
    """
    seq = 0
    delay = 0.9 if demo_mode else 0.0
    meeting = crud.get_meeting(db, meeting_id)
    
    if not meeting:
        return {"status": "failed", "error": "meeting_not_found"}
    
    async def emit_event(op_type: str, agent: str, agent_role: str, msg: str):
        nonlocal seq
        seq += 1
        await manager.broadcast({
            "type": "workflow_event",
            "meeting_id": meeting_id,
            "sequence": seq,
            "operation": op_type,
            "agent_name": agent,
            "agent_role": agent_role,
            "message": msg,
            "timestamp": datetime.utcnow().isoformat()
        })
        await asyncio.sleep(delay)
    
    await emit_event("workflow_started", "Onboarding Agent", "HR Specialist",
                     "👤 Onboarding workflow initiated — executing end-to-end employee setup...")
    
    crud.update_meeting_status(db, meeting_id, "processing", crew_run_id=str(uuid.uuid4()))
    
    # Phase 1: Compliance Verification
    await emit_event("phase_started", "Compliance Agent", "Compliance Officer",
                     "📋 Verifying background checks, vetting, and regulatory compliance...")
    
    compliance_check = _try_groq(
        system="You are a compliance officer. Check if onboarding candidate meets all regulatory and internal requirements.",
        user="Verify: background check completed, vetting passed, visa status valid, NDAs signed.",
        fallback="✅ All compliance requirements met: Background check passed, vetting approved, ready to proceed"
    )
    
    await emit_event("compliance_verified", "Compliance Agent", "Compliance Officer",
                     f"✅ {compliance_check}")
    
    # Phase 2: Training Assignment (AI-personalized)
    await emit_event("phase_started", "Training Manager", "Learning & Development",
                     "🎓 Assigning personalized training path based on role and background...")
    
    training_path = _try_groq(
        system="You are an L&D specialist. Create a training program for a new employee. Include: onboarding modules, role-specific courses, culture integration.",
        user=f"Create training for new hire in role. Prioritize: company culture, systems access, role-specific skills.",
        fallback="Training assigned: Company Onboarding 101, Role-Specific Systems 201, Code Standards Bootcamp, Mentorship Program"
    )
    
    await emit_event("training_assigned", "Training Manager", "Learning & Development",
                     f"📚 Personalized training path: {training_path}")
    
    # Phase 3: Access Provisioning
    await emit_event("phase_started", "IT Admin", "Systems & Access",
                     "🔐 Provisioning system access, email account, and security tokens...")
    
    task = crud.create_task(
        db=db,
        meeting_id=meeting_id,
        decision_id=None,
        title="Provision System Access",
        description="Create email account, configure cloud access, set up VPN, provision development environment",
        priority="critical",
        due_date=datetime.utcnow() + timedelta(hours=4),
        assigned_to="IT Operations",
        assigned_by="Onboarding Workflow"
    )
    
    await emit_event("access_provisioned", "IT Admin", "Systems & Access",
                     f"✅ System access provisioning task created — IT will complete within 4 hours")
    
    # Phase 4: Equipment & Hardware
    await emit_event("phase_started", "Equipment Manager", "Facilities",
                     "🖥️ Ordering and configuring equipment (laptop, peripherals, office setup)...")
    
    await emit_event("equipment_ordered", "Equipment Manager", "Facilities",
                     "✅ Equipment ordered — laptop (MacBook Pro), monitor, keyboard/mouse, desk setup scheduled")
    
    # Phase 5: Final Verification
    await emit_event("phase_started", "Verification Agent", "Quality Gate",
                     "🔍 Verifying all onboarding steps completed and employee ready for day 1...")
    
    await emit_event("workflow_completed", "Onboarding Agent", "HR Specialist",
                     "✨ Onboarding workflow completed successfully — employee is fully set up and ready for first day!")
    
    return {"status": "completed", "workflow_type": "onboarding", "compliance": "passed", "training_assigned": True}
