"""
WebSocketTool — Broadcast live events to the frontend dashboard
"""
import json
import asyncio
from typing import Any, Optional
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class WebSocketInput(BaseModel):
    event_type: str = Field(description="Type of event: agent_started|agent_thinking|tool_call|decision_made|task_created|task_assigned|escalation|workflow_complete|error")
    agent_name: str = Field(description="Name of the agent sending the event")
    agent_role: str = Field(description="Role/title of the agent")
    message: str = Field(description="Human-readable description of what happened")
    data: Optional[str] = Field(default=None, description="JSON string of structured payload")


class WebSocketTool(BaseTool):
    name: str = "broadcast_event"
    description: str = (
        "Broadcast a live event to the frontend dashboard. "
        "Use after every significant agent action for real-time visibility."
    )
    args_schema: type[BaseModel] = WebSocketInput

    meeting_id_ctx: str = ""
    loop: Any = None

    def _run(self, event_type: str, agent_name: str, agent_role: str,
             message: str, data: str = None) -> str:
        from websocket_manager import manager
        import uuid
        from datetime import datetime

        payload = {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "meeting_id": self.meeting_id_ctx,
            "event_type": event_type,
            "agent_name": agent_name,
            "agent_role": agent_role,
            "message": message,
            "data": json.loads(data) if data else {}
        }

        print(f"[WS BROADCAST] {event_type} | {agent_name}: {message}")

        # Try to broadcast via asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(manager.send_to_meeting(self.meeting_id_ctx, payload))
            else:
                loop.run_until_complete(manager.send_to_meeting(self.meeting_id_ctx, payload))
        except RuntimeError:
            try:
                new_loop = asyncio.new_event_loop()
                new_loop.run_until_complete(manager.send_to_meeting(self.meeting_id_ctx, payload))
                new_loop.close()
            except Exception:
                pass
        except Exception as e:
            print(f"[WS] Could not broadcast: {e}")

        return json.dumps({"status": "broadcast", "event_id": payload["event_id"]})
