# Phân công dự án — Nhóm E06
**7 thành viên • Platform: LangGraph • Trình độ: Beginner**

## KIẾN TRÚC TỔNG QUAN

**Luồng hệ thống:**
`[ Frontend (UI) ]` ➔ `[ LangGraph Agent ]` ➔ `[ School API / Data ]`

**Luồng LangGraph (Các Node):**
`[ Prioritization Node ]` ➔ `[ Summarizer Node ]` ➔ `[ Feedback Node ]`

---

## PHÂN CÔNG CHI TIẾT THEO THÀNH VIÊN

### 1. Quang
**Vai trò:** Team Lead · LangGraph Architect  
**Phân hệ:** `Backend · Core Agent`  
* Thiết kế graph tổng thể trong LangGraph (nodes, edges, state schema).
* Định nghĩa `AgentState` — lưu notification, priority, summary, feedback.
* Kết nối các node: prioritization ➔ summarizer ➔ feedback loop.
* Review code, merge nhánh, hỗ trợ các thành viên debug LangGraph.
> **Deliverable:** File `graph.py` — LangGraph graph hoàn chỉnh có thể chạy end-to-end.

### 2. Tuấn
**Vai trò:** AI Node Developer · Prioritization  
**Phân hệ:** `Backend · LangGraph Node`  
* Viết node `prioritize_notification` trong LangGraph.
* Prompt GPT-4o mini để phân loại Cao / Trung bình / Thấp.
* Xử lý từ khóa đặc thù Vinschool (học phí, họp, ngoại khóa...).
* Viết unit test cho node với các kịch bản Happy/Failure path.
> **Deliverable:** File `nodes/prioritizer.py` + test cases.

### 3. Hải
**Vai trò:** AI Node · Summarizer  
**Phân hệ:** `Backend · LangGraph Node`  
* Viết node `summarize_notification`.
* Xử lý text + tóm tắt thành 3–4 bullet points.
* Trích xuất entity: thời gian, địa điểm, số tiền.
* Fallback khi file mờ / không đọc được.
> **Deliverable:** File `nodes/summarizer.py`.

### 4. Long
**Vai trò:** File Processing · OCR  
**Phân hệ:** `Backend · File Handler`  
* Viết node `parse_attachment`.
* Xử lý PDF, ảnh ➔ text (dùng PyPDF2 / pytesseract).
* Kiểm tra chất lượng file, kích hoạt graceful fallback.
* Test với file mờ, file lỗi định dạng.
> **Deliverable:** File `nodes/file_parser.py`.

### 5. Dũng
**Vai trò:** API Integration · Data Layer  
**Phân hệ:** `Backend · API Trường`  
* Kết nối / mock API dữ liệu học sinh & thông báo từ hệ thống trường.
* Viết schema dữ liệu đầu vào (notification payload, student profile).
* Xây dựng `data_loader.py` — load & normalize dữ liệu cho graph.
* Nếu chưa có API thật: tạo mock data JSON đầy đủ để team test.
> **Deliverable:** File `api/data_loader.py` + mock data JSON.

### 6. Thuận
**Vai trò:** Feedback Loop · Learning Signal  
**Phân hệ:** `Backend · Human-in-loop`  
* Viết node `handle_feedback`.
* Lưu feedback upvote/downvote của phụ huynh.
* Cập nhật priority dựa theo correction của người dùng.
* Ghi log learning signal để fine-tune sau.
> **Deliverable:** File `nodes/feedback.py`.

### 7. Huy
**Vai trò:** Frontend · UI / Demo  
**Phân hệ:** `Frontend · Demo`  
* Xây dựng giao diện Streamlit / Gradio kết nối với LangGraph.
* Hiển thị thông báo với badge màu: 🔴 Cao / 🟡 TB / 🟢 Thấp.
* Nút Upvote / Downvote ➔ gửi feedback về graph.
* Demo end-to-end cho 4 user story paths.
> **Deliverable:** File `app.py` (Streamlit/Gradio).

---

## 3 GIAI ĐOẠN LÀM VIỆC

### Giai đoạn 1 · Setup
* Quang setup LangGraph project, định nghĩa State.
* Dũng tạo mock data JSON.
* Cả team đọc tài liệu LangGraph cơ bản.

### Giai đoạn 2 · Build nodes
* Tuấn, Hải, Long, Thuận build node song song.
* Quang kết nối các node thành graph hoàn chỉnh.
* Test từng node độc lập.

### Giai đoạn 3 · Demo
* Huy build UI kết nối graph.
* Dũng kết nối API thật (nếu có).
* Cả team test 4 user story paths.