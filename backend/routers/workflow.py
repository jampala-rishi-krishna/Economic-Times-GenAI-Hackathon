"""
Workflow API Router — starts and monitors CrewAI workflow runs
"""
import asyncio
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional

from database import crud

router = APIRouter(prefix="/api/workflow", tags=["workflow"])


def get_db():
    from main import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/start/{meeting_id}")
async def start_workflow(
    meeting_id: str,
    background_tasks: BackgroundTasks,
    demo_mode: bool = True,
    db: Session = Depends(get_db)
):
    meeting = crud.get_meeting(db, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if meeting.status == "processing":
        raise HTTPException(status_code=409, detail="Workflow already running")

    crud.update_meeting_status(db, meeting_id, "processing")

    async def run_workflow_bg():
        from main import SessionLocal
        bg_db = SessionLocal()
        try:
            from crews.flow import run_meeting_workflow
            # Workflow will handle setting status to "completed" when successful
            await run_meeting_workflow(bg_db, meeting_id, demo_mode=demo_mode)
        except Exception as e:
            # Only mark as failed for critical/unhandled exceptions
            print(f"[ERROR] Critical workflow error: {e}")
            crud.update_meeting_status(bg_db, meeting_id, "failed")
            from database.crud import create_audit_log
            create_audit_log(
                db=bg_db, action=f"Workflow error: {str(e)[:100]}",
                actor="NEXUS System", meeting_id=meeting_id,
                target_type="workflow", target_id=meeting_id,
                decision_rationale="Critical error in workflow pipeline"
            )
        finally:
            bg_db.close()

    background_tasks.add_task(run_workflow_bg)

    return {
        "status": "started",
        "meeting_id": meeting_id,
        "message": "CrewAI workflow initiated. Connect to WebSocket for live updates.",
        "websocket_url": f"/ws/workflow/{meeting_id}"
    }


@router.get("/status/{meeting_id}")
async def get_workflow_status(meeting_id: str, db: Session = Depends(get_db)):
    meeting = crud.get_meeting(db, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    tasks = crud.get_tasks(db, meeting_id=meeting_id)
    events = crud.get_agent_events(db, meeting_id=meeting_id)

    task_breakdown = {}
    for t in tasks:
        task_breakdown[t.status] = task_breakdown.get(t.status, 0) + 1

    return {
        "meeting_id": meeting_id,
        "status": meeting.status,
        "crew_run_id": meeting.crew_run_id,
        "total_tasks": len(tasks),
        "task_breakdown": task_breakdown,
        "agent_events": len(events),
        "summary": meeting.summary
    }


@router.get("/agents/events/{meeting_id}")
async def get_agent_events(meeting_id: str, db: Session = Depends(get_db)):
    events = crud.get_agent_events(db, meeting_id)
    return [
        {
            "id": e.id, "agent_name": e.agent_name, "agent_role": e.agent_role,
            "event_type": e.event_type, "input_context": e.input_context,
            "output_result": e.output_result, "tool_used": e.tool_used,
            "duration_ms": e.duration_ms,
            "timestamp": e.timestamp.isoformat(),
            "sequence_number": e.sequence_number
        } for e in events
    ]


@router.get("/dashboard/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    stats = crud.get_dashboard_stats(db)
    return stats
