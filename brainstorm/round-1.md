# Vòng 1 — kết luận (ACC-0001)

- Issue: [#1](https://github.com/vohoailinh90/Agentic-coding-course/issues/1) · yêu cầu:
  [bình luận 5846809760](https://github.com/vohoailinh90/Agentic-coding-course/issues/1#issuecomment-5846809760)
  · trả lời của Codex: [bình luận 5846845480](https://github.com/vohoailinh90/Agentic-coding-course/issues/1#issuecomment-5846845480)
  (bản sao nguyên văn: [round-1-codex.md](round-1-codex.md))
- Chế độ `BRAINSTORM`, chỉ đọc, trên commit `9c28f454f4e3789bcc344556daf902ca7e312d57` (2026-09-26).

## Kiểm chứng (docs/claude-to-codex.md §14)

```yaml
task_id: "ACC-0001"
codex_mode: "BRAINSTORM"
requested_sha: "9c28f454f4e3789bcc344556daf902ca7e312d57"
reported_sha: null
current_sha: "9c28f454f4e3789bcc344556daf902ca7e312d57"
status: "ACCEPTED"
unresolved_findings: []
next_action: "The course owner answers the decisions below; then Claude writes roadmap v1 into course/data/curriculum.yaml."
```

| Tiêu chí nghiệm thu | Kết quả | Cách kiểm |
|---|---|---|
| Câu hỏi 1–11, mỗi câu một mục riêng | ✓ | đếm tiêu đề bằng script |
| Lộ trình v1: chương → chủ đề → bài, mỗi bài có tên, mục tiêu, loại, số phút | ✓ 61 mục | script đọc từng mục |
| 57 id của v0 xuất hiện đúng một lần, có nhãn; bài mới ghi NEW | ✓ 57/57, 4 NEW | script so với `course/data/curriculum.yaml` |
| Lộ trình tối thiểu 15–20 id, đều có trong v1 | ✓ 18 id | script |
| Nhận định v0 tối đa 10 ý, mỗi ý dẫn đường dẫn file | ⚠️ 10 ý, **không có đường dẫn nào** | xem dưới |
| Nêu SHA đã đọc; kết thúc bằng Tóm tắt 5 dòng | ✓ | đọc |
| Không sửa gì trong repo | ✓ | không có nhánh, PR hay commit mới; `main` vẫn ở SHA trên |

- **Đường dẫn bị mất:** các ý có khoảng trắng thừa ở đúng chỗ trích dẫn, nên có lẽ trích dẫn bị mất khi
  đăng bình luận. Claude tự kiểm từng ý với repo và đều đúng: `first-agent-session` là bài thứ 30;
  10 bài nền tảng phần mềm + 8 bài nền tảng AI đứng trước chương agentic coding; 4 dự án đều ở chương
  cuối; harness có 15 bài, nhiều nhất trong các chương không phải dự án; mẫu bài có 11 phần và đố vui
  3 câu (`course/data/sections.yaml`, `docs/content-guide.md`); lịch đăng T2/T4/T6
  (`docs/facebook-plan.md`); bài mẫu nêu tên Claude Code.
- **Sai số:** Codex ghi lộ trình tối thiểu "khoảng 302 phút"; cộng lại là **337 phút** (≈ 5,6 giờ),
  trong đó 150 phút là 2 dự án.
- Bằng chứng Codex nêu (`validate` OK, `stats` 7 chương · 17 chủ đề · 57 bài · 944 phút) khớp với kết
  quả của Claude. Codex không vào được web để kiểm giá và gói miễn phí của các công cụ (lỗi 401), nên
  phần chọn công cụ chỉ nêu tiêu chí, không nêu tên cụ thể.

## Codex đề xuất gì

**Đổi thứ tự: thực hành sớm, học lý thuyết đúng lúc cần** (xoắn ốc). Người học xem agent làm việc →
biết giới hạn an toàn → tự làm một thứ nhỏ ngay buổi đầu → học cách giao việc và kiểm tra → kiến thức
phần mềm và AI đến khi bài thực hành cần tới → dự án văn phòng. Phần sâu (bên trong LLM, phần lớn
harness, MCP, multi-agent, eval) thành nhánh tùy chọn/nâng cao.

| Chương v1 | Bài | Phút |
|---|---|---|
| 1. Start Safely and Get a First Win | 7 | 79 |
| 2. Direct, Check and Improve an Agent | 7 | 131 |
| 3. Software Literacy Just in Time | 8 | 92 |
| 4. The AI Mental Models You Actually Need (2 chủ đề tùy chọn) | 12 | 118 |
| 5. Reliable Agent Work (1 chủ đề nâng cao) | 14 | 158 |
| 6. Build Something Useful (1 chủ đề nâng cao) | 4 | 315 |
| **Tổng** (v0: 7 chương · 57 bài · 944 phút) | **52** | **893** |

- So với v0: 44 bài chuyển chỗ, 3 giữ nguyên, 8 gộp vào bài khác, 1 bỏ (`fine-tuning-intro`), 1 tách
  (`chatbot-to-agent` → thêm `agent-parts-and-loop`), 4 bài mới (`agent-parts-and-loop`,
  `choose-your-learning-setup`, `data-safety-and-permissions`, `project-retrospective`). Không đổi id nào.
- **Lộ trình tối thiểu (18 bài, 337 phút):** `chatbot-to-agent`, `agent-parts-and-loop`,
  `watch-an-agent-build`, `choose-your-learning-setup`, `data-safety-and-permissions`,
  `first-agent-session`, `lead-not-typist`, `writing-good-specs`, `explore-plan-build-verify`,
  `reviewing-agent-changes`, `testing-basics`, `errors-and-debugging`, `files-folders-paths`,
  `git-version-control`, `hallucination`, `context-window`, `project-personal-page`,
  `project-office-automation`.
- **Lần thực hành đầu tiên** ngay buổi đầu: nhờ agent làm một trang HTML một file "My Weekly Task
  Card", rồi tự kiểm 6 tiêu chí (file nằm đúng thư mục, mở được, đủ nội dung, nút bấm chạy, agent nói
  rõ đã sửa file nào, sửa lại một lần đúng yêu cầu). Máy công ty bị khóa: xem demo, làm lại ở máy
  cá nhân hoặc trên trình duyệt, chỉ dùng dữ liệu giả.
- **Bài mẫu:** tách làm hai; 1–2 sơ đồ mỗi bài; bài tập phải làm chứ không chỉ đọc; không ngụ ý mọi
  agent đều tự sửa lỗi; tên công cụ chỉ là ví dụ có ghi ngày; mẫu bài đổi sang "các phần tối thiểu
  hữu ích"; thử bài với người học thật trước khi viết hàng loạt.
- **Dữ liệu:** thêm `track`, `minimum_path_order`, `prerequisites`, `outcomes`, `artifact`,
  `evidence`, `active_minutes`, `last_verified`… cho website và lịch đăng.
- **Infographic:** thêm 2 mẫu `boundary` (an toàn / hỏi trước / cấm) và `checklist` (sản phẩm bên
  cạnh các tiêu chí kiểm); có kế hoạch sơ đồ cho cả 18 bài.
- **Facebook:** giữ nhịp T2/T4/T6, thêm thử thách và "cho xem bằng chứng"; một nhóm nhân vật xuyên
  suốt (Mai, Tuấn, Hana, Huy) thay cho ví dụ rời rạc; không dùng chuỗi ngày (streak) gây áp lực.

## Nhận xét của Claude

Đồng ý với hướng chính: thực hành sớm, an toàn trước, lộ trình tối thiểu 18 bài, dự án rải trong lộ
trình, harness thành nhánh nâng cao, thêm trường dữ liệu. Điều chỉnh:

1. **Giữ đủ 4 sơ đồ của bài mẫu, chia cho 2 bài sau khi tách:** `chatbot-to-agent` giữ
   `ai-three-levels` và `maps-vs-taxi`; `agent-parts-and-loop` nhận `agent-formula` và `agent-loop`.
   Vừa đúng góp ý "1–2 sơ đồ mỗi bài", vừa giữ mục tiêu "nhìn sơ đồ là hiểu".
2. Lộ trình tối thiểu là 337 phút: 2–3 tuần ở nhịp 2–3 giờ/tuần, hoặc 18 tuần trên Facebook.
3. "Làm ngay buổi đầu" chỉ đứng được khi có một công cụ không cần cài đặt và dùng miễn phí được;
   phải thử thật trước khi viết `first-agent-session`.
4. Nên thêm các trường dữ liệu mới vào `curriculum.yaml`, kèm kiểm tra của `validate`, trước khi viết
   tiếp, vì website và lịch đăng đều cần chúng.
5. Chưa cần vòng 2 ngay. Nên dùng vòng 2 (vòng cuối) để Codex soát `curriculum.yaml` v1 sau khi chủ
   khóa học đã quyết định.

## Chủ khóa học cần quyết định

Codex nêu 10 câu; năm câu đầu ảnh hưởng tới lộ trình tối thiểu.

| # | Câu hỏi | Gợi ý của Claude |
|---|---|---|
| 1 | Buổi thực hành đầu được dùng dịch vụ chạy trên trình duyệt không, hay phải chạy trên máy? | Cho phép, kèm đường chạy trên máy cá nhân |
| 2 | Có giả định người học có máy tính cá nhân cho 2 buổi dự án? | Có, kèm đường "chỉ xem" |
| 3 | Dự án trang cá nhân có cần đăng lên mạng? | Không bắt buộc; đăng lên là thử thách thêm |
| 4 | Người học Nhật là đối tượng chính ngay từ đầu, hay bản Nhật làm sau khi bản Việt được thử? | Chủ khóa học quyết (chi phí 3 thứ tiếng) |
| 5 | Khóa học hứa "làm phần mềm không cần biết code" hay "biết đủ để giám sát agent viết code"? | Vế sau: trung thực hơn, khớp tinh thần kiểm chứng |
| 6 | Dự án văn phòng được dùng Python không? | Có (agent viết, người học chạy và kiểm), kèm đường chỉ dùng bảng tính |
| 7 | Ai rà soát tiếng Nhật ở mức bản ngữ? | Một người bản ngữ đọc thử 1–2 bài đầu trước khi làm hàng loạt |
| 8 | Việc gì luôn bị cấm trong mọi bài tập? | Dữ liệu thật của công ty/khách hàng, mật khẩu và khóa API, lệnh ngoài thư mục thực hành, vượt quyền trên máy công ty |
| 9 | Chỉ viết nhánh nâng cao sau khi có số liệu từ lộ trình tối thiểu? | Có |
| 10 | Có giới thiệu thêm khái niệm "agentic engineering"? | Một lần, sau dự án đầu tiên |

### Đã quyết (2026-09-26)

Linh đồng ý với gợi ý của Claude cho các câu 1, 4, 5 và 6: dùng được công cụ chạy trên trình duyệt
(kèm đường chạy trên máy cá nhân); bản tiếng Nhật làm sau khi bản tiếng Việt đã được thử với người học;
khóa học hứa "biết đủ để giám sát AI viết code"; dự án văn phòng được dùng Python, kèm đường chỉ dùng
bảng tính. Các câu còn lại tạm theo gợi ý của Claude cho đến khi Linh quyết khác. Lộ trình v1 đã áp
dụng vào `course/data/curriculum.yaml` ([ADR 007](../docs/decisions/007-roadmap-v1.md)); Linh cũng yêu
cầu mọi bài có một hình tóm tắt cả bài ([ADR 008](../docs/decisions/008-a-recap-infographic-in-every-lesson.md)).

## Bước tiếp theo

1. Chủ khóa học trả lời các câu trên (ít nhất 1, 4, 5 và 6). — *xong, xem "Đã quyết" ở trên.*
2. Claude viết lộ trình v1 vào `course/data/curriculum.yaml` (giữ nguyên id; ghi lại bài gộp/bỏ),
   thêm trường dữ liệu mới kèm kiểm tra, và tách bài mẫu.
3. Vòng 2 với Codex: soát `curriculum.yaml` v1.
4. Viết 6 bài mở đầu, thử với vài người học thật, rồi mới làm tiếp 18 bài và bản dịch.
