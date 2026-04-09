import json
import random
from faker import Faker
from datetime import datetime, timedelta

fake = Faker(['vi_VN']) # Sử dụng tiếng Việt

def generate_mock_db(num_students=50, num_notifications=100):
    data = {
        "students": [],
        "notifications": []
    }

    # 1. Tạo danh sách học sinh
    classes = [f"{grade}{letter}" for grade in range(1, 13) for letter in ["A1", "A2", "B1"]]
    categories = ["finance", "academic", "extracurricular", "emergency", "health"]
    
    for i in range(num_students):
        stu_id = f"STU{str(i+1).zfill(3)}"
        data["students"].append({
            "student_id": stu_id,
            "full_name": fake.name(),
            "class": random.choice(classes),
            "parent_id": f"PAR{str(i+1).zfill(3)}",
            "interests": random.sample(["Math", "Music", "Football", "Art", "Coding"], k=2),
            "history_priority_engagement": {
                cat: random.choice(["high", "medium", "low"]) for cat in categories
            }
        })

    # 2. Tạo danh sách thông báo với Template
    notif_templates = [
        {
            "category": "finance",
            "sender": "Phòng Tài vụ",
            "titles": ["Thông báo học phí tháng {month}", "Nhắc nhở đóng phí nội trú", "Hóa đơn dịch vụ xe đưa đón"],
            "content_fmt": "Kính gửi phụ huynh, vui lòng hoàn tất khoản phí {amount} VNĐ cho học sinh trước ngày {date}. Nội dung chuyển khoản: {stu_id} - {name}."
        },
        {
            "category": "academic",
            "sender": "Giáo viên Chủ nhiệm",
            "titles": ["Kết quả kiểm tra giữa kỳ", "Lịch ôn tập học kỳ", "Thông báo họp phụ huynh"],
            "content_fmt": "Thông báo về việc {action} vào lúc {time} ngày {date} tại {location}. Kính mời phụ huynh sắp xếp thời gian tham dự."
        },
        {
            "category": "emergency",
            "sender": "Ban Giám Hiệu",
            "titles": ["Thông báo nghỉ học khẩn cấp", "Cảnh báo an toàn đường bộ"],
            "content_fmt": "Do điều kiện {reason}, nhà trường thông báo học sinh toàn trường sẽ nghỉ học vào ngày {date}. Lịch học bù sẽ được gửi sau."
        },
        {
            "category": "extracurricular",
            "sender": "Đội Thiếu niên/Đoàn Thanh niên",
            "titles": ["Đăng ký tham quan dã ngoại", "Giải bóng đá học sinh", "Hội diễn văn nghệ"],
            "content_fmt": "Nhà trường tổ chức hoạt động {activity} tại {location}. Phí tham dự là {amount} VNĐ. Hạn đăng ký cuối cùng là {date}."
        }
    ]

    for i in range(num_notifications):
        template = random.choice(notif_templates)
        notif_id = f"NOTIF_{str(i+1).zfill(4)}"
        
        # Tạo ngày ngẫu nhiên trong 30 ngày qua
        days_ago = random.randint(0, 30)
        timestamp = (datetime.now() - timedelta(days=days_ago)).isoformat()
        
        # Điền dữ liệu vào template
        target_student = random.choice(data["students"])
        content = template["content_fmt"].format(
            month=random.randint(1, 12),
            amount=f"{random.randint(5, 50) * 100000:,}",
            date=(datetime.now() + timedelta(days=random.randint(1, 10))).strftime("%d/%m/%Y"),
            stu_id=target_student["student_id"],
            name=target_student["full_name"],
            action=random.choice(["họp phụ huynh", "kiểm tra chất lượng", "đổi lịch học"]),
            time="08:00",
            location=random.choice(["Hội trường A", "Phòng họp 2", "Sân vận động"]),
            reason=random.choice(["thời tiết xấu", "sửa chữa điện", "sự cố kỹ thuật"]),
            activity=random.choice(["cắm trại", "thăm bảo tàng", "thi bơi lội"])
        )

        data["notifications"].append({
            "id": notif_id,
            "sender": template["sender"],
            "timestamp": timestamp,
            "title": random.choice(template["titles"]).format(month=random.randint(1, 12)),
            "content": content,
            "attachments": [{"type": "pdf", "url": f"https://api.school.edu/files/{notif_id}.pdf"}] if random.random() > 0.5 else [],
            "category": template["category"]
        })

    # 3. Lưu ra file
    with open('api/data/mock_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Đã tạo xong {num_students} học sinh và {num_notifications} thông báo!")

if __name__ == "__main__":
    generate_mock_db(num_students=100, num_notifications=500)