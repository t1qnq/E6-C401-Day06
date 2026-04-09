"""
Muc dich file: Node parse_attachment.

Can thuc hien:
- Nhan file dinh kem tu notification.
- Ho tro doc PDF/anh va chuyen sang text (OCR neu can).
- Danh gia chat luong file, phat hien file mo hoac loi dinh dang.
- Thuc hien graceful fallback neu parse that bai.
- Dua attachment_text va parser status vao state.
"""

def parse_attachment(state: dict) -> dict:
    """Mock node phân tích tệp đính kèm OCR"""
    print("--- [Node] Parse Attachment Running ---")
    attachments = state.get("attachments", [])
    file_name = attachments[0] if attachments else "no_file"
    return {"extracted_text": f"Scanned from: {file_name}", "file_type": "pdf"}
