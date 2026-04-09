"""
Khai báo kiểu dữ liệu cho node feedback (TypedDict / Literal).
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict

Vote = Literal["upvote", "downvote"]


class UserFeedbackPayload(TypedDict, total=False):
    """
    Payload từ UI / API sau khi phụ huynh tương tác.

    - **vote:** upvote (đồng ý) hoặc downvote (phản đối / cần chỉnh).
    - **corrected_priority:** khi downvote vì *phân loại sai* — priority đúng theo phụ huynh.
    - **summary_feedback:** phản hồi trực tiếp về chất lượng tóm tắt.
    - **correction_note:** ghi chú tự do bổ sung.
    - **wants_more_detail:** True nếu phụ huynh yêu cầu “tóm tắt chi tiết hơn”.
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
    requested_summary_refresh: bool


__all__ = ["Vote", "UserFeedbackPayload", "FeedbackState"]

