"""
Node handle_feedback — Human-in-the-loop (Thuận).

Luồng LangGraph: prioritization -> summarizer -> feedback.

Nhiệm vụ:
- Nhận feedback phụ huynh (upvote / downvote).
- Khi có chỉnh sửa (correction), cập nhật priority trong state.
- Ghi learning signal (JSONL) phục vụ fine-tune / phân tích sau (SPEC: Correction Path, Learning Signal).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, TypedDict

logger = logging.getLogger(__name__)

# Đồng bộ nhãn với SPEC / UI (🔴 Cao / 🟡 TB / 🟢 Thấp)
PRIORITY_HIGH = "Cao"
PRIORITY_MEDIUM = "Trung bình"
PRIORITY_LOW = "Thấp"

VALID_PRIORITIES = frozenset({PRIORITY_HIGH, PRIORITY_MEDIUM, PRIORITY_LOW})

Vote = Literal["upvote", "downvote"]

# Từ khóa Vinschool — khi user sửa lên Cao cho nội dung liên quan, ghi nhận để fine-tune (SPEC §2.4)
FINANCE_KEYWORDS = (
    "học phí",
    "hoc phi",
    "tài chính",
    "tai chinh",
    "thanh toán",
    "thanh toan",
    "đóng tiền",
    "dong tien",
    "hạn chót",
    "han chot",
    "deadline",
)


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_learning_log_path() -> Path:
    """Đường dẫn file JSONL ghi learning signal (một dòng = một sự kiện)."""
    d = _project_root() / "api" / "data"
    d.mkdir(parents=True, exist_ok=True)
    return d / "learning_signals.jsonl"


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


class UserFeedbackPayload(TypedDict, total=False):
    """Payload từ UI: nút Upvote/Downvote và (tuỳ chọn) priority đúng sau chỉnh sửa."""

    vote: Vote
    corrected_priority: str


class FeedbackState(TypedDict, total=False):
    """
    Phần state mà node này đọc/ghi. AgentState đầy đủ trong graph là superset của dict này.
    """

    notification_id: str
    notification_text: str
    priority: str
    summary: str
    user_feedback: UserFeedbackPayload
    learning_signals: list[dict[str, Any]]
    feedback_status: str
    feedback_message: str


def _append_jsonl(record: dict[str, Any], path: Path) -> None:
    line = json.dumps(record, ensure_ascii=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(line)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _detect_finance_context(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in FINANCE_KEYWORDS)


def _build_learning_record(
    *,
    event: str,
    state: FeedbackState,
    old_priority: str | None,
    new_priority: str | None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    nid = state.get("notification_id") or "unknown"
    snippet = (state.get("notification_text") or "")[:500]
    rec: dict[str, Any] = {
        "ts": _utc_now_iso(),
        "event": event,
        "notification_id": nid,
        "notification_snippet": snippet,
        "old_priority": old_priority,
        "new_priority": new_priority,
        "summary_present": bool(state.get("summary")),
        "finance_context_detected": _detect_finance_context(state.get("notification_text") or ""),
    }
    if extra:
        rec.update(extra)
    return rec


def handle_feedback(state: FeedbackState, log_path: Path | None = None) -> dict[str, Any]:
    """
    Node LangGraph: xử lý feedback phụ huynh và ghi learning signal.

    - upvote: củng cố priority hiện tại, ghi signal tích cực.
    - downvote: nếu có `corrected_priority` thì cập nhật priority (Correction Path); luôn ghi signal.

    Trả về dict merge vào state (partial update).
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
        rec = _build_learning_record(
            event="invalid_vote",
            state=state,
            old_priority=state.get("priority"),
            new_priority=None,
            extra={"error": msg, "raw_vote": vote},
        )
        _append_jsonl(rec, path)
        signals.append(rec)
        return {
            "feedback_status": "error",
            "feedback_message": msg,
            "learning_signals": signals,
        }

    current = state.get("priority") or ""
    old_priority = current

    if vote == "upvote":
        rec = _build_learning_record(
            event="upvote",
            state=state,
            old_priority=old_priority,
            new_priority=old_priority,
            extra={"signal": "positive_reinforcement"},
        )
        _append_jsonl(rec, path)
        signals.append(rec)
        return {
            "feedback_status": "recorded",
            "feedback_message": "Đã ghi nhận upvote (đồng ý phân loại/tóm tắt).",
            "learning_signals": signals,
        }

    # downvote
    raw_correction = feedback.get("corrected_priority")
    normalized = normalize_priority(raw_correction) if raw_correction else None

    if normalized is None or normalized not in VALID_PRIORITIES:
        msg = (
            "Downvote: thiếu hoặc sai corrected_priority. "
            "Gửi corrected_priority là một trong: Cao | Trung bình | Thấp."
        )
        logger.info(msg)
        rec = _build_learning_record(
            event="downvote_needs_correction",
            state=state,
            old_priority=old_priority,
            new_priority=None,
            extra={
                "signal": "negative_without_valid_correction",
                "raw_corrected_priority": raw_correction,
            },
        )
        _append_jsonl(rec, path)
        signals.append(rec)
        return {
            "feedback_status": "needs_correction",
            "feedback_message": msg,
            "learning_signals": signals,
        }

    rec = _build_learning_record(
        event="priority_correction",
        state=state,
        old_priority=old_priority,
        new_priority=normalized,
        extra={
            "signal": "human_correction",
            "finance_boost_hint": _detect_finance_context(state.get("notification_text") or "")
            and normalized == PRIORITY_HIGH,
        },
    )
    _append_jsonl(rec, path)
    signals.append(rec)

    return {
        "priority": normalized,
        "feedback_status": "updated",
        "feedback_message": f"Đã cập nhật priority: {old_priority!r} -> {normalized!r} (learning signal đã ghi).",
        "learning_signals": signals,
    }


__all__ = [
    "PRIORITY_HIGH",
    "PRIORITY_MEDIUM",
    "PRIORITY_LOW",
    "VALID_PRIORITIES",
    "UserFeedbackPayload",
    "FeedbackState",
    "default_learning_log_path",
    "normalize_priority",
    "handle_feedback",
]
