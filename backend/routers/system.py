"""
System Maintenance API Router
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.models import Meeting, Decision, Task, AgentEvent, AuditLog, Notification
from main import get_db

router = APIRouter(prefix="/api/system", tags=["system"])

@router.post("/clear")
async def clear_system_data(db: Session = Depends(get_db)):
    """Deletes all data from the database for a fresh start."""
    try:
        # Delete in order to respect any potential foreign key constraints (though SQLite is lenient)
        db.query(Notification).delete()
        db.query(AgentEvent).delete()
        db.query(AuditLog).delete()
        db.query(Task).delete()
        db.query(Decision).delete()
        db.query(Meeting).delete()
        db.commit()
        return {"status": "success", "message": "All data cleared successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to clear data: {str(e)}")
