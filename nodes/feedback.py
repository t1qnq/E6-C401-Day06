"""

Node handle_feedback — Human-in-the-loop (Thuận).



Luồng LangGraph: prioritization -> summarizer -> feedback.



Nhiệm vụ (bám SPEC.md + Assign_Work):

- Nhận feedback phụ huynh (upvote / downvote).

- **Priority:** khi phụ huynh sửa mức ưu tiên (Correction Path §2.4).

- **Summary (Low-confidence Path §2.2):** nhận phản hồi dạng text — báo tóm tắt sai,

  ghi chú chỉnh sửa, hoặc yêu cầu “tóm tắt chi tiết hơn” (không bắt buộc kèm

  corrected_priority).

- Ghi learning signal (JSONL) cho fine-tune: ưu tiên lưu **summary hiện tại** và

  **toàn bộ notification_text** (trong giới hạn an toàn) để đánh giá tóm tắt đúng ý chính.

- Ghi file JSONL có **khóa (filelock)** để tránh race khi nhiều request đồng thời.

- Sau khi xử lý xong một payload feedback, **xóa user_feedback** khỏi state (consume)

  để tránh ghi log trùng ở bước graph sau.

"""



from __future__ import annotations



import json

import logging

from datetime import datetime, timezone

from pathlib import Path

from typing import Any, Literal, TypedDict



from filelock import FileLock



logger = logging.getLogger(__name__)



# Đồng bộ nhãn với SPEC / UI (🔴 Cao / 🟡 TB / 🟢 Thấp)

PRIORITY_HIGH = "Cao"

PRIORITY_MEDIUM = "Trung bình"

PRIORITY_LOW = "Thấp"



VALID_PRIORITIES = frozenset({PRIORITY_HIGH, PRIORITY_MEDIUM, PRIORITY_LOW})



Vote = Literal["upvote", "downvote"]



# Giới hạn ký tự khi ghi log (tránh JSON cực lớn); vẫn đủ cho fine-tune batch thông thường.

_MAX_NOTIFICATION_CHARS = 200_000

_MAX_SUMMARY_CHARS = 50_000

_MAX_TEXT_FEEDBACK_CHARS = 20_000



# Từ khóa Vinschool — khi user sửa lên Cao cho nội dung liên quan, ghi nhận (SPEC §2.4)

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





def _lock_file_for(log_path: Path) -> Path:

    """File khóa đi kèm JSONL (filelock sẽ tạo / giữ lock an toàn trên Windows & Unix)."""

    return log_path.with_name(log_path.name + ".lock")





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





def _clip(s: str | None, max_len: int) -> str:

    if not s:

        return ""

    if len(s) <= max_len:

        return s

    return s[:max_len] + f"\n…[truncated, total {len(s)} chars]"





class UserFeedbackPayload(TypedDict, total=False):

    """

    Payload từ UI / API sau khi phụ huynh tương tác.



    - **vote:** upvote (đồng ý) hoặc downvote (phản đối / cần chỉnh).

    - **corrected_priority:** khi downvote vì *phân loại sai* — priority đúng theo phụ huynh.

    - **summary_feedback:** phản hồi trực tiếp về chất lượng tóm tắt (vd. “tóm tắt thiếu

      phần dụng cụ”, “báo cáo tóm tắt sai” — SPEC §2.2, Learning Signal §1).

    - **correction_note:** ghi chú tự do bổ sung (lý do, ngữ cảnh).

    - **wants_more_detail:** True nếu phụ huynh bấm kiểu “Tóm tắt chi tiết hơn phần chuẩn bị”

      (Low-confidence Path §2.2) — graph có thể dùng để gọi lại summarizer.

    """



    vote: Vote

    corrected_priority: str

    summary_feedback: str

    correction_note: str

    wants_more_detail: bool





class FeedbackState(TypedDict, total=False):

    """

    Phần state mà node này đọc/ghi. AgentState đầy đủ trong graph là superset.



    `user_feedback` sau khi node consume sẽ được set **None** trong kết quả trả về.

    """



    notification_id: str

    notification_text: str

    priority: str

    summary: str

    user_feedback: UserFeedbackPayload | None

    learning_signals: list[dict[str, Any]]

    feedback_status: str

    feedback_message: str

    # Gợi ý cho bước summarizer / graph tiếp theo (tuỳ team nối edge):

    requested_summary_refresh: bool





def _append_jsonl(record: dict[str, Any], path: Path) -> None:

    """

    Ghi một dòng JSON vào file JSONL.



    Dùng **FileLock** quanh toàn bộ mở-append để tránh interleaving / mất dòng khi

    nhiều tiến trình / thread ghi cùng lúc (Streamlit + API).

    """

    line = json.dumps(record, ensure_ascii=False) + "\n"

    path.parent.mkdir(parents=True, exist_ok=True)

    lock_path = _lock_file_for(path)

    # timeout: tránh treo vĩnh viễn nếu lock bị kẹt (đơn vị giây)

    with FileLock(lock_path, timeout=60):

        with path.open("a", encoding="utf-8") as f:

            f.write(line)





def _utc_now_iso() -> str:

    return datetime.now(timezone.utc).isoformat()





def _detect_finance_context(text: str) -> bool:

    t = text.lower()

    return any(k in t for k in FINANCE_KEYWORDS)





