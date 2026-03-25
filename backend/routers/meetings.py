"""
Meetings API Router
"""
from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from database import crud

router = APIRouter(prefix="/api/meetings", tags=["meetings"])


def get_db():
    from main import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("")
async def upload_meeting(
    title: str = Form(...),
    raw_transcript: str = Form(...),
    participants: str = Form("[]"),
    duration_minutes: int = Form(0),
    db: Session = Depends(get_db)
):
    try:
        parts = json.loads(participants)
    except Exception:
        parts = [p.strip() for p in participants.split(",") if p.strip()]

    meeting = crud.create_meeting(
        db=db, title=title, raw_transcript=raw_transcript,
        participants=parts, duration_minutes=duration_minutes
    )
    return meeting


@router.get("")
async def list_meetings(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return crud.get_meetings(db, skip=skip, limit=limit)


@router.get("/{meeting_id}", response_model=dict)
async def get_meeting_detail(meeting_id: str, db: Session = Depends(get_db)):
    meeting = crud.get_meeting(db, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    decisions = crud.get_decisions_for_meeting(db, meeting_id)
    tasks = crud.get_tasks(db, meeting_id=meeting_id)

    return {
        "meeting": {
            "id": meeting.id,
            "title": meeting.title,
            "raw_transcript": meeting.raw_transcript,
            "uploaded_at": meeting.uploaded_at.isoformat(),
            "status": meeting.status,
            "participants": meeting.participants,
            "duration_minutes": meeting.duration_minutes,
            "crew_run_id": meeting.crew_run_id,
            "summary": meeting.summary
        },
        "decisions": [
            {
                "id": d.id, "decision_text": d.decision_text,
                "context": d.context, "confidence_score": d.confidence_score,
                "extracted_by": d.extracted_by,
                "extracted_at": d.extracted_at.isoformat()
            } for d in decisions
        ],
        "tasks": [
            {
                "id": t.id, "title": t.title, "description": t.description,
                "assigned_to": t.assigned_to, "priority": t.priority,
                "status": t.status, "due_date": t.due_date.isoformat() if t.due_date else None,
                "escalation_count": t.escalation_count,
                "assignment_rationale": t.assignment_rationale,
                "context_quote": t.context_quote,
                "is_human_override": t.is_human_override,
                "decision_id": t.decision_id
            } for t in tasks
        ]
    }


@router.delete("/{meeting_id}")
async def delete_meeting(meeting_id: str, db: Session = Depends(get_db)):
    success = crud.delete_meeting(db, meeting_id)
    if not success:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return {"status": "deleted", "meeting_id": meeting_id}


@router.post("/participants/emails")
async def save_emails(data: dict, db: Session = Depends(get_db)):
    meeting_id = data.get("meeting_id")
    participants = data.get("participants", [])
    if not meeting_id:
        raise HTTPException(status_code=400, detail="meeting_id is required")
    
    crud.save_participant_emails(db, meeting_id, participants)
    return {"status": "success", "count": len(participants)}


@router.get("/{meeting_id}/notifications")
async def get_meeting_notifications(meeting_id: str, db: Session = Depends(get_db)):
    return crud.get_notifications_for_meeting(db, meeting_id)
