# Individual reflection

## 1. Role
Slide support + technical support. Phụ trách brainstorm idea, hỗ trợ làm nội dung slide, rà soát flow trình bày và hỗ trợ các phần kỹ thuật khi nhóm cần.

## 2. Đóng góp cụ thể
- Xây dựng nội dung slide: sắp xếp lại flow kể chuyện để phần problem → solution → demo → evaluation rõ ràng và dễ theo dõi hơn
- Có thử làm 2 hướng UI ban đầu cho phần demo, nhưng không nối được với backend để dùng trong demo nên phần này đã được chuyển cho người khác tiếp tục triển khai
- Hỗ trợ kỹ thuật khi nhóm cần, đặc biệt ở các đoạn cần nối ý giữa phần sản phẩm, flow demo và cách giải thích kết quả

## 3. SPEC mạnh/yếu
- Mạnh nhất: phần ideation và hướng giải bài toán khá rõ, nhóm xác định được core use case nên khi làm slide có thể kể câu chuyện sản phẩm tương đối mạch lạc
- Yếu nhất: một số assumption trong SPEC còn hơi chung, nên khi chuyển thành slide phải mất thêm thời gian để diễn giải cho dễ hiểu và thuyết phục hơn

## 4. Đóng góp khác


## 5. Điều học được
Qua quá trình làm, mình hiểu rõ hơn về giới hạn của AI khi phát triển sản phẩm. AI có thể hỗ trợ brainstorm, gợi ý giao diện hoặc sinh code khá nhanh, nhưng nó không tự giải quyết được bài toán nối giữa frontend và backend nếu từ đầu team chưa tính rõ phần input và output cần trao đổi. Khi frontend chưa xác định trước sẽ gửi dữ liệu gì, nhận dữ liệu gì và hiển thị theo format nào, thì backend rất dễ đi theo hướng khác, và đến lúc ghép lại sẽ phát sinh lỗi hoặc phải chỉnh sửa nhiều. Từ đó mình hiểu thêm rằng việc nối front và back không chỉ là viết code cho khớp, mà quan trọng hơn là phải thống nhất data flow và contract giữa hai bên ngay từ sớm.

## 6. Nếu làm lại
Mình sẽ tham gia chốt hướng trình bày và demo flow sớm hơn. Nếu phần narrative của slide được khóa từ sớm thì cả nhóm sẽ đỡ mất thời gian chỉnh qua lại ở cuối, và các phần kỹ thuật cũng dễ bám theo một hướng thống nhất hơn.

## 7. AI giúp gì / AI sai gì
- **Giúp:** AI hỗ trợ brainstorm ý tưởng khá nhanh, gợi ý cách trình bày slide, cách diễn đạt ngắn gọn hơn và hỗ trợ thử một số hướng UI ban đầu để nhóm có thêm điểm xuất phát
- **Sai/mislead:** khi dùng AI cho phần giao diện và kết nối hệ thống, mình nhận ra AI thường sinh ra phần front và back khá tách rời nếu người dùng không mô tả trước input/output đủ rõ. Nhìn riêng từng phần thì có vẻ ổn, nhưng khi ghép lại dễ lệch format dữ liệu hoặc không chạy đúng flow mong muốn. Bài học là AI giúp tăng tốc rất tốt, nhưng không thay thế được việc tự xác định contract giữa các phần của hệ thống
