"""
TaskTool — CrewAI custom tool for managing tasks in the database
"""
import json
from datetime import datetime
from typing import Any, Optional
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class TaskInput(BaseModel):
    operation: str = Field(description="One of: create | update_status | assign | escalate | complete | query")
    task_data: str = Field(description="JSON string containing task fields relevant to operation")


class TaskTool(BaseTool):
    name: str = "manage_task"
    description: str = (
        "Create, update, or query tasks in the NEXUS database. "
        "Operations: create | update_status | assign | escalate | complete | query"
    )
    args_schema: type[BaseModel] = TaskInput

    db_session: Any = None
    meeting_id_ctx: str = ""

    def _run(self, operation: str, task_data: str) -> str:
        try:
            data = json.loads(task_data) if isinstance(task_data, str) else task_data
        except Exception:
            data = {}

        if not self.db_session:
            return json.dumps({"status": "error", "message": "No DB session"})

        from database import crud

        try:
            if operation == "create":
                due_date = None
                if data.get("due_date"):
                    try:
                        due_date = datetime.fromisoformat(data["due_date"])
                    except Exception:
                        pass
                task = crud.create_task(
                    db=self.db_session,
                    meeting_id=data.get("meeting_id", self.meeting_id_ctx),
                    title=data.get("title", "Untitled Task"),
                    description=data.get("description"),
                    decision_id=data.get("decision_id"),
                    assigned_to=data.get("assigned_to"),
                    priority=data.get("priority", "medium"),
                    due_date=due_date,
                    assigned_by=data.get("assigned_by", "Task Creator Agent"),
                    assignment_rationale=data.get("assignment_rationale"),
                    context_quote=data.get("context_quote")
                )
                return json.dumps({
                    "status": "created",
                    "task_id": task.id,
                    "title": task.title,
                    "priority": task.priority
                })

            elif operation == "update_status":
                task = crud.update_task(
                    db=self.db_session,
                    task_id=data.get("task_id"),
                    status=data.get("status")
                )
                return json.dumps({"status": "updated", "task_id": data.get("task_id")})

            elif operation == "assign":
                task = crud.update_task(
                    db=self.db_session,
                    task_id=data.get("task_id"),
                    assigned_to=data.get("assigned_to"),
                    assignment_rationale=data.get("rationale"),
                    status="in_progress"
                )
                return json.dumps({
                    "status": "assigned",
                    "task_id": data.get("task_id"),
                    "assigned_to": data.get("assigned_to")
                })

            elif operation == "escalate":
                task = crud.escalate_task(self.db_session, data.get("task_id"))
                return json.dumps({
                    "status": "escalated",
                    "task_id": data.get("task_id"),
                    "escalation_count": task.escalation_count if task else 0
                })

            elif operation == "complete":
                task = crud.complete_task(self.db_session, data.get("task_id"), False)
                return json.dumps({"status": "completed", "task_id": data.get("task_id")})

            elif operation == "query":
                tasks = crud.get_tasks(
                    db=self.db_session,
                    meeting_id=data.get("meeting_id", self.meeting_id_ctx)
                )
                return json.dumps({
                    "status": "ok",
                    "tasks": [{"id": t.id, "title": t.title, "status": t.status,
                                "assigned_to": t.assigned_to} for t in tasks]
                })

            else:
                return json.dumps({"status": "error", "message": f"Unknown operation: {operation}"})

        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
