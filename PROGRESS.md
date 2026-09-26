# PROGRESS

> Đọc file này đầu tiên khi bắt đầu một phiên làm việc mới (người hay AI đều vậy).

## Trạng thái hiện tại (cập nhật: 2026-09-26)

- **Đang làm:** Giai đoạn 0 — brainstorm lộ trình v0 → v1 với Codex trong
  [issue #1](https://github.com/vohoailinh90/Agentic-coding-course/issues/1). Vòng 1 xong và đã kiểm
  chứng: [brainstorm/round-1.md](brainstorm/round-1.md) — thực hành sớm, lộ trình tối thiểu 18 bài;
  chờ Linh trả lời các câu hỏi cần quyết định trong file đó.
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
  - Linh trả lời các câu hỏi cần quyết định trong `brainstorm/round-1.md` (ít nhất 1, 4, 5, 6).
  - Linh duyệt bài mẫu (giọng văn, độ dài, ví dụ, infographic) → đổi trạng thái `review` → `done`.
  - 56 bài còn lại chưa viết — chờ chốt lộ trình v1 và "lộ trình tối thiểu".
  - Website có nút chuyển ngôn ngữ (giai đoạn 3) — hiện dùng thanh 🌐 trên GitHub.
- **Quyết định gần nhất:** [docs/decisions/](docs/decisions/) 005 (thư mục theo ngôn ngữ) và 006
  (infographic SVG).

## Bước tiếp theo

1. Linh trả lời các câu hỏi cần quyết định trong [brainstorm/round-1.md](brainstorm/round-1.md).
2. Claude viết lộ trình v1 vào `course/data/curriculum.yaml` (giữ nguyên id), thêm các trường dữ liệu
   mới (track, lộ trình tối thiểu, bài học trước, kết quả đầu ra…) kèm kiểm tra, tách bài mẫu, rồi
   chạy `python -m src.main build`.
3. Vòng 2 với Codex (vòng cuối): soát `curriculum.yaml` v1.
4. Viết 6 bài mở đầu của lộ trình tối thiểu (`scaffold <lesson-id>`, vẽ infographic cho từng ý
   chính), thử với vài người học thật, rồi làm tiếp.
5. Bắt đầu đăng Facebook từ các bài `done`: `python -m src.main fb-draft <lesson-id>`.
