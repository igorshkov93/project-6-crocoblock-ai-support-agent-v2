
"""Agent #1: classifies incoming support requests."""
from pydantic import BaseModel, Field

from src.config import get_llm
from src.state import SupportState

SYSTEM_PROMPT = """You are the first-line triage agent for Crocoblock plugin \
support (JetFormBuilder, JetEngine). Classify each customer message into \
exactly one category.

Categories:
- how_to: the customer asks how to use an existing feature, how something \
works, or which setting to use. The answer exists in the documentation.
- bug: something is broken, missing, or behaves unexpectedly. Includes white \
screens, errors, and features that stopped working. The cause is unknown and \
must be investigated on the customer's site.
- code: the customer explicitly asks for a PHP snippet, CSS rule, or hook to \
extend functionality beyond what the plugin offers out of the box.
- rest: pre-sales questions, pricing, licensing, refunds, feature requests, \
feedback, greetings, and anything else. These need a human.

Rules:
- If the customer reports something broken AND asks for code, classify as \
bug. The problem must be diagnosed before any fix is written.
- If the customer asks how to achieve something that the plugin supports \
natively, that is how_to, not code.
- Set confidence below 0.6 when the message is too vague to classify \
reliably.

Reply with the category, a confidence score between 0 and 1, and one short \
sentence explaining your choice."""


class RoutingDecision(BaseModel):
    """Structured output of the router agent."""

    query_type: str = Field(
        description="One of: how_to, bug, code, rest"
    )
    confidence: float = Field(
        description="Confidence between 0.0 and 1.0", ge=0.0, le=1.0
    )
    reason: str = Field(description="One short sentence explaining the choice")


def classify(query: str) -> RoutingDecision:
    """Classify a single customer message."""
    llm = get_llm("fast").with_structured_output(RoutingDecision)
    return llm.invoke(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": query},
        ]
    )


def router_node(state: SupportState) -> dict:
    """Graph node: classify the latest user message."""
    query = state["messages"][-1].content
    decision = classify(query)
    return {
        "query_type": decision.query_type,
        "confidence": decision.confidence,
        "routing_reason": decision.reason,
    }