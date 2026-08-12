"""Agent #3: investigates bug reports using live site diagnostics."""
import asyncio

from langgraph.prebuilt import create_react_agent
from langgraph.types import interrupt
from pydantic import BaseModel, Field

from src.config import get_llm
from src.mcp_server.client import load_tools
from src.state import SupportState

MAX_ROUNDS = 2

SYSTEM_PROMPT = """You are a second-line support engineer for Crocoblock \
WordPress plugins. A customer reports that something is broken.

You have read-only access to their site through these tools:
- get_env_info: WordPress, PHP and MySQL versions, active theme, debug settings
- list_plugins: installed plugins with versions and activation status
- get_error_log: the tail of the WordPress debug log

Process:
1. Call get_env_info first. It is cheap and almost always relevant.
2. Call list_plugins when the report involves a feature that could conflict \
with another plugin, or when a version mismatch is plausible.
3. Call get_error_log when the customer reports a fatal error, a white \
screen, a 500 response, or any failure with no visible message.

Then decide:
- If the diagnostics point to a likely cause, write your findings.
- If you need information only the customer can provide (what they see on \
screen, which settings are configured, what they did before it broke), ask \
for it instead of guessing.

When writing findings:
- State what you checked and what you found.
- Give the most likely cause and how confident you are.
- Never claim a cause the diagnostics do not support.
- Do not include raw JSON or tool names. Write for a customer.

Keep it under 200 words."""


class Findings(BaseModel):
    """Structured outcome of a diagnostic round."""

    needs_input: bool = Field(
        description="True if customer input is required to proceed"
    )
    message: str = Field(
        description="Either the findings, or the questions for the customer"
    )


def extract_text(content) -> str:
    """Get plain text from a response that may contain thinking blocks."""
    if isinstance(content, str):
        return content
    parts = [
        block.get("text", "")
        for block in content
        if isinstance(block, dict) and block.get("type") == "text"
    ]
    return "\n".join(p for p in parts if p).strip()


def run_diagnostics(messages: list) -> str:
    """Run the ReAct agent over the conversation so far."""
    agent = create_react_agent(
        model=get_llm("smart"),
        tools=load_tools(),
        prompt=SYSTEM_PROMPT,
    )
    result = asyncio.run(agent.ainvoke({"messages": messages}))
    return extract_text(result["messages"][-1].content)


def classify_response(text: str) -> Findings:
    """Decide whether the agent is asking or concluding."""
    llm = get_llm("fast").with_structured_output(Findings)
    return llm.invoke(
        [
            {
                "role": "system",
                "content": (
                    "Read the support engineer's message. Decide whether it "
                    "primarily asks the customer for information needed to "
                    "continue (needs_input=true), or presents a diagnosis "
                    "(needs_input=false). Return the message unchanged."
                ),
            },
            {"role": "user", "content": text},
        ]
    )


def bug_investigator_node(state: SupportState) -> dict:
    """Graph node: diagnose, asking follow-up questions when needed."""
    rounds = state.get("clarifying_rounds", 0)
    history = state.get("investigation_log", [])

    conversation = [{"role": "user", "content": state["messages"][0].content}]
    for entry in history:
        conversation.append({"role": "assistant", "content": entry["question"]})
        conversation.append({"role": "user", "content": entry["reply"]})

    raw = run_diagnostics(conversation)
    verdict = classify_response(raw)

    if not verdict.needs_input or rounds >= MAX_ROUNDS:
        return {
            "final_answer": verdict.message,
            "clarifying_rounds": rounds,
            "handled_by": "bug_investigator",
            "needs_human": verdict.needs_input,
        }

    reply = interrupt({"question": verdict.message, "round": rounds + 1})

    return {
        "clarifying_rounds": rounds + 1,
        "investigation_log": history + [
            {"question": verdict.message, "reply": reply}
        ],
        "handled_by": "bug_investigator",
    }