"""LLM integration for summarization via OpenRouter."""

from __future__ import annotations

import importlib
import json
import os
import re
from typing import Any, Dict, Tuple

from utils.prompt_loader import load_prompt


DEFAULT_SUMMARIZER_PROMPT = (
    "You are a school-notification summarization assistant. "
    "Given a notification JSON input, return valid JSON only, with no markdown and no explanations. "
    "Important: all natural-language output content must be in Vietnamese. "
    "Mode brief: result must be a list with at most 3 concise key points, prioritizing action, deadline, and amount. "
    "Mode detailed: result must be exactly one concise paragraph of 2-4 sentences, with tone aligned to receiver_scope. "
    "Required schema:\n"
    "{\n"
    "  \"result\": [\"string\"] or \"string\" (depending on mode),\n"
    "  \"confidence\": \"high|medium|low\"\n"
    "}"
)


def llm_summarize_json(
    notification: Dict[str, Any],
    text: str,
    mode: str,
    tone_profile: Dict[str, Any],
    notif_type: str,
    model: str,
    force_local: bool,
) -> Tuple[str, Dict[str, Any]]:
    if force_local:
        return "disabled", {}

    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        return "no_api_key", {}

    try:
        module = importlib.import_module("langchain_openrouter")
        ChatOpenRouter = getattr(module, "ChatOpenRouter")
    except Exception:
        return "missing_dependency", {}

    system_prompt = load_prompt(
        prompt_name="summarizer_system_prompt",
        default_prompt=DEFAULT_SUMMARIZER_PROMPT,
        env_override_var="SUMMARIZER_SYSTEM_PROMPT_PATH",
    )

    payload = {
        "mode": mode,
        "expected_notification_type": notif_type,
        "tone_profile": tone_profile,
        "notification": notification,
        "text": text,
    }

    try:
        llm = ChatOpenRouter(
            model_name=model,
            openrouter_api_key=api_key,
            openrouter_api_base="https://openrouter.ai/api/v1",
            temperature=0,
        )
        response = llm.invoke(
            [
                ("system", system_prompt),
                ("human", json.dumps(payload, ensure_ascii=False)),
            ]
        )
        content = response.content if hasattr(response, "content") else str(response)
        parsed = parse_llm_json(str(content))
        if not isinstance(parsed, dict):
            return "invalid_json", {}
        return "ok", parsed
    except Exception:
        return "llm_error", {}


def parse_llm_json(content: str) -> Dict[str, Any]:
    text = content.strip()
    if not text:
        return {}

    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()

    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else {}
    except Exception:
        pass

    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return {}

    try:
        data = json.loads(match.group(0))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}
