# Vòng 2 — kết luận (ACC-0001, vòng cuối)

- Issue: [#1](https://github.com/vohoailinh90/Agentic-coding-course/issues/1) · yêu cầu:
  [bình luận 5850701628](https://github.com/vohoailinh90/Agentic-coding-course/issues/1#issuecomment-5850701628)
  · trả lời của Codex: [bình luận 5850735921](https://github.com/vohoailinh90/Agentic-coding-course/issues/1#issuecomment-5850735921)
  (bản sao nguyên văn: [round-2-codex.md](round-2-codex.md))
- Chế độ `BRAINSTORM`, chỉ đọc, trên commit `44c7fb8b44064be2f0b648937861e1eed00a1e88` (2026-09-26).
- Lần gửi đầu của vòng 2 (trên `8c942d2`) không chạy vì repo chưa có Codex environment; Linh tạo
  environment rồi yêu cầu được gửi lại trên commit trên.

## Kiểm chứng (docs/claude-to-codex.md §14)

```yaml
task_id: "ACC-0001"
codex_mode: "BRAINSTORM"
requested_sha: "44c7fb8b44064be2f0b648937861e1eed00a1e88"
reported_sha: null
current_sha: "44c7fb8b44064be2f0b648937861e1eed00a1e88"
status: "ACCEPTED"
unresolved_findings: []
next_action: "All five findings applied; write the minimum-path lessons in order, starting with watch-an-agent-build."
```

| Tiêu chí nghiệm thu | Kết quả | Cách kiểm |
|---|---|---|
| Tối đa 10 góp ý, mỗi góp ý có mức độ, đường dẫn file và một thay đổi cụ thể | ✓ 5 góp ý (1 high, 3 medium, 1 low) | đọc |
| Nói rõ có đồng ý giữ `project-personal-page` ngay sau `errors-and-debugging` không | ✓ đồng ý, kèm 5 lý do | đọc |
| Mỗi thay đổi lộ trình nêu id bài và giữ lộ trình tối thiểu hợp lệ | ✓ | áp hai thay đổi lên một bản sao rồi chạy `validate`: hợp lệ, 19 bài · 347 phút |
| Soát hai bài mẫu ở từng ngôn ngữ vi, en, ja, có đường dẫn file | ✓ | đọc |
| Nêu SHA đã đọc; kết thúc bằng Tóm tắt 5 dòng | ✓ (một chữ bị lỗi mã hóa khi đăng: "chi���n thắng") | đọc |
| Không sửa gì trong repo | ✓ | không có nhánh hay PR mới; `main` vẫn ở SHA trên |

Bằng chứng Codex nêu (`validate` OK, `stats` 18 bài · 337 phút trước khi sửa) khớp với kết quả của Claude.

## Các góp ý và việc đã làm

| # | Góp ý của Codex | Việc đã làm |
|---|---|---|
| 1 (high) | Người học đọc thay đổi (diff) và gỡ lỗi trước khi học file và đường dẫn | Chuyển `files-folders-paths` lên chủ đề *Kiểm tra kết quả*, ngay trước `reviewing-agent-changes` (cả trong lộ trình tối thiểu) |
| 2 (medium) | Dự án văn phòng thiếu bài về dữ liệu (CSV, bảng, dữ liệu có cấu trúc) | Thêm `data-formats` vào lộ trình tối thiểu, sau `project-personal-page` → **19 bài · 347 phút** |
| 3 (medium) | Ba bản `agent-parts-and-loop` nói quá tuyệt đối "LLM chỉ viết ra chữ", "LLM chọn công cụ" | Sửa cả ba bản: mô hình tạo ra đầu ra (chữ, hoặc *yêu cầu* dùng công cụ); phần mềm của agent quyết định có cho phép và thực hiện |
| 4 (medium) | Sơ đồ `ai-three-levels` hứa agent nào cũng "tự lập kế hoạch, tự kiểm tra" | Đổi ô đó thành "Lập kế hoạch và tự làm; tự kiểm tra khi công cụ cho phép" (en, ja tương ứng) |
| 5 (low) | Bản en và ja giữ tên Việt "An" trong ví dụ | Đổi thành **Alex** (en) và **あおいちゃん** (ja); bản vi giữ **An** |

Codex **đồng ý** với cách đặt dự án trang web cá nhân ngay sau bài gỡ lỗi: người học có sản phẩm sớm,
áp dụng ngay vòng giám sát vừa học, và bài Git sau đó có lý do rõ ràng.

## Còn lại cho chủ khóa học

- **Ai đọc duyệt bản tiếng Nhật ở mức bản ngữ** trước khi hai bài mẫu chuyển sang `done`?
- Bộ dữ liệu bảng tính giả (và kết quả đúng) cho `project-office-automation` — chọn khi viết bài đó.
- Rủi ro Codex nhắc lại: môi trường cho buổi thực hành đầu tiên; điều kiện ngầm của dự án văn phòng;
  "một thư mục riêng" là ranh giới chứ chưa phải hộp cát (sandbox) — phải nói rõ trong
  `data-safety-and-permissions`; chi phí làm 52 hình tóm tắt bằng 3 thứ tiếng.

## Bước tiếp theo (theo gợi ý của Codex)

1. Chốt cho 6 bài mở đầu: một tình huống chung, ranh giới an toàn và cách trình bày bằng chứng.
2. Viết các bài của lộ trình tối thiểu theo thứ tự, bắt đầu từ `watch-an-agent-build`; bản tiếng Việt
   trước, mỗi bài một hình tóm tắt.
3. Brainstorm lộ trình đã dùng đủ 2 vòng; câu hỏi mới về lộ trình mở thành task mới.
