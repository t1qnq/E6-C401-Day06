"""
Muc dich file: Node handle_feedback.

Can thuc hien:
- Nhan feedback tu phu huynh (upvote/downvote).
- Cap nhat priority theo correction cua nguoi dung.
- Luu learning signal/log de theo doi va fine-tune sau.
- Tra priority moi va thong tin log vao state.
"""

def handle_feedback(state: dict) -> dict:
    """Mock node phản hồi từ người dùng"""
    print("--- [Node] Handle Feedback Running ---")
    feedback = state.get("human_correction", "No feedback")
    return {"is_resolved": True}
