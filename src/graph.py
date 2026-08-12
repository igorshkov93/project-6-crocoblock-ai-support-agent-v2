
"""LangGraph assembly of the multi-agent support system."""
from langgraph.graph import END, START, StateGraph

from src.state import SupportState

from src.agents.router import router_node
from src.agents.docs_qa import docs_qa_node
from src.agents.bug_investigator import bug_investigator_node

def code_generator_node(state: SupportState) -> dict:
    """Stub: write a PHP/CSS snippet."""
    return {
        "final_answer": "[Code Generator stub] snippet will go here",
        "handled_by": "code_generator",
    }


def escalate_node(state: SupportState) -> dict:
    """Hand the ticket over to a human agent."""
    return {
        "final_answer": (
            "This request needs a human support agent. "
            "Your ticket has been escalated."
        ),
        "needs_human": True,
        "handled_by": "escalation",
    }


CONFIDENCE_THRESHOLD = 0.6


def route_after_router(state: SupportState) -> str:
    """Decide which agent handles the query."""
    if state.get("confidence", 0) < CONFIDENCE_THRESHOLD:
        return "escalate"

    destinations = {
        "how_to": "docs_qa",
        "bug": "bug_investigator",
        "code": "code_generator",
        "rest": "escalate",
    }
    return destinations.get(state.get("query_type"), "escalate")


def build_graph():
    """Assemble and compile the support graph."""
    builder = StateGraph(SupportState)

    builder.add_node("router", router_node)
    builder.add_node("docs_qa", docs_qa_node)
    builder.add_node("bug_investigator", bug_investigator_node)
    builder.add_node("code_generator", code_generator_node)
    builder.add_node("escalate", escalate_node)

    builder.add_edge(START, "router")
    builder.add_conditional_edges(
        "router",
        route_after_router,
        ["docs_qa", "bug_investigator", "code_generator", "escalate"],
    )
    builder.add_edge("docs_qa", END)
    builder.add_edge("bug_investigator", END)
    builder.add_edge("code_generator", END)
    builder.add_edge("escalate", END)

    return builder.compile()


graph = build_graph()