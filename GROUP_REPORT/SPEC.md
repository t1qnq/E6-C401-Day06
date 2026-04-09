# SPEC — Nhóm E06 - C401

**Track:** Vinschool | **Đối tượng:** Phụ huynh

---

## Bối Cảnh

**User:** Phụ huynh nhận thông báo

**Pain Points:**
- Phụ huynh mong muốn truy cập nhanh về thông tin học sinh và các hoạt động của nhà trường.
- Thông báo nhiều, không có phân loại mức độ ưu tiên (priority).
- Flow cần feedback của người dùng nếu đề xuất/file thông tin sai.

**Problem Statement:**
Phụ huynh gặp khó khăn trong việc nắm bắt nhanh và thường xuyên những thông tin quan trọng do có quá nhiều thông báo, thiếu phân loại mức độ ưu tiên (priority), đặc biệt là khi thông báo được gửi dưới dạng file đính kèm không có tính năng xem trước.

---

## 1. AI Product Canvas

### Value (Giá trị)

- **User & Pain point:** Phụ huynh bị quá tải thông báo, khó nắm bắt ý chính, tin nhắn trôi nhanh; hỏi lại giáo viên thì chưa chắc nhận được câu trả lời sớm.
- **Augmentation (Giải pháp):** AI tự động tóm tắt ý chính của văn bản/tệp đính kèm và phân loại mức độ ưu tiên (Cao / Trung bình / Thấp). Hỗ trợ hỏi đáp 24/7 dựa trên thông báo.

### Trust (Độ tin cậy)

- **Precision:** Đảm bảo độ chính xác cao trong việc trích xuất thực thể quan trọng (thời gian, địa điểm, số tiền).
- **Recovery:** Khi AI không thể xử lý (file mờ, nội dung thiếu logic), hệ thống tự động cảnh báo: *"Tôi không thể phân tích tài liệu này, vui lòng đọc bản gốc hoặc để tôi chuyển hướng sang giáo viên."*

### Feasibility (Tính khả thi)

- **Chi phí:** ~$0.005 / truy vấn (sử dụng GPT-4o mini)
- **Độ trễ (Latency):** < 3 giây để ra kết quả
- **Dependencies:** Cần API kết nối với hệ thống dữ liệu thông báo và hồ sơ học sinh của nhà trường

### Learning Signal (Tín hiệu học tập)

- Dữ liệu phản hồi (Feedback) của phụ huynh thông qua nút **"Báo cáo tóm tắt/phân loại sai"**.
- Sử dụng tỷ lệ "Recovery thành công" (hệ thống sửa sai sau khi nhận feedback) để đánh giá và fine-tune mô hình ở các chu kỳ sau.

---

## 2. User Stories × 4 Paths

### 2.1 Happy Path (Thành công trọn vẹn)

- **Kịch bản:** Phụ huynh nhận được thông báo về lịch họp khẩn dạng PDF.
- **Hệ thống:** Bot tự động gắn nhãn **[Ưu tiên Cao]** và hiển thị tóm tắt: *"Họp trực tuyến 19h tối nay về chương trình ngoại khóa mới"*.
- **Kết quả:** Phụ huynh nắm bắt thông tin trong 3 giây, bấm "Xác nhận tham gia" ngay trên UI.

### 2.2 Low-confidence Path (Độ tin cậy thấp — Cần can thiệp nhẹ)

- **Kịch bản:** Thông báo ngoại khóa có nhiều danh mục phức tạp. Bot gắn nhãn **[Ưu tiên Trung bình]** nhưng tóm tắt thiếu phần "dụng cụ cần mang".
- **Hệ thống:** Phụ huynh bấm *"Tóm tắt chi tiết hơn phần chuẩn bị"*. Bot truy xuất lại ngữ cảnh và bổ sung: *"Cần chuẩn bị giày thể thao và mũ lưỡi trai."*

### 2.3 Failure Path (Thất bại kỹ thuật — Graceful Degradation)

- **Kịch bản:** Trường gửi thông báo là một bức ảnh chụp bảng thông báo viết tay, bị mờ và nhòe.
- **Hệ thống:** Trình OCR/AI không thể đọc nội dung một cách tự tin. Bot kích hoạt Fallback: *"Rất tiếc, AI không thể phân tích ảnh này do chất lượng thấp. Vui lòng tải file để xem chi tiết."*

### 2.4 Correction Path (Chỉnh sửa và Học hỏi)

- **Kịch bản:** Bot phân loại nhầm thông báo *"Hạn chót nộp học phí"* thành **[Ưu tiên Thấp]**.
- **Hệ thống:** Phụ huynh chỉnh sửa lại thành **[Ưu tiên Cao]**. Hệ thống lưu Learning Signal này lại. Lần sau, mọi thông báo chứa từ khóa *"học phí/tài chính"* sẽ được tự động đẩy lên mức Cao.

---

## 3. Eval Metrics

| Metric (Chỉ số) | Threshold (Ngưỡng đạt) | Red Flag (Cảnh báo đỏ) |
|---|---|---|
| Độ chính xác phân loại ưu tiên | > 90% (Gắn nhãn đúng Cao/TB/Thấp) | < 80% (Nguy cơ phụ huynh lỡ việc gấp) |
| Tỷ lệ tóm tắt đúng ý chính | > 85% (Bao phủ đủ 80% Entity quan trọng) | < 75% (Phụ huynh vẫn phải đọc lại file gốc) |
| Độ trễ phản hồi (Latency) | < 3 giây (Thời gian load kết quả) | > 5 giây (Trải nghiệm tệ, gây ức chế) |

