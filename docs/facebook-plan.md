# Kế hoạch đăng Facebook từ kho dữ liệu

Mục tiêu: đăng **đều đặn** về AI agentic coding cho người mới, mà không phải nghĩ lại nội dung mỗi
tuần. Mọi bài đăng đều sinh ra từ kho dữ liệu `course/` — sửa một bài học hay một thuật ngữ là mọi
bài đăng về sau tự đúng theo.

## Nguyên tắc

- **Một nguồn sự thật.** Không viết bài đăng từ đầu; bài đăng là "lát cắt" của một bài học `done`.
- **Người duyệt cuối cùng là Linh.** Công cụ chỉ soạn nháp; đăng lúc nào, sửa câu chữ ra sao là
  quyết định của người.
- **Nhất quán hơn số lượng.** 3 bài/tuần đều đặn tốt hơn 10 bài một tuần rồi nghỉ một tháng.

## Năm dạng bài đăng lấy từ một bài học

| Dạng | Lấy từ đâu trong kho dữ liệu | Mục đích |
|---|---|---|
| A. Bài học | `social.hook` + tiêu đề + `summary` + phần `takeaways` + thuật ngữ + `social.question` (lệnh `fb-draft`) | giá trị chính, kéo người đọc vào khóa học |
| B. Ví dụ đời thường | phần `analogy` | dễ chia sẻ, dễ lan truyền |
| C. Đố vui | phần `quiz` (câu hỏi hôm nay, đáp án ở bình luận / bài sau) | tương tác, ôn tập ngắt quãng |
| D. Thuật ngữ 3 thứ tiếng | một mục trong `glossary.yaml` | học AI + từ vựng Anh/Nhật; 43 bài có sẵn |
| E. Tổng kết tuần | câu hỏi cộng đồng + link các bài trong tuần | xây cộng đồng |

Hiện đã tự động hóa dạng **A** (`python -m src.main fb-draft <lesson-id>`). Các dạng B–E sẽ được
thêm vào chương trình khi bắt đầu giai đoạn đăng bài.

## Nhịp đăng đề xuất

| Ngày | Dạng | Ví dụ |
|---|---|---|
| Thứ 2 | A. Bài học của tuần | "Google Maps chỉ đường cho bạn tự lái. Tài xế taxi thì chở bạn tới nơi…" |
| Thứ 4 | D. Thuật ngữ 3 thứ tiếng (hoặc B) | "AI agent · AIエージェント · tác tử AI" |
| Thứ 6 | C. Đố vui | "Việc nào cần AI agent thay vì chatbot? A/B/C — đáp án ở bình luận" |

Một bài học mỗi tuần → lộ trình v0 (57 bài) đủ cho khoảng một năm. Nên đăng theo **lộ trình tối
thiểu** (chốt sau buổi brainstorm với Codex) trước, rồi mới đến các bài nâng cao.

## Quy trình mỗi tuần

1. Chọn bài học tiếp theo có trạng thái `done` (xem `python -m src.main stats`).
2. `python -m src.main fb-draft <lesson-id> --post-lang vi --out outputs/facebook/<lesson-id>-vi.txt`
3. Đọc lại, chỉnh câu chữ cho hợp giọng Facebook, chọn ảnh minh họa.
4. Hẹn giờ đăng trong Meta Business Suite.
5. Ghi lại bài đã đăng (giai đoạn 2 sẽ có file nhật ký đăng bài trong repo).

Thư mục `outputs/` không được commit — đó là bản nháp, không phải nguồn sự thật.

## Các giai đoạn tự động hóa

| Giai đoạn | Làm gì | Ghi chú |
|---|---|---|
| 1 — thủ công (bây giờ) | `fb-draft` soạn nháp dạng A, người đăng tay | không cần token, không rủi ro |
| 2 — bán tự động | sinh cả 5 dạng bài và một lịch đăng (CSV) để tải lên Meta Business Suite; nhật ký đăng bài trong repo | vẫn có người duyệt từng bài |
| 3 — tự động | đăng qua Facebook Graph API lên **Fanpage** (không áp dụng cho trang cá nhân) | token chỉ nằm trong `.env` (xem `.env.example`), không bao giờ trong repo; giữ bước duyệt |

## Đo lường

Mỗi tháng xem: lượt tiếp cận, lượt lưu, bình luận, lượt theo dõi mới — theo từng dạng bài. Dạng nào
được lưu và bình luận nhiều nhất thì tăng tần suất; bài học nào có nhiều câu hỏi trong bình luận thì
cần viết lại cho dễ hiểu hơn (ghi vào `PROGRESS.md`).

## Lưu ý

- Không đăng thông tin nội bộ của công ty hay dự án, kể cả làm ví dụ.
- Ghi nguồn khi dùng ý của người khác; chỉ dùng ảnh có quyền sử dụng.
- Trang tiếng Việt trước; bản tiếng Nhật và tiếng Anh có thể dùng cho nhóm/trang khác sau
  (`--post-lang ja`, `--post-lang en`).
