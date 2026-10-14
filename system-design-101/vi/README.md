# System Design 101 — tiếng Việt

Kho nội dung bài học System Design bằng tiếng Việt, học bằng hình. Quyết định, schema và quy tắc
nằm ở [brainstorm/system-design-101-vi/DECISIONS.md](../../brainstorm/system-design-101-vi/DECISIONS.md);
bảng đối chiếu 404 mục nguồn ở [source-map.json](../../brainstorm/system-design-101-vi/source-map.json).

Kiểm tra trước khi commit: `python3 scripts/sd101_check.py`.

Quy tắc ngắn: mỗi bài là một thư mục `lessons/<id>/` có `lesson.md` và `lesson.yaml` (nơi duy nhất
ghi tiến độ). Bài viết độc lập bằng lời riêng, sơ đồ tự thiết kế, không dịch sát nguồn và không dùng
ảnh nguồn, vì nguồn là CC BY-NC-ND 4.0 và kho này công khai. Hình trong bài là Mermaid trong
`lesson.md` hoặc tệp `.svg` tự vẽ nằm cạnh bài; thư mục bài chỉ chứa `lesson.md`, `lesson.yaml`
và các tệp `.svg` đó (PNG/JPG không được phép, kể cả khi tự chụp). Hình trong `lesson.md` phải nằm
ngay trong thư mục của chính bài đó. Tệp `.svg` phải là bản vẽ thuần (vẽ tay hoặc xuất từ sơ đồ, không dùng
nhãn HTML): chỉ phần tử vẽ như `path`, `rect`, `text`, `g`, `marker`, `use`; không `<image>`,
`<foreignObject>`, `<script>`, `<a>` hay hoạt ảnh; không liên kết hay `url()` ra ngoài ngoài các
`#fragment` của nó. HTML thô
trong `lesson.md` chỉ gồm `details`, `summary`, `br`, `a`, `img`, `sub`, `sup`, `kbd`.

| ID | Bài |
|---|---|
| [sd-01-001](lessons/sd-01-001/lesson.md) | Polling ngắn, polling dài, SSE và WebSocket |
| [sd-01-002](lessons/sd-01-002/lesson.md) | Ứng dụng thực tế của bộ cân bằng tải |
| [sd-01-003](lessons/sd-01-003/lesson.md) | 5 mã HTTP kỳ lạ và bối cảnh sử dụng |
| [sd-01-004](lessons/sd-01-004/lesson.md) | gRPC hoạt động thế nào? |
| [sd-01-005](lessons/sd-01-005/lesson.md) | NAT giúp Internet mở rộng ra sao? |
| [sd-01-006](lessons/sd-01-006/lesson.md) | Những điều cần biết về HTTP headers |

Trạng thái từng bài xem ở `lesson.yaml` của bài đó, không lặp lại ở đây.
