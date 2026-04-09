import json
import os
from typing import List, Optional
from schemas import NotificationPayload, StudentProfile, ReceiverScope

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
    
    def get_notifications_by_category(self, category: str) -> List[NotificationPayload]:
        """Lọc thông báo theo loại (ví dụ: chỉ lấy thông báo khẩn cấp)"""
        return [
            NotificationPayload(**n) 
            for n in self._data["notifications"] 
            if n["category"] == category
        ]

    def get_notifications_for_student(self, student_id: str) -> List[NotificationPayload]:
        student = self.get_student_by_id(student_id)
        if not student:
            return []

        student_class = student.student_class # Ví dụ: "12A1"
        student_grade = student_class[:2]    # Ví dụ: "12"

        relevant_notifications = []
        
        for n_dict in self._data["notifications"]:
            n = NotificationPayload(**n_dict)
            
            # Kiểm tra quyền nhận thông báo
            is_relevant = (
                n.receiver_scope == ReceiverScope.ALL or
                (n.receiver_scope == ReceiverScope.GRADE and student_grade in n.receiver_ids) or
                (n.receiver_scope == ReceiverScope.CLASS and student_class in n.receiver_ids) or
                (n.receiver_scope == ReceiverScope.INDIVIDUAL and student_id in n.receiver_ids)
            )
            
            if is_relevant:
                relevant_notifications.append(n)
                
        return relevant_notifications

# Singleton instance để sử dụng trong toàn bộ project
data_loader = DataLoader()