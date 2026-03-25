"""
Task Creator Agent — Converts decisions into SMART actionable tasks
"""
from crewai import Agent
from tools.audit_tool import AuditTool
from tools.task_tool import TaskTool
from tools.websocket_tool import WebSocketTool


def create_task_creator_agent(audit_tool: AuditTool, task_tool: TaskTool,
                               ws_tool: WebSocketTool) -> Agent:
    return Agent(
        role="Project Management Architect",
        goal=(
            "Convert each decision into 1 or more SMART tasks with clear titles, "
            "detailed descriptions, appropriate priority levels, and realistic due dates. "
            "Create tasks that are Specific, Measurable, Achievable, Relevant, and Time-bound."
        ),
        backstory=(
            "You are a certified PMP (Project Management Professional) with deep expertise "
            "in translating strategic decisions into actionable, time-bound work items. "
            "You have managed portfolios worth over $500M and know exactly how to break "
            "down vague commitments into concrete deliverables. You set priorities based "
            "on urgency keywords (by Friday = critical, by end of quarter = low) and "
            "business impact signals. You create tasks that any team member can pick up "
            "and execute without additional clarification."
        ),
        tools=[audit_tool, task_tool, ws_tool],
        verbose=True,
        allow_delegation=False,
        max_iter=3
    )
