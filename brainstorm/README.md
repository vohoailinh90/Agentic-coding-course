# Brainstorm lộ trình học với Codex

Mục tiêu: tìm lộ trình **dễ hiểu nhất, gây hứng thú nhất và hiệu quả nhất** cho người chưa biết gì
về AI, trước khi viết hàng chục bài học bằng 3 thứ tiếng.

## Cách làm

1. Claude soạn lộ trình v0 ([course/data/curriculum.yaml](../course/data/curriculum.yaml), xem bản đồ
   lộ trình ở [course/vi/README.md](../course/vi/README.md)) và "đề bài" [BRIEF.md](BRIEF.md): người học là ai,
   ràng buộc gì, v0 dựa trên nguyên tắc nào, điểm yếu đã thấy, 11 câu hỏi cần trả lời.
2. Claude mở một GitHub Issue và gọi Codex **đúng một lần mỗi vòng**, theo giao thức
   [docs/claude-to-codex.md](../docs/claude-to-codex.md): chế độ `BRAINSTORM`, chỉ đọc
   (`write_policy: none`), gắn với một commit SHA cụ thể.
3. Codex trả lời trong issue. Claude **kiểm chứng** câu trả lời (§14 của giao thức): đúng issue,
   đúng SHA, trả lời đủ từng tiêu chí nghiệm thu — không nhận kết quả chỉ vì "Codex nói vậy".
4. Kết luận của mỗi vòng được ghi vào `round-<n>.md` trong thư mục này; quyết định cuối cùng
   (lộ trình v1) được cập nhật vào `course/data/curriculum.yaml`.
5. Tối đa **2 vòng** brainstorm. Những điểm cần Linh quyết định (sản phẩm, đối tượng, chi phí)
   được đưa lại cho Linh, không để AI tự quyết.

## Các vòng

| Vòng | Issue | Commit gửi Codex | Trạng thái | Kết luận |
|---|---|---|---|---|
| 1 | [#1](https://github.com/vohoailinh90/Agentic-coding-course/issues/1) | ghi trong bình luận gọi Codex và trong `round-1.md` | chờ Codex | |

## Nhãn trên GitHub

`ai:needs-codex-brainstorm` → `ai:waiting-for-codex` → `ai:codex-complete` →
`ai:ready-for-implementation`.
