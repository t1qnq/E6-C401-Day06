# Tài liệu parse_attachment

## Input Schema

| Trường (Field) | Kiểu dữ liệu | Yêu cầu | Mô tả |
| :--- | :--- | :--- | :--- |
| `file` | `bytes` | Bắt buộc | Dữ liệu nhị phân của file (`bytes`) |
| `file_name` | `str` | Tùy chọn | Tên gốc của tệp đính kèm (VD: `thong_bao_hoc_phi.pdf`). |
| `mime_type` | `str` | Bắt buộc | Loại định dạng của file để phân luồng xử lý (VD: `application/pdf`, `image/jpeg`). |
## Kiểu trả về của method

```json
{
  "status": "string",       // Bắt buộc: Trạng thái chạy ("success" hoặc "error")
  "content": "string",      // Nội dung text rút ra được (Format Markdown). Rỗng "" nếu lỗi.
  "error": {                // Chứa thông tin lỗi. Sẽ là null/None nếu status là "success"
    "code": "string",       // Mã lỗi (để code backend dễ if/else)
    "message": "string"     // Thông báo lỗi  (để in ra log hoặc cho Agent đọc)
  },
  "metadata": {             // Các thông tin để checklog
    "file_type": "string",  // "pdf" hoặc "image"
    "parser_used": "string" // Báo cho biết đã dùng tool gì: "pdfplumber" hay "vision_llm"
  }
}
```
## Danh sách Dependencies

Dưới đây là các thư viện Python cần thiết để triển khai luồng xử lý tài liệu đính kèm (PDF & Image).

### 1. Thư viện bên ngoài (Cần cài đặt qua `pip`)

| Tên thư viện | Lệnh cài đặt (`pip`) | Vai trò trong luồng xử lý |
| :--- | :--- | :--- |
| **pdfplumber** | `pip install pdfplumber` | **Core (Lõi):** Dùng để trích xuất văn bản (text) và cấu trúc bảng biểu (tables) từ các file PDF chuẩn (sinh ra từ Word/Excel). |
| **PyMuPDF** | `pip install pymupdf` | **Hỗ trợ (Utility):** Dùng để chuyển đổi (render) các trang PDF Scan thành hình ảnh một cách cực kỳ nhanh chóng, sau đó đẩy hình ảnh này cho Vision LLM. |
| **OpenAI SDK** <br>*(hoặc)*<br> **Google GenAI** | `pip install openai`<br>*(hoặc)*<br>`pip install google-generativeai` | **Vision LLM:** Gọi API (GPT-4o-mini hoặc Gemini 1.5 Flash) để đọc nội dung từ hình ảnh trực tiếp hoặc từ các file PDF Scan bị mờ nhòe. |

### 2. Thư viện chuẩn của Python 

| Tên thư viện | Vai trò trong luồng xử lý |
| :--- | :--- |
| `base64` | Mã hóa hình ảnh hoặc file PDF sang chuỗi Base64 để truyền qua API của Vision LLM. |
| `io` | Xử lý luồng dữ liệu nhị phân (như `io.BytesIO`) khi thao tác đọc/ghi file trên RAM mà không cần lưu xuống ổ cứng. |
| `json` | Xây dựng và định dạng kiểu dữ liệu trả về (Return Type schema) của hàm. |
| `typing` | Định nghĩa kiểu dữ liệu (Type Hinting) cho tham số đầu vào và đầu ra giúp code dễ bảo trì (VD: `Dict`, `Optional`, `Union`). |

### Mẫu file `requirements.txt` tham khảo:
```text
pdfplumber==0.11.0
pymupdf==1.24.1
openai==1.14.0
# google-generativeai==0.4.1 # Bỏ comment dòng này nếu dùng Gemini thay vì OpenAI

```

## Error Code

| Code | Message |
| :--- | :--- |
| `UNSUPPORTED_FILE_TYPE` | Định dạng tệp không được hỗ trợ. Chỉ chấp nhận ảnh và PDF. |
| `FILE_CORRUPTED` | Tệp bị hỏng hoặc không thể mở được. |
| `PDF_PASSWORD_PROTECTED` | Không thể đọc tệp PDF do có mật khẩu bảo vệ. |
| `VISION_LLM_FAILED` | Lỗi trích xuất nội dung từ dịch vụ Vision LLM (timeout hoặc API error). |
| `NO_CONTENT_FOUND` | Không tìm thấy bất kỳ nội dung văn bản nào trong tệp. |


## Ví dụ minh hoạ

### Thành công

```json

{
  "status": "success",
  "content": "### Thông báo thực đơn\n| Thứ | Món chính | Món phụ |\n| 2 | Thịt kho | Canh rau |\n...",
  "error": null,
  "metadata": {
    "file_type": "pdf",
    "parser_used": "pdfplumber"
  }
}

```

### Thất bại

```json

{
  "status": "error",
  "content": "",
  "error": {
    "code": "PDF_PASSWORD_PROTECTED",
    "message": "Không thể đọc tệp PDF do có mật khẩu bảo vệ."
  },
  "metadata": {
    "file_type": "pdf",
    "parser_used": "pdfplumber"
  }
}

```