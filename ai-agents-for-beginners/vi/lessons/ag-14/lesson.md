# Bài 14 · Tìm hiểu Microsoft Agent Framework

## Từ viết tắt

- **MAF** (Microsoft Agent Framework) — khung hợp nhất của Microsoft để dựng AI agent.
- **LLM** (Large Language Model) — mô hình ngôn ngữ lớn: bộ não chữ nghĩa đứng sau agent.
- **SDK** (Software Development Kit) — bộ công cụ lập trình của một dịch vụ.
- **API** (Application Programming Interface) — cổng để chương trình này gọi dịch vụ của chương trình khác.
- **MCP** (Model Context Protocol) — giao thức để agent kết nối với công cụ và dữ liệu bên ngoài.
- **A2A** (Agent-to-Agent) — giao thức để các agent nói chuyện và cùng làm việc với nhau.
- **OTel** (OpenTelemetry) — chuẩn chung để agent phát ra dữ liệu theo dõi.
- **RAG** (Retrieval Augmented Generation) — cách cho mô hình tra cứu thông tin ngoài rồi mới trả lời.

## MAF là gì

**Microsoft Agent Framework (MAF)** là khung hợp nhất của Microsoft để dựng AI agent, đủ linh hoạt cho
nhiều tình huống thật, từ sản xuất đến nghiên cứu. Về **cách điều phối** agent, nó hỗ trợ:

- **Tuần tự**: làm từng bước theo thứ tự.
- **Đồng thời**: nhiều agent cùng làm một lúc.
- **Trò chuyện nhóm**: các agent cùng cộng tác trên một việc.
- **Bàn giao**: agent chuyển việc cho nhau khi xong từng việc con.
- **Magnetic**: một agent quản lý tạo và sửa danh sách việc, rồi điều phối các agent con.

Để đưa agent vào sản xuất, MAF có thêm: **quan sát** bằng OpenTelemetry (mọi hành động của agent đều ghi
được, theo dõi hiệu năng qua bảng điều khiển Microsoft Foundry); **bảo mật** khi chạy agent trên
Microsoft Foundry (phân quyền theo vai trò, xử lý dữ liệu riêng tư, kiểm duyệt nội dung); **bền bỉ**
(luồng và quy trình có thể tạm dừng, chạy tiếp, phục hồi sau lỗi); **kiểm soát** (có bước cần con người
duyệt).

MAF cũng chú trọng khả năng kết nối: **không phụ thuộc đám mây** (chạy trong container, tại chỗ hay nhiều
đám mây), **không phụ thuộc nhà cung cấp** (dùng SDK bạn thích, như Azure OpenAI hay OpenAI), **dùng
chuẩn mở** (A2A và MCP để tìm và dùng agent, công cụ khác), và **plugin, connector** nối đến dịch vụ dữ
liệu, bộ nhớ như Microsoft Fabric, SharePoint, Pinecone, Qdrant.

## Các khái niệm chính

### Agent

Tạo agent bằng cách khai báo: dịch vụ suy luận (nhà cung cấp LLM), chỉ dẫn agent phải theo, và một tên.

```python
agent = client.create_agent(
    instructions="You are good at recommending trips",
    name="TripRecommender")
result = await agent.run("Where to visit in Amsterdam?")
print(result.text)
```

Chạy agent bằng `.run` (nhận trọn câu trả lời) hoặc `.run_stream` (nhận từng phần khi đang tạo). Mỗi lần
chạy có thể kèm tùy chọn như `max_tokens`, `tools` hay cả `model`.

**Công cụ** có thể gắn lúc tạo agent, hoặc chỉ cho một lần chạy. **Luồng (thread)** dùng cho hội thoại
nhiều lượt: tạo bằng `get_new_thread()` để lưu lại theo thời gian, hoặc để agent tự tạo luồng chỉ sống
trong lần chạy đó. Luồng có thể được tuần tự hóa (serialize) để lưu và khôi phục sau.

### Middleware

