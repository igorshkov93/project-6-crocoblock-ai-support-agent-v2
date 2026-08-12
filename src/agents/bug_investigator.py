
"""Agent #3: investigates bug reports using live site diagnostics."""
import asyncio

from langgraph.prebuilt import create_react_agent

from src.config import get_llm
from src.mcp_server.client import load_tools
from src.state import SupportState

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

Then write your findings for the customer:
- State what you checked and what you found.
- Give the most likely cause, and say plainly how confident you are.
- If the data is inconclusive, say what additional information would help.
- Never claim a cause the diagnostics do not support.
- Do not include raw JSON or tool names in your reply. Write for a customer, \
not for an engineer reading logs.

Keep it under 200 words."""

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

def investigate(query: str) -> str:
    """Run the diagnostic agent on a bug report."""
    agent = create_react_agent(
        model=get_llm("smart"),
        tools=load_tools(),
        prompt=SYSTEM_PROMPT,
    )

    result = asyncio.run(
        agent.ainvoke({"messages": [{"role": "user", "content": query}]})
    )
    return extract_text(result["messages"][-1].content)


def bug_investigator_node(state: SupportState) -> dict:
    """Graph node: diagnose the reported problem."""
    query = state["messages"][-1].content
    findings = investigate(query)

    return {
        "final_answer": findings,
        "handled_by": "bug_investigator",
    }