# Individual Reflection — Nguyễn Hoàng Long (2A202600160)

## 1. Role

Backend Developer — File Processing & OCR. Phụ trách thiết kế và triển khai node `parse_attachment` trong LangGraph pipeline, xử lý file đính kèm (PDF, ảnh) thành văn bản để các node downstream (prioritizer, summarizer) sử dụng. Ngoài ra hỗ trợ tích hợp UI và debug integration bugs giữa các node.

## 2. Đóng góp cụ thể

- **Thiết kế và triển khai `nodes/file_parser.py` (~450 dòng):** Xây dựng toàn bộ pipeline xử lý file đính kèm theo kiến trúc SOLID — bao gồm `BaseParser` interface, `PdfPlumberParser` (trích xuất text + bảng biểu từ PDF chuẩn), `PdfVisionParser` (fallback: render PDF scan thành ảnh qua PyMuPDF → gọi Vision LLM), `ImageParser` (encode base64 → gọi GPT-4o-mini Vision), và `ParserFactory` (Open/Closed — thêm định dạng mới không cần sửa parser cũ). Thiết kế Chain of Responsibility pattern: pdfplumber không đọc được text → tự động chuyển sang fallback Vision LLM.

- **Viết spec tài liệu `docs/parse_attachment.md`:** Định nghĩa rõ Input Schema (file bytes, mime_type, file_name), Return Type Schema (status/content/error/metadata), danh sách Error Code chuẩn (5 mã: `UNSUPPORTED_FILE_TYPE`, `FILE_CORRUPTED`, `PDF_PASSWORD_PROTECTED`, `VISION_LLM_FAILED`, `NO_CONTENT_FOUND`), và dependencies (pdfplumber, PyMuPDF, OpenAI SDK).

- **Viết unit test `tests/test_file_parser.py` (~24KB):** Bao phủ các kịch bản: PDF chuẩn (text-based), PDF scan (fallback sang Vision LLM), ảnh (JPEG/PNG), file rỗng, file định dạng không hỗ trợ, PDF có mật khẩu, và Vision LLM timeout.

## 3. SPEC mạnh/yếu

- **Mạnh nhất: Failure Modes (phần 4)** — Nhóm phân tích được 3 failure mode thực tế và có mitigation cụ thể. Đặc biệt failure mode #2 "Lỗi xử lý tệp đính kèm" rất sát với thực tế triển khai: trong quá trình code mình gặp đúng vấn đề file PDF scan mà pdfplumber không đọc được text → phải build cả hệ thống fallback (PyMuPDF render → Vision LLM). Spec dự đoán đúng pain point kỹ thuật.

- **Yếu nhất: ROI (phần 5)** — 3 kịch bản (Conservative/Realistic/Optimistic) khác nhau chủ yếu ở tỷ lệ phụ huynh sử dụng (20%/60%/90%), nhưng giả định về chi phí vận hành và effort bảo trì hệ thống gần như giống nhau. Realistic lẽ ra phải tính thêm chi phí API ($0.005/req × lượng request thực tế) và chi phí DevOps duy trì hệ thống. Con số ROI 1.5x / 4x / 8x chưa có cơ sở tính toán rõ ràng, mang tính ước lượng.

## 4. Đóng góp khác

- **Debug integration bugs giữa các node:** Phát hiện và sửa lỗi mismatch key giữa `parse_attachment_node` (trả về `"attachment_text"`) và `prioritizer` / `summarizer` (đọc `"extracted_text"`). Nội dung file đính kèm bị extract thành công nhưng downstream node không nhận được → summary chỉ dùng teacher_note, bỏ mất nội dung file. Fix bằng cách thêm `"extracted_text"` vào return dict của `parse_attachment_node`.

- **Fix compatibility bug với pdfminer phiên bản mới:** `pdf.doc.is_encrypted` bị remove trong pdfminer mới (thay bằng `pdf.doc.encryption`). Viết version-safe check dùng `hasattr()` để hỗ trợ cả phiên bản cũ lẫn mới.

