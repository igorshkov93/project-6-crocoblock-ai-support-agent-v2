"""Central configuration: provider switching and model tiers."""
import os
from dotenv import load_dotenv

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()

# "fast" — classification and simple tasks
# "smart" — reasoning, diagnostics and code generation
MODELS = {
    "anthropic": {
        "fast": "claude-haiku-4-5-20251001",
        "smart": "claude-sonnet-5",
    },
    "gemini": {
        "fast": "gemini-2.5-flash",
        "smart": "gemini-2.5-flash",
    },
}


def get_llm(tier: str = "smart", temperature: float = 0.0):
    """Return a LangChain chat model for the active provider."""
    if LLM_PROVIDER not in MODELS:
        raise ValueError(
            f"Unknown LLM_PROVIDER: {LLM_PROVIDER}. "
            f"Expected one of: {', '.join(MODELS)}"
        )
    if tier not in MODELS[LLM_PROVIDER]:
        raise ValueError(f"Unknown tier: {tier}. Expected 'fast' or 'smart'.")

    model_name = MODELS[LLM_PROVIDER][tier]

    if LLM_PROVIDER == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=model_name, temperature=temperature, max_tokens=2000
        )

    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(model=model_name, temperature=temperature)