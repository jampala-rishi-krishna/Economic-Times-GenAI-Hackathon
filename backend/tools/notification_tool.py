"""
NotificationTool — Simulated notification sender (email/slack/in_app)
"""
import json
from typing import Any, Optional
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from datetime import datetime
from services.email_service import email_service


class NotificationInput(BaseModel):
    recipient: str = Field(description="Name or email of the recipient")
    channel: str = Field(description="One of: email | slack | in_app")
    message: str = Field(description="Notification message content")
    notification_type: str = Field(description="One of: assignment | reminder | escalation | completion")
    task_id: str = Field(description="ID of the associated task")


class NotificationTool(BaseTool):
    name: str = "send_notification"
    description: str = (
        "Send a simulated notification via email/slack/in_app. "
        "Logs the notification to DB. Returns delivery confirmation."
    )
    args_schema: type[BaseModel] = NotificationInput

    db_session: Any = None

    def _run(self, recipient: str, channel: str, message: str,
             notification_type: str, task_id: str) -> str:
        import uuid
        from database.crud import create_notification, get_participant_email, get_task, get_meeting

        notification_id = "pending"
        email_sent = False
        email_sent_at = None
        email_error = None

        # Check for real email mapping if channel is email
        if channel == "email" and self.db_session:
            try:
                task = get_task(self.db_session, task_id)
                if task:
                    meeting_id = task.meeting_id
                    real_email = get_participant_email(self.db_session, meeting_id, recipient)
                    
                    if real_email:
                        meeting = get_meeting(self.db_session, meeting_id)
                        meeting_title = meeting.title if meeting else "NEXUS Project"
                        
                        try:
                            if notification_type == "assignment":
                                email_sent = email_service.send_task_assignment(
                                    recipient_email=real_email,
                                    recipient_name=recipient,
                                    task_title=task.title,
                                    task_description=task.description or "No description provided",
                                    priority=task.priority,
                                    due_date=task.due_date.strftime("%Y-%m-%d %H:%M") if task.due_date else "TBD",
                                    assigned_by="NEXUS AI Agent",
                                    meeting_title=meeting_title
                                )
                            elif notification_type == "escalation":
                                email_sent = email_service.send_escalation_alert(
                                    recipient_email=real_email,
                                    recipient_name=recipient,
                                    task_title=task.title,
                                    escalation_reason=message,
                                    attempts_made=task.escalation_count or 1
                                )
                            
                            if email_sent:
                                email_sent_at = datetime.utcnow()
                            else:
                                email_error = "SMTP failure or service disabled"
                        except Exception as e:
                            print(f"[EMAIL] NotificationTool failed to send to {recipient}: {e}")
                            email_error = str(e)
                            email_sent = False
            except Exception as e:
                print(f"[ERROR] NotificationTool internal fault: {e}")
                email_error = str(e)

        # Log to DB
        try:
            if self.db_session:
                notif = create_notification(
                    db=self.db_session,
                    task_id=task_id,
                    recipient=recipient,
                    channel=channel,
                    message=message,
                    notification_type=notification_type,
                    email_sent=email_sent,
                    email_sent_at=email_sent_at,
                    email_error=email_error
                )
                notification_id = notif.id
        except Exception as e:
            print(f"[WARN] Could not persist notification: {e}")

        return json.dumps({
            "status": "sent" if email_sent else "logged",
            "notification_id": notification_id,
            "recipient": recipient,
            "channel": channel,
            "email_sent": email_sent,
            "simulated": not email_sent
        })
