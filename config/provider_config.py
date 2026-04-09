import os
from typing import List

DEFAULT_PROVIDER_ORDER = ["deepseek", "openai", "openrouter", "anthropic", "google"]

DEFAULT_MODELS = {
    "deepseek": "deepseek-chat",
    "openai": "gpt-4o-mini",
    "openrouter": "openai/gpt-4o-mini",
    "anthropic": "claude-3-5-haiku-latest",
    "google": "gemini-1.5-flash",
}


def get_provider_order() -> List[str]:
    configured = os.getenv("PRIORITIZER_PROVIDER_ORDER", ",".join(DEFAULT_PROVIDER_ORDER))
    providers = [item.strip().lower() for item in configured.split(",") if item.strip()]
    return providers or list(DEFAULT_PROVIDER_ORDER)


def get_model_name(provider: str) -> str:
    env_map = {
        "deepseek": "DEEPSEEK_MODEL",
        "openai": "OPENAI_MODEL",
        "openrouter": "OPENROUTER_MODEL",
        "anthropic": "ANTHROPIC_MODEL",
        "google": "GOOGLE_MODEL",
    }
    env_name = env_map[provider]
    return os.getenv(env_name, DEFAULT_MODELS[provider])
