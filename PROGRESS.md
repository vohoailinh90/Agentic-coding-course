# PROGRESS

> Đọc file này đầu tiên khi bắt đầu một phiên làm việc mới (người hay AI đều vậy).

## Trạng thái hiện tại (cập nhật: 2026-09-26)

- **Đang làm:** Giai đoạn 0 — brainstorm lộ trình v0 → v1 với Codex trong
  [issue #1](https://github.com/vohoailinh90/Agentic-coding-course/issues/1). Brief ở
  [brainstorm/BRIEF.md](brainstorm/BRIEF.md); tiến trình từng vòng ở
  [brainstorm/README.md](brainstorm/README.md).
- **Đã xong:**
  - Repo tạo từ `claude-agent-routing-template` (harness Claude Code, giao thức Codex).
  - **Mỗi ngôn ngữ một thư mục** (`course/vi`, `course/en`, `course/ja`): mọi trang chỉ dùng một
    ngôn ngữ và có thanh 🌐 để chuyển ngôn ngữ; dữ liệu dùng chung nằm ở `course/data/`
    ([ADR 005](docs/decisions/005-language-folders-and-language-bar.md)).
  - Lộ trình v0 (7 chương · 17 chủ đề · 57 bài), 43 thuật ngữ 3 thứ tiếng, cấu trúc 11 phần của
    một bài học; trang chủ khóa học, trang thuật ngữ và bản đồ lộ trình được sinh tự động cho mỗi
    ngôn ngữ.
  - **Infographic:** bộ vẽ SVG từ một file nội dung cho cả 3 ngôn ngữ, 4 mẫu (compare, equation,
    cycle, flow) + bản đồ lộ trình ([ADR 006](docs/decisions/006-infographics-as-generated-svg.md)).
    Không ô nào bị vẽ đè lên ô khác (có test trên chữ dài ở cả 3 ngôn ngữ); sơ đồ quá nhiều chữ bị
    `validate` báo lỗi `diagram_crowded`.
  - Bài mẫu `chatbot-to-agent` đủ 3 thứ tiếng, có 4 infographic, trạng thái `review` (chờ Linh duyệt).
  - Chương trình `python -m src.main`: `validate`, `build`, `stats`, `scaffold`, `fb-draft`
    (thông báo bằng vi/en/ja), có test, mutation check và bước kiểm tra trong CI.
- **Chưa xong / đang vướng:**
  - Brainstorm với Codex (vòng 1, issue #1): chờ Codex trả lời; Claude kiểm chứng câu trả lời theo
    `docs/claude-to-codex.md` §14 rồi ghi kết luận vào `brainstorm/round-1.md`.
  - Linh duyệt bài mẫu (giọng văn, độ dài, ví dụ, infographic) → đổi trạng thái `review` → `done`.
  - 56 bài còn lại chưa viết — chờ chốt lộ trình v1 và "lộ trình tối thiểu".
  - Website có nút chuyển ngôn ngữ (giai đoạn 3) — hiện dùng thanh 🌐 trên GitHub.
- **Quyết định gần nhất:** [docs/decisions/](docs/decisions/) 005 (thư mục theo ngôn ngữ) và 006
  (infographic SVG).

## Bước tiếp theo

1. Đọc câu trả lời của Codex trong issue brainstorm; ghi kết luận vào `brainstorm/round-1.md`.
2. Cập nhật `course/data/curriculum.yaml` thành v1, rồi chạy `python -m src.main build`.
3. Viết các bài của lộ trình tối thiểu: `python -m src.main scaffold <lesson-id>`, vẽ infographic
   cho từng ý chính (`course/data/diagrams/`).
4. Bắt đầu đăng Facebook từ các bài `done`: `python -m src.main fb-draft <lesson-id>`.
