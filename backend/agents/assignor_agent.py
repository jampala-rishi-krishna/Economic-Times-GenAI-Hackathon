"""
Intelligent Assignor Agent — Assigns tasks to appropriate team members
"""
from crewai import Agent
from tools.audit_tool import AuditTool
from tools.task_tool import TaskTool
from tools.notification_tool import NotificationTool
from tools.websocket_tool import WebSocketTool


def create_assignor_agent(audit_tool: AuditTool, task_tool: TaskTool,
                           notification_tool: NotificationTool,
                           ws_tool: WebSocketTool) -> Agent:
    return Agent(
        role="Resource & Ownership Specialist",
        goal=(
            "Assign each task to the most appropriate team member based on who was present "
            "in the meeting, what was discussed about ownership, and task type. "
            "Send notifications to each assignee. If no clear owner exists, flag for human review."
        ),
        backstory=(
            "You understand organizational dynamics, accountability structures, and team capabilities. "
            "You are masterful at reading meeting transcripts to identify who volunteered, who was "
            "assigned by a senior stakeholder, and who has the appropriate expertise. You match tasks "
            "to owners based on explicit mentions ('James, you're taking ownership'), role mentions, "
            "and expertise implied in the discussion. When in doubt, you consult the participant list "
            "and assign to the most senior person if no specific owner is named. You always document "
            "your reasoning and send notifications to confirmed assignees."
        ),
        tools=[audit_tool, task_tool, notification_tool, ws_tool],
        verbose=True,
        allow_delegation=False,
        max_iter=3
    )
