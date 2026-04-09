# Individual reflection — Quách Ngọc Quang (2A202600285)

## 1. Role
Team Lead & LangGraph Architect. Phụ trách thiết kế kiến trúc tổng thể của LangGraph, định nghĩa State, kiểm soát luồng dữ liệu (Data Flow) và quản lý tiến độ chung của nhóm.

## 2. Đóng góp cụ thể
- Thiết kế và lập trình cấu trúc luồng LangGraph với 2 giai đoạn: Auto-Push (Tự động) và On-demand (Theo yêu cầu).
- Định nghĩa `AgentState` chi tiết để lưu trữ metadata từ các module AI (chẳng hạn như `priority_explainability`, `entities`, `summary_json`).
- Triển khai cơ chế vòng lặp phản hồi (Feedback Loop) trên LangGraph và chèn điểm rẽ nhánh xác nhận thủ công của giáo viên (Manual Fallback).
- Lập trình file `graph.py` chạy end-to-end, đảm nhiệm vai trò liên kết toàn bộ các Node của các thành viên khác lại với nhau một cách mượt mà.
- Tự động hóa việc tạo sơ đồ kiến trúc hệ thống bằng Mermaid (`generate_graph_viz.py`).

## 3. SPEC mạnh/yếu
- **Mạnh nhất:** Cơ chế Graceful Degradation và Fallback. Nhóm đã lường trước kịch bản AI thiếu tự tin (Low Confidence) và thiết lập cơ chế "Manual Required" bắt buộc trả về cho giáo viên quyết định, thay vì để hệ thống đoán bừa dẫn đến hậu quả nghiêm trọng.
- **Yếu nhất:** Đánh giá mức độ tải hệ thống. Việc sử dụng các module OCR có thể gây ngẽn (bottleneck) nếu có luồng hàng ngàn văn bản vào cùng lúc mà không có cơ chế xếp hàng đợi (Queue) chuyên dụng.

## 4. Đóng góp khác
- Review code và refactor toàn bộ dự án từ các tệp script rời rạc thành một dự án có kiến trúc "Service-Oriented" chuyên nghiệp (chia rõ folder `core/`, `services/`, `nodes/`, `config/`).
- Sửa lỗi tương thích giữa các Node trong tích tắc (Ví dụ: fix lỗi runtime ngớ ngẩn do signature thay đổi từ hàm gốc `parse_attachment` sang lớp vỏ bọc `parse_attachment_node`).

## 5. Điều học được
Trước Hackathon, thiết kế AI với tôi chỉ dừng lại ở các Chatbot đơn thuần. Qua dự án Notifications này, tôi nhận ra sức mạnh thực thụ của LangGraph là quản lý cấu trúc dữ liệu (State Machine). Việc định hình State tốt, kết hợp logic rẽ nhánh có điều kiện (Conditional Edges), là nền tảng cốt lõi để các Agent không bao giờ bị "chết" hay rối tung giữa một rừng tính năng.

## 6. Nếu làm lại
Sẽ tập trung thống nhất thật kỹ các lược đồ dữ liệu (như Pydantic models hay TypedDict) làm chuẩn đầu ra/đầu vào cho từng thành viên sớm hơn 1 ngày. Điều này sẽ giúp việc tôi ráp nối code thành Graph sau này trơn tru hơn thay vì mất vài tiếng ngồi khớp lại các Keys dữ liệu (vd `attachment` vs `attachments`).

## 7. AI giúp gì / AI sai gì
- **Giúp:** AI (Gemini/Claude) đóng vai trò một "Co-architect" tuyệt vời, giúp tôi refactor code nhanh chóng từ cấu trúc Mock-up nguyên thủy sang kiến trúc Production-ready. Đặc biệt, nó dựng code Mermaid để vẽ biểu đồ cực kỳ trực quan tiết kiệm hàng giờ căn chỉnh.
- **Sai/mislead:** AI khá cứng nhắc và thiếu bao quát khi ráp nối code. Khi update node OCR, nó tự ý gọi trực tiếp hàm thực thi `parse_attachment` thay vì gọi lớp vỏ LangGraph `parse_attachment_node`, dẫn đến sập ứng dụng. Ngoài ra ở sơ đồ Mermaid, AI cố vẽ các khung Subgraph rất "academic" làm sơ đồ rối rắm, buộc tôi phải ép nó xóa bỏ các Subgraph đó đi cho đồ thị thoáng hơn. 
  **Bài học:** Có AI hỗ trợ không có nghĩa là buông thói quen đọc kỹ function signature; con người luôn cần làm người phán xử cuối cùng.
