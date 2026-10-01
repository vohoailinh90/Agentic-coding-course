---
lesson: agents-and-workflows
lang: vi
status: review
summary: >-
  Workflow là các bước cố định do bạn (hay code) định sẵn; agent là khi mô hình tự quyết định bước tiếp theo. Bắt đầu
  bằng cách đơn giản nhất làm được việc, và chỉ thêm độ phức tạp khi cần. Một agent thứ hai (subagent) có ích khi một
  việc phụ sẽ làm ngập ngữ cảnh chính, khi cần một lượt review trong ngữ cảnh mới, hay khi có những phần độc lập làm
  song song — nhưng mỗi agent thêm vào đều tốn thêm và cần được giao việc rõ ràng.
social:
  hook: "Video trên mạng: \"10 agent làm việc như một công ty\". Bản tin câu lạc bộ của Huy có cần 5 agent không? 🤖🤖🤖"
  question: Trong việc của bạn, có phần nào thật sự cần một "người" thứ hai kiểm tra với con mắt mới không?
---

🌐 **Tiếng Việt** · [English](../../en/lessons/agents-and-workflows.md) · [日本語](../../ja/lessons/agents-and-workflows.md)

# Agent và workflow: khi nào cần nhiều agent?

<!-- section: objective -->
## Mục tiêu bài học

Sau bài này, bạn sẽ:

- Phân biệt **workflow** (các bước định sẵn) với **agent** (mô hình tự quyết định các bước).
- Chọn cách đơn giản nhất làm được việc, theo một "chiếc thang" bốn bậc.
- Biết ba trường hợp một **subagent** (agent phụ) thật sự có ích, và cái giá của nó.

<!-- section: hook -->
## Mở đầu: vì sao nên quan tâm?

Huy xem một video: mười agent làm việc như một công ty — agent nghiên cứu, agent viết, agent biên tập, agent dịch, agent đăng bài. Cậu muốn làm y vậy cho **bản tin tháng** của câu lạc bộ: năm agent, mỗi agent một vai.

Nghe rất hay. Nhưng bản tin của Huy dài một trang, lấy thông tin từ ba file lịch sự kiện, mỗi tháng một lần. Năm agent là đúng công cụ — hay là thuê năm đầu bếp để nấu một bữa cơm nhà?

<!-- section: concept -->
## Nội dung chính

### Workflow và agent

Anthropic (12/2024) phân biệt hai kiểu hệ thống:

- **Workflow:** các bước được định sẵn — bởi code, hay bởi bạn. Mô hình làm từng bước, nhưng không chọn bước. Ví dụ: kỹ năng làm báo cáo tháng của Mai trong [Bộ nhớ dự án và kỹ năng dùng lại](memory-and-skills.md).
- **Agent:** mô hình **tự quyết định** bước tiếp theo và công cụ cần dùng, như bạn đã thấy trong [vòng lặp của agent](the-agent-loop.md).

Workflow dễ đoán, ổn định cho việc đã rõ. Agent linh hoạt cho việc không đoán trước được các bước.

### Bắt đầu đơn giản

Lời khuyên của Anthropic: tìm **cách đơn giản nhất** làm được việc, và chỉ tăng độ phức tạp khi cần — đôi khi nghĩa là không cần hệ thống agent nào cả. Hệ thống agent thường đổi thời gian và chi phí lấy kết quả tốt hơn; hãy tự hỏi sự đánh đổi đó có đáng không.

![Chiếc thang độ phức tạp](../diagrams/complexity-ladder.svg)

Leo từng bậc, và chỉ leo khi bậc dưới không đủ:

1. **Một yêu cầu** cho chatbot hay agent — đủ cho phần lớn việc nhỏ.
2. **Workflow cố định** — việc lặp lại với cùng các bước.
3. **Một agent** — việc mà các bước phụ thuộc vào điều phát hiện ra giữa chừng.
4. **Agent + subagent** — khi có một lý do cụ thể, như ba trường hợp dưới đây.

