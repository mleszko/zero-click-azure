from __future__ import annotations

from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from .nodes import finalize_response, generate_response, grade_response, route_after_grading
from .state import AgentState


@lru_cache(maxsize=1)
def get_agent_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node('generate', generate_response)
    workflow.add_node('grade', grade_response)
    workflow.add_node('finalize', finalize_response)

    workflow.add_edge(START, 'generate')
    workflow.add_edge('generate', 'grade')
    workflow.add_conditional_edges(
        'grade',
        route_after_grading,
        {
            'generate': 'generate',
            'finalize': 'finalize',
        },
    )
    workflow.add_edge('finalize', END)

    return workflow.compile()
