from __future__ import annotations

from agent.graph import get_agent_graph
from core.settings import Settings


def _test_settings() -> Settings:
    return Settings(
        ENABLE_AZURE_OPENAI='false',
        MAX_CORRECTION_LOOPS='3',
    )


def test_correction_loop_retries_until_required_facts_present() -> None:
    graph = get_agent_graph()
    result = graph.invoke(
        {
            'prompt': 'Explain the platform design',
            'required_facts': ['Fact A', 'Fact B'],
            'attempt': 0,
            'max_attempts': 3,
            'draft_response': '',
            'approved': False,
            'missing_facts': [],
            'feedback': '',
            'evaluation_history': [],
            'settings': _test_settings(),
        }
    )

    assert result['approved'] is True
    assert result['attempt'] == 2
    assert any('needs_correction' in item for item in result['evaluation_history'])
    assert 'Fact A' in result['draft_response']
    assert 'Fact B' in result['draft_response']


def test_finalize_marks_unresolved_when_max_attempts_reached() -> None:
    graph = get_agent_graph()
    result = graph.invoke(
        {
            'prompt': 'Explain the platform design',
            'required_facts': ['Fact A', 'Fact B', 'Fact C'],
            'attempt': 0,
            'max_attempts': 1,
            'draft_response': '',
            'approved': False,
            'missing_facts': [],
            'feedback': '',
            'evaluation_history': [],
            'settings': _test_settings(),
        }
    )

    assert result['approved'] is False
    assert result['attempt'] == 1
    assert 'maximum correction attempts reached' in result['draft_response'].lower()