- **Fix Teacher Portal file upload flow:** Phát hiện `app.py` chỉ lưu metadata file (name, type, size) mà không đọc bytes thực từ `uploaded_file.read()` → `parse_attachment_node` nhận được file rỗng. Sửa lại để đọc bytes thực và truyền đúng key (`"attachment"` thay vì `"attachments"` list).

- **Sửa mock path trong `graph_runner.py`:** Code mock cũ chỉ nối chuỗi placeholder `" (Parsed attachment text)"` thay vì gọi parser thật → summary hiển thị nội dung giả. Thay bằng gọi `parse_attachment()` thật để extract text từ bytes thực, kể cả trong mock mode (không có API key cho LLM prioritizer/summarizer nhưng vẫn parse file thật).

## 5. Điều học được

Trước hackathon mình nghĩ "xử lý file" chỉ là gọi 1 thư viện đọc PDF rồi trả text — đơn giản. Nhưng thực tế gặp nhiều edge case hơn tưởng tượng: PDF scan (không có text layer, chỉ là ảnh embedded), PDF có mật khẩu, ảnh chụp bảng thông báo viết tay bị mờ, API pdfminer thay đổi giữa các phiên bản. Quan trọng nhất là bài học về **integration boundary** — node của mình trả output xong nhưng node tiếp theo không đọc được vì key khác nhau (`attachment_text` vs `extracted_text`). Khi mỗi người code 1 node riêng, ranh giới I/O giữa các node rất dễ bị lệch nếu không có spec chung rõ ràng ngay từ đầu.

## 6. Nếu làm lại

Sẽ viết integration test end-to-end sớm hơn — không chỉ test từng node độc lập. Cụ thể: ngay sau khi có mock node từ team lead, mình sẽ chạy thử luồng `parse_attachment → prioritize → summarize` với 1 file PDF thật để phát hiện lỗi mismatch key sớm. Lần này bug `"attachment_text"` vs `"extracted_text"` tồn tại từ lúc build xong node nhưng mãi đến demo mới phát hiện vì mỗi người chỉ test node của mình. Ngoài ra, sẽ viết `docs/parse_attachment.md` chi tiết hơn phần **output key mapping** — ghi rõ downstream node nào đọc key nào, để tránh ai đó đổi tên key mà không biết ảnh hưởng.

## 7. AI giúp gì / AI sai gì

- **Giúp:** Dùng AI (Antigravity/Claude) để scaffold kiến trúc SOLID cho file_parser.py — AI gợi ý pattern Factory + Chain of Responsibility phù hợp với yêu cầu mở rộng (thêm định dạng DOCX/XLSX sau này chỉ cần thêm parser mới). AI cũng giúp viết unit test bao phủ nhiều edge case nhanh hơn tự nghĩ ra (file rỗng, mime_type không hỗ trợ, Vision LLM timeout). Dùng AI để debug lỗi pdfminer version — AI nhận diện ngay `is_encrypted` bị deprecate và gợi ý dùng `hasattr()` check.

- **Sai/mislead:** Ban đầu AI suggest dùng `pytesseract` (Tesseract OCR) cho ảnh — nhưng setup Tesseract trên Windows rất phiền (cần cài binary riêng, config PATH), và kết quả OCR tiếng Việt kém hơn nhiều so với GPT-4o-mini Vision. Mất gần 1 tiếng cài đặt Tesseract trước khi chuyển sang approach Vision LLM. Ngoài ra, AI có lúc suggest refactor quá sâu (tách thêm abstract class `VisionProvider` trong khi chỉ có 1 implementation duy nhất) — scope creep cho hackathon. Bài học: AI gợi ý pattern đúng về mặt lý thuyết nhưng không biết cân scope theo thời gian hackathon.
