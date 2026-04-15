from __future__ import annotations

from typing import TypedDict


class AgentState(TypedDict):
    prompt: str
    required_facts: list[str]
    attempt: int
    max_attempts: int
    settings: object
    draft_response: str
    approved: bool
    missing_facts: list[str]
    feedback: str
    evaluation_history: list[str]
