# Xây ứng dụng chat

> Câu hỏi mở đầu: một chatbot trả lời "đơn hàng của bạn đang ở đâu" khác gì một ứng dụng chat dùng AI tạo sinh?

## Từ viết tắt

- **AI** (Artificial Intelligence) — trí tuệ nhân tạo.
- **LLM** (Large Language Model) — mô hình ngôn ngữ lớn: mô hình AI nhận chữ và trả ra chữ.
- **API** (Application Programming Interface) — giao diện lập trình: cách chương trình của bạn gọi một dịch vụ.
- **SDK** (Software Development Kit) — bộ công cụ phát triển: thư viện giúp gọi một dịch vụ dễ hơn.
- **UX** (User Experience) — trải nghiệm người dùng. **UI** (User Interface) — giao diện người dùng.
- **DSL** (Domain Specific Language) — ngôn ngữ chuyên ngành; *mô hình DSL* là mô hình được huấn luyện cho một lĩnh vực.

## Bài này giúp bạn làm gì

Ứng dụng chat đã thành một phần đời sống: chăm sóc khách hàng, hỗ trợ kỹ thuật, cả những hệ thống tư vấn phức tạp. Khi
đưa AI tạo sinh vào, chúng mạnh hơn nhưng cũng khó hơn. Hai câu hỏi lớn: **xây** ứng dụng thế nào cho hiệu quả, và khi
đã chạy thì **theo dõi** thế nào để chất lượng luôn cao và đúng sáu nguyên tắc AI có trách nhiệm. Sau bài này bạn sẽ:

- biết cần cân nhắc gì khi xây ứng dụng chat và gắn nó vào hệ thống có sẵn;
- tùy chỉnh ứng dụng chat cho một việc cụ thể;
- biết các chỉ số chính để theo dõi và giữ chất lượng ứng dụng;
- bảo đảm ứng dụng dùng AI có trách nhiệm.

## Chatbot hay ứng dụng chat?

**Chatbot** tự động hóa một vài việc trò chuyện cụ thể, như trả lời câu hỏi thường gặp hay tra đơn hàng. **Ứng dụng chat
dùng AI tạo sinh** là một môi trường rộng hơn nhiều cho nhiều kiểu trò chuyện số.

| Chatbot | Ứng dụng chat dùng AI tạo sinh |
|---|---|
| Theo việc, theo luật | Hiểu ngữ cảnh |
| Thường gắn vào một hệ thống lớn hơn | Có thể chứa một hay nhiều chatbot |
| Chỉ làm những gì được lập trình | Dùng mô hình AI tạo sinh |
| Trò chuyện chuyên biệt, có khuôn | Trò chuyện được về mọi chủ đề |

## Dùng sẵn SDK và API

Bước đầu tốt là xem có gì làm sẵn. Dùng SDK và API có tài liệu tốt giúp:

- **làm nhanh hơn, đỡ tốn**: dồn sức cho phần quan trọng của bạn, như nghiệp vụ;
- **chạy tốt hơn**: SDK và API được bảo trì tốt thường đã lo chuyện nhiều người dùng cùng lúc;
- **bảo trì dễ hơn**: thường chỉ cần cập nhật thư viện khi có bản mới;
- **dùng công nghệ mới**: mô hình đã được huấn luyện trên lượng dữ liệu lớn cho ứng dụng của bạn khả năng ngôn ngữ tự
  nhiên.

Muốn dùng, bạn thường cần **khóa API** (hay token xác thực). Ví dụ với thư viện OpenAI cho Python, khóa đọc từ biến môi
trường:

```python
import os
from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
response = client.responses.create(model="gpt-5-mini",
    input="Gợi ý hai tiêu đề cho bài học về ứng dụng chat dùng AI tạo sinh.", store=False)
print(response.output_text)
```

Nếu chưa đặt khóa, lệnh gọi sẽ báo lỗi.

## Trải nghiệm người dùng (UX)

Ngoài các nguyên tắc UX chung, ứng dụng chat dùng AI cần thêm:

- **Xử lý chỗ mơ hồ**: mô hình đôi khi trả lời mơ hồ; nên có cách để người dùng hỏi lại cho rõ.
- **Giữ ngữ cảnh**: mô hình nhớ được ngữ cảnh trong cuộc trò chuyện, rất có ích. Cho người dùng quản lý ngữ cảnh thì tốt
  hơn, nhưng có nguy cơ giữ cả thông tin nhạy cảm; nên có **chính sách lưu giữ** (giữ bao lâu) để cân bằng với quyền
  riêng tư.
- **Cá nhân hóa**: ví dụ hồ sơ người dùng. Tính năng "Custom instructions" của ChatGPT cho bạn khai thông tin về mình để
  làm ngữ cảnh cho mọi prompt; nhờ vậy, khi nhờ soạn giáo án, câu trả lời hợp với trình độ của bạn hơn.

**Khung viết tin nhắn hệ thống của Microsoft** chia làm bốn phần:

1. mô hình phục vụ ai, làm được gì và không làm được gì;
2. định dạng câu trả lời;
3. ví dụ cụ thể về cách mô hình nên làm;
4. các "rào chắn" thêm cho hành vi của mô hình.

**Trợ năng**: ứng dụng tốt phải dùng được cho mọi người.

