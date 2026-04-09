# Individual reflection — Khổng Mạnh Tuấn(2A202600086)
## 1. Role
Project manager + Phụ trách thiết kế tool chatbot và viết system prompt cho tính năng priorititizer.

## 2. Đóng góp cụ thể
Lên ý tưởng cho đề tài spec ,thiết kế flow chatbot và prompt cho tính năng prioritizer
phân tích failure modes và ROI của tính năng prioritizer
điều phối quản lý tiến độ nhóm, đảm bảo mọi người có task phù hợp và hỗ trợ khi cần


## 3. SPEC mạnh/yếu
- Mạnh nhất: phần failure modes. Nhóm xác định được các tình huống AI dễ sai
  (ngôn ngữ mơ hồ, tệp đính kèm chất lượng thấp, quá tải giờ cao điểm), đồng thời có hướng xử lý rõ ràng
  như fallback thông báo lỗi, gắn cờ low-confidence và thu thập feedback để cải thiện dần.
- Yếu nhất: phần ROI. Ba kịch bản hiện chủ yếu khác nhau ở số lượng user,
  trong khi assumption còn khá giống nhau. Nếu làm tốt hơn, cần tách rõ giả định cho từng kịch bản
  (ví dụ: conservative = triển khai ở 1 chi nhánh; optimistic = rollout toàn hệ thống).

## 4. Đóng góp khác
- Test prompt với 10 nhóm thông báo khác nhau và ghi log kết quả vào prompt-tests.md.
- Hỗ trợ Châu debug bộ eval metrics: ban đầu chỉ có "accuracy" tổng,
  sau đó tách thêm precision theo từng nhóm ưu tiên (Cao/Trung bình/Thấp)
  để phản ánh chất lượng sát với thực tế sử dụng hơn.

## 5. Điều học được
Trước hackathon, mình xem precision và recall chủ yếu là chỉ số kỹ thuật.
Sau khi tham gia thiết kế tính năng AI prioritization cho thông báo phụ huynh, mình hiểu rằng
việc chọn metric phụ thuộc vào bối cảnh sản phẩm: với tin khẩn (y tế, kỷ luật, học phí đến hạn)
cần ưu tiên recall cao để tránh bỏ sót; với tin thường nhật nên ưu tiên precision cao
để giảm cảnh báo không cần thiết và tránh làm phụ huynh bị quá tải thông tin.
Nói cách khác, chọn metric là quyết định sản phẩm, không chỉ là quyết định kỹ thuật.
Bên cạnh đó việc xác đinh tiến độ dự án , checklist tiến độ cần cụ thể rõ ràng để cập nhật được tiến độ tốt hơn .

## 6. Nếu làm lại
Em sẽ bắt đầu test prompt sớm hơn.
Ở lần này, nhóm dành ngày đầu chủ yếu để viết SPEC và đến trưa D6 mới test prompt.
Nếu bắt đầu từ tối D5, nhóm có thể iterate thêm 2-3 vòng và chất lượng prompt sẽ tốt hơn đáng kể.
Lên kế hoạch chi tiết hơn cho từng ngày, ví dụ: D5 tối test prompt nhóm 1, D6 sáng test nhóm 2, D6 chiều tổng hợp kết quả và chỉnh sửa prompt.
## 7. AI giúp gì / AI sai gì
- **AI hỗ trợ tốt:** Em dùng Claude để brainstorm failure modes và nhận được gợi ý
  về trường hợp phân loại sai giữa thông báo "khẩn" và "thường" mà nhóm chưa nghĩ tới.
  Ngoài ra, Gemini giúp test prompt nhanh
  trên AI Studio để rút ngắn thời gian thử nghiệm.
- **AI có thể gây lệch hướng:** Khi viết prompt, em có xu hướng dựa vào gợi ý của AI về cách phân loại thông báo,đôi khi dẫn đến việc bỏ qua các yếu tố khác như tần suất thông báo hoặc phản hồi của phụ huynh.
  Bài học rút ra: AI rất hữu ích để mở rộng ý tưởng, nhưng con người phải giữ vai trò chốt phạm vi.