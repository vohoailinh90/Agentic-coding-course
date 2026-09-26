# Agentic Coding cho người mới bắt đầu

Giáo trình dạy người chưa biết gì về AI đi từ *"phần mềm là gì?"* đến tự giao việc cho **AI agent**
làm phần mềm: nền tảng phần mềm, AI và machine learning, LLM, agentic coding và harness engineering.
Khóa học có **3 ngôn ngữ, mỗi ngôn ngữ một thư mục riêng**; mọi trang đều có thanh 🌐 để chuyển
sang ngôn ngữ khác.

## 🌐 Chọn ngôn ngữ · Choose a language · 言語を選ぶ

| | |
|---|---|
| **[Tiếng Việt →](course/vi/README.md)** | Agentic Coding cho người mới bắt đầu |
| **[English →](course/en/README.md)** | Agentic Coding for Absolute Beginners |
| **[日本語 →](course/ja/README.md)** | ゼロから学ぶエージェント型コーディング |

Repo này là **kho dữ liệu** của khóa học — nguồn duy nhất để đăng bài Facebook đều đặn và sau này
dựng website khóa học. Nội dung là Markdown + YAML, được kiểm tra tự động bằng CI, nên cả người lẫn
AI agent (Claude, Codex) đều viết và sửa được mà không làm hỏng cấu trúc.

## Trạng thái hiện tại

Giai đoạn 0 → 1 — lộ trình v1 đã chốt, bắt đầu viết lộ trình tối thiểu. Xem [PROGRESS.md](PROGRESS.md)
để biết đang làm gì và bước tiếp theo.

| | |
|---|---|
| Lộ trình v1 | 6 chương · 17 chủ đề · 52 bài · ~15 giờ — [xem bản đồ lộ trình](course/vi/README.md) |
| ⭐ Lộ trình tối thiểu | 19 bài · 347 phút, gồm 2 dự án — học trước, đăng Facebook trước |
| Bài mẫu | [Từ chatbot đến AI agent](course/vi/lessons/chatbot-to-agent.md) và [Bộ não, đôi tay và vòng lặp](course/vi/lessons/agent-parts-and-loop.md) — mỗi bài có infographic và một hình tóm tắt cả bài |
| Thuật ngữ 3 thứ tiếng | 43 thuật ngữ — [trang thuật ngữ](course/vi/glossary.md) |
| Brainstorm với Codex | [brainstorm/](brainstorm/README.md) — xong cả 2 vòng, đã áp dụng thành lộ trình v1 |

## Repo này có gì

```text
course/
  vi/  en/  ja/          Mỗi thư mục là toàn bộ khóa học bằng MỘT ngôn ngữ:
    README.md              trang chủ khóa học + bản đồ lộ trình (tự sinh)
    glossary.md            thuật ngữ (tự sinh)
    lessons/<id>.md        bài học
    diagrams/<id>.svg      infographic (tự sinh)
  data/                  Dữ liệu dùng chung, chứa cả 3 ngôn ngữ (sửa tay):
    course.yaml            thông tin khóa học
    curriculum.yaml        cây khóa học: chương → chủ đề → bài
    sections.yaml          các phần của một bài học
    glossary.yaml          thuật ngữ Việt · Anh · Nhật
    diagrams/<id>.yaml     nội dung các infographic
  README.md              trang chọn ngôn ngữ (tự sinh)
brainstorm/              Brief và kết quả brainstorm lộ trình với Codex
docs/                    Hướng dẫn viết bài, cấu trúc dữ liệu, kế hoạch Facebook, quyết định (ADR)
src/                     Chương trình quản lý kho dữ liệu (python -m src.main)
tests/                   Test cho chương trình (và cho harness của template)
```

Repo được tạo từ [`claude-agent-routing-template`](TEMPLATE.md), nên có sẵn harness cho Claude Code:
`CLAUDE.md`, các agent và skill trong `.claude/`, chính sách routing trong `agent-routing/`, và giao
thức làm việc với Codex trong [`docs/claude-to-codex.md`](docs/claude-to-codex.md).