### Ba lúc subagent có ích

Một **subagent** là agent phụ do agent chính gọi ra, làm một phần việc trong **ngữ cảnh riêng** của nó rồi trả về kết quả. Tài liệu Claude Code (9/2026) nêu các lý do dùng nó; ba lý do hay gặp nhất:

- **Việc phụ sẽ làm ngập ngữ cảnh chính.** Tìm trong hàng trăm file, đọc log dài — subagent làm trong ngữ cảnh của nó và chỉ trả về bản tóm tắt.
- **Cần một con mắt mới.** Một lượt review trong ngữ cảnh mới, chỉ thấy kết quả và tiêu chí — như bạn đã học trong [Thêm quy trình khi việc cần](workflow-frameworks.md).
- **Những phần độc lập làm song song**, không phần nào cần kết quả của phần kia.

### Cái giá của mỗi agent thêm vào

- **Tốn thêm:** mỗi subagent tự gửi yêu cầu tới mô hình, tính vào cùng giới hạn sử dụng với phiên chính.
- **Bắt đầu từ con số không:** subagent không thấy cuộc trò chuyện của bạn, cũng không thấy file agent chính đã đọc. Nó chỉ biết những gì được giao — giao mơ hồ thì nó đoán.
- **Thêm chỗ để sai:** kết quả chuyền qua nhiều tay; mỗi lần chuyền có thể mất hay méo thông tin. Và bạn vẫn phải kiểm tra kết quả cuối.

<!-- section: analogy -->
## Ví dụ đời thường

Bếp của một nhà hàng lớn có bếp trưởng, người sơ chế, người lo món nướng, người nếm cuối. Hợp lý — vì mỗi tối họ nấu hàng trăm suất. Nhưng thuê năm đầu bếp để nấu một bữa cơm nhà cho bốn người thì chỉ thêm việc chỉ đạo, thêm chỗ va nhau, và thêm tiền.

Một thứ đáng thuê thêm ngay cả ở bếp nhỏ: **một người nếm lại** trước khi dọn ra — người không nấu món đó nên nếm khách quan hơn.

Phép so sánh sai ở chỗ: một đầu bếp mới vào bếp còn nghe thấy, nhìn thấy mọi thứ xung quanh. Subagent thì không — nó chỉ biết đúng những gì được viết trong lời giao việc.

<!-- section: example -->
## Ví dụ thực tế

Huy viết ra kế hoạch năm agent, rồi đi từng bậc của chiếc thang.

**Việc thật sự cần làm mỗi tháng:** đọc ba file lịch sự kiện (dữ liệu giả, trong `ai-practice`), viết bản tin một trang, kiểm tra ngày giờ và địa điểm, lưu ra `ban_tin_thang_X.md`.

- **Bậc 1 — một yêu cầu?** Gần đủ. Nhưng tháng nào cũng làm lại cùng các bước.
- **Bậc 2 — workflow cố định?** Đúng: các bước không đổi. Huy viết một kỹ năng `ban-tin-thang`: đọc ba file, viết theo mẫu, ghi ra file.
- **Có cần subagent không?** Cậu xét ba lý do. Ba file lịch ngắn — không làm ngập ngữ cảnh. Không có phần nào cần làm song song. Còn **con mắt mới**? Có: ngày giờ sai trong bản tin là thứ cả câu lạc bộ sẽ dựa vào.

Huy thêm một bước cuối vào kỹ năng: *"Giao cho một subagent mới: so từng ngày giờ và địa điểm trong bản tin với ba file lịch. Chỉ báo chỗ không khớp, không sửa gì."*

Tháng đầu tiên, subagent review báo một chỗ: buổi dã ngoại ghi *thứ Bảy 17/10*, nhưng file lịch ghi *Chủ nhật 18/10*. Agent viết đã nhầm khi gộp hai dòng lịch. Huy sửa, rồi tự đọc lại cả bản tin trước khi gửi.

