# Bài 11 · Giao thức cho agent: MCP, A2A và NLWeb

## Từ viết tắt

- **LLM** (Large Language Model) — mô hình ngôn ngữ lớn: bộ não chữ nghĩa đứng sau agent.
- **MCP** (Model Context Protocol) — giao thức để agent kết nối với công cụ và dữ liệu bên ngoài.
- **A2A** (Agent-to-Agent) — giao thức để các agent nói chuyện và cùng làm việc với nhau.
- **NLWeb** (Natural Language Web) — cách đưa giao diện ngôn ngữ tự nhiên vào website, để website trả lời bằng chữ.
- **API** (Application Programming Interface) — cổng để chương trình này gọi dịch vụ của chương trình khác.
- **JSON** (JavaScript Object Notation) — định dạng dữ liệu dạng văn bản có cấu trúc.
- **HTML** (HyperText Markup Language) — ngôn ngữ dựng trang web.

## Vì sao agent cần giao thức

Khi agent ngày càng nhiều, ta cần những quy ước chung để chúng an toàn, nói cùng một ngôn ngữ và cho
phép mọi người cùng đổi mới. Bài này giới thiệu ba giao thức: MCP cho agent với công cụ, A2A cho agent
với agent, NLWeb cho agent với website.

## MCP: bộ chuyển đổi vạn năng

**Model Context Protocol (MCP)** là một chuẩn mở, giúp ứng dụng đưa ngữ cảnh và công cụ cho LLM theo một
cách thống nhất. Hãy hình dung nó như một "bộ chuyển đổi vạn năng" cho mọi nguồn dữ liệu và công cụ.

MCP chạy theo mô hình client và server:

- **Host**: ứng dụng LLM (ví dụ trình soạn mã như VSCode) khởi tạo kết nối đến MCP server.
- **Client**: thành phần trong host, giữ kết nối một-một với từng server.
- **Server**: chương trình nhẹ, cung cấp các khả năng cụ thể.

Một MCP server có ba thành phần cốt lõi:

- **Tools** (công cụ): hành động agent có thể gọi, như "lấy thời tiết" hay "mua sản phẩm". Server khai
  báo tên, mô tả và dạng dữ liệu vào/ra của từng công cụ.
- **Resources** (tài nguyên): dữ liệu chỉ đọc mà client lấy khi cần, như nội dung tệp, bản ghi cơ sở dữ
  liệu, tệp nhật ký.
- **Prompts**: mẫu lời nhắc dựng sẵn, hỗ trợ quy trình phức tạp hơn.

### Lợi ích so với gọi API trực tiếp

- **Khám phá công cụ động**: agent nhận danh sách công cụ kèm mô tả từ server. API truyền thống thường
  phải viết mã tích hợp cố định, API đổi là phải sửa mã. MCP hướng đến "tích hợp một lần".
- **Dùng được với nhiều LLM**: dễ đổi mô hình lõi để so sánh hiệu quả.
- **Bảo mật chuẩn hóa**: có cách xác thực chung, đỡ phải quản lý nhiều loại khóa cho nhiều API.

### Ví dụ đặt vé máy bay

1. **Kết nối**: trợ lý AI (client) nối vào MCP server của hãng bay.
2. **Khám phá công cụ**: client hỏi server có công cụ gì; server trả "tìm chuyến bay" và "đặt vé".
3. **Gọi công cụ**: bạn nhờ tìm chuyến từ Portland đến Honolulu; LLM chọn công cụ "tìm chuyến bay" và
   truyền điểm đi, điểm đến.
4. **Thực thi và trả lời**: server gọi API đặt chỗ nội bộ của hãng, nhận dữ liệu (ví dụ JSON) rồi gửi
   lại trợ lý.
5. **Tiếp tục**: trợ lý đưa các lựa chọn; khi bạn chọn xong, nó gọi công cụ "đặt vé" trên cùng server.

## A2A: các agent làm việc cùng nhau

Nếu MCP nối LLM với công cụ thì **A2A** đi xa hơn: cho các agent khác nhau, thuộc tổ chức, môi trường và
công nghệ khác nhau, giao tiếp và cùng hoàn thành một việc chung. Các thành phần:

