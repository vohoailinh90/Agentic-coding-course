# Agentic Coding cho người mới bắt đầu · Agentic Coding for Absolute Beginners · ゼロから学ぶエージェント型コーディング

Giáo trình **3 thứ tiếng (Tiếng Việt · English · 日本語)** dạy người chưa biết gì về AI đi từ
*"phần mềm là gì?"* đến tự giao việc cho **AI agent** làm phần mềm: nền tảng phần mềm, AI và
machine learning, LLM, agentic coding và harness engineering.

Repo này là **kho dữ liệu** của khóa học — nguồn duy nhất để sau này đăng bài Facebook đều đặn
và dựng website khóa học. Nội dung được lưu dưới dạng Markdown + YAML, được kiểm tra tự động
bằng CI, nên cả người lẫn AI agent (Claude, Codex) đều có thể viết và sửa mà không làm hỏng
cấu trúc.

> **English** — A trilingual (Vietnamese · English · Japanese) course that takes complete
> beginners from "what is software?" to directing AI agents that build software. This repository
> is the course's content store: the single source for regular Facebook posts and, later, the
> course website.
>
> **日本語** — AIをまったく知らない人が「ソフトウェアとは？」から、AIエージェントにソフトウェアづくりを
> 任せられるようになるまでを学ぶ、3か国語（ベトナム語・英語・日本語）の講座です。このリポジトリは
> 講座のコンテンツ置き場で、Facebook投稿と将来の講座サイトの唯一の元データになります。

## Trạng thái hiện tại

**Giai đoạn 0 — Lộ trình v0 và kho dữ liệu.** Xem [PROGRESS.md](PROGRESS.md) để biết đang làm gì
và bước tiếp theo.

| | |
|---|---|
| Lộ trình v0 | 7 chương · 17 chủ đề · 57 bài · ~16 giờ — xem [course/OUTLINE.md](course/OUTLINE.md) |
| Bài mẫu | [Từ chatbot đến AI agent](course/lessons/chatbot-to-agent/vi.md) · [English](course/lessons/chatbot-to-agent/en.md) · [日本語](course/lessons/chatbot-to-agent/ja.md) |
| Thuật ngữ 3 thứ tiếng | 43 thuật ngữ — [course/glossary.yaml](course/glossary.yaml) |
| Brainstorm với Codex | [brainstorm/](brainstorm/README.md) |

## Repo này có gì

```text
course/                  Kho dữ liệu — nguồn sự thật của khóa học
  course.yaml            Thông tin khóa học (tên, đối tượng, hashtag) bằng 3 thứ tiếng
  curriculum.yaml        Cây khóa học: chương → chủ đề → bài (lộ trình)
  sections.yaml          Các phần của một bài học và thứ tự của chúng
  glossary.yaml          Thuật ngữ Việt · Anh · Nhật (kèm cách đọc tiếng Nhật)
  lessons/<id>/          Mỗi bài một thư mục: vi.md, en.md, ja.md
  OUTLINE.md             Lộ trình dạng bảng — tự động sinh từ curriculum.yaml
brainstorm/              Brief và kết quả brainstorm lộ trình với Codex
docs/
  content-guide.md       Cách viết một bài học (giọng văn, 3 thứ tiếng, quiz, nguồn)
  data-model.md          Cấu trúc dữ liệu và các quy tắc được kiểm tra tự động
  facebook-plan.md       Kế hoạch đăng Facebook từ kho dữ liệu
  decisions/             Các quyết định kiến trúc (ADR)
src/                     Chương trình quản lý kho dữ liệu (python -m src.main)
tests/                   Test cho chương trình (và cho harness của template)
```

Repo được tạo từ [`claude-agent-routing-template`](TEMPLATE.md), nên có sẵn harness cho Claude Code:
`CLAUDE.md`, các agent và skill trong `.claude/`, chính sách routing trong `agent-routing/`, và
giao thức làm việc với Codex trong [`docs/claude-to-codex.md`](docs/claude-to-codex.md).

## Chương trình quản lý kho dữ liệu

Cần Python 3.10+ và PyYAML (`python -m pip install -r requirements-eval.txt`). Chạy từ thư mục gốc
của repo; thêm `--lang vi|en|ja` để chọn ngôn ngữ thông báo.

```bash
python -m src.main validate                  # kiểm tra toàn bộ kho dữ liệu (CI cũng chạy)
python -m src.main stats                     # quy mô khóa học + tiến độ viết theo từng ngôn ngữ
python -m src.main outline --write           # sinh lại course/OUTLINE.md sau khi sửa curriculum.yaml
python -m src.main scaffold what-is-software # tạo sẵn khung 3 file cho một bài mới
python -m src.main fb-draft chatbot-to-agent --post-lang vi   # bản nháp bài đăng Facebook
```

## Quy trình viết một bài

1. `scaffold <lesson-id>` → có sẵn `vi.md`, `en.md`, `ja.md` ở trạng thái `todo`.
2. Viết bản **tiếng Việt** trước (ngôn ngữ gốc), theo [docs/content-guide.md](docs/content-guide.md).
3. Bản địa hóa sang tiếng Anh và tiếng Nhật — giữ nguyên các phần, thay ví dụ cho hợp văn hóa.
4. `validate` cho đến khi sạch lỗi; đổi trạng thái `draft → review → done`.
5. Bài `done` → `fb-draft` → đọc lại → đăng Facebook (xem [docs/facebook-plan.md](docs/facebook-plan.md)).

## Các giai đoạn

| Giai đoạn | Nội dung | Trạng thái |
|---|---|---|
| 0 | Kho dữ liệu, lộ trình v0, bài mẫu, brainstorm lộ trình với Codex | đang làm |
| 1 | Chốt lộ trình v1; viết "lộ trình tối thiểu" (vi trước, rồi en/ja) | sắp tới |
| 2 | Đăng Facebook đều đặn từ kho dữ liệu | sắp tới |
| 3 | Website khóa học: cây khóa học, tiến độ, mục lục từng bài | sau này |
