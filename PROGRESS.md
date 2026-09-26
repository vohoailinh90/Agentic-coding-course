# PROGRESS

> Đọc file này đầu tiên khi bắt đầu một phiên làm việc mới (người hay AI đều vậy).

## Trạng thái hiện tại (cập nhật: 2026-09-26)

- **Đang làm:** Giai đoạn 1 — lộ trình v1 đã áp dụng
  ([ADR 007](docs/decisions/007-roadmap-v1.md)); vòng 2 với Codex soát lại lộ trình v1 trong
  [issue #1](https://github.com/vohoailinh90/Agentic-coding-course/issues/1) (vòng cuối).
- **Đã xong:**
  - Repo tạo từ `claude-agent-routing-template` (harness Claude Code, giao thức Codex).
  - **Mỗi ngôn ngữ một thư mục** (`course/vi`, `course/en`, `course/ja`): mọi trang chỉ dùng một
    ngôn ngữ và có thanh 🌐 để chuyển ngôn ngữ; dữ liệu dùng chung nằm ở `course/data/`
    ([ADR 005](docs/decisions/005-language-folders-and-language-bar.md)).
  - **Lộ trình v1** (6 chương · 17 chủ đề · 52 bài · 893 phút), rút ra từ vòng 1 brainstorm với Codex
    ([brainstorm/round-1.md](brainstorm/round-1.md)) và 4 quyết định của Linh: thực hành ngay buổi đầu,
    **lộ trình tối thiểu 18 bài** (337 phút) đi trước, phần sâu thành nhánh tùy chọn / nâng cao,
    9 bài cũ được gộp hoặc bỏ (id không bao giờ dùng lại).
  - **Infographic:** bộ vẽ SVG từ một file nội dung cho cả 3 ngôn ngữ, 5 mẫu (compare, equation,
    cycle, flow, summary) + bản đồ lộ trình ([ADR 006](docs/decisions/006-infographics-as-generated-svg.md)).
    Không ô nào bị vẽ đè lên ô khác; sơ đồ quá nhiều chữ bị `validate` báo lỗi `diagram_crowded`.
  - **Bài nào cũng có hình tóm tắt cả bài** (phần "Tóm tắt bằng hình", mẫu `summary`) — `validate`
    bắt buộc từ trạng thái `review` ([ADR 008](docs/decisions/008-a-recap-infographic-in-every-lesson.md)).
  - Hai bài mẫu đủ 3 thứ tiếng, trạng thái `review` (chờ Linh duyệt): `chatbot-to-agent` và
    `agent-parts-and-loop` (tách từ bài mẫu cũ theo góp ý của Codex).
  - Chương trình `python -m src.main`: `validate`, `build`, `stats`, `scaffold`, `fb-draft`
    (thông báo bằng vi/en/ja), có test, mutation check và bước kiểm tra trong CI.
- **Chưa xong / đang vướng:**
  - Codex vòng 2: soát lộ trình v1; Claude kiểm chứng theo `docs/claude-to-codex.md` §14.
  - Linh duyệt hai bài mẫu (giọng văn, độ dài, ví dụ, infographic) → đổi trạng thái `review` → `done`.
  - 16 bài còn lại của lộ trình tối thiểu chưa viết; phải thử thật công cụ cho buổi thực hành đầu tiên
    (trình duyệt, máy cá nhân, máy công ty) trước khi viết `choose-your-learning-setup` và
    `first-agent-session`.
  - Website có nút chuyển ngôn ngữ (giai đoạn 3) — hiện dùng thanh 🌐 trên GitHub.
- **Quyết định gần nhất:** [docs/decisions/](docs/decisions/) 007 (lộ trình v1) và 008 (hình tóm tắt
  trong mọi bài).

## Bước tiếp theo

1. Kiểm chứng câu trả lời vòng 2 của Codex; ghi kết luận vào `brainstorm/round-2.md`.
2. Viết các bài của lộ trình tối thiểu theo thứ tự (`python -m src.main scaffold <lesson-id>`), bản
   tiếng Việt trước, mỗi bài một hình tóm tắt; thử 6 bài đầu với vài người học thật.
3. Bắt đầu đăng Facebook từ các bài `done`: `python -m src.main fb-draft <lesson-id>`, ảnh đăng kèm là
   hình tóm tắt của bài.
