from __future__ import annotations

from pydantic import BaseModel, Field


class InvokeRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description='User prompt for the AI agent')
    required_facts: list[str] = Field(
        default_factory=list,
        description='Facts the grader requires in the generated response.',
    )
    max_correction_loops: int | None = Field(
        default=None,
        ge=1,
        le=10,
        description='Optional per-request correction limit override.',
    )


class InvokeResponse(BaseModel):
    answer: str
    attempts_used: int
    approved: bool
    missing_facts: list[str]
    evaluation_history: list[str]
