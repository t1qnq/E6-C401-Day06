# Individual reflection — Nguyễn Mạnh Dũng (AI20K001)

## 1. Role
API Integration · Data Layer 

## 2. Đóng góp cụ thể
- Thiết kế data schemas
- Viết script generate data mock, data loader
- Thu thập dữ liệu thật

## 3. SPEC mạnh/yếu
- Mạnh nhất: phân loại ưu tiên tự động - Agent có khả năng phân tích ngữ cảnh (hồ sơ học sinh, documents) để đánh giá mức độ ưu tiên của notification
- Yếu nhất: Correction Path chưa thực tế - Khi agent phân loại và gửi nhầm notification, hệ thống chưa được thiết kế để nhận diện và lấy feedback từ người dùng (phụ huynh)

## 4. Đóng góp khác
- Update eval metrics, cập nhật một số metrics để handle edge case

## 5. Điều học được
Học được tầm quan trọng của việc phân tích yêu cầu dự án trước khi bắt tay vào thực hiện.
Học được tầm quan trọng của việc quản lý tiến độ dự án và phân chia hợp lý workload cho các thành viên
Tuỳ thuộc vào tính chất và yêu cầu của dự án mà có những metrics và edge cases khác nhau, cũng như xác định các red-flags và kill point cụ thể

## 6. Nếu làm lại
Define work plan từ sớm và kỹ hơn, cân nhắc tầm quan trọng của các milestone khác nhau để đặt ưu tiên và deadlines, cũng như tránh tình trạng phải đợi chờ nhau làm - các luồng công việc được thực hiện song song


## 7. AI giúp gì / AI sai gì
- **Giúp:** Giúp đưa insight về vấn đề cũng như gợi ý về data (schemas, data loader) - nguồn collect real life data.
- **Sai/mislead:** Gemini gợi ý một số metrics không quá thực tế - LLM có thể sẽ không hiểu pain point trong thực tế