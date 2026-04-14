from __future__ import annotations

from fastapi import APIRouter, Depends

from agent.graph import get_agent_graph
from agent.state import AgentState
from api.models import InvokeRequest, InvokeResponse
from core.settings import Settings, get_settings

router = APIRouter()


@router.get('/healthz')
def healthz(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    return {
        'status': 'ok',
        'environment': settings.app_env,
    }


@router.post('/invoke', response_model=InvokeResponse)
def invoke_agent(
    payload: InvokeRequest,
    settings: Settings = Depends(get_settings),
) -> InvokeResponse:
    graph = get_agent_graph()

    max_attempts = payload.max_correction_loops or settings.max_correction_loops
    initial_state: AgentState = {
        'prompt': payload.prompt,
        'required_facts': payload.required_facts,
        'attempt': 0,
        'max_attempts': max_attempts,
        'draft_response': '',
        'approved': False,
        'missing_facts': [],
        'feedback': '',
        'evaluation_history': [],
    }

    result = graph.invoke(initial_state)

    return InvokeResponse(
        answer=result['draft_response'],
        attempts_used=result['attempt'],
        approved=result['approved'],
        missing_facts=result['missing_facts'],
        evaluation_history=result['evaluation_history'],
    )
