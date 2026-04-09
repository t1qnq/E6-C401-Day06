"""
Hằng số & cấu hình dùng chung cho node feedback.
"""

from __future__ import annotations

# Đồng bộ nhãn với SPEC / UI (🔴 Cao / 🟡 TB / 🟢 Thấp)
PRIORITY_HIGH = "Cao"
PRIORITY_MEDIUM = "Trung bình"
PRIORITY_LOW = "Thấp"

VALID_PRIORITIES = frozenset({PRIORITY_HIGH, PRIORITY_MEDIUM, PRIORITY_LOW})

# Giới hạn ký tự khi ghi log (tránh JSON cực lớn); vẫn đủ cho fine-tune batch thông thường.
MAX_NOTIFICATION_CHARS = 200_000
MAX_SUMMARY_CHARS = 50_000
MAX_TEXT_FEEDBACK_CHARS = 20_000

# Từ khóa Vinschool — khi user sửa lên Cao cho nội dung liên quan, ghi nhận (SPEC §2.4)
FINANCE_KEYWORDS: tuple[str, ...] = (
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

__all__ = [
    "PRIORITY_HIGH",
    "PRIORITY_MEDIUM",
    "PRIORITY_LOW",
    "VALID_PRIORITIES",
    "MAX_NOTIFICATION_CHARS",
    "MAX_SUMMARY_CHARS",
    "MAX_TEXT_FEEDBACK_CHARS",
    "FINANCE_KEYWORDS",
]

