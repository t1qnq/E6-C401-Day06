from typing import Any, Dict

from core.constants.prioritization import DEFAULT_SYSTEM_PROMPT
from core.types.prioritization import PrioritizationResult
from services.prioritization.rules import (
    extract_text_from_state,
    keyword_priority,
    to_title_case,
)
from utils.llm_providers import classify_with_provider_chain
from utils.prompt_loader import DEFAULT_PROMPT_DIR, load_prompt

PROMPT_NAME = "prioritizer_system_prompt"
PROMPT_ENV_OVERRIDE = "PRIORITIZER_SYSTEM_PROMPT_FILE"


def prioritize_notification(state: Dict[str, Any]) -> PrioritizationResult:
    """LangGraph node for notification prioritization using rules + multi-provider LLM chain."""
    text = extract_text_from_state(state)
    if not text:
        return {
            "priority_level": "Low",
            "priority_confidence": 0.35,
            "priority_reason": "No text found in state",
            "priority_source": "default",
        }

    keyword_level, keyword_confidence, keyword_reason = keyword_priority(text)

    # Critical Vinschool keywords are forced to HIGH to reduce missed urgent actions.
    if keyword_level == "HIGH":
        return {
            "priority_level": "High",
            "priority_confidence": keyword_confidence,
            "priority_reason": keyword_reason,
            "priority_source": "keyword_guardrail",
        }

    system_prompt = load_prompt(
        prompt_name=PROMPT_NAME,
        default_prompt=DEFAULT_SYSTEM_PROMPT,
        env_override_var=PROMPT_ENV_OVERRIDE,
        prompt_dir=DEFAULT_PROMPT_DIR,
    )
    try:
        llm_result = classify_with_provider_chain(text, system_prompt)
        llm_level = llm_result["priority"]
        llm_conf = float(llm_result.get("confidence", 0.7))

        if keyword_level == "MEDIUM" and llm_level == "LOW" and llm_conf < 0.85:
            return {
                "priority_level": "Medium",
                "priority_confidence": max(keyword_confidence, llm_conf),
                "priority_reason": "keyword_medium_override",
                "priority_source": "keyword_override",
                "priority_provider": llm_result.get("provider"),
                "priority_model": llm_result.get("model"),
            }

        return {
            "priority_level": to_title_case(llm_level),
            "priority_confidence": llm_conf,
            "priority_reason": llm_result.get("reason", "llm_classification"),
            "priority_source": "llm",
            "priority_provider": llm_result.get("provider"),
            "priority_model": llm_result.get("model"),
        }
    except Exception as exc:  # noqa: BLE001
        if keyword_level is not None:
            return {
                "priority_level": to_title_case(keyword_level),
                "priority_confidence": keyword_confidence,
                "priority_reason": f"keyword_fallback_after_llm_error: {keyword_reason}",
                "priority_source": "keyword_fallback",
                "priority_error": str(exc),
            }

        return {
            "priority_level": "Low",
            "priority_confidence": 0.5,
            "priority_reason": "llm_failed_and_no_keyword",
            "priority_source": "safe_default",
            "priority_error": str(exc),
        }
