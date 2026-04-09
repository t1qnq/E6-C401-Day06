from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from config.prioritization_runtime import load_runtime_config
from core.constants.prioritization import (
    HIGH_KEYWORDS,
    LOW_KEYWORDS,
    MEDIUM_KEYWORDS,
    PRIORITY_TITLE_CASE,
)
from services.prioritization.feedback_learning import feedback_learner


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


def _effective_keywords() -> Dict[str, set[str]]:
    learned = feedback_learner.load_learned_keywords()
    return {
        "HIGH": set(HIGH_KEYWORDS).union(learned.get("HIGH", set())),
        "MEDIUM": set(MEDIUM_KEYWORDS).union(learned.get("MEDIUM", set())),
        "LOW": set(LOW_KEYWORDS).union(learned.get("LOW", set())),
    }


def keyword_priority(text: str) -> Tuple[Optional[str], float, str]:
    runtime_cfg = load_runtime_config()
    confidence_cfg = runtime_cfg.get("keyword_confidence", {})
    keywords = _effective_keywords()

    normalized = normalize_text(text)
    if any(keyword in normalized for keyword in keywords["HIGH"]):
        return "HIGH", float(confidence_cfg.get("HIGH", 0.97)), "high_keyword_match"
    if any(keyword in normalized for keyword in keywords["MEDIUM"]):
        return "MEDIUM", float(confidence_cfg.get("MEDIUM", 0.8)), "medium_keyword_match"
    if any(keyword in normalized for keyword in keywords["LOW"]):
        return "LOW", float(confidence_cfg.get("LOW", 0.7)), "low_keyword_match"
    return None, 0.0, "no_keyword_match"


def _receiver_scope_score(receiver_scope: str) -> Tuple[float, str]:
    scope = (receiver_scope or "").lower()
    if scope == "student":
        return 1.0, "receiver_scope=individual"
    if scope == "class":
        return 0.7, "receiver_scope=class"
    if scope == "grade":
        return 0.5, "receiver_scope=grade"
    if scope == "all":
        return 0.3, "receiver_scope=all"
    return 0.2, "receiver_scope=unknown"


def _category_score(category: str, cfg: Dict[str, Any]) -> Tuple[float, str, str]:
    cat = (category or "").lower().strip()
    hint_map = cfg.get("category_priority_hint", {})
    hinted_priority = str(hint_map.get(cat, "")).upper()
    if hinted_priority == "HIGH":
        return 1.0, hinted_priority, f"category={cat}:HIGH"
    if hinted_priority == "MEDIUM":
        return 0.65, hinted_priority, f"category={cat}:MEDIUM"
    if hinted_priority == "LOW":
        return 0.35, hinted_priority, f"category={cat}:LOW"
    return 0.4, "", f"category={cat or 'unknown'}:DEFAULT"


def _urgency_score(notification: Dict[str, Any]) -> Tuple[float, str]:
    ts = notification.get("timestamp") if isinstance(notification, dict) else None
    if not ts:
        return 0.3, "urgency=no_timestamp"

    try:
        ts_str = str(ts).replace("Z", "+00:00")
        dt = datetime.fromisoformat(ts_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        hours = (now - dt).total_seconds() / 3600.0
    except Exception:
        return 0.3, "urgency=invalid_timestamp"

    if hours <= 6:
        return 1.0, "urgency<=6h"
    if hours <= 24:
        return 0.8, "urgency<=24h"
    if hours <= 72:
        return 0.6, "urgency<=72h"
    return 0.3, "urgency>72h"


def _profile_score(student_profile: Dict[str, Any], category: str) -> Tuple[float, str]:
    if not isinstance(student_profile, dict):
        return 0.4, "profile=missing"

    history = student_profile.get("history_priority_engagement")
    if not isinstance(history, dict):
        return 0.4, "profile=no_history"

    value = str(history.get((category or "").lower(), "")).lower()
    mapping = {"high": 1.0, "medium": 0.6, "low": 0.3}
    score = mapping.get(value, 0.4)
    return score, f"profile_{category or 'unknown'}={value or 'unknown'}"


def _score_to_priority(score: float, cfg: Dict[str, Any]) -> str:
    thresholds = cfg.get("score_thresholds", {})
    high_th = float(thresholds.get("high", 0.75))
    med_th = float(thresholds.get("medium", 0.45))

    if score >= high_th:
        return "HIGH"
    if score >= med_th:
        return "MEDIUM"
    return "LOW"


def context_priority_score(state: Dict[str, Any]) -> Tuple[str, float, list[str]]:
    """Compute context score from api data fields (category/timestamp/scope/profile)."""
    cfg = load_runtime_config()
    weights = cfg.get("weights", {})

    notification = state.get("notification") if isinstance(state.get("notification"), dict) else {}
    category = str(notification.get("category", "")).lower()
    receiver_scope = str(notification.get("receiver_scope", ""))

    c_score, _, c_reason = _category_score(category, cfg)
    u_score, u_reason = _urgency_score(notification)
    r_score, r_reason = _receiver_scope_score(receiver_scope)

    student_profile = state.get("student_profile") if isinstance(state.get("student_profile"), dict) else {}
    p_score, p_reason = _profile_score(student_profile, category)

    total = (
        float(weights.get("category", 0.35)) * c_score
        + float(weights.get("urgency", 0.25)) * u_score
        + float(weights.get("receiver_scope", 0.15)) * r_score
        + float(weights.get("profile", 0.25)) * p_score
    )

    return _score_to_priority(total, cfg), total, [c_reason, u_reason, r_reason, p_reason]


def to_title_case(priority_upper: str) -> str:
    return PRIORITY_TITLE_CASE.get(priority_upper, "Low")
