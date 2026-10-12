# Kết luận brainstorm — System Design tiếng Việt

Ngày chốt: 2026-10-12. Người dùng đã giao viết lần lượt từng bài sau brainstorm.

## Evidence và giới hạn

- [Phản hồi vòng 1](https://github.com/vohoailinh90/Agentic-coding-course/pull/23#issuecomment-6126033008)
  trả lời đủ 8 câu hỏi, đúng commit `1f5d505013def2c007a89eefff7ae571a8688a5a`.
- [Phản biện vòng 2](https://github.com/vohoailinh90/Agentic-coding-course/pull/23#issuecomment-6126126060)
  có 7 điểm cần thu gọn. Phản hồi sau đó là **code review** với hai finding, không phải
  câu trả lời đủ 7 điểm. Không ghi nhận là Codex đã phê duyệt toàn bộ quyết định dưới đây.
- Hai finding đã xử lý: ghim commit/tree và blob từng bài nguồn; đổi nhãn SSE thành
  “Đơn được xác nhận”. Đây là kết luận biên tập của người biên soạn để tiếp tục trong phạm vi
  người dùng đã giao, không phải kết quả user testing hay xác nhận của ByteByteGo.
- Kiểm kê độc lập: 15 nhóm, 404 ID, 400 đường dẫn nguồn duy nhất; vẫn giữ đủ 404 vị trí.

## Quyết định để bắt đầu viết

| Hạng mục | Chốt |
|---|---|
| Mục lục | Đúng thứ tự nguồn; bài cùng nguồn có thể liên kết, không mất ID |
| Ngôn ngữ | Chỉ tiếng Việt; tên công nghệ giữ nguyên |
| Kho nội dung | `system-design-101/vi/`, nằm ngoài `course/` của khóa cũ |
| Mật độ | Mặc định mềm 150–300 từ phần chính; phần sâu tùy chọn, không viết cho đủ quota |
| Hình | Một hình chính hoặc các khung so sánh dọc; không thêm hình trùng ý |
| Đánh đổi | Một giới hạn, ngộ nhận hoặc bối cảnh quan trọng; không ép failure mode lên mọi bài |
| Tiến độ | `content_status` riêng; đọc nguồn, kiểm chứng, kỹ thuật và mobile là các trạng thái riêng |
| Duyệt | Ghim nguồn, kiểm chứng claim, review kỹ thuật, kiểm tra hình mobile |
| Người học thử | Ghi riêng; chưa thực hiện thì không báo đạt, không chặn việc viết nháp |
| Công cụ | Metadata JSON + Markdown + SVG thiết kế mới; chưa xây framework renderer |
| PR | Đợt nhỏ theo thứ tự; gọi Codex review; chưa tự merge hoặc deploy |

## Phản biện kỹ thuật đã kiểm chứng độc lập

- [RFC 6202 §2.1–2.2](https://www.rfc-editor.org/rfc/rfc6202.html): polling ngắn hỏi định kỳ;
  polling dài trả khi có sự kiện hoặc hết hạn rồi mở request mới. Request lặp không có nghĩa
  TCP connection luôn bị tạo lại; không đưa hiểu lầm đó vào hình.
- [WHATWG SSE §9.2](https://html.spec.whatwg.org/multipage/server-sent-events.html): luồng sự kiện,
  điều kiện reconnect và Last-Event-ID. Reconnect không tự bảo đảm ứng dụng phát lại dữ liệu bị bỏ lỡ.
- [RFC 6455 §1.2](https://www.rfc-editor.org/rfc/rfc6455.html): sau handshake, hai phía có thể
  gửi dữ liệu độc lập. Chi tiết heartbeat/auth/backpressure để phần sâu, không chất lên bài nhập môn.

## Thứ tự triển khai

1. `sd-01-001`: Polling ngắn, polling dài, SSE và WebSocket.
2. `sd-01-002`: Ứng dụng thực tế của bộ cân bằng tải.
3. `sd-01-003`: Các mã HTTP kỳ lạ và bối cảnh sử dụng.
4. Sau đợt thử, tiếp tục từng ID theo bảng đối chiếu và ghi tiến độ bền vững trong kho mới.

Sửa chữa theo review sau này được ghi vào PR nội dung, không mở thêm vòng brainstorm tự động.
