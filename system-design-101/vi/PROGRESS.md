# Tiến độ System Design tiếng Việt

Cập nhật 2026-10-12: 4/404 vị trí đã viết.

Bài sd-01-001–003 đã có Codex review không nêu vấn đề lớn và CI thành công:
head 034a992d1b90d023083b2fe03790c06fdf991bca, base 89186c1a1aeb90a47e2a563fdc7786b2dacec787,
review comment 6128611337, CI run 38279292220. Đây là review kỹ thuật trên snapshot đó,
không phải phê duyệt phát hành; user testing chưa thực hiện.

Đợt hiện tại: sd-01-004, gRPC trong PR #30; đang xử lý review.
Base của #30 là nhánh codex/system-design-vi-sd-01-002 ở SHA 034a992d1b90d023083b2fe03790c06fdf991bca.
GitHub xác nhận #25 vẫn open, merged=false; main hiện là 89186c1a1aeb90a47e2a563fdc7786b2dacec787.
Commit 034a992 đã tích hợp main vào nhánh #25, không phải đã merge PR #25 vào main.
Bài tiếp theo: sd-01-005 (NAT). Metadata JSON là nguồn trạng thái duy nhất, YAML chỉ trỏ tới JSON.
Không tự merge/deploy. Đọc progress và PR hiện hành trước mỗi lượt để tránh viết trùng.
