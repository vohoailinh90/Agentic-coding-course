# System Design 101 — học bằng hình

Chương trình tiếng Việt bám sát mục lục ByteByteGo: **15 nhóm, 404 vị trí bài học**.
Các mục gần nhau hoặc dùng chung nguồn vẫn giữ ID và vị trí riêng.

## API và phát triển web

1. [Polling ngắn, polling dài, SSE và WebSocket](lessons/sd-01-001.md) — đã qua review ở PR #24.
2. [Ứng dụng thực tế của bộ cân bằng tải](lessons/sd-01-002.md) — đã viết, chờ review.
3. Các mã HTTP kỳ lạ và bối cảnh sử dụng — sẽ viết tiếp.

Danh mục đầy đủ và snapshot nguồn: [bảng đối chiếu](../../brainstorm/system-design-101-vi/source-map.json).
Quy tắc đã chốt: [kết luận brainstorm](../../brainstorm/system-design-101-vi/DECISIONS.md).
Tiến độ từng đợt: [PROGRESS.md](PROGRESS.md).

## Cách đọc một bài

Nhìn hình trước → đọc vài chú thích → thử trả lời câu hỏi. Mục “Xem sâu hơn” là tùy chọn.
Không cần đọc phần nâng cao để nắm ý chính. Các sơ đồ được thiết kế mới cho chương trình này.

## Quy ước biên soạn

- `lessons/<id>.md`: bài tiếng Việt.
- `diagrams/<id>-main.svg`: hình chính, có mô tả văn bản trong SVG và alt text trong bài.
- `metadata/<id>.json`: trạng thái bài, nguồn ghim phiên bản, claim và kiểm chứng.
- `progress.json`: bài đã viết và ID sẽ viết tiếp; cập nhật sau mỗi đợt.

Trạng thái nội dung: `draft → review → done`. Kiểm chứng nguồn, review kỹ thuật,
kiểm tra hình mobile và thử với người học được ghi riêng. `done` cần review kỹ thuật
và hình đạt; không coi đọc nguồn là mọi claim đã đúng, không coi screenshot là user testing.

## Các nhóm còn lại theo thứ tự nguồn

Tình huống thực tế → AI và học máy → Cơ sở dữ liệu và lưu trữ → Phỏng vấn kỹ thuật →
Bộ nhớ đệm và hiệu năng → Thanh toán và công nghệ tài chính → Kiến trúc phần mềm →
Công cụ và năng suất → Phát triển phần mềm → Đám mây và hệ thống phân tán →
Hệ thống hoạt động thế nào? → DevOps và CI/CD → Bảo mật → Nền tảng máy tính.
