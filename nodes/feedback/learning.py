"""
Chuẩn hoá bản ghi learning signal cho feedback node.
"""

from __future__ import annotations

from typing import Any

from .constants import MAX_NOTIFICATION_CHARS, MAX_SUMMARY_CHARS, MAX_TEXT_FEEDBACK_CHARS
from .types import FeedbackState, UserFeedbackPayload
from .utils import clip, detect_finance_context, utc_now_iso


def build_learning_record(
    *,
    event: str,
    state: FeedbackState,
    old_priority: str | None,
    new_priority: str | None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Chuẩn hoá một bản ghi learning signal.

    Lưu **notification_text** và **summary** đầy đủ (sau clip an toàn) để phục vụ
    đánh giá “tóm tắt đúng ý chính” và fine-tune summarizer; giữ thêm snippet ngắn
    để xem nhanh trong dashboard.
    """
    nid = state.get("notification_id") or "unknown"
    raw_text = state.get("notification_text") or ""
    raw_summary = state.get("summary") or ""
    rec: dict[str, Any] = {
        "ts": utc_now_iso(),
        "event": event,
        "notification_id": nid,
        "notification_snippet": raw_text[:500],
        "notification_text_full": clip(raw_text, MAX_NOTIFICATION_CHARS),
        "summary_full": clip(raw_summary, MAX_SUMMARY_CHARS),
        "old_priority": old_priority,
        "new_priority": new_priority,
        "summary_present": bool(raw_summary.strip()),
        "finance_context_detected": detect_finance_context(raw_text),
    }
    if extra:
        rec.update(extra)
    return rec


def feedback_extra_from_payload(fb: UserFeedbackPayload) -> dict[str, Any]:
    """Trích các trường text feedback để đưa vào log (đã giới hạn độ dài)."""
    return {
        "summary_feedback": clip(fb.get("summary_feedback"), MAX_TEXT_FEEDBACK_CHARS),
        "correction_note": clip(fb.get("correction_note"), MAX_TEXT_FEEDBACK_CHARS),
        "wants_more_detail": bool(fb.get("wants_more_detail")),
    }


__all__ = ["build_learning_record", "feedback_extra_from_payload"]