def _has_summary_related_feedback(fb: UserFeedbackPayload) -> bool:

    """True nếu có tín hiệu nghiệp vụ về tóm tắt (không chỉ priority)."""

    if fb.get("wants_more_detail"):

        return True

    if (fb.get("summary_feedback") or "").strip():

        return True

    if (fb.get("correction_note") or "").strip():

        return True

    return False





def _build_learning_record(

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

        "ts": _utc_now_iso(),

        "event": event,

        "notification_id": nid,

        # Xem nhanh (giữ tương thích với log cũ / dashboard)

        "notification_snippet": raw_text[:500],

        # Dữ liệu đầy đủ phục vụ fine-tune / so sánh input vs output tóm tắt

        "notification_text_full": _clip(raw_text, _MAX_NOTIFICATION_CHARS),

        "summary_full": _clip(raw_summary, _MAX_SUMMARY_CHARS),

        "old_priority": old_priority,

        "new_priority": new_priority,

        "summary_present": bool(raw_summary.strip()),

        "finance_context_detected": _detect_finance_context(raw_text),

    }

    if extra:

        rec.update(extra)

    return rec





def _feedback_extra_from_payload(fb: UserFeedbackPayload) -> dict[str, Any]:

    """Trích các trường text feedback để đưa vào log (đã giới hạn độ dài)."""

    return {

        "summary_feedback": _clip(fb.get("summary_feedback"), _MAX_TEXT_FEEDBACK_CHARS),

        "correction_note": _clip(fb.get("correction_note"), _MAX_TEXT_FEEDBACK_CHARS),

        "wants_more_detail": bool(fb.get("wants_more_detail")),

    }





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

            "user_feedback": None,

        }



    current = state.get("priority") or ""

    old_priority = current



    if vote == "upvote":
        # SPEC §2.2: ngay cả khi upvote, phụ huynh vẫn có thể yêu cầu “tóm tắt chi tiết hơn”.
        requested_refresh = bool(feedback.get("wants_more_detail")) or bool(
            (feedback.get("summary_feedback") or "").strip()
        )

        rec = _build_learning_record(

            event="upvote",

            state=state,

            old_priority=old_priority,

            new_priority=old_priority,

            extra={

                "signal": "positive_reinforcement",

                **_feedback_extra_from_payload(feedback),

            },

        )

        _append_jsonl(rec, path)

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

    summary_ok = _has_summary_related_feedback(feedback)



    if not priority_ok and not summary_ok:

        msg = (

            "Downvote: cần ít nhất một trong các tín hiệu sau — "

            "corrected_priority (Cao | Trung bình | Thấp), "

            "summary_feedback, correction_note, hoặc wants_more_detail=true."

        )

        logger.info(msg)

        rec = _build_learning_record(

            event="downvote_incomplete",

            state=state,

            old_priority=old_priority,

            new_priority=None,

            extra={

                "signal": "negative_without_actionable_feedback",

                "raw_corrected_priority": raw_correction,

                **_feedback_extra_from_payload(feedback),

            },

        )

        _append_jsonl(rec, path)

        signals.append(rec)

        return {

            "feedback_status": "needs_action",

            "feedback_message": msg,

            "learning_signals": signals,

            "user_feedback": None,

        }



    out: dict[str, Any] = {

        "learning_signals": signals,

        "user_feedback": None,

    }

    wants_detail = bool(feedback.get("wants_more_detail"))

    requested_refresh = wants_detail or bool((feedback.get("summary_feedback") or "").strip())

    if requested_refresh:

        out["requested_summary_refresh"] = True



    # Ghi nhận phản hồi liên quan tóm tắt (Low-confidence / báo sai tóm tắt)

    if summary_ok:

        rec_s = _build_learning_record(

            event="summary_feedback",

            state=state,

            old_priority=old_priority,

            new_priority=normalized if priority_ok else old_priority,

            extra={

                "signal": "summary_quality_or_detail_request",

                "low_confidence_path": True,

                **_feedback_extra_from_payload(feedback),

            },

        )

        _append_jsonl(rec_s, path)

        signals.append(rec_s)



    # Cập nhật priority nếu có chỉnh sửa hợp lệ (Correction Path)

    if priority_ok:

        rec_p = _build_learning_record(

            event="priority_correction",

            state=state,

            old_priority=old_priority,

            new_priority=normalized,

            extra={

                "signal": "human_correction",

                "finance_boost_hint": _detect_finance_context(state.get("notification_text") or "")

                and normalized == PRIORITY_HIGH,

                **_feedback_extra_from_payload(feedback),

            },

        )

        _append_jsonl(rec_p, path)

        signals.append(rec_p)

        out["priority"] = normalized

        out["feedback_status"] = "updated" if not summary_ok else "updated_with_summary_feedback"

        parts = [f"priority {old_priority!r} -> {normalized!r}"]

        if summary_ok:

            parts.append("đã ghi nhận feedback tóm tắt")

        out["feedback_message"] = "Đã cập nhật: " + "; ".join(parts) + "."

    else:

        # Chỉ feedback tóm tắt, không đổi priority

        out["feedback_status"] = "summary_feedback_recorded"

        out["feedback_message"] = (

            "Đã ghi nhận feedback về tóm tắt (không đổi priority). "

            "Có thể kích hoạt bước tóm tắt lại nếu requested_summary_refresh."

        )



    out["learning_signals"] = signals

    return out





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


