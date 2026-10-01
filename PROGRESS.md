# PROGRESS

> Đọc file này đầu tiên khi bắt đầu một phiên làm việc mới (người hay AI đều vậy).

## Trạng thái hiện tại (cập nhật: 2026-09-30)

- **Đang làm:** Giai đoạn 1 — lộ trình v1 đã chốt sau 2 vòng brainstorm với Codex
  ([brainstorm/round-2.md](brainstorm/round-2.md), [ADR 007](docs/decisions/007-roadmap-v1.md)); viết cả
  khóa học bằng 3 thứ tiếng, theo thứ tự lộ trình tối thiểu rồi đến phần còn lại (Linh quyết định
  2026-09-27: không cần người bản ngữ duyệt bản tiếng Nhật).
- **Đã xong:**
  - Repo tạo từ `claude-agent-routing-template` (harness Claude Code, giao thức Codex).
  - **Mỗi ngôn ngữ một thư mục** (`course/vi`, `course/en`, `course/ja`): mọi trang chỉ dùng một
    ngôn ngữ và có thanh 🌐 để chuyển ngôn ngữ; dữ liệu dùng chung nằm ở `course/data/`
    ([ADR 005](docs/decisions/005-language-folders-and-language-bar.md)).
  - **Lộ trình v1** (6 chương · 17 chủ đề · 52 bài · 946 phút), rút ra từ vòng 1 brainstorm với Codex
    ([brainstorm/round-1.md](brainstorm/round-1.md)) và 4 quyết định của Linh: thực hành ngay buổi đầu,
    **lộ trình tối thiểu 19 bài** (347 phút) đi trước, phần sâu thành nhánh tùy chọn / nâng cao,
    9 bài cũ được gộp hoặc bỏ (id không bao giờ dùng lại).
  - **Infographic:** bộ vẽ SVG từ một file nội dung cho cả 3 ngôn ngữ, 5 mẫu (compare, equation,
    cycle, flow, summary) + bản đồ lộ trình ([ADR 006](docs/decisions/006-infographics-as-generated-svg.md)).
    Không ô nào bị vẽ đè lên ô khác; sơ đồ quá nhiều chữ bị `validate` báo lỗi `diagram_crowded`.
  - **Bài nào cũng có hình tóm tắt cả bài** (phần "Tóm tắt bằng hình", mẫu `summary`) — `validate`
    bắt buộc từ trạng thái `review` ([ADR 008](docs/decisions/008-a-recap-infographic-in-every-lesson.md)).
  - **Lộ trình tối thiểu viết xong: 19 bài** (347 phút), đủ 3 thứ tiếng, trạng thái `review` (chờ Linh
    duyệt), mỗi bài một infographic giải thích và một hình tóm tắt; hai dự án có dữ liệu mẫu và kết quả
    đúng biết trước. Dữ kiện về công cụ ghi rõ "tính đến tháng 9/2026" và dẫn tài liệu chính thức.
  - Đã viết thêm `how-to-learn-this-course`, `programming-building-blocks`, `command-line-basics`,
    `ai-ml-dl`, `how-machines-learn` (PR #10), `rag-intro`, `prompt-rag-finetune-compare` (PR #11),
    `tokens`, `reasoning-models` (PR #12), `choosing-models`,
    `traditional-vs-agentic` (PR #13), `vibe-vs-agentic`, `the-agent-loop` (PR #15), `tool-landscape`,
    `workflow-frameworks` (PR #16), `model-plus-harness`, `context-engineering`, `prompt-engineering-for-agents`, `hooks-and-permissions`, `tests-and-ci-for-agents`, `memory-and-skills`, `agents-and-workflows`, `mcp`; Codex viết `security-basics`, `prompting-basics` (PR #5),
    `next-token-prediction`, `tool-calling` (PR #8), `what-is-software`, `project-anatomy` (PR #9) —
    **48/52 bài**. Từ PR #10, mỗi đợt Claude viết đều
    qua Codex review (tối đa 2 vòng) trước khi Linh merge.
  - `validate` báo lỗi khi một sơ đồ phải cắt đôi một từ vì ô quá hẹp (`diagram_word_split`), khi đáp
    án quiz khác nhau giữa các ngôn ngữ, và khi nhắc tới một bài bằng số thứ tự hay vị trí.
  - Chương trình `python -m src.main`: `validate`, `build`, `stats`, `scaffold`, `fb-draft`, `export`
    (thông báo bằng vi/en/ja), có test, mutation check và bước kiểm tra trong CI.
  - **Chia sẻ không cần GitHub:** `export` ghi file HTML tự chứa vào `outputs/html/` — một file đủ
    3 thứ tiếng và một file cho mỗi ngôn ngữ; in ra PDF được
    ([ADR 009](docs/decisions/009-offline-html-export.md)).
- **Chưa xong / đang vướng:**
  - Linh duyệt 48 bài ở trạng thái `review` (giọng văn, độ dài, ví dụ, infographic) → `done`.
  - 4 bài còn lại (bảng trong [docs/handoff.md](docs/handoff.md)). Khi thử thật
    công cụ cho buổi thực hành đầu tiên (trình duyệt, máy cá nhân, máy công ty), cập nhật
    `choose-your-learning-setup` và `first-agent-session` theo kết quả.
  - Môi trường làm việc của Claude chặn nhiều trang tài liệu (Wikipedia, Microsoft, Apple, MDN,
    docs.github.com, docs.python.org…), nên nguồn tham khảo hiện chỉ lấy từ tài liệu của Anthropic và
    Google Cloud. Mở thêm trong cài đặt Network access của môi trường nếu muốn nguồn đa dạng hơn.
  - Website có nút chuyển ngôn ngữ (giai đoạn 3) — hiện dùng thanh 🌐 trên GitHub.
- **Quyết định gần nhất:** [docs/decisions/](docs/decisions/) 007 (lộ trình v1, và quyết định viết cả
  khóa học ngay), 008 (hình tóm tắt trong mọi bài), 009 (file HTML xem offline), 010 (Claude viết bài,
  Codex review).

## Bước tiếp theo

1. Linh đọc duyệt lộ trình tối thiểu (bản HTML: `python -m src.main export`), thử 6 bài đầu với vài
   người học thật, rồi đổi các bài đạt sang `done`.
2. **Cách làm (Linh quyết định 27/9/2026, [ADR 010](docs/decisions/010-claude-writes-codex-reviews.md)):
   Claude viết bài, Codex review.** Mỗi đợt khoảng 2 bài × 3 thứ tiếng nằm trên một nhánh `claude/…`
   và một PR; Claude gọi Codex review ngay trên PR (không cần bấm Create PR), sửa các lỗi đã kiểm
   chứng; **Linh bấm Merge** khi CI xanh. Bản bàn giao: [docs/handoff.md](docs/handoff.md). Sau mỗi
   đợt, xuất lại HTML.
3. Bắt đầu đăng Facebook từ các bài `done`: `python -m src.main fb-draft <lesson-id>`, ảnh đăng kèm là
   hình tóm tắt của bài.