## Chương trình quản lý kho dữ liệu

Cần Python 3.10+, PyYAML và markdown-it-py (`python -m pip install -r requirements.txt`). Chạy từ thư
mục gốc của repo; thêm `--lang vi|en|ja` để chọn ngôn ngữ thông báo.

```bash
python -m src.main validate                  # kiểm tra toàn bộ kho dữ liệu (CI cũng chạy)
python -m src.main build                     # vẽ infographic, sinh trang chủ + thuật ngữ cho 3 ngôn ngữ
python -m src.main stats                     # quy mô khóa học + tiến độ viết theo từng ngôn ngữ
python -m src.main scaffold what-is-software # tạo sẵn bài mới trong cả 3 thư mục ngôn ngữ
python -m src.main fb-draft chatbot-to-agent --post-lang vi   # bản nháp bài đăng Facebook
python -m src.main export                    # file HTML xem offline để chia sẻ (outputs/html/)
```

### Chia sẻ khóa học không cần GitHub

`export` ghi vào `outputs/html/` (Git bỏ qua thư mục này) các file HTML **tự chứa**: mở bằng trình
duyệt, không cần mạng, không cần file nào khác — infographic nằm sẵn bên trong.

- `agentic-coding-course.html` — cả 3 thứ tiếng, mở ra trang chọn ngôn ngữ. Gửi một file này là đủ.
- `agentic-coding-course-vi.html`, `-en.html`, `-ja.html` — từng ngôn ngữ riêng, nhẹ hơn; để chung
  một thư mục thì liên kết 🌐 chuyển ngôn ngữ giữa các file vẫn chạy.
- Muốn **PDF**: mở file của một ngôn ngữ → in (Ctrl+P, trên Mac ⌘+P) → "Lưu dưới dạng PDF": cả khóa học
  trong một file, đáp án câu hỏi được in ra.

Chỉ bài đã viết xong (`review` hoặc `done`) được xuất; bài còn ở `review` có nhãn "Bản nháp, đang chờ
duyệt". Xem [ADR 009](docs/decisions/009-offline-html-export.md).

## Quy trình viết một bài

1. `scaffold <lesson-id>` → có sẵn file bài học trong `course/vi`, `course/en`, `course/ja`.
2. Viết bản **tiếng Việt** trước (ngôn ngữ gốc) theo [docs/content-guide.md](docs/content-guide.md);
   ý nào so sánh, cộng dồn, lặp lại hay theo bước thì vẽ thành infographic trong `course/data/diagrams/`,
   và bài nào cũng kết thúc bằng **một hình tóm tắt cả bài** (phần "Tóm tắt bằng hình").
3. Bản địa hóa sang tiếng Anh và tiếng Nhật — giữ nguyên các phần và các sơ đồ, thay ví dụ cho hợp
   văn hóa.
4. `build` rồi `validate` cho đến khi sạch lỗi; đổi trạng thái `draft → review → done`.
5. Bài `done` → `fb-draft` → đọc lại → đăng Facebook (xem [docs/facebook-plan.md](docs/facebook-plan.md)).

## Các giai đoạn

| Giai đoạn | Nội dung | Trạng thái |
|---|---|---|
| 0 | Kho dữ liệu, lộ trình v0, bài mẫu, infographic, brainstorm lộ trình với Codex | xong |
| 1 | Chốt lộ trình v1 (xong); viết cả khóa học bằng 3 thứ tiếng, "lộ trình tối thiểu" trước; xuất HTML để chia sẻ (xong) | đang làm |
| 2 | Đăng Facebook đều đặn từ kho dữ liệu (xuất infographic thành ảnh) | sắp tới |
| 3 | Website khóa học: nút chuyển ngôn ngữ, cây khóa học, tiến độ, mục lục từng bài | sau này |
