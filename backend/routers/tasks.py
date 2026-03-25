"""
Tasks API Router
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from database import crud

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


def get_db():
    from main import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("")
async def list_tasks(
    meeting_id: Optional[str] = None,
    status: Optional[str] = None,
    assignee: Optional[str] = None,
    skip: int = 0,
    limit: int = 200,
    db: Session = Depends(get_db)
):
    tasks = crud.get_tasks(db, meeting_id=meeting_id, status=status,
                           assignee=assignee, skip=skip, limit=limit)
    return [
        {
            "id": t.id, "meeting_id": t.meeting_id, "decision_id": t.decision_id,
            "title": t.title, "description": t.description,
            "assigned_to": t.assigned_to, "assigned_by": t.assigned_by,
            "priority": t.priority, "status": t.status,
            "due_date": t.due_date.isoformat() if t.due_date else None,
            "created_at": t.created_at.isoformat(),
            "updated_at": t.updated_at.isoformat(),
            "escalation_count": t.escalation_count,
            "stall_detected_at": t.stall_detected_at.isoformat() if t.stall_detected_at else None,
            "completed_at": t.completed_at.isoformat() if t.completed_at else None,
            "assignment_rationale": t.assignment_rationale,
            "context_quote": t.context_quote,
            "is_human_override": t.is_human_override
        } for t in tasks
    ]


@router.put("/{task_id}")
async def update_task(task_id: str, body: dict, db: Session = Depends(get_db)):
    """Human override — update any task field."""
    task = crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    before_state = {
        "status": task.status, "assigned_to": task.assigned_to,
        "priority": task.priority
    }

    updated = crud.update_task(
        db, task_id,
        **{k: v for k, v in body.items() if v is not None}
    )
    updated.is_human_override = True
    db.commit()

    # Write human override audit entry
    crud.create_audit_log(
        db=db, action=f"Human override: task updated",
        actor="Human User", meeting_id=task.meeting_id,
        target_type="task", target_id=task_id,
        before_state=before_state,
        after_state={"status": updated.status, "assigned_to": updated.assigned_to},
        decision_rationale="Manual human override via NEXUS dashboard",
        is_human_override=True
    )

    return {
        "id": updated.id, "title": updated.title,
        "status": updated.status, "assigned_to": updated.assigned_to,
        "is_human_override": True
    }


@router.post("/{task_id}/complete")
async def complete_task(task_id: str, db: Session = Depends(get_db)):
    task = crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    updated = crud.complete_task(db, task_id, is_human_override=True)
    crud.create_audit_log(
        db=db, action="Task marked complete by human",
        actor="Human User", meeting_id=task.meeting_id,
        target_type="task", target_id=task_id,
        before_state={"status": task.status},
        after_state={"status": "completed"},
        decision_rationale="Human manually marked task as complete via NEXUS dashboard",
        is_human_override=True
    )

    return {"status": "completed", "task_id": task_id}


@router.post("/{task_id}/escalate")
async def escalate_task(task_id: str, db: Session = Depends(get_db)):
    task = crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    updated = crud.escalate_task(db, task_id)
    crud.create_audit_log(
        db=db, action="Task manually escalated by human",
        actor="Human User", meeting_id=task.meeting_id,
        target_type="task", target_id=task_id,
        before_state={"status": task.status, "escalation_count": task.escalation_count},
        after_state={"status": "escalated", "escalation_count": updated.escalation_count},
        decision_rationale="Human triggered manual escalation via NEXUS dashboard",
        is_human_override=True
    )

    return {"status": "escalated", "task_id": task_id,
            "escalation_count": updated.escalation_count}
