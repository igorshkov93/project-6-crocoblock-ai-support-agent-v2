"""Единая точка входа в граф: используется и CLI, и Streamlit."""
import uuid
from langgraph.types import Command

from src.graph import build_graph
from langchain_core.messages import HumanMessage

_graph = build_graph()  # подставь своё имя фабрики/переменной


def new_thread_id() -> str:
    return str(uuid.uuid4())


def _pending_question(config) -> str | None:
    """Возвращает текст уточняющего вопроса, если граф встал на interrupt()."""
    snapshot = _graph.get_state(config)
    for task in snapshot.tasks:
        if task.interrupts:
            payload = task.interrupts[0].value
            if isinstance(payload, dict):
                return payload.get("question") or str(payload)
            return str(payload)
    return None


def start(query: str, thread_id: str):
    """Первый запуск. Возвращает (state, question|None)."""
    config = {"configurable": {"thread_id": thread_id}}
    _graph.invoke({"messages": [HumanMessage(content=query)]}, config)
    return _graph.get_state(config).values, _pending_question(config)


def resume(answer: str, thread_id: str):
    """Продолжение после ответа пользователя на уточняющий вопрос."""
    config = {"configurable": {"thread_id": thread_id}}
    _graph.invoke(Command(resume=answer), config)
    return _graph.get_state(config).values, _pending_question(config)