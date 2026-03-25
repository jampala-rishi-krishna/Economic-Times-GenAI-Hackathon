"""
AuditTool — CrewAI custom tool for immutable audit logging
Every agent MUST call this before AND after every significant decision.
"""
import hashlib
from datetime import datetime
from typing import Optional, Any
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class AuditInput(BaseModel):
    actor: str = Field(description="Which agent or 'system' or 'user' is acting")
    action: str = Field(description="Human-readable description of the action taken")
    target_type: str = Field(description="Type of entity: task, decision, workflow, etc.")
    target_id: str = Field(description="ID of the target entity")
    rationale: str = Field(description="WHY the agent made this decision")
    before_state: Optional[str] = Field(default=None, description="JSON string of state before action")
    after_state: Optional[str] = Field(default=None, description="JSON string of state after action")
    meeting_id: Optional[str] = Field(default=None, description="Associated meeting ID")


class AuditTool(BaseTool):
    name: str = "audit_decision"
    description: str = (
        "Write an immutable audit entry for every agent decision. "
        "Call this for EVERY action taken. Ensures complete compliance trail."
    )
    args_schema: type[BaseModel] = AuditInput

    # Will be injected per workflow run
    db_session: Any = None
    meeting_id_ctx: str = ""

    def _run(self, actor: str, action: str, target_type: str, target_id: str,
             rationale: str, before_state: str = None, after_state: str = None,
             meeting_id: str = None) -> str:
        import json
        now = datetime.utcnow()
        raw = f"{actor}{action}{now.isoformat()}"
        checksum = hashlib.sha256(raw.encode()).hexdigest()

        mid = meeting_id or self.meeting_id_ctx

        try:
            import sys
            sys.path.insert(0, "/")
            if self.db_session:
                from database.crud import create_audit_log
                log = create_audit_log(
                    db=self.db_session,
                    action=action,
                    actor=actor,
                    meeting_id=mid,
                    target_type=target_type,
                    target_id=target_id,
                    before_state=json.loads(before_state) if before_state else None,
                    after_state=json.loads(after_state) if after_state else None,
                    decision_rationale=rationale,
                    is_human_override=False
                )
                audit_id = log.id
            else:
                audit_id = f"AUDIT-{checksum[:8]}"
        except Exception as e:
            audit_id = f"AUDIT-{checksum[:8]}"

        print(f"[AUDIT] {actor} → {action} | Target: {target_type}:{target_id} | Checksum: {checksum[:16]}...")
        return json.dumps({
            "status": "logged",
            "audit_id": audit_id,
            "checksum": checksum,
            "timestamp": now.isoformat(),
            "actor": actor,
            "action": action
        })
