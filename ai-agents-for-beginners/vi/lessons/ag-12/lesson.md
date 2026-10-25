# Bài 12 · Thiết kế ngữ cảnh cho AI agent

## Từ viết tắt

- **LLM** (Large Language Model) — mô hình ngôn ngữ lớn: bộ não chữ nghĩa đứng sau agent.
- **RAG** (Retrieval Augmented Generation) — cách cho mô hình tra cứu thông tin ngoài rồi mới trả lời.
- **MCP** (Model Context Protocol) — giao thức để agent kết nối với công cụ và dữ liệu bên ngoài.
- **API** (Application Programming Interface) — cổng để chương trình này gọi dịch vụ của chương trình khác.

## Ngữ cảnh là gì và vì sao cần "thiết kế"

Với một AI agent, **ngữ cảnh** (context) là thứ định hướng cách nó lên kế hoạch và chọn bước tiếp theo.
**Thiết kế ngữ cảnh** (context engineering) là việc bảo đảm agent có đúng thông tin để hoàn thành bước kế
tiếp. Cửa sổ ngữ cảnh (phần chữ mô hình nhìn thấy trong một lần gọi) có kích thước giới hạn, nên người dựng agent phải có hệ thống và quy
trình để thêm, bớt và cô đọng thông tin trong đó.

**Khác với prompt engineering**: prompt engineering tập trung vào một bộ chỉ dẫn tĩnh để dẫn dắt agent
theo luật. Còn thiết kế ngữ cảnh là quản lý một tập thông tin động, gồm cả prompt ban đầu, để agent có
thứ nó cần theo thời gian. Ý chính là làm cho quá trình này lặp lại được và đáng tin.

### Ví dụ: "Đặt cho tôi chuyến đi Paris"

- Agent chỉ dùng prompt có thể đáp: "Được rồi, bạn muốn đi khi nào?".
- Agent có thiết kế ngữ cảnh làm nhiều hơn trước khi trả lời: **xem lịch** để biết ngày rảnh, **nhớ sở
  thích cũ** từ bộ nhớ dài hạn (hãng bay, ngân sách, bay thẳng hay không), **nhận ra công cụ** đặt vé và
  khách sạn. Rồi nó hỏi: "Tuần đầu tháng Mười bạn rảnh, tôi tìm chuyến bay thẳng đến Paris với hãng quen
  và ngân sách thường dùng nhé?".

## Năm loại ngữ cảnh

Ngữ cảnh không chỉ là một thứ; nó đến từ nhiều nguồn và ta phải bảo đảm agent chạm được các nguồn đó:

1. **Chỉ dẫn**: "luật" của agent, gồm prompt, tin nhắn hệ thống (chỉ dẫn nền cho mô hình), ví dụ mẫu (few-shot: cho mô hình xem cách làm) và mô tả công cụ.
2. **Kiến thức**: sự kiện, thông tin lấy từ cơ sở dữ liệu, hoặc ký ức dài hạn; có thể tích hợp RAG.
3. **Công cụ**: định nghĩa các hàm bên ngoài, API, MCP server mà agent gọi được, cùng kết quả nhận về.
4. **Lịch sử trò chuyện**: càng lâu càng dài, chiếm chỗ trong cửa sổ ngữ cảnh.
5. **Sở thích người dùng**: điều thích hay không thích học được theo thời gian, dùng khi ra quyết định.

## Chiến lược lập kế hoạch

1. **Xác định rõ kết quả**: khi agent xong việc, thế giới sẽ trông thế nào? Người dùng nhận được thay
   đổi, thông tin hay câu trả lời nào?
2. **Vẽ bản đồ ngữ cảnh**: agent cần thông tin gì để hoàn thành việc, và thông tin nằm ở đâu?
3. **Dựng đường ống ngữ cảnh**: agent lấy thông tin đó bằng cách nào (RAG, MCP server hoặc công cụ khác)?

## Chiến lược thực hành

Sáu chiến lược dưới đây giúp viết, chọn, nén và tách thông tin trong ngữ cảnh.

Khi thông tin bắt đầu đổ vào cửa sổ ngữ cảnh, ta cần chủ động quản lý:

