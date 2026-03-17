"""
LLM provider abstraction.

get_llm(provider, model) → BaseChatModel
Supports "openai" and "anthropic".
"""

from __future__ import annotations

from typing import Optional

from langchain_core.language_models.chat_models import BaseChatModel

_DEFAULT_MODELS = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-3-5-haiku-20241022",
}


def get_llm(
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> BaseChatModel:
    """
    Return a configured LangChain chat model.

    Args:
        provider: "openai" | "anthropic". Defaults to settings.DEFAULT_LLM_PROVIDER.
        model: Model name override. Defaults to the provider's default model.

    Returns:
        BaseChatModel instance ready for ainvoke() calls.

    Raises:
        ValueError: If the provider is not supported.
    """
    from app.core.config import settings

    if provider is None:
        provider = settings.DEFAULT_LLM_PROVIDER

    if model is None:
        model = _DEFAULT_MODELS.get(provider, "gpt-4o-mini")

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model,
            api_key=settings.OPENAI_API_KEY or None,
            temperature=0.2,
            max_tokens=4096,
        )
    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=model,
            api_key=settings.ANTHROPIC_API_KEY or None,
            temperature=0.2,
            max_tokens=4096,
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider!r}. Use 'openai' or 'anthropic'.")
