import sys
from src.runner import start, resume, new_thread_id

ANSWER_FIELDS = ("final_answer", "answer", "response")


def show(state: dict) -> None:
    print(f"\n[{state.get('query_type')}] → {state.get('handled_by')}\n")
    for field in ANSWER_FIELDS:
        if state.get(field):
            print(state[field])
            return
    print("(!) Ответ не найден в стейте. Ключи:", list(state))


def main() -> None:
    query = " ".join(sys.argv[1:]).strip()
    if not query:
        query = input("Запрос: ").strip()

    thread_id = new_thread_id()
    state, question = start(query, thread_id)

    while question:
        print(f"\n? {question}")
        answer = input("> ").strip()
        state, question = resume(answer, thread_id)

    show(state)


if __name__ == "__main__":
    main()