| Chiến lược | Ý chính |
|---|---|
| Sổ nháp của agent | Ghi chú trong một phiên, để ngoài cửa sổ ngữ cảnh (tệp hoặc đối tượng lúc chạy) |
| Bộ nhớ | Lưu và lấy thông tin qua nhiều phiên: tóm tắt, sở thích, phản hồi |
| Nén ngữ cảnh | Tóm tắt hoặc cắt bớt khi cửa sổ gần đầy: giữ điều liên quan, bỏ tin cũ |
| Hệ nhiều agent | Mỗi agent có cửa sổ ngữ cảnh riêng; phải lên kế hoạch cách chia sẻ ngữ cảnh |
| Môi trường sandbox (khu chạy mã tách biệt) | Chạy mã hoặc xử lý tài liệu lớn ở ngoài, agent chỉ đọc kết quả |
| Đối tượng trạng thái lúc chạy | Lưu kết quả từng bước con, để ngữ cảnh chỉ bám vào bước con đó |

### Soi lại ngữ cảnh

Sau khi áp dụng một chiến lược, hãy kiểm tra lần gọi mô hình kế tiếp thực sự nhận được gì. Câu hỏi gỡ
lỗi hữu ích: *agent đã nạp quá nhiều ngữ cảnh, sai ngữ cảnh, hay thiếu ngữ cảnh cần có?* Bạn không cần ghi
nguyên văn prompt hay kết quả công cụ. Trong thực tế, nên ghi các bản ghi nhỏ: số lượng, mã định danh, mã
băm và nhãn chính sách, để thấy chiến lược nào đã chạy và có thay đổi lần gọi kế tiếp đúng ý không.

## Bốn lỗi ngữ cảnh thường gặp

- **Đầu độc ngữ cảnh (poisoning)**: một thông tin bịa hay lỗi lọt vào ngữ cảnh và bị nhắc đi nhắc lại,
  khiến agent theo đuổi mục tiêu bất khả thi. *Cách xử lý*: kiểm tra thông tin trước khi lưu vào bộ nhớ
  dài hạn và cách ly (quarantine) phần nghi ngờ, ví dụ bắt đầu luồng ngữ cảnh mới; ví dụ xác thực chuyến bay bằng API thời gian thực trước
  khi đưa vào ngữ cảnh làm việc.
- **Xao nhãng (distraction)**: ngữ cảnh quá lớn, mô hình bám vào lịch sử thay vì điều đã học khi huấn
  luyện, nên lặp lại hoặc làm việc vô ích. *Cách xử lý*: tóm tắt định kỳ ngữ cảnh, giữ chi tiết quan
  trọng, bỏ lịch sử thừa.
- **Nhầm lẫn (confusion)**: ngữ cảnh thừa, thường là quá nhiều công cụ, khiến mô hình gọi sai công cụ;
  mô hình nhỏ càng dễ bị. *Cách xử lý*: quản lý "bộ công cụ" bằng RAG, lưu mô tả công cụ trong vector
  database (kho lưu dạng vector để tìm theo nghĩa) và chỉ chọn công cụ liên quan nhất cho từng việc. Nghiên cứu nêu nên giới hạn dưới 30 công
  cụ.
- **Xung đột (clash)**: thông tin mâu thuẫn trong ngữ cảnh, thường vì thông tin đến theo từng đợt và giả
  định sai ban đầu còn sót lại. *Cách xử lý*: tỉa bớt (pruning) thông tin lỗi thời, hoặc chuyển bớt
  (offloading) sang sổ nháp riêng để xử lý mà không làm rối ngữ cảnh chính. Ví dụ bạn nói "đi hạng phổ
  thông", sau đổi thành "hạng thương gia": hãy bỏ hoặc ghi đè chỉ dẫn cũ.

## Nhìn hình trả lời

Bạn từng nói "đi hạng phổ thông", rồi đổi ý thành "hạng thương gia", và agent bắt đầu tìm vé lộn xộn.
Đây là lỗi ngữ cảnh nào, và cách xử lý là gì?

<details>
<summary>Đáp án</summary>

Xung đột ngữ cảnh. Tỉa bỏ chỉ dẫn cũ hoặc ghi đè nó, hoặc dùng sổ nháp để chốt lựa chọn cuối trước khi
quyết định.

</details>

## Nguồn đối chiếu

- Bài gốc: [12-context-engineering](https://github.com/microsoft/ai-agents-for-beginners/blob/9923c54bcc2df67e7119945e12cd2d45944da2f6/12-context-engineering/README.md)
- *Dựa trên bài 12 của microsoft/ai-agents-for-beginners (MIT License, © Microsoft Corporation).*
