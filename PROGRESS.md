# PROGRESS

> Đọc file này đầu tiên khi bắt đầu một phiên làm việc mới (người hay AI đều vậy).

## Trạng thái hiện tại (cập nhật: 2026-09-27)

- **Đang làm:** Giai đoạn 1 — lộ trình v1 đã chốt sau 2 vòng brainstorm với Codex
  ([brainstorm/round-2.md](brainstorm/round-2.md), [ADR 007](docs/decisions/007-roadmap-v1.md)); viết cả
  khóa học bằng 3 thứ tiếng, theo thứ tự lộ trình tối thiểu rồi đến phần còn lại (Linh quyết định
  2026-09-27: không cần người bản ngữ duyệt bản tiếng Nhật).
- **Đã xong:**
  - Repo tạo từ `claude-agent-routing-template` (harness Claude Code, giao thức Codex).
  - **Mỗi ngôn ngữ một thư mục** (`course/vi`, `course/en`, `course/ja`): mọi trang chỉ dùng một
    ngôn ngữ và có thanh 🌐 để chuyển ngôn ngữ; dữ liệu dùng chung nằm ở `course/data/`
    ([ADR 005](docs/decisions/005-language-folders-and-language-bar.md)).
  - **Lộ trình v1** (6 chương · 17 chủ đề · 52 bài · 893 phút), rút ra từ vòng 1 brainstorm với Codex
    ([brainstorm/round-1.md](brainstorm/round-1.md)) và 4 quyết định của Linh: thực hành ngay buổi đầu,
    **lộ trình tối thiểu 19 bài** (347 phút) đi trước, phần sâu thành nhánh tùy chọn / nâng cao,
    9 bài cũ được gộp hoặc bỏ (id không bao giờ dùng lại).
  - **Infographic:** bộ vẽ SVG từ một file nội dung cho cả 3 ngôn ngữ, 5 mẫu (compare, equation,
    cycle, flow, summary) + bản đồ lộ trình ([ADR 006](docs/decisions/006-infographics-as-generated-svg.md)).
    Không ô nào bị vẽ đè lên ô khác; sơ đồ quá nhiều chữ bị `validate` báo lỗi `diagram_crowded`.
  - **Bài nào cũng có hình tóm tắt cả bài** (phần "Tóm tắt bằng hình", mẫu `summary`) — `validate`
    bắt buộc từ trạng thái `review` ([ADR 008](docs/decisions/008-a-recap-infographic-in-every-lesson.md)).
  - Hai bài mẫu đủ 3 thứ tiếng, trạng thái `review` (chờ Linh duyệt): `chatbot-to-agent` và
    `agent-parts-and-loop` (tách từ bài mẫu cũ theo góp ý của Codex).
  - Chương trình `python -m src.main`: `validate`, `build`, `stats`, `scaffold`, `fb-draft`, `export`
    (thông báo bằng vi/en/ja), có test, mutation check và bước kiểm tra trong CI.
  - **Chia sẻ không cần GitHub:** `export` ghi file HTML tự chứa vào `outputs/html/` — một file đủ
    3 thứ tiếng và một file cho mỗi ngôn ngữ; in ra PDF được
    ([ADR 009](docs/decisions/009-offline-html-export.md)).
- **Chưa xong / đang vướng:**
  - Linh duyệt các bài ở trạng thái `review` (giọng văn, độ dài, ví dụ, infographic) → `done`.
  - 17 bài còn lại của lộ trình tối thiểu, rồi 33 bài còn lại của lộ trình, chưa viết. Khi thử thật
    công cụ cho buổi thực hành đầu tiên (trình duyệt, máy cá nhân, máy công ty), cập nhật
    `choose-your-learning-setup` và `first-agent-session` theo kết quả.
  - Website có nút chuyển ngôn ngữ (giai đoạn 3) — hiện dùng thanh 🌐 trên GitHub.
- **Quyết định gần nhất:** [docs/decisions/](docs/decisions/) 007 (lộ trình v1, và quyết định viết cả
  khóa học ngay), 008 (hình tóm tắt trong mọi bài), 009 (file HTML xem offline).

## Bước tiếp theo

1. Viết các bài của lộ trình tối thiểu theo thứ tự, bắt đầu từ `watch-an-agent-build`
   (`python -m src.main scaffold <lesson-id>`), cả 3 thứ tiếng, mỗi bài một hình tóm tắt, theo các quy
   ước chung trong [docs/content-guide.md](docs/content-guide.md); thử 6 bài đầu với vài người học thật.
2. Sau mỗi đợt bài mới: `python -m src.main export` để có bản HTML mới gửi đồng nghiệp.
3. Bắt đầu đăng Facebook từ các bài `done`: `python -m src.main fb-draft <lesson-id>`, ảnh đăng kèm là
   hình tóm tắt của bài.