| Khó khăn | Tính năng |
|---|---|
| Thị giác | Giao diện tương phản cao, chữ phóng to được, hỗ trợ trình đọc màn hình |
| Thính giác | Chuyển chữ thành giọng nói và ngược lại, tín hiệu hình cho thông báo âm thanh |
| Vận động | Điều khiển bằng bàn phím, ra lệnh bằng giọng nói |
| Nhận thức | Tùy chọn ngôn ngữ đơn giản |

## Tùy chỉnh cho một lĩnh vực

Hãy hình dung một ứng dụng chat hiểu thuật ngữ riêng của công ty bạn. Có hai cách:

- **Dùng mô hình DSL**: mô hình được huấn luyện hay tinh chỉnh để hiểu và viết về một lĩnh vực, ngành hay chủ đề. Có thể
  tự huấn luyện từ đầu, hoặc dùng mô hình có sẵn qua SDK và API.
- **Tinh chỉnh** (fine-tuning): huấn luyện thêm mô hình có sẵn bằng dữ liệu riêng. Thường dùng khi mô hình chung làm chưa
  tốt một lĩnh vực hay một việc chuyên biệt.

Ví dụ: ứng dụng chat giúp bác sĩ tra nhanh phác đồ điều trị, tương tác thuốc hay nghiên cứu mới. Mô hình chung đủ cho câu
hỏi y khoa cơ bản, nhưng khó với **ca rất phức tạp** (như cách điều trị động kinh kháng thuốc ở trẻ em) và **thiếu tiến
bộ mới nhất** trong thần kinh học và dược học. Tinh chỉnh bằng một bộ dữ liệu y khoa chuyên biệt giúp trả lời chính xác
và đáng tin hơn, nhưng cần một bộ dữ liệu lớn, sát với các câu hỏi của lĩnh vực.

## Giữ chất lượng: các chỉ số chính

| Chỉ số | Đo gì | Câu hỏi cho người làm |
|---|---|---|
| Thời gian hoạt động (uptime) | Ứng dụng chạy và dùng được bao lâu | Giảm thời gian ngừng thế nào? |
| Thời gian phản hồi | Bao lâu thì trả lời người dùng | Tăng tốc xử lý câu hỏi thế nào? |
| Precision | Trong các lần đoán "có", tỉ lệ đoán đúng | Kiểm tra thế nào? |
| Recall | Trong các trường hợp thật sự "có", tỉ lệ đoán ra | Đo và cải thiện thế nào? |
| F1 | Trung bình điều hòa của precision và recall | Mục tiêu bao nhiêu, cân bằng hai cái thế nào? |
| Perplexity | Phân bố xác suất mô hình đoán khớp dữ liệu thật tới đâu | Giảm thế nào? |
| Mức hài lòng | Người dùng thấy ứng dụng ra sao, thường qua khảo sát | Bao lâu thu phản hồi một lần? |
| Tỉ lệ lỗi | Mô hình sai khi hiểu hay khi trả lời bao nhiêu | Có cách gì để giảm? |
| Chu kỳ huấn luyện lại | Bao lâu cập nhật mô hình với dữ liệu mới | Điều gì kích hoạt việc huấn luyện lại? |
| Phát hiện bất thường | Công cụ tìm hành vi lạ | Xử lý bất thường thế nào? |

## AI có trách nhiệm trong ứng dụng chat

Sáu nguyên tắc của Microsoft, áp vào ứng dụng chat:

| Nguyên tắc | Người làm chat nên |
|---|---|
| Công bằng | Không phân biệt đối xử dựa trên dữ liệu người dùng |
| Tin cậy và an toàn | Kiểm thử, có cơ chế an toàn khi lỗi |
| Riêng tư và bảo mật | Mã hóa mạnh, bảo vệ dữ liệu |
| Bao trùm | Giao diện dễ dùng cho nhiều kiểu người |
| Minh bạch | Tài liệu rõ, giải thích được câu trả lời |
| Chịu trách nhiệm | Có quy trình rà soát và cải thiện quyết định của AI |

## Thực hành

Bài nguồn có bài tập (nhiều ngôn ngữ lập trình) đi từ chạy những prompt chat đầu tiên tới phân loại và tóm tắt văn bản.
Thử chạy đoạn code ở trên với khóa API của bạn, rồi đổi prompt và quan sát câu trả lời.

## Nhìn hình trả lời

Điều nào đúng với ứng dụng chat dùng AI tạo sinh, so với chatbot theo luật?

1. Chỉ làm được những việc đã lập trình sẵn.
2. Hiểu ngữ cảnh và trò chuyện được về nhiều chủ đề.
3. Không bao giờ cần theo dõi sau khi chạy.

<details>
<summary>Đáp án</summary>

**Câu 2.** Câu 1 là đặc điểm của chatbot theo luật. Câu 3 sai: ứng dụng chat cần được theo dõi bằng các chỉ số như thời
gian phản hồi, tỉ lệ lỗi, mức hài lòng.

</details>

## Nguồn đối chiếu

- Bài nguồn (đã ghim): [Building Generative AI-Powered Chat Applications](https://github.com/microsoft/generative-ai-for-beginners/blob/c35bc1950f9dc56af773d2c362dafce6f76e9a56/07-building-chat-applications/README.md)

*Dựa trên bài 07 của microsoft/generative-ai-for-beginners (MIT License, © Microsoft Corporation), commit c35bc19.*
