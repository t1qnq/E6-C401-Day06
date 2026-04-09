"""
Node `handle_feedback` (LangGraph) — xử lý phản hồi phụ huynh và ghi learning signals.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from .constants import PRIORITY_HIGH, VALID_PRIORITIES
from .learning import build_learning_record, feedback_extra_from_payload
from .paths import default_learning_log_path
from .storage import append_jsonl
from .types import FeedbackState
from .utils import detect_finance_context, has_summary_related_feedback, normalize_priority

logger = logging.getLogger(__name__)


def handle_feedback(state: FeedbackState, log_path: Path | None = None) -> dict[str, Any]:
    """
    Node LangGraph: xử lý feedback phụ huynh và ghi learning signal.

    **Upvote:** củng cố trạng thái hiện tại (priority + chất lượng tóm tắt được coi là ok).

    **Downvote — ba nhánh hợp lệ (ít nhất một):**
    1. **Sửa priority:** `corrected_priority` hợp lệ → cập nhật `priority` trong state.
    2. **Phản hồi tóm tắt / Low-confidence:** `summary_feedback`, `correction_note`, hoặc
       `wants_more_detail` → ghi signal cho summarizer, không bắt buộc có priority.
    3. Có thể **vừa** sửa priority **vừa** gửi ghi chú tóm tắt trong cùng payload.

    Mọi nhánh đã xử lý đều trả về `user_feedback: None` để tránh xử lý trùng.
    """
    path = log_path or default_learning_log_path()
    feedback = state.get("user_feedback")
    signals: list[dict[str, Any]] = list(state.get("learning_signals") or [])

    if not feedback:
        msg = "Không có user_feedback trong state; bỏ qua bước feedback."
        logger.info(msg)
        return {
            "feedback_status": "skipped",
            "feedback_message": msg,
            "learning_signals": signals,
        }

    vote = feedback.get("vote")
    if vote not in ("upvote", "downvote"):
        msg = "user_feedback.vote không hợp lệ (cần 'upvote' hoặc 'downvote')."
        logger.warning(msg)
        rec = build_learning_record(
            event="invalid_vote",
            state=state,
            old_priority=state.get("priority"),
            new_priority=None,
            extra={"error": msg, "raw_vote": vote},
        )
        append_jsonl(rec, path)
        signals.append(rec)
        return {
            "feedback_status": "error",
            "feedback_message": msg,
            "learning_signals": signals,
            "user_feedback": None,
        }

    current = state.get("priority") or ""
    old_priority = current

    if vote == "upvote":
        requested_refresh = bool(feedback.get("wants_more_detail")) or bool(
            (feedback.get("summary_feedback") or "").strip()
        )
        rec = build_learning_record(
            event="upvote",
            state=state,
            old_priority=old_priority,
            new_priority=old_priority,
            extra={
                "signal": "positive_reinforcement",
                **feedback_extra_from_payload(feedback),
            },
        )
        append_jsonl(rec, path)
        signals.append(rec)
        out: dict[str, Any] = {
            "feedback_status": "recorded",
            "feedback_message": "Đã ghi nhận upvote (đồng ý phân loại / tóm tắt).",
            "learning_signals": signals,
            "user_feedback": None,
        }
        if requested_refresh:
            out["requested_summary_refresh"] = True
        return out

    # --- downvote ---
    raw_correction = feedback.get("corrected_priority")
    normalized = normalize_priority(raw_correction) if raw_correction else None
    priority_ok = normalized is not None and normalized in VALID_PRIORITIES
    summary_ok = has_summary_related_feedback(feedback)

    if not priority_ok and not summary_ok:
        msg = (
            "Downvote: cần ít nhất một trong các tín hiệu sau — "
            "corrected_priority (Cao | Trung bình | Thấp), "
            "summary_feedback, correction_note, hoặc wants_more_detail=true."
        )
        logger.info(msg)
        rec = build_learning_record(
            event="downvote_incomplete",
            state=state,
            old_priority=old_priority,
            new_priority=None,
            extra={
                "signal": "negative_without_actionable_feedback",
                "raw_corrected_priority": raw_correction,
                **feedback_extra_from_payload(feedback),
            },
        )
        append_jsonl(rec, path)
        signals.append(rec)
        return {
            "feedback_status": "needs_action",
            "feedback_message": msg,
            "learning_signals": signals,
            "user_feedback": None,
        }

    out: dict[str, Any] = {"learning_signals": signals, "user_feedback": None}
    wants_detail = bool(feedback.get("wants_more_detail"))
    requested_refresh = wants_detail or bool((feedback.get("summary_feedback") or "").strip())
    if requested_refresh:
        out["requested_summary_refresh"] = True

    if summary_ok:
        rec_s = build_learning_record(
            event="summary_feedback",
            state=state,
            old_priority=old_priority,
            new_priority=normalized if priority_ok else old_priority,
            extra={
                "signal": "summary_quality_or_detail_request",
                "low_confidence_path": True,
                **feedback_extra_from_payload(feedback),
            },
        )
        append_jsonl(rec_s, path)
        signals.append(rec_s)

    if priority_ok:
        rec_p = build_learning_record(
            event="priority_correction",
            state=state,
            old_priority=old_priority,
            new_priority=normalized,
            extra={
                "signal": "human_correction",
                "finance_boost_hint": detect_finance_context(state.get("notification_text") or "")
                and normalized == PRIORITY_HIGH,
                **feedback_extra_from_payload(feedback),
            },
        )
        append_jsonl(rec_p, path)
        signals.append(rec_p)
        out["priority"] = normalized
        out["feedback_status"] = "updated" if not summary_ok else "updated_with_summary_feedback"
        parts = [f"priority {old_priority!r} -> {normalized!r}"]
        if summary_ok:
            parts.append("đã ghi nhận feedback tóm tắt")
        out["feedback_message"] = "Đã cập nhật: " + "; ".join(parts) + "."
    else:
        out["feedback_status"] = "summary_feedback_recorded"
        out["feedback_message"] = (
            "Đã ghi nhận feedback về tóm tắt (không đổi priority). "
            "Có thể kích hoạt bước tóm tắt lại nếu requested_summary_refresh."
        )

    out["learning_signals"] = signals
    return out


__all__ = ["handle_feedback"]

