import json
import os
import re
from typing import Dict

from config.provider_config import get_model_name, get_provider_order
from core.types.prioritization import LlmClassification


def parse_llm_json(text: str) -> Dict[str, object]:
    cleaned = text.strip()
    if not cleaned:
        raise ValueError("Empty LLM response")

    cleaned = cleaned.replace("```json", "").replace("```", "").strip()
    match = re.search(r"\{[\s\S]*\}", cleaned)
    if match:
        cleaned = match.group(0)

    payload = json.loads(cleaned)
    priority = str(payload.get("priority", "")).upper().strip()
    if priority not in {"HIGH", "MEDIUM", "LOW"}:
        raise ValueError(f"Invalid priority from LLM: {priority}")

    confidence = float(payload.get("confidence", 0.6))
    confidence = max(0.0, min(1.0, confidence))
    reason = str(payload.get("reason", "LLM classification"))

    return {"priority": priority, "confidence": confidence, "reason": reason}


def classify_openai(text: str, system_prompt: str) -> LlmClassification:
    from openai import OpenAI  # type: ignore[import-not-found]

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    model = get_model_name("openai")
    client = OpenAI(api_key=api_key)
    user_prompt = f"Notification text:\n{text}"

    response = client.responses.create(
        model=model,
        temperature=0,
        input=[
            {"role": "system", "content": [{"type": "text", "text": system_prompt}]},
            {"role": "user", "content": [{"type": "text", "text": user_prompt}]},
        ],
    )

    parsed = parse_llm_json(response.output_text)
    return {
        "priority": parsed["priority"],
        "confidence": parsed["confidence"],
        "reason": parsed["reason"],
        "provider": "openai",
        "model": model,
    }


def classify_openrouter(text: str, system_prompt: str) -> LlmClassification:
    from openai import OpenAI  # type: ignore[import-not-found]

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    model = get_model_name("openrouter")
    user_prompt = f"Notification text:\n{text}"

    headers = {}
    referer = os.getenv("OPENROUTER_HTTP_REFERER")
    title = os.getenv("OPENROUTER_X_TITLE")
    if referer:
        headers["HTTP-Referer"] = referer
    if title:
        headers["X-Title"] = title

    client = OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        default_headers=headers if headers else None,
    )

    response = client.responses.create(
        model=model,
        temperature=0,
        input=[
            {"role": "system", "content": [{"type": "text", "text": system_prompt}]},
            {"role": "user", "content": [{"type": "text", "text": user_prompt}]},
        ],
    )

    parsed = parse_llm_json(response.output_text)
    return {
        "priority": parsed["priority"],
        "confidence": parsed["confidence"],
        "reason": parsed["reason"],
        "provider": "openrouter",
        "model": model,
    }


def classify_anthropic(text: str, system_prompt: str) -> LlmClassification:
    from anthropic import Anthropic  # type: ignore[import-not-found]

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")

    model = get_model_name("anthropic")
    client = Anthropic(api_key=api_key)

    message = client.messages.create(
        model=model,
        max_tokens=200,
        temperature=0,
        system=system_prompt,
        messages=[{"role": "user", "content": f"Notification text:\n{text}"}],
    )

    content_text = "".join(
        block.text for block in message.content if hasattr(block, "text")
    )
    parsed = parse_llm_json(content_text)
    return {
        "priority": parsed["priority"],
        "confidence": parsed["confidence"],
        "reason": parsed["reason"],
        "provider": "anthropic",
        "model": model,
    }


def classify_google(text: str, system_prompt: str) -> LlmClassification:
    import google.generativeai as genai  # type: ignore[import-not-found]

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY is not set")

    model_name = get_model_name("google")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
    response = model.generate_content(
        f"{system_prompt}\n\nNotification text:\n{text}",
        generation_config={"temperature": 0},
    )

    parsed = parse_llm_json(response.text or "")
    return {
        "priority": parsed["priority"],
        "confidence": parsed["confidence"],
        "reason": parsed["reason"],
        "provider": "google",
        "model": model_name,
    }


def classify_with_provider_chain(text: str, system_prompt: str) -> LlmClassification:
    provider_impl = {
        "openai": classify_openai,
        "openrouter": classify_openrouter,
        "anthropic": classify_anthropic,
        "google": classify_google,
    }

    last_error = None
    for provider in get_provider_order():
        impl = provider_impl.get(provider)
        if not impl:
            continue
        try:
            return impl(text, system_prompt)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            continue

    raise RuntimeError(f"All providers failed: {last_error}")
