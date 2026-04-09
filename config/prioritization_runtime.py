import json
from pathlib import Path
from typing import Any, Dict

RUNTIME_CONFIG_PATH = Path(__file__).parent / "prioritization_runtime.json"

DEFAULT_RUNTIME_CONFIG: Dict[str, Any] = {
    "medium_override_llm_confidence_threshold": 0.85,
    "score_thresholds": {"high": 0.75, "medium": 0.45},
    "weights": {"category": 0.35, "urgency": 0.25, "receiver_scope": 0.15, "profile": 0.25},
    "category_priority_hint": {
        "finance": "HIGH",
        "health": "HIGH",
        "emergency": "HIGH",
        "academic": "MEDIUM",
        "extracurricular": "MEDIUM",
    },
    "keyword_confidence": {"HIGH": 0.97, "MEDIUM": 0.8, "LOW": 0.7},
    "feedback_learning": {
        "enabled": True,
        "feedback_log_path": "data/feedback/priority_feedback.jsonl",
        "learned_keywords_path": "data/feedback/learned_keywords.json",
        "rebuild_interval_seconds": 1800,
        "min_token_length": 4,
        "min_keyword_frequency": 2,
        "max_keywords_per_level": 60,
        "ignored_tokens": ["thong", "bao", "phu", "huynh", "vinschool", "ngay", "tuan"],
    },
}


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged: Dict[str, Any] = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_runtime_config() -> Dict[str, Any]:
    if not RUNTIME_CONFIG_PATH.exists():
        return dict(DEFAULT_RUNTIME_CONFIG)

    payload = json.loads(RUNTIME_CONFIG_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return dict(DEFAULT_RUNTIME_CONFIG)
    return _deep_merge(DEFAULT_RUNTIME_CONFIG, payload)
