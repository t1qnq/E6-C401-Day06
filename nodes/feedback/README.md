## Package `nodes.feedback`

Package này cung cấp node `handle_feedback` (LangGraph) để xử lý phản hồi phụ huynh (upvote/downvote), đồng thời ghi **learning signals** (JSONL + file lock) phục vụ đánh giá và/hoặc fine-tune.

### Import nhanh (public API)

Bạn nên import qua `nodes.feedback` (từ `__init__.py`) để ổn định và ít phụ thuộc vào cấu trúc nội bộ:

```python
from nodes.feedback import (
    handle_feedback,
    normalize_priority,
    default_learning_log_path,
    PRIORITY_HIGH,
    PRIORITY_MEDIUM,
    PRIORITY_LOW,
    VALID_PRIORITIES,
    FeedbackState,
    UserFeedbackPayload,
)
```

### Cách dùng `handle_feedback`

Chữ ký hàm:

```python
handle_feedback(state: FeedbackState, log_path: Path | None = None) -> dict[str, Any]
```

- **Input**: `state` là dict “giống AgentState”, có thể chỉ cần các key mà node đọc.
- **Output**: dict partial-update để merge vào state.
- **Consume**: sau khi xử lý, node sẽ trả về `user_feedback: None` để tránh ghi log trùng.

### Ví dụ payload/state

#### 1) Upvote

```python
state = {
    "notification_id": "N001",
    "notification_text": "Thông báo ...",
    "priority": "Trung bình",
    "summary": "Tóm tắt ...",
    "learning_signals": [],
    "user_feedback": {"vote": "upvote"},
}

out = handle_feedback(state)
```

Kết quả thường có:
- `feedback_status="recorded"`
- `learning_signals` được append thêm 1 record
- `user_feedback=None`

#### 2) Downvote + sửa priority (Correction Path)

```python
state = {
    "notification_id": "N002",
    "notification_text": "Nhắc đóng học phí trước hạn ...",
    "priority": "Thấp",
    "summary": "Tóm tắt ...",
    "learning_signals": [],
    "user_feedback": {"vote": "downvote", "corrected_priority": "Cao"},
}

out = handle_feedback(state)
```

Kết quả thường có:
- `priority` được cập nhật thành `"Cao"`
- `feedback_status="updated"` (hoặc `"updated_with_summary_feedback"` nếu có kèm feedback tóm tắt)

#### 3) Downvote chỉ góp ý tóm tắt / yêu cầu chi tiết hơn (Low-confidence Path)

```python
state = {
    "notification_id": "N003",
    "notification_text": "Thông báo ...",
    "priority": "Trung bình",
    "summary": "Tóm tắt ngắn ...",
    "learning_signals": [],
    "user_feedback": {
        "vote": "downvote",
        "summary_feedback": "Tóm tắt thiếu phần yêu cầu mang dụng cụ.",
        "wants_more_detail": True,
    },
}

out = handle_feedback(state)
```

Kết quả thường có:
- `feedback_status="summary_feedback_recorded"`
- `requested_summary_refresh=True` (nếu `wants_more_detail=True` hoặc có `summary_feedback`)

### Log learning signals (JSONL)

- Mặc định ghi vào: `api/data/learning_signals.jsonl` (tạo thư mục nếu chưa có).
- Nếu bạn muốn đổi vị trí log:

```python
from pathlib import Path
from nodes.feedback import handle_feedback

out = handle_feedback(state, log_path=Path("somewhere/learning_signals.jsonl"))
```

Ghi chú:
- Ghi JSONL có **file lock** (đuôi `.lock`) để tránh race khi nhiều request ghi cùng lúc.
- Các trường text dài sẽ được clip theo giới hạn trong `constants.py`.

### Cấu trúc module nội bộ

- `node.py`: triển khai `handle_feedback`
- `constants.py`: hằng số priority, limits, keywords
- `types.py`: `FeedbackState`, `UserFeedbackPayload`, `Vote`
- `paths.py`: default path + lock path
- `utils.py`: normalize/clip/detect helpers
- `storage.py`: append JSONL + file lock
- `learning.py`: build learning record + extract extra fields

