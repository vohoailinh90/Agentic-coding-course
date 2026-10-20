# Nguyên tắc thiết kế AI agent

Có nhiều cách để nghĩ về việc xây hệ thống agent. Vì sự mơ hồ là đặc điểm chứ không phải lỗi của AI tạo sinh, kỹ sư thường khó biết bắt đầu từ đâu. Bài này giới thiệu một bộ nguyên tắc thiết kế trải nghiệm lấy con người làm trung tâm, để dựng agent phục vụ đúng nhu cầu của khách hàng. Đây không phải một kiến trúc bắt buộc, mà là điểm xuất phát cho nhóm đang thiết kế trải nghiệm agent.

Sau bài này bạn có thể:

- Giải thích các nguyên tắc thiết kế agent là gì.
- Nêu các hướng dẫn khi áp dụng chúng.
- Hiểu cách dựng một agent theo các nguyên tắc đó.

## Từ viết tắt

- **AI** (Artificial Intelligence) — trí tuệ nhân tạo.
- **UX** (User Experience) — trải nghiệm người dùng.
- **UI** (User Interface) — giao diện người dùng.
- **Prompt** — lời nhắc hoặc yêu cầu bạn gõ cho mô hình AI.
- **System Prompt** — chỉ dẫn nền mà người tạo agent đặt ra để định hình cách agent cư xử.

## Agent nên làm gì cho con người

Nói chung, agent nên:

- **Mở rộng năng lực con người**: động não, giải quyết vấn đề, tự động hóa.
- **Lấp khoảng trống kiến thức**: giúp nắm nhanh một lĩnh vực, dịch thuật.
- **Hỗ trợ cộng tác** theo cách mỗi người thích làm việc với người khác.
- **Giúp ta trở thành phiên bản tốt hơn của mình**: ví dụ như huấn luyện viên cuộc sống, giúp rèn điều tiết cảm xúc, chánh niệm và sự bền bỉ.

## Ba chiều của nguyên tắc: Không gian, Thời gian, Lõi

### Agent (Không gian)

Đây là môi trường agent hoạt động, cả thế giới thực lẫn số.

- **Kết nối, không thay thế**: agent giúp kết nối con người với người khác, với sự kiện và với tri thức dùng được. Nó kéo mọi người lại gần nhau, không sinh ra để thay thế hay coi thường con người.
- **Dễ tiếp cận nhưng đôi khi vô hình**: agent phần lớn chạy ngầm và chỉ nhắc ta khi thật sự phù hợp. Người dùng được phép dùng nó trên mọi thiết bị, nó hỗ trợ nhiều dạng vào ra (âm thanh, giọng nói, văn bản) và chuyển mượt giữa chạy nền với chạy nổi, giữa chủ động với phản ứng. Dù vô hình, đường chạy nền và sự phối hợp với agent khác vẫn minh bạch và người dùng kiểm soát được.

### Agent (Thời gian)

Đây là cách agent hoạt động theo thời gian: quá khứ, hiện tại, tương lai.

- **Quá khứ: nhìn lại lịch sử** gồm cả trạng thái lẫn ngữ cảnh. Agent cho kết quả sát hơn nhờ phân tích dữ liệu lịch sử phong phú, và chủ động nhớ lại để xử lý tình huống hiện tại.
- **Hiện tại: gợi ý nhẹ hơn là báo tin**. Khi có sự kiện, agent không chỉ gửi thông báo tĩnh: nó đơn giản hóa luồng việc hoặc tạo gợi ý động để hướng sự chú ý đúng lúc, theo ngữ cảnh và ý định của người dùng. Tương tác có thể tăng dần độ phức tạp để trao thêm năng lực cho người dùng về lâu dài.
- **Tương lai: thích nghi và tiến hóa**. Agent thích nghi với nhiều thiết bị, nền tảng, kiểu tương tác, với hành vi và nhu cầu tiếp cận của người dùng, cho tùy chỉnh tự do, và được định hình qua tương tác liên tục.

### Agent (Lõi)

- **Chấp nhận sự bất định nhưng xây dựng niềm tin.** Agent có mức bất định nhất định là điều được dự kiến, và là yếu tố chính của thiết kế agent. Niềm tin và sự minh bạch là lớp nền. Con người quyết định lúc nào bật hay tắt agent, và trạng thái của agent luôn hiển thị rõ.

## Ba hướng dẫn khi áp dụng

1. **Minh bạch**: cho người dùng biết có AI tham gia, nó vận hành thế nào (kể cả các hành động trước đó), cách đưa phản hồi và cách chỉnh hệ thống.
2. **Kiểm soát**: cho người dùng tùy chỉnh, đặt sở thích, cá nhân hóa và nắm quyền với hệ thống cùng các thuộc tính của nó (kể cả khả năng "quên").
3. **Nhất quán**: hướng tới trải nghiệm đa phương thức nhất quán trên mọi thiết bị. Dùng phần tử UI quen thuộc khi có thể (ví dụ biểu tượng micro cho giọng nói) và giảm tải nhận thức cho khách hàng (câu trả lời ngắn gọn, hình minh họa, nội dung "Tìm hiểu thêm").

## Ví dụ: thiết kế agent du lịch

| Hướng dẫn | Việc cụ thể |
|---|---|
| Minh bạch | Cho người dùng biết đây là agent dùng AI; có lời chào hoặc prompt mẫu để bắt đầu; ghi rõ trên trang sản phẩm; hiện danh sách prompt đã hỏi; chỉ rõ cách phản hồi (thích, không thích, nút gửi phản hồi); nói rõ nếu agent có giới hạn về cách dùng hoặc chủ đề |
| Kiểm soát | Làm rõ cách chỉnh agent sau khi tạo (ví dụ qua System Prompt); cho chọn độ dài câu trả lời, văn phong và những điều agent không nên nói; cho xem và xóa tệp, dữ liệu, prompt và cuộc trò chuyện cũ |
| Nhất quán | Dùng biểu tượng quen thuộc cho chia sẻ prompt, thêm tệp hoặc ảnh, gắn thẻ; dùng kẹp giấy cho tệp, biểu tượng hình ảnh cho đồ họa |

## Nhìn hình trả lời

Bạn muốn người dùng agent du lịch xem và xóa được các cuộc trò chuyện cũ của họ. Việc đó thuộc hướng dẫn nào: minh bạch, kiểm soát hay nhất quán?

<details>
<summary>Đáp án</summary>

**Kiểm soát**: cho người dùng xem và xóa tệp, dữ liệu, prompt và cuộc trò chuyện cũ.

</details>

## Nguồn đối chiếu

- [AI Agentic Design Principles](https://github.com/microsoft/ai-agents-for-beginners/blob/9923c54bcc2df67e7119945e12cd2d45944da2f6/03-agentic-design-patterns/README.md)

*Dựa trên bài 03 của microsoft/ai-agents-for-beginners (MIT License, © Microsoft Corporation).*
