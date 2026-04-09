from typing import Any, Dict, Optional, Tuple

from core.constants.prioritization import (
    HIGH_KEYWORDS,
    LOW_KEYWORDS,
    MEDIUM_KEYWORDS,
    PRIORITY_TITLE_CASE,
)


def normalize_text(text: str) -> str:
    return " ".join(text.lower().split())


def extract_text_from_state(state: Dict[str, Any]) -> str:
    parts = []
    for key in ("teacher_note", "extracted_text"):
        value = state.get(key)
        if isinstance(value, str) and value.strip():
            parts.append(value.strip())

    notification = state.get("notification")
    if isinstance(notification, dict):
        for key in ("title", "content"):
            value = notification.get(key)
            if isinstance(value, str) and value.strip():
                parts.append(value.strip())

    return "\n".join(parts).strip()


def keyword_priority(text: str) -> Tuple[Optional[str], float, str]:
    normalized = normalize_text(text)
    if any(keyword in normalized for keyword in HIGH_KEYWORDS):
        return "HIGH", 0.97, "vinschool_high_keyword"
    if any(keyword in normalized for keyword in MEDIUM_KEYWORDS):
        return "MEDIUM", 0.80, "vinschool_medium_keyword"
    if any(keyword in normalized for keyword in LOW_KEYWORDS):
        return "LOW", 0.70, "vinschool_low_keyword"
    return None, 0.0, "no_keyword_match"


def to_title_case(priority_upper: str) -> str:
    return PRIORITY_TITLE_CASE.get(priority_upper, "Low")