Kết quả: một workflow và một subagent review — thay vì năm agent. Ít tốn hơn, ít chỗ để sai hơn, và chỗ duy nhất cần con mắt mới thì có con mắt mới.

<!-- section: misconceptions -->
## Hiểu lầm thường gặp

- **"Càng nhiều agent càng thông minh."** — Mỗi agent thêm vào tốn thêm, và thêm một lần chuyền thông tin có thể sai. Thêm agent khi có lý do cụ thể, không phải vì nó nghe hiện đại.
- **"Subagent biết những gì mình đã nói với agent chính."** — Nó bắt đầu từ ngữ cảnh mới, chỉ biết những gì được giao. Lời giao việc cho subagent cần rõ như một yêu cầu cho người mới.
- **"Có agent review rồi thì mình không cần đọc."** — Subagent review giúp bắt lỗi; nó không thay trách nhiệm của bạn với kết quả cuối.

<!-- section: recap -->
## Tóm tắt bằng hình

![Tóm tắt: agent và workflow](../diagrams/agents-and-workflows-recap.svg)

<!-- section: takeaways -->
## Ghi nhớ

- Workflow: các bước định sẵn. Agent: mô hình tự chọn bước.
- Bắt đầu đơn giản; chỉ leo lên bậc phức tạp hơn khi bậc dưới không đủ.
- Subagent có ích khi việc phụ làm ngập ngữ cảnh, khi cần con mắt mới, hay khi có phần độc lập làm song song.
- Mỗi agent thêm vào đều tốn thêm, bắt đầu từ con số không, và thêm chỗ để sai.
- Nhiều agent không thay bạn kiểm tra kết quả cuối.

<!-- section: quiz -->
## Tự kiểm tra

**Câu 1.** Điểm khác cốt lõi giữa workflow và agent là gì?

- A) Workflow dùng mô hình rẻ, agent dùng mô hình đắt
- B) Ở workflow các bước được định sẵn; ở agent mô hình tự quyết định bước tiếp theo
- C) Workflow không dùng AI

**Câu 2.** Trường hợp nào đáng dùng một subagent nhất?

- A) Việc đổi màu một tiêu đề
- B) Viết một email ngắn
- C) Tìm một thông tin trong hàng trăm file log dài, rồi chỉ cần bản tóm tắt

**Câu 3.** Vì sao lời giao việc cho subagent cần rõ ràng?

- A) Vì subagent bắt đầu với ngữ cảnh mới, không thấy cuộc trò chuyện của bạn với agent chính
- B) Vì subagent dùng ngôn ngữ khác
- C) Vì subagent không được dùng công cụ nào

<details>
<summary>Xem đáp án</summary>

1. **B** — ai chọn bước tiếp theo là khác biệt chính; cả hai đều dùng mô hình.
2. **C** — việc phụ sẽ làm ngập ngữ cảnh chính; subagent làm riêng và chỉ trả về tóm tắt.
3. **A** — nó chỉ biết những gì được viết trong lời giao việc.

</details>

<!-- section: sources -->
## Nguồn tham khảo

- Anthropic — [Building Effective AI Agents](https://www.anthropic.com/engineering/building-effective-agents) (tiếng Anh, 12/2024): workflow là hệ thống mà mô hình và công cụ được điều phối theo các bước định sẵn, agent là hệ thống mà mô hình tự điều khiển quá trình và việc dùng công cụ; tìm cách đơn giản nhất và chỉ tăng độ phức tạp khi cần; hệ thống agent đổi thời gian và chi phí lấy kết quả tốt hơn.
- Anthropic — [Create custom subagents](https://code.claude.com/docs/en/sub-agents) (tiếng Anh, tính đến 9/2026): subagent làm việc trong ngữ cảnh riêng và chỉ trả về tóm tắt; dùng khi việc phụ tạo nhiều đầu ra không cần giữ trong ngữ cảnh chính; subagent không thấy lịch sử trò chuyện hay file agent chính đã đọc; mỗi subagent tự gửi yêu cầu, tính vào cùng giới hạn sử dụng.
