# Làm việc với họ mô hình Mistral

Mistral có nhiều mô hình, mỗi cái mạnh một kiểu. Bài này giới thiệu ba mô hình: **Mistral Large**,
**Mistral Small** và **Mistral NeMo**, mỗi cái hợp với việc gì, và vài ví dụ mã cho thấy điểm riêng của
từng mô hình. Cả ba đều dùng miễn phí được trên Microsoft Foundry Models.

## Từ viết tắt

- **LLM** (Large Language Model) — mô hình ngôn ngữ lớn: mô hình đọc và viết văn bản.
- **SLM** (Small Language Model) — mô hình ngôn ngữ nhỏ: gọn và rẻ hơn LLM.
- **RAG** (Retrieval Augmented Generation) — tìm tài liệu liên quan rồi đưa vào prompt cho mô hình.
- **API** (Application Programming Interface) — cổng để một chương trình gọi chức năng của chương trình khác.

## Bài này giúp bạn làm gì

Học xong, bạn sẽ:

1. biết ba mô hình Mistral trong bài;
2. hiểu mỗi mô hình hợp với việc gì;
3. đọc được ví dụ mã cho thấy điểm riêng của từng mô hình.

## Ba mô hình Mistral

| Mô hình | Là gì | Hợp với |
|---|---|---|
| Mistral Large 2 | Mô hình hàng đầu, cho doanh nghiệp | RAG, gọi hàm, sinh mã |
| Mistral Small | Mô hình ngôn ngữ nhỏ (SLM) | Việc chữ, gọi nhiều lần, cần nhanh |
| Mistral NeMo | Mô hình miễn phí, giấy phép Apache 2 | Tinh chỉnh, gọi hàm, nhiều ngôn ngữ |

Lưu ý: GitHub Models ngừng hoạt động cuối tháng 7/2026; Microsoft Foundry Models là nơi thay thế.

## Mistral Large 2

Mistral Large 2 (bản 2407) là mô hình hàng đầu của Mistral, làm cho doanh nghiệp. So với Mistral Large
gốc, nó có:

- **Cửa sổ ngữ cảnh lớn hơn**: 128k token so với 32k. *Token* là mẩu chữ mô hình đọc; cửa sổ ngữ cảnh là
  lượng chữ mô hình đọc được một lần.
- **Giỏi toán và viết mã hơn**: độ chính xác trung bình 76,9% so với 60,4%.
- **Nhiều ngôn ngữ hơn**: tiếng Anh, Pháp, Đức, Tây Ban Nha, Ý, Bồ Đào Nha, Hà Lan, Nga, Trung, Nhật,
  Hàn, Ả Rập và Hindi.

Nhờ vậy Mistral Large mạnh ở ba việc:

- **RAG**, nhờ cửa sổ ngữ cảnh lớn.
- **Gọi hàm** (function calling): có sẵn khả năng gọi công cụ và API bên ngoài, gọi song song hoặc lần lượt.
- **Sinh mã**: giỏi Python, Java, TypeScript và C++.

**Ví dụ RAG.** Câu hỏi viết bằng tiếng Hàn, hỏi về việc tác giả làm trước khi vào đại học. Mô hình
embedding của Cohere biến tài liệu và câu hỏi thành dãy số; thư viện `faiss` làm kho vector. Prompt gửi
Mistral gồm câu hỏi và các mẩu tài liệu giống câu hỏi nhất; mô hình trả lời bằng ngôn ngữ tự nhiên.

```python
D, I = index.search(question_embeddings.reshape(1, -1), k=2)
retrieved_chunks = [chunks[i] for i in I.tolist()[0]]
```

## Mistral Small

Mistral Small cũng thuộc nhóm cao cấp cho doanh nghiệp. Như tên gọi, nó là một **SLM**. Lợi thế:

- **Rẻ**: giá giảm 80% so với các LLM của Mistral như Large và NeMo.
- **Nhanh**: trả lời nhanh hơn các LLM của Mistral.
- **Linh hoạt**: triển khai được ở nhiều môi trường, ít đòi hỏi tài nguyên hơn.

Mistral Small hợp với:

- việc chữ như tóm tắt, phân tích cảm xúc, dịch;
- ứng dụng gọi mô hình thường xuyên, vì nó rẻ;
- việc mã cần nhanh, như xem lại mã và gợi ý mã.

**So Small với Large.** Gửi cùng một prompt cho hai mô hình: thời gian trả lời chênh nhau khoảng 3–5 giây.
Để ý cả độ dài và văn phong của hai câu trả lời.

## Mistral NeMo

Trong ba mô hình, NeMo là mô hình **miễn phí duy nhất có giấy phép Apache 2**. Có thể xem nó là bản nâng
cấp của Mistral 7B, LLM mã nguồn mở trước đó của Mistral. Điểm đáng chú ý:

- **Tách token hiệu quả hơn**: dùng bộ tách token (tokenizer) Tekken thay vì tiktoken phổ biến hơn, nên
  làm tốt hơn với nhiều ngôn ngữ và với mã.
- **Tinh chỉnh được**: có sẵn mô hình gốc để tinh chỉnh khi việc của bạn cần.
- **Gọi hàm có sẵn**: như Mistral Large, NeMo được huấn luyện để gọi hàm, là một trong những mô hình mã
  nguồn mở đầu tiên làm được việc này.

**So bộ tách token.** Đưa cùng một prompt cho NeMo và Large rồi đếm token: NeMo trả về ít token hơn Large.

## Nhìn hình trả lời

Ứng dụng của bạn gọi mô hình hàng nghìn lần mỗi ngày để tóm tắt tin nhắn ngắn, và cần trả lời nhanh.
Theo bảng "Ba mô hình Mistral", bạn chọn mô hình nào?

<details>
<summary>Đáp án</summary>

**Mistral Small**. Nó rẻ hơn (giá giảm 80% so với các LLM của Mistral), trả lời nhanh hơn, và hợp với việc
chữ như tóm tắt trong ứng dụng gọi mô hình thường xuyên.

</details>

## Nguồn đối chiếu

- [20-mistral/README.md, ghim ở commit c35bc19](https://github.com/microsoft/generative-ai-for-beginners/blob/c35bc1950f9dc56af773d2c362dafce6f76e9a56/20-mistral/README.md)

*Dựa trên bài 20 của microsoft/generative-ai-for-beginners (MIT License, © Microsoft Corporation).*
