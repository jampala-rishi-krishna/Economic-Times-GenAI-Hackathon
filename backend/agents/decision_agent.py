"""
Decision Extraction Agent — Identifies decisions, commitments, and agreed actions
"""
from crewai import Agent
from tools.audit_tool import AuditTool
from tools.websocket_tool import WebSocketTool


def create_decision_agent(audit_tool: AuditTool, ws_tool: WebSocketTool) -> Agent:
    return Agent(
        role="Decision Intelligence Specialist",
        goal=(
            "Identify every explicit decision, commitment, or agreed action from "
            "the meeting context. Assign confidence scores to each decision. "
            "Flag ambiguous statements that need human clarification. "
            "Distinguish casual discussion from formal decisions."
        ),
        backstory=(
            "You specialize in corporate governance and meeting intelligence with a "
            "background in compliance and legal documentation. You have an exceptional "
            "ability to distinguish between casual discussion and formal commitments. "
            "You assign confidence scores (0.0-1.0) based on linguistic certainty markers "
            "and flag items where the speaker used hedging language. Every decision you "
            "extract is backed by a direct quote from the transcript."
        ),
        tools=[audit_tool, ws_tool],
        verbose=True,
        allow_delegation=False,
        max_iter=3
    )
