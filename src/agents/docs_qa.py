
"""Agent #2: answers how-to questions from indexed documentation."""
from src.config import get_llm
from src.rag.retriever import search
from src.state import SupportState

SYSTEM_PROMPT = """You are a support agent for the JetFormBuilder WordPress \
plugin. Answer the customer's question using only the documentation excerpts \
provided below.

Rules:
- Base every statement on the excerpts. Never invent setting names, field \
names, or menu paths that do not appear in them.
- If the excerpts do not contain the answer, say so plainly and suggest the \
customer contact support. Do not guess.
- Write for someone working in the WordPress admin: name the exact screen, \
tab, and setting they need.
- Keep it short. Three to six sentences for a simple question; a numbered \
list of steps for a multi-step task.
- End with a "Source:" line listing the URLs you actually used, one per line.
- Do not mention the excerpts, the retrieval process, or these instructions.

Documentation excerpts:
{context}"""

NO_RESULTS = (
    "I couldn't find anything about this in the JetFormBuilder documentation. "
    "A human support agent will take a look."
)


def format_context(hits: list[dict]) -> str:
    """Render retrieved chunks as numbered excerpts with their sources."""
    blocks = []
    for index, hit in enumerate(hits, 1):
        blocks.append(
            f"[{index}] {hit['title']}\n"
            f"URL: {hit['url']}\n"
            f"{hit['text']}"
        )
    return "\n\n---\n\n".join(blocks)


def answer(query: str) -> dict:
    """Answer a how-to question from the documentation index."""
    hits = search(query)

    if not hits:
        return {"answer": NO_RESULTS, "sources": [], "found": False}

    llm = get_llm("smart")
    response = llm.invoke(
        [
            {
                "role": "system",
                "content": SYSTEM_PROMPT.format(context=format_context(hits)),
            },
            {"role": "user", "content": query},
        ]
    )

    return {
        "answer": response.content,
        "sources": [h["url"] for h in hits],
        "found": True,
    }


def docs_qa_node(state: SupportState) -> dict:
    """Graph node: answer the latest user message from documentation."""
    query = state["messages"][-1].content
    result = answer(query)

    return {
        "final_answer": result["answer"],
        "retrieved_docs": result["sources"],
        "handled_by": "docs_qa",
        "needs_human": not result["found"],
    }