Middleware cho phép chạy hay ghi vết một hành động ở giữa các tương tác của agent. **Function
middleware** nằm giữa agent và công cụ nó gọi (ví dụ ghi nhật ký lời gọi hàm); **chat middleware** nằm
giữa agent và yêu cầu gửi đến LLM, nơi thấy được các tin nhắn gửi đi. Hàm `next` quyết định có chạy
middleware kế tiếp hoặc hàm thật hay không.

### Bộ nhớ

MAF có ba kiểu: **trong bộ nhớ** (lưu trong luồng khi ứng dụng chạy), **tin nhắn bền** (lưu lịch sử qua
nhiều phiên, qua `chat_message_store_factory`), và **bộ nhớ động** (thêm vào ngữ cảnh trước khi agent
chạy, có thể đặt ở dịch vụ ngoài như Mem0).

### Quan sát

MAF tích hợp OpenTelemetry để có vết (tracing) và số đo (meter), giúp hệ agent đáng tin và dễ bảo trì.

### Quy trình (workflow)

**Workflow** là các bước định sẵn để làm một việc, trong đó agent AI là thành phần của các bước. Workflow
cho phép điều phối nhiều agent và **checkpoint** để lưu trạng thái. Hai thành phần cốt lõi:

- **Executor**: nhận tin nhắn vào, làm việc được giao, tạo tin nhắn ra để đẩy quy trình tiến lên. Có thể
  là agent AI hoặc mã tự viết.
- **Edge** (cạnh): định hướng luồng tin nhắn: **trực tiếp** (một-một), **có điều kiện** (khi hết phòng
  khách sạn thì gợi ý lựa chọn khác), **switch-case** (khách ưu tiên đi theo quy trình riêng), **fan-out**
  (một tin gửi nhiều đích) và **fan-in** (gom nhiều tin về một đích).

Workflow còn phát các **sự kiện** dựng sẵn (bắt đầu, có kết quả, lỗi, executor bắt đầu và xong...) để
quan sát.

## Mẫu nâng cao

- **Ghép middleware**: nối nhiều bộ xử lý (ghi nhật ký, xác thực, giới hạn tốc độ) để kiểm soát chi tiết.
- **Checkpoint workflow**: dùng sự kiện và tuần tự hóa để lưu và chạy tiếp quy trình dài.
- **Chọn công cụ động**: kết hợp RAG trên mô tả công cụ để chỉ đưa công cụ liên quan cho mỗi câu hỏi.
- **Bàn giao nhiều agent**: dùng cạnh workflow và định tuyến có điều kiện để chuyển việc giữa agent chuyên môn.

## Chạy agent LangChain/LangGraph trên Foundry

MAF mở với framework khác: nếu đã có agent dựng bằng **LangChain** hoặc **LangGraph**, bạn có thể chạy nó
như agent được lưu trữ trên Microsoft Foundry; Foundry lo việc chạy, phiên, mở rộng và danh tính, còn
logic agent vẫn ở LangGraph. Nên bắt đầu với giao thức **Responses** (tương thích OpenAI, cho trò
chuyện có luồng và lịch sử), còn giao thức **Invocations** dành cho dạng JSON tùy biến hoặc xử lý không
phải hội thoại.

## Nhìn hình trả lời

Agent đặt phòng cần: nếu hết phòng thì gợi ý phương án khác, và khách ưu tiên thì đi theo quy trình riêng.
Hai việc đó dùng loại cạnh (edge) nào của workflow?

<details>
<summary>Đáp án</summary>

Hết phòng thì gợi ý phương án khác: cạnh có điều kiện. Khách ưu tiên đi quy trình riêng: cạnh switch-case.

</details>

## Nguồn đối chiếu

- Bài gốc: [14-microsoft-agent-framework](https://github.com/microsoft/ai-agents-for-beginners/blob/9923c54bcc2df67e7119945e12cd2d45944da2f6/14-microsoft-agent-framework/README.md)
- *Dựa trên bài 14 của microsoft/ai-agents-for-beginners (MIT License, © Microsoft Corporation).*