- **Agent Card**: "danh thiếp" của agent, gồm tên, mô tả việc nó làm, danh sách kỹ năng, địa chỉ
  (endpoint) hiện tại, phiên bản và khả năng như trả lời dạng luồng hay thông báo đẩy.
- **Agent Executor**: chuyển ngữ cảnh cuộc trò chuyện cho agent từ xa để nó hiểu việc cần làm. Agent đó
  dùng LLM riêng và công cụ riêng để thực hiện.
- **Artifact**: sản phẩm khi agent từ xa làm xong, gồm kết quả, mô tả việc đã làm và nội dung chữ. Sau khi
  gửi, kết nối đóng lại cho đến lần cần sau.
- **Event Queue**: hàng đợi xử lý cập nhật và chuyển tin nhắn, giúp kết nối không đóng trước khi xong việc
  lâu.

Lợi ích: **cộng tác** giữa agent của nhiều hãng; **mỗi agent tự chọn LLM** của mình; **xác thực có sẵn**
trong giao thức.

Ví dụ đặt cả chuyến đi Honolulu: người dùng nhờ "Travel Agent" đặt vé, khách sạn và xe thuê. Travel Agent
dùng LLM để chia việc, rồi qua A2A giao cho Airline Agent, Hotel Agent và Car Rental Agent do các công ty
khác nhau làm. Mỗi agent chạy LLM và công cụ riêng (có thể chính là MCP server). Xong hết, Travel Agent
gom kết quả và trả một câu trả lời dạng trò chuyện cho người dùng.

## NLWeb: website biết trò chuyện

**NLWeb** đưa giao diện ngôn ngữ tự nhiên vào bất kỳ website nào, để người dùng và agent tìm và tương tác
với nội dung. Các thành phần:

- **NLWeb Application**: dịch vụ lõi xử lý câu hỏi, "động cơ" của tính năng ngôn ngữ tự nhiên.
- **NLWeb Protocol**: bộ quy tắc cơ bản để trò chuyện với website, trả lời bằng JSON (thường theo
  Schema.org). Mục tiêu là nền móng cho "AI Web", như HTML từng làm cho việc chia sẻ tài liệu.
- **MCP server**: mỗi bản NLWeb cũng là một MCP server, chia sẻ công cụ (như phương thức `ask`) và dữ liệu
  cho agent khác.
- **Embedding model**: đổi nội dung website thành vector, những con số nắm giữ ý nghĩa để máy so sánh.
- **Vector database**: lưu các vector và tìm nhanh thông tin liên quan nhất, xếp theo độ giống.

Ví dụ: danh mục khách sạn, chuyến bay của website du lịch được nạp (dạng Schema.org hoặc RSS), biến thành
vector và lưu lại. Người dùng gõ "tìm khách sạn thân thiện với gia đình ở Honolulu, có hồ bơi". NLWeb gửi
câu hỏi cho LLM và đồng thời tìm trong vector database; LLM chọn kết quả khớp nhất và trả lời bằng ngôn
ngữ tự nhiên, nhắc đúng khách sạn có thật trong danh mục, không bịa. Vì NLWeb cũng là MCP server, một
agent du lịch bên ngoài có thể gọi `ask` để hỏi trực tiếp và nhận JSON có cấu trúc.

## Nhìn hình trả lời

Agent du lịch cần: (1) hỏi một website về khách sạn, (2) giao việc đặt vé cho agent của hãng bay, (3) gọi một công cụ xem thời tiết. Mỗi việc dùng giao thức nào?

<details>
<summary>Đáp án</summary>

(1) Hỏi website bằng ngôn ngữ tự nhiên: NLWeb. (2) Giao việc cho agent của hãng bay: A2A. (3) Gọi công cụ hoặc lấy dữ liệu ngoài: MCP.

</details>

## Nguồn đối chiếu

- Bài gốc: [11-agentic-protocols](https://github.com/microsoft/ai-agents-for-beginners/blob/9923c54bcc2df67e7119945e12cd2d45944da2f6/11-agentic-protocols/README.md)
- *Dựa trên bài 11 của microsoft/ai-agents-for-beginners (MIT License, © Microsoft Corporation).*
