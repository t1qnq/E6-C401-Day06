"""
Muc dich file: Node summarize_notification.

Can thuc hien:
- Nhan noi dung thong bao (text hoac text tu file).
- Tom tat thanh 3-4 bullet points gon, de doc.
- Trich xuat entity quan trong: thoi gian, dia diem, so tien.
- Co fallback khi noi dung mo/khong du thong tin.
- Tra summary + entities vao state.
"""

def summarize_brief(state: dict) -> dict:
    """Mock node tóm tắt sơ lược (1 câu)"""
    print("--- [Node] Summarize Brief Running ---")
    return {"brief_summary": "Họp phụ huynh cuối kỳ vào 19h tối nay."}

def summarize_detailed(state: dict) -> dict:
    """Mock node tóm tắt chi tiết (nhiều gạch đầu dòng)"""
    print("--- [Node] Summarize Detailed Running ---")
    return {
        "detailed_summary": [
            "Báo cáo kết quả học tập kỳ 2",
            "Phổ biến kế hoạch hè",
            "Đóng quỹ lớp đợt cuối"
        ]
    }
