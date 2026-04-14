from __future__ import annotations

from .state import AgentState


def _normalize(text: str) -> str:
    return ' '.join(text.lower().split())


def generate_response(state: AgentState) -> AgentState:
    """Create a candidate answer and incorporate grader feedback on retries."""

    next_attempt = state['attempt'] + 1
    prompt = state['prompt'].strip()
    required_facts = [fact.strip() for fact in state['required_facts'] if fact.strip()]

    response_lines: list[str] = [f"Answer: {prompt}"]

    if required_facts:
        if next_attempt == 1 and len(required_facts) > 1:
            facts_to_include = required_facts[:1]
        else:
            facts_to_include = required_facts

        response_lines.append('Supporting facts:')
        response_lines.extend(f"- {fact}" for fact in facts_to_include)

    if state['feedback']:
        response_lines.append(f"Correction applied: {state['feedback']}")

    return {
        **state,
        'attempt': next_attempt,
        'draft_response': '\n'.join(response_lines),
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
