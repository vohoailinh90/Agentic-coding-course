# Bài 13 · Bộ nhớ của AI agent

## Từ viết tắt

- **LLM** (Large Language Model) — mô hình ngôn ngữ lớn: bộ não chữ nghĩa đứng sau agent.
- **RAG** (Retrieval Augmented Generation) — cách cho mô hình tra cứu thông tin ngoài rồi mới trả lời.
- **MAF** (Microsoft Agent Framework) — khung dựng agent của Microsoft.

## Bộ nhớ là gì và vì sao cần

Hai điều làm agent đặc biệt: biết gọi công cụ để hoàn thành việc, và biết tốt lên theo thời gian. Bộ nhớ
là nền móng của điều thứ hai: nó giúp agent tự cải thiện và mang lại trải nghiệm tốt hơn cho người dùng.

**Bộ nhớ của agent** là các cơ chế giúp nó giữ lại và nhắc lại thông tin: chi tiết một cuộc trò chuyện,
sở thích người dùng, hành động đã làm, hay quy luật đã học. Không có bộ nhớ, ứng dụng AI thường
"không trạng thái" (stateless): mỗi lần tương tác bắt đầu từ đầu, agent "quên" ngữ cảnh và sở thích cũ,
khiến người dùng bực vì phải lặp lại.

Bộ nhớ giúp agent biết **nhìn lại** (học từ hành động và kết quả cũ), **tương tác** (giữ mạch trong cuộc
trò chuyện), **chủ động và phản ứng đúng** (đoán nhu cầu, trả lời theo dữ liệu quá khứ) và **tự chủ**
hơn (dựa vào kiến thức đã lưu). Mục tiêu là làm agent đáng tin và có năng lực hơn.

## Các loại bộ nhớ

Các ví dụ đều lấy từ một agent đặt chuyến du lịch.

| Loại | Là gì | Ví dụ |
|---|---|---|
| Bộ nhớ làm việc | Tờ giấy nháp cho việc đang làm; giữ yêu cầu, quyết định, hành động chính | "Tôi muốn đặt chuyến đi Paris" |
| Bộ nhớ ngắn hạn | Giữ thông tin trong một cuộc trò chuyện | Hỏi giá vé Paris, rồi "chỗ ở ở đó thì sao?": "đó" là Paris |
| Bộ nhớ dài hạn | Tồn tại qua nhiều cuộc trò chuyện, giúp cá nhân hóa | Ben thích trượt tuyết, tránh dốc khó vì từng chấn thương |
| Bộ nhớ nhân cách (persona) | Giúp agent có "tính cách" nhất quán | Agent là "chuyên gia lên kế hoạch trượt tuyết" |
| Bộ nhớ quy trình (episodic) | Lưu chuỗi bước đã làm, gồm thành công lẫn thất bại | Chuyến bay hết chỗ: lần sau thử chuyến khác |
| Bộ nhớ thực thể | Nhớ người, nơi chốn, vật và sự kiện | Nhớ nhà hàng "Le Chat Noir", đề nghị đặt bàn lại |
| Structured RAG | Rút thông tin dày, có cấu trúc từ hội thoại, thư, ảnh | Lấy chi tiết chuyến bay từ thư để hỏi chính xác |

Với MAF (bản Python), bộ nhớ ngắn hạn tương ứng với `AgentSession`: giữ ngữ cảnh khi còn dùng cùng một
phiên, nhưng mất khi phiên kết thúc hoặc ứng dụng khởi động lại. Điều cần sống qua nhiều phiên thì dùng
bộ nhớ dài hạn, thường qua cơ sở dữ liệu, vector index hoặc kho lưu bền khác.

## Lưu và quản lý bộ nhớ

Quản lý bộ nhớ gồm: tạo, lưu, truy xuất, tích hợp, cập nhật, và cả "quên" (xóa) thông tin. Truy xuất
(tìm lại ký ức đã lưu) đặc biệt quan trọng.

- **Mem0**: lớp bộ nhớ bền, biến agent không trạng thái thành có trạng thái. Chạy theo **hai pha: trích
  xuất và cập nhật**. Tin nhắn trong luồng (thread, chuỗi tin nhắn của một cuộc trò chuyện) của agent được gửi lên Mem0; một LLM tóm tắt hội thoại và
  rút ra ký ức mới. Sau đó một LLM quyết định thêm, sửa hay xóa ký ức, lưu trong kho dữ liệu lai: vector (cách biểu diễn nghĩa của chữ bằng số để tìm theo độ giống), graph (lưu quan hệ giữa các thứ) và key-value (lưu theo cặp tên và giá trị).
- **Cognee**: bộ nhớ ngữ nghĩa mã nguồn mở, biến dữ liệu thành đồ thị tri thức (mạng các khái niệm và quan hệ giữa chúng) có hỗ trợ bởi embedding (số hóa nghĩa của chữ).
  Nó có kiến trúc hai kho: tìm theo độ giống (vector) kết hợp quan hệ trong đồ thị (graph), nên agent hiểu
  không chỉ điều gì giống nhau mà còn khái niệm liên hệ với nhau thế nào.
- **Azure AI Search**: dịch vụ tìm kiếm làm kho lưu và truy xuất ký ức, nhất là Structured RAG. Nhờ nó,
  câu trả lời của agent bám vào dữ liệu của chính bạn.

## Cho agent tự cải thiện

Một mẫu thường gặp là thêm một **agent tri thức** (knowledge agent) đứng quan sát cuộc trò chuyện giữa
người dùng và agent chính. Nó làm bốn việc:

1. **Nhận ra thông tin đáng giá** để lưu thành kiến thức chung hoặc sở thích.
2. **Rút gọn và tóm tắt** điều đã học.
3. **Lưu vào kho tri thức**, thường là vector database.
4. **Bổ sung cho câu hỏi sau**: khi người dùng hỏi mới, nó lấy thông tin liên quan và gắn vào câu hỏi,
   cho agent chính thêm ngữ cảnh (giống RAG).

Hai cách tối ưu:

- **Quản lý độ trễ**: dùng mô hình rẻ, nhanh để kiểm tra trước thông tin có đáng lưu hay lấy không; chỉ khi
  cần mới chạy bước trích xuất hoặc truy xuất phức tạp.
- **Bảo trì kho tri thức**: khi kho lớn dần, chuyển thông tin ít dùng sang "kho lạnh" để tiết kiệm chi phí.

## Nhìn hình trả lời

Agent du lịch nhớ rằng Ben tránh dốc trượt tuyết khó vì từng chấn thương, dù đã qua nhiều cuộc trò
chuyện. Đó là loại bộ nhớ nào, và nó khác bộ nhớ ngắn hạn ở điểm gì?

<details>
<summary>Đáp án</summary>

Bộ nhớ dài hạn. Nó tồn tại qua nhiều cuộc trò chuyện hoặc phiên, còn bộ nhớ ngắn hạn chỉ giữ thông tin
trong một cuộc trò chuyện.

</details>

## Nguồn đối chiếu

- Bài gốc: [13-agent-memory](https://github.com/microsoft/ai-agents-for-beginners/blob/9923c54bcc2df67e7119945e12cd2d45944da2f6/13-agent-memory/README.md)
- *Dựa trên bài 13 của microsoft/ai-agents-for-beginners (MIT License, © Microsoft Corporation).*
