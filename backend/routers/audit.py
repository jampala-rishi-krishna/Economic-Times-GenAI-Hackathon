"""
Audit Trail API Router
"""
import hashlib
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from database import crud

router = APIRouter(prefix="/api/audit", tags=["audit"])


def get_db():
    from main import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/{meeting_id}")
async def get_audit_trail(
    meeting_id: str,
    skip: int = 0,
    limit: int = 500,
    db: Session = Depends(get_db)
):
    logs = crud.get_audit_logs(db, meeting_id=meeting_id, skip=skip, limit=limit)
    result = []
    for log in logs:
        raw = f"{log.actor}{log.action}{log.timestamp.isoformat()}"
        computed = hashlib.sha256(raw.encode()).hexdigest()
        checksum_valid = log.checksum == computed
        result.append({
            "id": log.id,
            "meeting_id": log.meeting_id,
            "action": log.action,
            "actor": log.actor,
            "target_type": log.target_type,
            "target_id": log.target_id,
            "before_state": log.before_state,
            "after_state": log.after_state,
            "decision_rationale": log.decision_rationale,
            "timestamp": log.timestamp.isoformat(),
            "is_human_override": log.is_human_override,
            "checksum": log.checksum,
            "checksum_valid": checksum_valid
        })
    return result


@router.get("")
async def get_all_audit(
    skip: int = 0, limit: int = 200, db: Session = Depends(get_db)
):
    logs = crud.get_audit_logs(db, skip=skip, limit=limit)
    result = []
    for log in logs:
        raw = f"{log.actor}{log.action}{log.timestamp.isoformat()}"
        computed = hashlib.sha256(raw.encode()).hexdigest()
        result.append({
            "id": log.id,
            "meeting_id": log.meeting_id,
            "action": log.action,
            "actor": log.actor,
            "target_type": log.target_type,
            "target_id": log.target_id,
            "before_state": log.before_state,
            "after_state": log.after_state,
            "decision_rationale": log.decision_rationale,
            "timestamp": log.timestamp.isoformat(),
            "is_human_override": log.is_human_override,
            "checksum": log.checksum,
            "checksum_valid": log.checksum == computed
        })
    return result


@router.get("/verify/{log_id}")
async def verify_audit_entry(log_id: str, db: Session = Depends(get_db)):
    result = crud.verify_audit_log(db, log_id)
    return result


@router.post("/tamper/{log_id}")
async def simulate_tamper(log_id: str, db: Session = Depends(get_db)):
    """Demo: Tamper with an audit entry to demonstrate integrity detection."""
    from database.models import AuditLog
    log = db.query(AuditLog).filter(AuditLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")

    original_action = log.action
    log.action = log.action + " [TAMPERED]"
    db.commit()

    raw = f"{log.actor}{log.action}{log.timestamp.isoformat()}"
    computed = hashlib.sha256(raw.encode()).hexdigest()

    return {
        "tampered": True,
        "log_id": log_id,
        "original_action": original_action,
        "tampered_action": log.action,
        "stored_checksum": log.checksum,
        "computed_checksum": computed,
        "integrity_violated": log.checksum != computed
    }
