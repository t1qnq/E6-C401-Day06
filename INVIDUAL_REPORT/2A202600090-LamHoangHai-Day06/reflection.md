# Individual reflection — Lâm Hoàng Hải (2A202600090)

## 1. Role

Code hai node brief summarization và detail summarization trong pipeline.

## 2. Đóng góp cụ thể

- Thiết kế node brief summarization, khi người dùng chỉ yêu cầu tóm gọn một vài thông tin, hệ thống sẽ trả về tối đa 3 bullet points
- Thiết kế node detail summarization, khi người dùng yêu cầu tóm tắt chi tiết, hệ thống trả về văn bản tóm tắt chi tiết từ 2-4 câu.
- Hệ thống ghi nhận loại tài liệu và đối tượng gửi để sử dụng tông giọng phù hợp.

## 3. SPEC mạnh/yếu

- Mạnh nhất: User Stories x 4 Paths. Các kịch bản chỉ ra rõ ràng các tình huống cần thiết đến sự sử dụng của công cụ. Cho người dùng thấy được sản phẩm có phân loại ưu tiên thông báo, đồng thời còn đảm bảo chất lượng và tiếp thu cải tiến.
- Yếu nhất: ROI — 3 kịch bản thực ra chỉ khác số lượng user, lợi ích và tác động còn hơi võ đoán, thiếu cơ sở.

## 4. Đóng góp khác

- Tham gia vào quá trình sửa lại graph pipeline

## 5. Điều học được

Trước hackathon nghĩ xây dựng sản phẩm AI chỉ đơn thuần là tìm được pain point và tệp người dùng rồi bắt tay vào làm. Sau đó em học được đó còn là xây dựng Deliverables, Prototype, SPEC.

## 6. Nếu làm lại

Sẽ plan ra chi tiết các phần sớm hơn, chứ không để Ngày 2 mới bắt đầu lên plan và code chi tiết các phần, dẫn đến nhiều tính năng chưa kịp triển khai và test thực tế.

## 7. AI giúp gì / AI sai gì

- **Giúp:** Lên plan để viết node một cách tường tận. Hỗ trợ các kịch bản kiểm thử cho mock data.
- **Sai/mislead:** Overthinking về plan, ví dụ như Codex đã lên cả kế hoạch sử dụng extractive summarization + abstractive summarization, tuy nhiên trong bối cảnh hiện giờ, việc chunking và dùng abstract summarize nhanh hơn. Khi yêu cầu đầu vào là tiếng Việt, AI hiểu sai và xử lý mock data như không dấu.
