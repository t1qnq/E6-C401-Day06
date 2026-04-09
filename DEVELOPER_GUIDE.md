# 🚀 Hướng dẫn Lập trình (Developer Guide) - Nhóm E06

Tài liệu này hướng dẫn các thành viên trong nhóm cách bắt đầu viết code thực tế (logic AI, Prompt LLM) vào hệ thống LangGraph đã được dựng sẵn.

---

## 1. Cấu trúc Hệ thống Hiện tại
Core Graph (bộ não điều phối) nằm ở `graph.py` đã được team lead (Quang) cấu hình xong với luồng **2 Giai đoạn**:

*   **Pha 1 (Tự động):** Nhận tin từ giáo viên ➔ Quét file (OCR) ➔ Đánh giá mức độ khẩn cấp (Ưu tiên) ➔ Tạo tóm tắt siêu ngắn (1 dòng).
*   **Pha 2 (Tương tác):** Khi phụ huynh bấm "Xem chi tiết" ➔ Tóm tắt chi tiết (nhiều gạch đầu dòng) ➔ Trích xuất sự kiện để đặt lịch ➔ Phản hồi.

Bạn **KHÔNG CẦN CHỈNH SỬA** file `graph.py` nữa, trừ khi muốn đổi cấu trúc luồng. Mọi dữ liệu trung gian được lưu trong `AgentState`.

---

## 2. Nhiệm vụ của từng thành viên (Thay thế Mock Functions)

Các file trong thư mục `nodes/` hiện tại đang chứa các "Mã giả" (Mock Functions) để giữ chỗ. Nhiệm vụ của các bạn là vào file tương ứng, xoá mã giả và viết code của mình (Prompt gọi OpenAI, code xử lý file...) vào đó.

### 🐍 A. Đội AI & RAG (Tuấn, Hải, Long, Dũng)
Sử dụng thư viện `langchain_openai` hoặc API trực tiếp để xử lý văn bản:

1.  **Long - `nodes/file_parser.py`:**
    *   **Input:** `state["attachments"]` (Danh sách tên file/đường dẫn).
    *   **Việc cần làm:** Viết code đọc file PDF/Image (dùng `PyPDF2`, `pdfplumber`, `pytesseract`...), chuyển thành text.
    *   **Output:** Gán text vào `{"extracted_text": "..."}` rồi return.

2.  **Tuấn - `nodes/prioritizer.py`:**
    *   **Input:** `state["teacher_note"]` và `state["extracted_text"]`.
    *   **Việc cần làm:** Gọi LLM (GPT-4o-mini), truyền prompt yêu cầu LLM phân loại mức độ ưu tiên của tin nhắn này (Cao/Trung Bình/Thấp) và trả về điểm tự tin (0.0 -> 1.0).
    *   **Output:** Return `{"priority_level": "...", "priority_confidence": 0.9}`.

3.  **Hải - `nodes/summarizer.py`:** File này có 2 hàm cần xử lý!
    *   **Hàm 1: `summarize_brief`:** Gọi LLM tóm tắt siêu ngắn gọn toàn bộ `extracted_text` thành 1 câu duy nhất. Trả về `{"brief_summary": "..."}`.
    *   **Hàm 2: `summarize_detailed`:** Gọi LLM tóm tắt chi tiết thành 2-4 gạch đầu dòng theo giọng điệu thân thiện. Trả về `{"detailed_summary": ["...", "..."]}`.

4.  **Dũng/Quang - `nodes/scheduler.py` (Nằm trong `graph.py` hiện tại hoặc tạo mới):**
    *   **Input:** `state["extracted_text"]`.
    *   **Việc cần làm:** Gọi LLM với output schema (JSON) yêu cầu trích xuất "Tên sự kiện" và "Thời gian" từ thông báo.
    *   **Output:** Return `{"schedule_events": [{"event": "...", "date": "..."}]}`.

### 📱 B. Đội UI & Tích hợp (Thuận, Huy)
1.  **Thuận - `nodes/feedback.py`:**
    *   Nhận `state["human_correction"]` (Phản hồi từ UI: Like/Dislike, sửa đổi).
    *   In log hoặc lưu vào database (JSON mock) để làm Learning Signal.
2.  **Huy - `app.py`:**
    *   Sử dụng Streamlit hoặc Gradio.
    *   Tạo 2 màn hình (Hoặc 2 khu vực):
        *   **Màn hình 1:** Box tin nhắn cảnh báo ngắn (Chứa `priority_level` có màu + `brief_summary`) kèm nút **"Xem chi tiết"**.
        *   **Màn hình 2:** Khi bấm "Xem chi tiết", hiển thị `detailed_summary` và danh sách `schedule_events` để phụ huynh có thể bấm "Lưu vào lịch".

---

## 3. Cách chạy và Kiểm thử (Testing)

1.  Mở file `.env` (copy từ `.env.example`).
2.  Điền `OPENAI_API_KEY` của nhóm vào.
3.  Cài đặt các gói: `pip install -r requirements.txt`.
4.  Mở terminal, chạy lệnh:
    ```bash
    python graph.py
    ```
5.  Kiểm tra terminal xem các Node của bạn đã in ra kết quả thật (thay vì kết quả giả định) chưa.

> [!TIP]
> **Best Practice cho Hackathon:** Hãy bắt đầu bằng những Prompt rất đơn giản để đảm bảo luồng thông tin đi thông suốt từ đầu đến cuối trước. Khi hệ thống đã chạy trơn tru, hãy dành thời gian "vuốt ve" (fine-tune) lại câu từ của Prompt cho hay hơn. Chúc team E06 code vui vẻ!
