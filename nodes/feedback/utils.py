"""
Các hàm tiện ích (normalize / clip / detect context) cho node feedback.
"""

from __future__ import annotations

from datetime import datetime, timezone

from .constants import FINANCE_KEYWORDS, PRIORITY_HIGH, PRIORITY_LOW, PRIORITY_MEDIUM
from .types import UserFeedbackPayload


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clip(s: str | None, max_len: int) -> str:
    if not s:
        return ""
    if len(s) <= max_len:
        return s
    return s[:max_len] + f"\n…[truncated, total {len(s)} chars]"


def normalize_priority(label: str | None) -> str | None:
    """Chuẩn hoá nhãn priority từ UI/API (hỗ trợ có/không dấu, tiếng Anh)."""
    if label is None:
        return None

    s = label.strip().lower()
    if not s:
        return None

    mapping: dict[str, str] = {
        "cao": PRIORITY_HIGH,
        "high": PRIORITY_HIGH,
        "urgent": PRIORITY_HIGH,
        "trung binh": PRIORITY_MEDIUM,
        "trung bình": PRIORITY_MEDIUM,
        "tb": PRIORITY_MEDIUM,
        "medium": PRIORITY_MEDIUM,
        "thap": PRIORITY_LOW,
        "thấp": PRIORITY_LOW,
        "low": PRIORITY_LOW,
    }
    return mapping.get(s, None)


def detect_finance_context(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in FINANCE_KEYWORDS)


def has_summary_related_feedback(fb: UserFeedbackPayload) -> bool:
    """True nếu có tín hiệu nghiệp vụ về tóm tắt (không chỉ priority)."""
    if fb.get("wants_more_detail"):
        return True
    if (fb.get("summary_feedback") or "").strip():
        return True
    if (fb.get("correction_note") or "").strip():
        return True
    return False


__all__ = [
    "utc_now_iso",
    "clip",
    "normalize_priority",
    "detect_finance_context",
    "has_summary_related_feedback",
]