---

## 4. Top 3 Failure Modes

| Failure Mode | Trigger (Yếu tố kích hoạt) | Hậu quả | Mitigation (Biện pháp giảm thiểu) |
|---|---|---|---|
| **1. Nhận thức ngữ cảnh sai** | Thông báo chứa ngôn ngữ mơ hồ, từ ngữ chuyên môn đặc thù của Vinschool. | Bot phân loại ưu tiên sai hoặc tóm tắt thông tin bị hiểu nhầm (Hallucination). | Xây dựng bộ từ điển riêng (Custom Glossary). Kích hoạt cảnh báo "Low-confidence" yêu cầu con người duyệt nếu AI không chắc chắn. |
| **2. Lỗi xử lý tệp đính kèm** | Tệp đính kèm (PDF, Ảnh) bị lỗi định dạng, mã hóa hoặc chất lượng quá thấp. | Tính năng xem trước và tóm tắt tệp thất bại hoàn toàn. | Fallback sang thông báo cho phụ huynh biết không thể xử lý tệp và đề xuất tải xuống. |
| **3. Quá tải hệ thống** | Quá nhiều phụ huynh sử dụng tính năng cùng lúc trong thời gian cao điểm (ngay sau khi trường gửi thông báo chung). | Độ trễ (Latency) tăng vọt, vượt quá ngưỡng 5s. | Tăng cường tài nguyên tính toán (scaling up) hoặc áp dụng cơ chế hàng đợi (queueing) và thông báo độ trễ cho người dùng. |

---

## 5. ROI Kịch Bản

| Kịch bản | Giả định chính | Lợi ích & Tác động | Dự phóng ROI |
|---|---|---|---|
| **Conservative (Thận trọng)** | 20% phụ huynh sử dụng thường xuyên. Giảm 50% câu hỏi lặp lại trên group lớp. | Tiết kiệm ~0.8 phút/thông báo. Duy trì hệ thống vận hành ổn định. | **1.5x** |
| **Realistic (Thực tế)** | 60% phụ huynh sử dụng thường xuyên. Giảm 75% câu hỏi lặp lại gửi đến giáo viên. | Tiết kiệm trung bình 4 phút/tuần/phụ huynh. Giáo viên dôi dư 1–2h/tuần cho chuyên môn. | **4.0x** |
| **Optimistic (Lạc quan)** | 90% phụ huynh dùng. Không còn tình trạng miss thông báo đóng tiền/họp. | Tăng 15% sự hài lòng của phụ huynh (CSAT). Định vị Vinschool là trường học EdTech tiên phong. | **8.0x** |

---

## 6. Mini AI Spec 1 Trang

### Mục tiêu Sản phẩm

Giải quyết triệt để tình trạng quá tải thông tin của phụ huynh Vinschool bằng một luồng phân phối thông báo thông minh được sức mạnh bởi AI. Sản phẩm không thay thế giao tiếp giữa giáo viên - phụ huynh mà đóng vai trò **màng lọc (filter)** để tôn vinh các thông tin quan trọng nhất.

### Kiến trúc Tính năng Cốt lõi

**AI Prioritization Engine**
Mô hình tự động phân loại thông báo mới thành 3 luồng ưu tiên (🔴 Cao / 🟡 Trung bình / 🟢 Thấp) dựa trên phân tích ngữ nghĩa (Semantic Analysis) và lịch sử hành vi của người dùng.

**Smart Summarizer** *(Powered by GPT-4o mini)*
Trích xuất văn bản từ nội dung tin nhắn và tệp đính kèm (PDF / Word / Image), tổng hợp thành 3–4 gạch đầu dòng súc tích, bao hàm đầy đủ thời gian, địa điểm và hành động cần làm.

**Tự động điều phối thông tin**
Điều phối tài liệu thông báo cho phụ huynh dựa trên phân loại, tận dụng dữ liệu học sinh và tập dữ liệu thông báo do giáo viên cung cấp.

**Human-in-the-loop Feedback**
Giao diện cho phép phụ huynh đánh giá (Upvote / Downvote) chất lượng tóm tắt, tạo ra Learning Signal để liên tục tối ưu hóa mô hình.

### Cam kết Chất lượng (SLA)

- Tỷ lệ phản hồi chính xác: **> 90%**
- Thời gian xử lý: **< 3 giây**
- Nguyên tắc **Zero-Hallucination** đối với các con số (tiền bạc, ngày tháng)
- Dữ liệu truy vấn được **ẩn danh hóa (Anonymized) 100%** trước khi xử lý bằng LLM

### Tác động Kinh doanh

Với chi phí truy vấn cận biên cực thấp (**$0.005/req**), giải pháp dự kiến mang lại **ROI thực tế gấp 4 lần** thông qua:
- Giải phóng thời gian đọc hiểu cho phụ huynh
- Giảm thiểu chi phí "chăm sóc khách hàng" lặp lại cho giáo viên
- Gia tăng tỷ lệ chuyển đổi các hành động cần thiết từ phía gia đình học sinh