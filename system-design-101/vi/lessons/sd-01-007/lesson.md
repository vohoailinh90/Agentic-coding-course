# Chính sách định tuyến lưu lượng Internet

> Bản nháp `sd-01-007`, chưa duyệt. Trạng thái và các bước kiểm chứng ở [lesson.yaml](lesson.yaml).

**Một cửa hàng online đặt máy chủ ở nhiều nước. Khi khách gõ địa chỉ trang web, ai quyết định đưa họ tới máy chủ nào?**

## 🏠 Hiểu bằng chuyện đời thường

Hãy hình dung một tổng đài chỉ đường cho chuỗi cửa hàng. Khách gọi hỏi "cửa hàng ở đâu?", tổng đài tùy theo luật mà
đọc ra một địa chỉ: có khi luôn là một chi nhánh, có khi chi nhánh chính đóng cửa thì chỉ sang chi nhánh dự phòng,
có khi chỉ chi nhánh gần khách nhất. **DNS** là tổng đài đó: nó là danh bạ đổi tên trang web thành địa chỉ máy chủ,
và các **chính sách định tuyến** là luật tổng đài dùng để chọn địa chỉ nào.

## 🗺️ Nhìn hình

```mermaid
%%{init: {"flowchart": {"nodeSpacing": 12, "rankSpacing": 16, "padding": 8}}}%%
flowchart TB
    Q["Khách gõ tên trang web"]:::who
    D{"DNS chọn đích<br/>theo chính sách"}:::dns
    A["Máy chủ A<br/>gần khách"]:::srv
    B["Máy chủ B<br/>theo tỷ lệ"]:::srv
    C["Dự phòng<br/>khi A hỏng"]:::srv
    Q --> D
    D --> A
    D --> B
    D --> C
    classDef who fill:#e2e8f0,stroke:#475569,color:#0f172a
    classDef dns fill:#fef9c3,stroke:#a16207,color:#0f172a
    classDef srv fill:#dcfce7,stroke:#15803d,color:#0f172a
```

Đọc hình: khách hỏi DNS, DNS áp dụng chính sách rồi trả về địa chỉ của một máy chủ. Mỗi mũi tên là một kiểu luật
khác nhau; bảng dưới đây nêu cả sáu.

## 🔍 Sáu chính sách

| Chính sách | DNS làm gì | Ví dụ dễ hiểu |
|---|---|---|
| **Simple** (đơn giản) | Chỉ có một đích, ai hỏi cũng nhận cùng câu trả lời | Trang nhỏ chỉ có một máy chủ |
| **Failover** (dự phòng) | Dùng đích chính; khi đích đó hỏng thì chuyển sang đích phụ (nhờ kiểm tra sức khỏe, và vẫn chịu độ trễ do cache) | Máy chủ chính sập mà trang vẫn mở được |
| **Geolocation** (theo vị trí) | Xem người hỏi ở đâu rồi chọn đích tương ứng | Khách ở châu Á đến máy chủ châu Á, hoặc nội dung theo từng vùng |
| **Latency** (độ trễ) | Chọn đích mà người hỏi nhận được câu trả lời nhanh nhất | Khách ở Nhật được dẫn tới máy chủ cho độ trễ thấp nhất, kể cả khi đó không phải máy chủ gần nhất |
| **Multivalue answer** (nhiều giá trị) | Đưa ra vài địa chỉ để máy khách tự thử | Trả vài địa chỉ; nếu một máy hỏng, trình duyệt có thể thử địa chỉ khác |
| **Weighted** (theo trọng số) | Chia khách theo tỷ lệ định trước | Cho một phần nhỏ khách thử máy chủ mới |

Tên gọi tương tự xuất hiện ở một số dịch vụ DNS đám mây (chưa đối chiếu tài liệu trong bản nháp này).

## ⚠️ Giới hạn cần nhớ

- DNS chỉ trả về địa chỉ. Nó không nhìn thấy máy chủ đang bận hay rảnh như một bộ cân bằng tải. Vì vậy chính sách
  nhiều giá trị không phải là cách thay thế cho bộ cân bằng tải.
- Câu trả lời của DNS thường được lưu tạm (cache) trong một khoảng thời gian, nên khi đổi chính sách, một số khách
  vẫn thấy địa chỉ cũ trong lúc chờ hết hạn.

## 📖 Từ khó, giải nghĩa

- **DNS:** hệ thống danh bạ đổi tên trang web thành địa chỉ máy chủ.
- **Độ trễ:** thời gian một yêu cầu đi và nhận lại câu trả lời; càng thấp càng nhanh.
- **Trọng số:** con số thể hiện phần chia, ví dụ máy chủ A nhận gấp ba lần máy chủ B.

## ❓ Nhìn hình trả lời

Hai chính sách Geolocation và Latency khác nhau chỗ nào?

<details>
<summary>Xem đáp án</summary>

Geolocation chọn theo vị trí địa lý của người hỏi. Latency chọn theo độ trễ mạng, nên có thể chọn một nơi xa hơn nếu
nơi đó trả lời nhanh hơn.

</details>

## 🔗 Liên hệ nguồn

Chủ đề và thứ tự theo mục `sd-01-007` của
[bài ByteByteGo, bản đã ghim](https://github.com/ByteByteGoHq/system-design-101/blob/b28380a4710c5ec9638ec037d4168e288f334cba/data/guides/internet-traffic-routing-policies.md).
Bài này viết bằng lời riêng, sơ đồ thiết kế mới, không dùng ảnh nguồn. Những nhận định kỹ thuật ngoài bài nguồn
chưa được đối chiếu với tài liệu chính thức trong bản nháp này; chỗ ghi "theo nguồn" chỉ dựa vào bài nguồn.
