import json
import os
from typing import List, Optional
from schemas import NotificationPayload, StudentProfile

class DataLoader:
    def __init__(self, mock_path: str = "data/mock_data.json"):
        self.mock_path = mock_path
        self._data = self._load_mock_file()

    def _load_mock_file(self):
        if os.path.exists(self.mock_path):
            with open(self.mock_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"students": [], "notifications": []}

    def get_student_by_id(self, student_id: str) -> Optional[StudentProfile]:
        """Lấy thông tin học sinh - Mock API Call"""
        student_data = next((s for s in self._data["students"] if s["student_id"] == student_id), None)
        if student_data:
            return StudentProfile(**student_data)
        return None

    def fetch_latest_notifications(self) -> List[NotificationPayload]:
        """Lấy danh sách thông báo mới - Mock API Call"""
        return [NotificationPayload(**n) for n in self._data["notifications"]]

    def normalize_payload(self, raw_data: dict) -> NotificationPayload:
        """
        Hàm chuẩn hóa dữ liệu từ nhiều nguồn khác nhau 
        (Trường A gửi JSON khác Trường B nhưng vào Graph phải giống nhau)
        """
        return NotificationPayload(**raw_data)

# Singleton instance để sử dụng trong toàn bộ project
data_loader = DataLoader()