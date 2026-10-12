# Brief: chương trình System Design 101 bằng tiếng Việt

> Brief đầu vào của vòng brainstorm (đề xuất v0). Quyết định đã chốt nằm ở [DECISIONS.md](DECISIONS.md);
> nếu mâu thuẫn với bảng bên dưới thì DECISIONS.md thắng.

## Mục tiêu và phạm vi

Người học muốn hiểu cách hệ thống hoạt động qua hình và lời giải thích ngắn. Chương trình mới
bám sát **từng mục** của repo ByteByteGo: cùng chủ đề, thứ tự nhóm và thứ tự bài. Đợt này chỉ
brainstorm bằng draft PR, chưa viết cả khóa, chưa xuất bản website, chưa làm bản Anh hoặc Nhật.

Đề xuất người học đã từng dùng ứng dụng web nhưng mới học System Design. Đây là giả định để
Codex phản biện, không phải thông tin người dùng đã xác nhận.

## Những gì đã quan sát

- README nguồn hiện có 15 nhóm, 404 mục; bảng đối chiếu đã tìm được file Markdown tương ứng
  cho cả 404 mục. Đây là số mục trong mục lục, không khẳng định tất cả đều là chủ đề độc lập.
- Bài nguồn dùng ảnh lớn + lời giải thích gọn; giữ cách đọc này cho chương trình mới.
- Đã mở và đọc 8 bài: Polling/SSE/WebSocket, ứng dụng Load Balancer, mã HTTP kỳ lạ,
  Read Replica, Redis 101, AWS Lambda, IPC trên Linux, DevSecOps.
- Bài Load Balancer và bài mã HTTP cùng tham chiếu một URL ảnh
  (`…/0232-http-status-code-shouldnt-exist.png`; kiểm từ Markdown đã ghim, dòng 16 và dòng 14).
  Nội dung ảnh chưa được mở và chưa được ghim; nhận định "không phù hợp chủ đề" mới dựa trên tên file
  và việc trùng URL. Cần xem ảnh và tìm nguồn đúng trước khi biên soạn.
- Bài SSE dùng cách diễn đạt dễ khiến người đọc hiểu rằng browser không thể gửi request khác.
  Mẫu đề xuất ghi rõ **luồng SSE** chỉ đi một chiều; browser vẫn có thể gửi HTTP request riêng.
- Những bài kể kiến trúc công ty và công cụ cần giữ mốc thời gian nguồn, không biến mô tả lịch sử
  thành tuyên bố về hệ thống hiện tại. Redis 101 cần kiểm chứng danh sách module khi biên soạn.

## Quyết định đề xuất

| Vấn đề | Đề xuất v0 |
|---|---|
| Mục lục | Giữ nguyên 15 nhóm / 404 mục; nhãn và nội dung học bằng tiếng Việt |
| Bài gần trùng | Giữ ID riêng, thêm liên kết “đọc cùng”; không tự gộp hay bỏ |
| Bài khó với người mới | Thẻ “cần biết trước” dẫn sang bài cùng khóa; không đảo mục lục |
| Mật độ chữ | Mặc định mềm 150–300 từ phần chính, phần sâu tùy chọn (xem DECISIONS.md) |
| Hình | Sơ đồ chính + hình so sánh hoặc hình đánh đổi nếu cần |
| Màu | Xanh: client; tím: dịch vụ; xanh lá: dữ liệu; cam: chờ/cảnh báo |
| Trên điện thoại | Một luồng đọc dọc, chia hình rộng thành khung nhỏ, nhãn ngắn |
| Kiểm tra hiểu | Một câu hỏi đọc sơ đồ, đáp án ngắn có lý do |
| Kiến trúc nội dung | Đề xuất kho riêng `system-design-101/vi/`, metadata và assets riêng |
| Giai đoạn hiện tại | Chỉ `brainstorm/system-design-101-vi/`; chưa sửa schema của khóa cũ |

## Hình và nguồn

Mỗi bài có link nguồn gốc, commit/blob để đối chiếu, trạng thái đọc và kiểm chứng.
Sơ đồ được thiết kế mới từ kiến thức kỹ thuật đã kiểm chứng; không sao chép bố cục ảnh hay dịch
nguyên văn toàn bộ bài nguồn. Repo nguồn ghi [CC BY-NC-ND 4.0](https://github.com/ByteByteGoHq/system-design-101/blob/b28380a4710c5ec9638ec037d4168e288f334cba/LICENSE.md).
Nếu muốn phát hành bản dịch hoặc ảnh cải biên từ tài sản gốc, cần giải quyết quyền sử dụng trước.
Đợt brainstorm chỉ dùng metadata đối chiếu, link nguồn và sơ đồ tự thiết kế.

## Câu hỏi cần Codex brainstorm

1. Cách giữ đủ 404 mục mà người mới không bị ngợp? Đề xuất thẻ kiến thức nền và điều hướng;
   không thay mục lục nguồn bằng một lộ trình rút gọn.
2. Khung bài 150–300 từ có phù hợp từng loại bài không? Nêu ngoại lệ có giới hạn cụ thể.
3. Phản biện mẫu Polling/SSE/WebSocket: đúng kỹ thuật, dễ nhìn trên mobile, thiếu gì?
4. Chọn bộ mẫu sơ đồ tối thiểu: luồng, sequence, so sánh, topology, vòng lặp, cây quyết định.
   Dùng Mermaid cho draft, SVG cho bản học cuối có hợp lý không?
5. Giữ các bài Load Balancer, API Gateway, Redis và CDN gần nhau về nội dung như thế nào mà
   vẫn còn đủ mục nguồn? Nêu ví dụ liên kết thay vì gộp.
6. Đề xuất schema tối thiểu cho bài, nguồn, hình, prerequisite và tiến độ kiểm chứng.
   Tính đến việc kho hiện tại bắt buộc 3 ngôn ngữ và bài dài hơn yêu cầu mới.
7. Đề xuất checklist bắt lỗi nguồn: ảnh sai, mô tả giản lược quá mức, công nghệ cũ, thiếu đánh đổi,
   claim về kiến trúc nội bộ công ty không có bằng chứng.
8. Đề xuất đợt thử nghiệm 3 bài đầu và tiêu chí để bắt đầu viết các nhóm còn lại.

## Kết quả yêu cầu

Codex trả lời bằng tiếng Việt ngay trên PR: nhận xét theo 8 câu hỏi, một sơ đồ cấu trúc đề xuất,
bảng giữ/sửa và việc ưu tiên làm tiếp. Phải dẫn file + commit đã đọc, chỉ rõ suy luận hoặc nội dung
chưa kiểm chứng. Chế độ brainstorm chỉ đọc: không commit, không sửa file, không merge/deploy.

## Tiêu chí chấp nhận đề xuất

- Đủ 15 nhóm / 404 mục, không mất ID hoặc đổi thứ tự nguồn.
- Chỉ tiếng Việt cho nội dung học; thuật ngữ kỹ thuật và metadata nguồn được giữ nguyên.
- Một bài mẫu dùng hình làm trung tâm và có diễn giải đánh đổi chính xác.
- Có cách lưu nguồn và kiểm chứng; không coi bài mới kiểm kê là bài đã biên soạn.
- Không áp đặt bộ sinh 3 ngôn ngữ của khóa cũ lên khóa mới chỉ tiếng Việt.
- Không sửa nội dung khóa hiện có; đề xuất cấu trúc mới đủ cụ thể để triển khai sau brainstorm.
