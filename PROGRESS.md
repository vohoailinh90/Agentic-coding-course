# PROGRESS

> Đọc file này đầu tiên khi bắt đầu một phiên làm việc mới (người hay AI đều vậy).

## Trạng thái hiện tại (cập nhật: 2026-09-26)

- **Đang làm:** Giai đoạn 0 — brainstorm lộ trình v0 → v1 với Codex. Brief ở
  [brainstorm/BRIEF.md](brainstorm/BRIEF.md); tiến trình từng vòng ở
  [brainstorm/README.md](brainstorm/README.md).
- **Đã xong:**
  - Repo tạo từ `claude-agent-routing-template` (harness Claude Code, giao thức Codex).
  - Kho dữ liệu `course/`: thông tin khóa học, lộ trình v0 (7 chương · 17 chủ đề · 57 bài),
    43 thuật ngữ 3 thứ tiếng, cấu trúc 11 phần của một bài học.
  - Bài mẫu `chatbot-to-agent` đủ 3 thứ tiếng, trạng thái `review` (chờ Linh duyệt).
  - Chương trình `python -m src.main`: `validate`, `stats`, `outline`, `scaffold`, `fb-draft`
    (thông báo bằng vi/en/ja), có test, mutation check và bước kiểm tra trong CI.
  - Tài liệu: hướng dẫn viết bài, mô hình dữ liệu, kế hoạch Facebook, 4 ADR.
- **Chưa xong / đang vướng:**
  - Chờ Codex trả lời vòng brainstorm 1, rồi Claude kiểm chứng câu trả lời theo
    `docs/claude-to-codex.md` §14.
  - Linh duyệt bài mẫu (giọng văn, độ dài, ví dụ) → đổi trạng thái `review` → `done`.
  - 56 bài còn lại chưa viết — chờ chốt lộ trình v1 và "lộ trình tối thiểu".
- **Quyết định gần nhất:** [docs/decisions/](docs/decisions/) 001–004.

## Bước tiếp theo

1. Đọc câu trả lời của Codex trong issue brainstorm; ghi kết luận vào `brainstorm/round-1.md`.
2. Cập nhật `course/curriculum.yaml` thành v1, rồi chạy `python -m src.main outline --write`.
3. Viết các bài của lộ trình tối thiểu: `python -m src.main scaffold <lesson-id>`.
4. Bắt đầu đăng Facebook từ các bài `done`: `python -m src.main fb-draft <lesson-id>`.
