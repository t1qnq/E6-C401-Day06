"""
Muc dich file: Node prioritize_notification.

Can thuc hien:
- Nhan notification dau vao tu state.
- Phan loai muc do uu tien: Cao / Trung binh / Thap.
- Xu ly keyword dac thu truong hoc (hoc phi, hop, ngoai khoa, deadline...).
- Tra ket qua priority vao state de node sau su dung.
- Viet test happy path va failure path cho node nay.
"""

def prioritize_notification(state: dict) -> dict:
    """Mock node phân loại độ ưu tiên"""
    print("--- [Node] Prioritize Notification Running ---")
    return {"priority_level": "High", "priority_confidence": 0.9}
