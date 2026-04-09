from typing import Any, Dict

from config.prioritization_runtime import load_runtime_config
from core.constants.prioritization import DEFAULT_SYSTEM_PROMPT
from core.types.prioritization import PrioritizationResult
from services.prioritization.rules import (
    context_priority_score,
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
            "priority_explainability": {
                "summary": "No text found. Fallback to Low.",
                "source": "default",
                "evidence": ["missing_input_text"],
            },
        }

    runtime_cfg = load_runtime_config()
    medium_override_threshold = float(
        runtime_cfg.get("medium_override_llm_confidence_threshold", 0.85)
    )

    context_level, context_score, context_evidence = context_priority_score(state)
    keyword_level, keyword_confidence, keyword_reason = keyword_priority(text)

    # Critical Vinschool keywords are forced to HIGH to reduce missed urgent actions.
    if keyword_level == "HIGH":
        return {
            "priority_level": "High",
            "priority_confidence": keyword_confidence,
            "priority_reason": keyword_reason,
            "priority_source": "keyword_guardrail",
            "priority_explainability": {
                "summary": "High priority by keyword guardrail.",
                "source": "keyword_guardrail",
                "evidence": [keyword_reason, f"context={context_level}:{context_score:.2f}"],
            },
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

        if keyword_level == "MEDIUM" and llm_level == "LOW" and llm_conf < medium_override_threshold:
            return {
                "priority_level": "Medium",
                "priority_confidence": max(keyword_confidence, llm_conf),
                "priority_reason": "keyword_medium_override",
                "priority_source": "keyword_override",
                "priority_provider": llm_result.get("provider"),
                "priority_model": llm_result.get("model"),
                "priority_explainability": {
                    "summary": "Keep Medium due to keyword while LLM is Low with low confidence.",
                    "source": "keyword_override",
                    "evidence": [
                        keyword_reason,
                        f"llm={llm_level}",
                        f"llm_conf={llm_conf:.2f}",
                        f"threshold={medium_override_threshold:.2f}",
                    ],
                },
            }

        # Context score can promote/demote one level when LLM confidence is weak.
        if llm_conf < 0.65 and context_level != llm_level:
            return {
                "priority_level": to_title_case(context_level),
                "priority_confidence": max(llm_conf, context_score),
                "priority_reason": "context_override_low_llm_confidence",
                "priority_source": "context_override",
                "priority_provider": llm_result.get("provider"),
                "priority_model": llm_result.get("model"),
                "priority_explainability": {
                    "summary": "Context score overrides low-confidence LLM decision.",
                    "source": "context_override",
                    "evidence": context_evidence + [f"llm={llm_level}:{llm_conf:.2f}"],
                },
            }

        return {
            "priority_level": to_title_case(llm_level),
            "priority_confidence": llm_conf,
            "priority_reason": llm_result.get("reason", "llm_classification"),
            "priority_source": "llm",
            "priority_provider": llm_result.get("provider"),
            "priority_model": llm_result.get("model"),
            "priority_explainability": {
                "summary": f"{to_title_case(llm_level)} predicted by LLM.",
                "source": "llm",
                "evidence": [
                    str(llm_result.get("reason", "llm_classification")),
                    f"provider={llm_result.get('provider', 'unknown')}",
                    f"context={context_level}:{context_score:.2f}",
                ] + context_evidence,
            },
        }
    except Exception as exc:  # noqa: BLE001
        if keyword_level is not None:
            return {
                "priority_level": to_title_case(keyword_level),
                "priority_confidence": keyword_confidence,
                "priority_reason": f"keyword_fallback_after_llm_error: {keyword_reason}",
                "priority_source": "keyword_fallback",
                "priority_error": str(exc),
                "priority_explainability": {
                    "summary": "LLM failed, fallback to keyword result.",
                    "source": "keyword_fallback",
                    "evidence": [keyword_reason, str(exc)],
                },
            }

        # Use context score as safer fallback before default low.
        if context_level in {"HIGH", "MEDIUM", "LOW"}:
            return {
                "priority_level": to_title_case(context_level),
                "priority_confidence": context_score,
                "priority_reason": "context_fallback_after_llm_error",
                "priority_source": "context_fallback",
                "priority_error": str(exc),
                "priority_explainability": {
                    "summary": "LLM failed, fallback to context score.",
                    "source": "context_fallback",
                    "evidence": context_evidence + [str(exc)],
                },
            }

        return {
            "priority_level": "Low",
            "priority_confidence": 0.5,
            "priority_reason": "llm_failed_and_no_keyword",
            "priority_source": "safe_default",
            "priority_error": str(exc),
            "priority_explainability": {
                "summary": "LLM failed and no rule matched. Fallback to Low.",
                "source": "safe_default",
                "evidence": [str(exc)],
            },
        }
