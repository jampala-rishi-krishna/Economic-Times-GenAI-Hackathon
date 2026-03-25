"""
Transcription & Context Agent — Parses and structures meeting transcripts
"""
from crewai import Agent
from tools.audit_tool import AuditTool
from tools.websocket_tool import WebSocketTool


def create_transcription_agent(audit_tool: AuditTool, ws_tool: WebSocketTool) -> Agent:
    return Agent(
        role="Senior Meeting Analyst",
        goal=(
            "Parse raw meeting transcripts, identify all participants, timeline, "
            "topics discussed, and produce a structured meeting context document "
            "with complete metadata and a clear executive summary."
        ),
        backstory=(
            "You are an expert at analyzing business meeting transcripts with 15 years "
            "of experience in corporate communications and business intelligence. "
            "You extract key metadata, identify speakers and their roles from context, "
            "and structure unstructured conversational text into clean, machine-readable "
            "summaries. You always audit your actions before and after."
        ),
        tools=[audit_tool, ws_tool],
        verbose=True,
        allow_delegation=False,
        max_iter=3
    )
