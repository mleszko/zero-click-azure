from __future__ import annotations

from core.llm import GenerationInput, LLMService
from core.settings import Settings

from .state import AgentState


def _normalize(text: str) -> str:
    return ' '.join(text.lower().split())


def generate_response(state: AgentState) -> AgentState:
    """Create a candidate answer and incorporate grader feedback on retries."""

    next_attempt = state['attempt'] + 1
    settings = state['settings']
    if not isinstance(settings, Settings):
        raise TypeError('Agent state settings must be a Settings instance.')

    llm_service = LLMService(settings)
    draft_response = llm_service.generate(
        GenerationInput(
            prompt=state['prompt'],
            required_facts=state['required_facts'],
            feedback=state['feedback'],
            attempt=next_attempt,
        )
    )

    return {
        **state,
        'attempt': next_attempt,
        'draft_response': draft_response,
    }


def grade_response(state: AgentState) -> AgentState:
    """Grade the candidate answer and capture any missing required facts."""

    normalized_answer = _normalize(state['draft_response'])
    missing_facts = [
        fact for fact in state['required_facts'] if _normalize(fact) not in normalized_answer
    ]

    approved = not missing_facts
    feedback = 'All required facts are present.'
    if not approved:
        feedback = f"Missing facts: {', '.join(missing_facts)}"

    history_entry = (
        f"Attempt {state['attempt']}: "
        + ('approved' if approved else f"needs_correction ({feedback})")
    )

    return {
        **state,
        'approved': approved,
        'missing_facts': missing_facts,
        'feedback': feedback,
        'evaluation_history': [*state['evaluation_history'], history_entry],
    }


def finalize_response(state: AgentState) -> AgentState:
    """Emit a final response and annotate if quality checks still failed."""

    if state['approved']:
        return state

    warning = (
        '\n\nFinal note: maximum correction attempts reached before all required facts '
        'could be verified.'
    )
    return {
        **state,
        'draft_response': f"{state['draft_response']}{warning}",
    }


def route_after_grading(state: AgentState) -> str:
    if state['approved']:
        return 'finalize'
    if state['attempt'] >= state['max_attempts']:
        return 'finalize'
    return 'generate'
