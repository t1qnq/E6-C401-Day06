import json
import random
import sys
from faker import Faker
from datetime import datetime, timedelta
from pathlib import Path

# Cấu hình đường dẫn
main_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(main_dir))

from api.schemas import ReceiverScope

fake = Faker(['vi_VN'])

def generate_mock_db(num_students=100, num_notifications=300):
    data = {
        "students": [],
        "notifications": []
    }

    # 1. TẠO DATA HỌC SINH
    classes = [f"{grade}{letter}" for grade in range(10, 13) for letter in ["A1", "A2", "B1"]]
    categories_interest = ["finance", "academic", "extracurricular", "emergency", "health", "discipline"]
    
    for i in range(num_students):
        stu_id = f"STU{str(i+1).zfill(3)}"
        data["students"].append({
            "student_id": stu_id,
            "full_name": fake.name(),
            "class": random.choice(classes),
            "parent_id": f"PAR{str(i+1).zfill(3)}",
            "interests": random.sample(["Math", "Physics", "Music", "Football", "Art", "Coding", "Esports"], k=2),
            "history_priority_engagement": {
                cat: random.choice(["high", "medium", "low"]) for cat in categories_interest
            }
        })

    # 2. KHAI BÁO TEMPLATES VỚI LOGIC RÀNG BUỘC CHẶT CHẼ
    notif_templates = [
        # --- TÀI CHÍNH (Chỉ cá nhân / Khối) ---
        {
            "category": "finance", "sender": "Phòng Tài vụ",
            "allowed_scopes": [ReceiverScope.INDIVIDUAL], "is_group_event": False,
            "titles": ["Thông báo học phí tháng {month}", "Hóa đơn dịch vụ xe đưa đón", "Nhắc nhở hoàn thiện phí nội trú"],
            "content_fmt": "Kính gửi phụ huynh, nhà trường thông báo khoản phí {amount} VNĐ cho học sinh {names} ({stu_ids}). Vui lòng thanh toán trước ngày {date}."
        },
        {
            "category": "finance", "sender": "Phòng Tài vụ",
            "allowed_scopes": [ReceiverScope.ALL, ReceiverScope.GRADE], "is_group_event": False,
            "titles": ["Chính sách miễn giảm học phí học kỳ II", "Điều chỉnh mức phí ăn trưa"],
            "content_fmt": "Kính gửi quý phụ huynh, nhà trường xin thông báo về việc cập nhật chính sách tài chính mới áp dụng từ {date}. Chi tiết vui lòng xem tệp đính kèm."
        },
        
        # --- HỌC THUẬT (Lớp / Khối / Cá nhân bị kém) ---
        {
            "category": "academic", "sender": "Giáo viên Chủ nhiệm",
            "allowed_scopes": [ReceiverScope.CLASS, ReceiverScope.GRADE], "is_group_event": False,
            "titles": ["Lịch kiểm tra giữa kỳ", "Thông báo họp phụ huynh định kỳ", "Kế hoạch ôn tập chuyên đề"],
            "content_fmt": "Kính mời quý phụ huynh sắp xếp tham dự sự kiện {action} vào lúc {time} ngày {date} tại {location}. Sự có mặt của quý vị rất quan trọng."
        },
        {
            "category": "academic", "sender": "Ban Giám Hiệu",
            "allowed_scopes": [ReceiverScope.INDIVIDUAL], "is_group_event": False,
            "titles": ["Cảnh báo kết quả học tập", "Thư mời phụ huynh làm việc riêng"],
            "content_fmt": "Kính gửi phụ huynh em {names} ({stu_ids}). Hiện tại kết quả môn {subject} của em đang ở mức báo động. Kính mong phụ huynh phối hợp với nhà trường để đôn đốc."
        },

        # --- KỶ LUẬT / SỰ CỐ (Đặc biệt: Hỗ trợ nhóm học sinh xô xát) ---
        {
            "category": "discipline", "sender": "Ban Giám thị",
            "allowed_scopes": [ReceiverScope.INDIVIDUAL], "is_group_event": True, # Bật cờ sự kiện nhóm
            "titles": ["Thông báo xử lý vi phạm kỷ luật", "Mời phụ huynh lên làm việc do sự cố trên lớp"],
            "content_fmt": "Nhà trường vô cùng tiếc khi thông báo về việc nhóm học sinh gồm: {names} đã có hành vi {bad_action} vào ngày {date}. Kính mời phụ huynh các em có mặt lúc {time} tại {location} để giải quyết."
        },

        # --- Y TẾ & SỨC KHỎE ---
        {
            "category": "health", "sender": "Phòng Y tế",
            "allowed_scopes": [ReceiverScope.INDIVIDUAL], "is_group_event": False,
            "titles": ["Thông báo sức khỏe học sinh", "Học sinh có biểu hiện sốt tại trường"],
            "content_fmt": "Thông báo khẩn: Học sinh {names} đang có biểu hiện {symptom} tại Phòng Y tế. Kính mong phụ huynh phản hồi hoặc đến đón em sớm nhất có thể."
        },
        {
            "category": "health", "sender": "Phòng Y tế",
            "allowed_scopes": [ReceiverScope.ALL, ReceiverScope.GRADE], "is_group_event": False,
            "titles": ["Kế hoạch khám sức khỏe định kỳ", "Tiêm phòng dịch cúm mùa"],
            "content_fmt": "Nhà trường tổ chức khám sức khỏe tổng quát vào ngày {date}. Đề nghị phụ huynh nhắc nhở các em ăn uống đầy đủ trước khi tiêm."
        },

        # --- KHẨN CẤP / CHUNG TỪ BGH (Toàn trường) ---
        {
            "category": "emergency", "sender": "Ban Giám Hiệu",
            "allowed_scopes": [ReceiverScope.ALL], "is_group_event": False,
            "titles": ["Nghỉ học khẩn cấp do thời tiết xấu", "Sự cố mất điện toàn trường"],
            "content_fmt": "Do tình hình {reason}, nhà trường quyết định cho toàn bộ học sinh nghỉ học ngày hôm nay {date}. Các lớp sẽ chuyển sang hình thức học online."
        },

        # --- NGOẠI KHÓA ---
        {
            "category": "extracurricular", "sender": "Đoàn Thanh niên",
            "allowed_scopes": [ReceiverScope.ALL, ReceiverScope.CLASS], "is_group_event": False,
            "titles": ["Lễ hội chào tân học sinh", "Đăng ký giải bóng đá cấp trường", "Dã ngoại mùa thu"],
            "content_fmt": "Chương trình {activity} sẽ diễn ra tại {location}. Phí tham gia (nếu có): {amount} VNĐ. Hạn chót đăng ký là ngày {date}."
        }
    ]

    # 3. SINH THÔNG BÁO DỰA TRÊN LOGIC ĐÃ ĐỊNH NGHĨA
    for i in range(num_notifications):
        template = random.choice(notif_templates)
        notif_id = f"NOTIF_{str(i+1).zfill(4)}"
        
        # Thời gian ngẫu nhiên
        days_ago = random.randint(0, 30)
        timestamp = (datetime.now() - timedelta(days=days_ago)).isoformat()
        
        # CHỌN SCOPE HỢP LÝ TỪ TEMPLATE
        scope = random.choice(template["allowed_scopes"])
        receiver_ids = []
        
        target_names = ""
        target_ids = ""

        # XỬ LÝ LOGIC NGƯỜI NHẬN DỰA THEO SCOPE
        if scope == ReceiverScope.GRADE:
            receiver_ids = [random.choice(["10", "11", "12"])]
        elif scope == ReceiverScope.CLASS:
            receiver_ids = [random.choice(classes)]
        elif scope == ReceiverScope.INDIVIDUAL:
            # Nếu là sự kiện nhóm (VD: đánh nhau)
            if template.get("is_group_event"):
                num_involved = random.randint(2, 4) # 2 đến 4 em tham gia
                involved_students = random.sample(data["students"], k=num_involved)
                receiver_ids = [s["student_id"] for s in involved_students]
                target_names = ", ".join([s["full_name"] for s in involved_students])
                target_ids = ", ".join([s["student_id"] for s in involved_students])
            else:
                # Sự kiện cá nhân bình thường
                target_student = random.choice(data["students"])
                receiver_ids = [target_student["student_id"]]
                target_names = target_student["full_name"]
                target_ids = target_student["student_id"]

        # Điền dữ liệu động vào nội dung
        content = template["content_fmt"].format(
            month=random.randint(1, 12),
            amount=f"{random.randint(5, 50) * 100000:,}",
            date=(datetime.now() + timedelta(days=random.randint(1, 10))).strftime("%d/%m/%Y"),
            names=target_names,
            stu_ids=target_ids,
            action=random.choice(["họp phụ huynh", "kiểm tra chất lượng", "đổi lịch học"]),
            time=random.choice(["08:00", "14:30", "18:00"]),
            location=random.choice(["Hội trường A", "Phòng họp Ban Giám Hiệu", "Sân vận động", "Phòng Y tế"]),
            reason=random.choice(["bão lũ nghiêm trọng", "đứt cáp điện ngầm", "lụt cục bộ"]),
            activity=random.choice(["cắm trại sinh thái", "thăm bảo tàng lịch sử", "thi văn nghệ"]),
            subject=random.choice(["Toán", "Vật Lý", "Hóa Học", "Tiếng Anh"]),
            bad_action=random.choice(["xô xát đánh nhau", "sử dụng điện thoại trong giờ", "trốn tiết nhiều lần"]),
            symptom=random.choice(["sốt cao trên 39 độ", "đau bụng dữ dội", "phát ban ngoài da"])
        )

        data["notifications"].append({
            "id": notif_id,
            "sender": template["sender"],
            "timestamp": timestamp,
            "title": random.choice(template["titles"]).format(month=random.randint(1, 12)),
            "content": content,
            "receiver_scope": scope.value,
            "receiver_ids": receiver_ids,
            "attachments": [{"type": "pdf", "url": f"https://api.school.edu/files/{notif_id}.pdf"}] if random.random() > 0.7 else [],
            "category": template["category"]
        })

    # 4. LƯU FILE JSON
    output_path = main_dir / "api" / "data" / "mock_data.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Đã tạo xong {num_students} học sinh và {num_notifications} thông báo!")
    print(f"File được lưu tại: {output_path}")

if __name__ == "__main__":
    generate_mock_db(num_students=100, num_notifications=300)