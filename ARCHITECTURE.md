## Agents

| Agent | Responsibility | Tools | Model tier |
|---|---|---|---|
| #1 Router | Classifies the request into `how_to` / `bug` / `code` / `rest`. Returns type + confidence | — | Haiku (cheap, fast) |
| #2 Docs Q&A | Answers how-to questions from indexed plugin documentation | Pinecone retrieval + Cohere rerank | Sonnet |
| #3 Bug Investigator | Asks clarifying questions, collects environment data from the live site | MCP: `get_env_info`, `list_plugins`, `get_error_log` | Sonnet |
| #4 Code Generator | Writes PHP/CSS fixes against the collected context | MCP: `get_env_info` + syntax validator | Sonnet |

Exact model IDs live in `src/config.py`. The provider is switchable via
`LLM_PROVIDER`, so the same graph runs on Gemini during development.

**Scope of v1:** the documentation index covers JetEngine only. JetFormBuilder
and JetSmartFilters are additional namespaces in the same Pinecone index and
require no code changes to add.

## Flow

```mermaid
graph TD
    A["User query"] --> B["Agent 1: Router"]
    B -->|how_to| C["Agent 2: Docs Q&A"]
    B -->|bug| D["Agent 3: Bug Investigator"]
    B -->|code| E["Agent 4: Code Generator"]
    B -->|rest| H["Escalate to human"]
    B -->|confidence below threshold| H
    D -->|needs more info| F["Clarifying questions"]
    F --> D
    D -->|max rounds reached| H
    D -->|env collected, fix needs code| E
    D -->|root cause explained| G["Final answer"]
    C --> G
    E --> G
    H --> G
```

## State schema

| Field | Type | Written by | Purpose |
|---|---|---|---|
| `messages` | list | all | Conversation history |
| `query_type` | str | Router | `how_to` / `bug` / `code` / `rest` |
| `confidence` | float | Router | Classification certainty; below threshold → escalate |
| `env_info` | dict | Bug Investigator | WP/PHP versions, active plugins, theme |
| `retrieved_docs` | list | Docs Q&A | Retrieved documentation chunks |
| `clarifying_rounds` | int | Bug Investigator | Question counter; caps the loop at 3 rounds |
| `final_answer` | str | Docs Q&A / Code Generator | Response to the user |
| `needs_human` | bool | any | Escalation flag for a live support agent |

## Tech stack

- **Orchestration:** LangGraph — conditional edges, `interrupt` for
  human-in-the-loop questioning, checkpointer for conversation memory
- **LLM:** Anthropic Claude (primary), Google Gemini (development) — switched
  via a single `LLM_PROVIDER` variable
- **Retrieval:** Pinecone with contextual retrieval + Cohere reranking
- **WordPress integration:** custom MCP server over the WP REST API
