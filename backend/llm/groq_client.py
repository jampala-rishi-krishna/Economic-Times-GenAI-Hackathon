"""
Groq LLM Client for NEXUS
Replaces OpenAI — uses Groq API with llama-3.1-8b-instant
"""
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

_client = None


def get_groq_client():
    """Get or create the Groq client singleton."""
    global _client
    if _client is None:
        try:
            from groq import Groq
            _client = Groq(api_key=GROQ_API_KEY)
        except ImportError:
            raise RuntimeError("groq package not installed. Run: pip install groq")
    return _client


def chat(system_prompt: str, user_prompt: str,
         temperature: float = 0.3, max_tokens: int = 1024) -> str:
    """
    Send a chat completion request to Groq.
    Returns the assistant's response text.
    """
    client = get_groq_client()
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


def extract_decisions_with_llm(transcript: str) -> list[dict]:
    """
    Use Groq LLM to extract decisions from a meeting transcript.
    Returns a list of decision dicts.
    """
    system = (
        "You are an expert meeting analyst. Given a meeting transcript, "
        "identify every explicit decision, commitment, or agreed action. "
        "Return a JSON array of objects with keys: "
        "decision_text, speaker, confidence_score (0.0-1.0), context_quote. "
        "Only return the JSON array, no explanation."
    )
    user = f"TRANSCRIPT:\n{transcript}\n\nExtract all decisions as JSON array:"

    try:
        raw = chat(system, user, temperature=0.1, max_tokens=2048)
        import json
        # Strip markdown code blocks if present
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception as e:
        print(f"[GROQ] Decision extraction failed: {e}")
        return []


def summarize_meeting_with_llm(transcript: str) -> str:
    """Use Groq to generate a concise meeting summary."""
    system = (
        "You are an expert meeting analyst. Summarize the meeting transcript "
        "in 3-4 sentences covering: decisions made, owners assigned, and next steps. "
        "Be concise and professional."
    )
    try:
        return chat(system, f"TRANSCRIPT:\n{transcript}", temperature=0.2, max_tokens=300)
    except Exception as e:
        print(f"[GROQ] Summary failed: {e}")
        return "Meeting summary unavailable."


def generate_task_description_with_llm(decision_text: str, context: str) -> str:
    """Use Groq to expand a decision into a detailed task description."""
    system = (
        "You are a certified Project Manager. Given a meeting decision, "
        "write a clear, actionable task description (2-3 sentences) that any "
        "team member can pick up and execute. Be specific, measurable, and professional."
    )
    user = f"Decision: {decision_text}\nContext: {context}\n\nWrite the task description:"
    try:
        return chat(system, user, temperature=0.3, max_tokens=200)
    except Exception as e:
        print(f"[GROQ] Task description failed: {e}")
        return decision_text


def explain_assignment_with_llm(task_title: str, assignee: str,
                                 participants: list, context: str) -> str:
    """Use Groq to explain why a task was assigned to a specific person."""
    system = (
        "You are an organizational dynamics expert. Explain in 1-2 sentences "
        "why this task is being assigned to this specific person based on the "
        "meeting context. Be direct and reference specific meeting evidence."
    )
    user = (
        f"Task: {task_title}\n"
        f"Assigned to: {assignee}\n"
        f"Meeting participants: {', '.join(participants)}\n"
        f"Context: {context}\n\n"
        "Explain the assignment rationale:"
    )
    try:
        return chat(system, user, temperature=0.3, max_tokens=150)
    except Exception as e:
        print(f"[GROQ] Assignment rationale failed: {e}")
        return f"{assignee} was identified as the owner based on meeting context."


def is_available() -> bool:
    """Check if Groq is configured and available."""
    if not GROQ_API_KEY:
        return False
    try:
        get_groq_client()
        return True
    except Exception:
        return False
