"""Shared OpenAI-compatible client configuration for the course notebooks."""

import os

from dotenv import load_dotenv
from openai import OpenAI

MONO_BASE_URL = "https://monogpt.kr/api/monorouter/v1/openai/v1"
OLLAMA_BASE_URL = "http://localhost:11434/v1"

_PROVIDERS = {
    "mono": (MONO_BASE_URL, "gpt-5.5"),
    "ollama": (OLLAMA_BASE_URL, "llama3.2:3b"),
}


def create_llm_client(
    provider: str,
    api_key_env: str = "MY_API_KEY",
) -> tuple[OpenAI, str]:
    """Return an OpenAI-compatible client and its default model.

    For ``mono``, the API key is loaded from the environment variable named
    by ``api_key_env`` (``MY_API_KEY`` by default) or a ``.env`` file. Ollama
    is local and does not require a real API key.
    """
    normalized_provider = provider.strip().lower()
    if normalized_provider not in _PROVIDERS:
        choices = ", ".join(_PROVIDERS)
        raise ValueError(
            f"Unsupported provider {provider!r}. Choose one of: {choices}."
        )

    base_url, model = _PROVIDERS[normalized_provider]
    if normalized_provider == "mono":
        load_dotenv()
        resolved_api_key = os.getenv(api_key_env)
        if not resolved_api_key:
            raise ValueError(
                f"MonoRouter requires an API key. Set {api_key_env} in the "
                "environment or .env file."
            )
    else:
        resolved_api_key = "ollama"

    client = OpenAI(base_url=base_url, api_key=resolved_api_key)
    return client, model
