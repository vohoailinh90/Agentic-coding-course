# Bộ cân bằng tải làm những việc gì?

> Bản nháp `sd-01-002`, chưa duyệt. Trạng thái và các bước kiểm chứng ở [lesson.yaml](lesson.yaml).

**Cửa hàng online chạy trên ba máy chủ, khách chỉ biết một địa chỉ.** Ai quyết định khách vào máy
nào, và chuyện gì xảy ra khi một máy hỏng? Đó là việc của bộ cân bằng tải.

```mermaid
%%{init: {"flowchart": {"nodeSpacing": 12, "rankSpacing": 36, "padding": 8}}}%%
flowchart TB
    K["Khách"]:::client --> LB(["Bộ cân bằng tải"]):::service
    LB --> A["Máy A"]:::service
    LB --> B["Máy B"]:::service
    LB -.->|"bỏ qua"| C["Máy C (lỗi)"]:::bad
    classDef client fill:#dbeafe,stroke:#1d4ed8,color:#0f172a
    classDef service fill:#ede9fe,stroke:#6d28d9,color:#0f172a
    classDef bad fill:#ffedd5,stroke:#c2410c,color:#0f172a,stroke-dasharray: 4 3
```

Khách luôn nói chuyện với bộ cân bằng tải, không nói thẳng với máy nào. Nó chia khách vào các máy còn
khỏe; máy C đang lỗi bị bỏ qua cho đến khi hồi phục.

## Sáu việc thường gặp

1. **Kiểm tra sức khỏe:** định kỳ hỏi từng máy "còn làm việc được không?", chỉ chuyển khách vào máy
   trả lời tốt.
2. **Xử lý khi máy hỏng:** máy không qua kiểm tra bị tạm loại khỏi danh sách; khi hồi phục thì được
   nhận lại. Khách không phải biết máy nào hỏng.
3. **Định tuyến theo nền tảng:** dựa vào nội dung yêu cầu (đường dẫn, header) để đưa khách di động
   và khách web tới các nhóm máy khác nhau.
4. **Kết thúc SSL:** bộ cân bằng tải mã hóa và giải mã HTTPS thay cho các máy phía sau, nên các máy
   đó nhẹ việc hơn.
5. **Cân bằng giữa nhiều vùng:** chia khách ra các máy đặt ở nhiều vùng, nên một vùng gặp sự cố thì
   vùng khác vẫn phục vụ.
6. **Giữ phiên:** đưa cùng một khách vào cùng một máy trong suốt phiên, để dữ liệu phiên lưu trên
   máy đó vẫn dùng được.

**Giới hạn cần nhớ:** nếu chỉ có một bộ cân bằng tải thì chính nó là điểm hỏng duy nhất. Hệ thống
thật thường chạy từ hai bộ trở lên hoặc dùng dịch vụ được quản lý.

**Nhìn hình:** trong hình, máy C báo lỗi. Khách mới sẽ được đưa tới máy nào, và bộ cân bằng tải biết
C lỗi bằng cách nào?

<details>
<summary>Xem gợi ý</summary>

Khách mới đi vào máy A hoặc B. Bộ cân bằng tải biết nhờ kiểm tra sức khỏe định kỳ (việc 1): máy C
không trả lời tốt nên bị bỏ qua (việc 2).

</details>

<details>
<summary>Xem sâu hơn (tùy chọn, chưa kiểm chứng bằng tài liệu)</summary>

- Kết thúc SSL nghĩa là đoạn từ bộ cân bằng tải tới máy phía sau có thể đi không mã hóa. Nếu mạng
  nội bộ chưa đủ tin cậy thì mã hóa lại đoạn đó.
- Giữ phiên có giá: tải có thể lệch, và máy chết thì mất phiên trên máy đó. Nhiều hệ thống lưu phiên
  ở một kho dùng chung để không cần giữ phiên.
- Kiểm tra sức khỏe quá nông (chỉ thấy cổng mở) có thể bỏ sót lỗi của ứng dụng; nên kiểm tra một
  đường dẫn phản ánh đúng tình trạng làm việc.
- Định tuyến theo nội dung yêu cầu cần bộ cân bằng tải đọc được HTTP (tầng ứng dụng), không chỉ
  chuyển các gói tin.

</details>

## Liên hệ nguồn

Chủ đề và thứ tự theo mục `sd-01-002` của
[bài ByteByteGo, bản đã ghim](https://github.com/ByteByteGoHq/system-design-101/blob/b28380a4710c5ec9638ec037d4168e288f334cba/data/guides/load-balancer-realistic-use-cases-you-may-not-know.md).
Bài này viết bằng lời riêng, sơ đồ thiết kế mới. Bài nguồn dùng cùng một URL ảnh với bài về mã HTTP
(`sd-01-003`, xem hai bản đã ghim); ảnh đó chưa được mở, nên bài này không dùng ảnh nguồn và dựng lại
hình từ các ý ở trên. Các điểm kỹ thuật chưa đối chiếu với tài liệu chính thức trong bản nháp này.

Đọc cùng: `sd-01-011` (các tình huống dùng bộ cân bằng tải), `sd-01-016` và `sd-01-018` (so với
reverse proxy và API gateway).
