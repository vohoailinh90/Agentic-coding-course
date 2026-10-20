# Generative AI cho người mới: bài học và slide Moda (quy trình nhiều phiên)

21 bài của [microsoft/generative-ai-for-beginners](https://github.com/microsoft/generative-ai-for-beginners)
(MIT, ghim ở commit `c35bc19`) được viết lại thành bài học tiếng Việt và một bộ slide Moda cho mỗi bài,
trong kho `genai-for-beginners/vi/` ([ADR 012](decisions/012-genai-for-beginners-slides.md)). Nhiều phiên
Claude làm cùng lúc; quy trình này mượn cách `tool-marketing-studio` làm bộ System Design 101
(`docs/sd101-slides.md`, `docs/sd101-assignments.md` ở repo đó): **chia dải trước, nhận bài trước khi làm,
mỗi phiên một nhánh, không ai sửa file của phiên khác.**

## Ai làm gì

| Vai | Làm gì | Không được làm |
|---|---|---|
| Phiên điều phối | Sửa `genai-for-beginners/vi/assignments.yaml` (giao dải), mở và theo dõi các phiên làm việc, gom kết quả | Viết bài trong dải đã giao cho phiên khác |
| Phiên làm việc (1 dải) | Nhận bài trong dải của mình, viết `lesson.md`, dựng deck Moda, xuất PPTX, gọi agent phản biện, mở PR | Sửa bất kỳ file nào ngoài `genai-for-beginners/vi/lessons/<id>/` của dải mình |
| Agent phản biện (Claude subagent) | Đọc bài + nguồn + ảnh chụp slide, báo lỗi | Sửa file |

Không dùng Codex cho bộ này (owner quyết định 2026-10-20: Codex hết quota). Phản biện độc lập là một Claude
subagent do chính phiên làm việc gọi (mục *Phản biện* bên dưới). Owner (Linh) merge các PR (ADR 010: `main`
chưa có branch protection).

## Luật chống trùng

1. **Bảng giao việc** `genai-for-beginners/vi/assignments.yaml`: mỗi dải `ga-NN..ga-MM` thuộc đúng một nhánh.
   Chỉ phiên điều phối sửa bảng.
2. **Nhận trước khi làm**: `python3 scripts/genai_check.py claim <id>... --session <session_id>` ghi
   `lessons/<id>/deck.yaml` với `status: doing`. `status`, `claim` và `scope` tự `git fetch` mọi nhánh của
   `origin` trước (bản clone của phiên cloud chỉ theo dõi `main`; khi không có mạng, đặt cờ trước lệnh con:
   `genai_check.py --no-fetch status`). Lệnh từ chối bài không thuộc dải của nhánh đang đứng, và bài
   mà một nhánh `origin/*` khác đang giữ. Commit và **push ngay** bản ghi `doing`: chưa push thì chưa giữ được gì.
3. `python3 scripts/genai_check.py status` cho biết từng bài `free`, `doing` hay `done`
   trên mọi nhánh, và cảnh báo khi một bài bị hai nhánh giữ.
4. **Mỗi phiên chỉ sửa thư mục bài của mình.** Không sửa README, bảng giao việc, script, tài liệu hay
   `PROGRESS.md`: những file chung đó do phiên điều phối cập nhật sau khi PR merge. Nhờ vậy các PR không
   bao giờ xung đột. `python3 scripts/genai_check.py scope` kiểm điều này (so với nhánh setup khi nhánh đó còn,
   sau đó so với `origin/main`) và phải qua trước khi mở PR.
5. **Nhánh**: dùng đúng tên nhánh bảng giao cho dải, tạo từ `origin/claude/genai-slides-setup` khi PR setup
   chưa merge, từ `origin/main` khi đã merge. Nhánh của phiên mang tên khác thì dừng, hỏi phiên điều phối.
6. Phiên chết giữa chừng: phiên điều phối giao lại **nguyên** dải cho một nhánh mới (đổi `branch` trong bảng; không
   chia đôi dải chết, vì nhánh mới mang theo mọi thư mục bài của nhánh cũ và `scope` sẽ báo phần không thuộc nó). Phiên mới tạo nhánh từ nhánh
   cũ (để giữ bài đã xong), rồi `claim <id>... --session ... --take-over` cho các bài cũ đang `doing`: lệnh chỉ
   nhường bản ghi `doing` của nhánh mà bảng không còn giao, không bao giờ nhường bài `done`. Tìm canvas cũ bằng
   `canvas_search` theo id (`ga-07`) và làm tiếp trên đó, không tạo canvas thứ hai.

## Vòng làm một bài

```bash
python3 scripts/genai_check.py status
python3 scripts/genai_check.py claim ga-01 ga-02 --session session_...   # rồi commit + push
```

1. **Đọc nguồn** ở đúng commit ghim: `source_url` trong `source-map.json` (bản thô:
   `https://raw.githubusercontent.com/microsoft/generative-ai-for-beginners/<commit>/<source_path>`).
2. **Viết `lesson.md`** (mục *Bài học* bên dưới).
3. **Dựng deck trên Moda** (mục *Slide*): `moda_bootstrap`, `load_skill("moda-core")`, `load_skill("moda-deck")`
   và các skill nó chỉ tới. Brand kit: **không dùng** (đã chốt, không hỏi lại). Mỗi slide một
   `canvas_apply_markup`; chụp **mọi** slide bằng `canvas_screenshot` và sửa trước khi sang slide sau.
   **Không gọi `canvas_delete`**: Moda bắt người duyệt tay lệnh này, phiên không ai trông sẽ đứng chờ. Muốn bỏ
   một phần slide thì vẽ lại cả trang bằng `canvas_apply_markup` thay trang (`replace_page_nodes`).
4. **Xuất PPTX**: `export(canvas, format="pptx")`, tải link bằng `curl` về
   `lessons/<id>/<id>.pptx`. Gói Moda miễn phí gắn huy hiệu `moda.app` lên mọi slide: **không bao giờ gỡ**.
5. **Phản biện** (mục *Phản biện*), sửa mọi lỗi được xác nhận.
6. **Ghi `done`** vào `deck.yaml` (mẫu bên dưới), chạy `python3 scripts/genai_check.py` (phải `genai store OK`),
   commit + push. Làm xong cả dải thì mở **một PR** vào `main`, không merge.

```yaml
id: ga-01
status: done
owner: claude/genai-slides-w1
session: session_...
claimed_at: '2026-10-20T09:00:00Z'      # giữ nguyên từ lúc claim
done_at: '2026-10-20T12:00:00Z'
moda_canvas: cvs_...
moda_url: https://moda.app/canvas/...
slide_count: 11
size: 1920x1080
exports: badged                          # pending nếu chưa tải được PPTX
review: passed                           # chỉ ghi khi phản biện đã xử lý xong
layouts:
  slides: [one-highlighted-sentence, card-grid, flow, ...]   # mỗi slide một kiểu, theo thứ tự
  first_concept: 3
  # cannot: {flow: "bài không có quy trình nào"}             # chỉ khi kiểu chữ ký phải lùi
```

## Bài học (`lesson.md`)

- Viết lại bằng lời của mình cho người mới, tiếng Việt có dấu, khoảng 700–1.200 chữ; **không dịch từng câu**.
  Chỉ dùng điều bài nguồn nói: không thêm số liệu, ví dụ hay khẳng định mới. Bỏ phần quảng cáo, video, link
  khóa học khác; giữ ý chính, ví dụ và phần thực hành cốt lõi (tối đa một đoạn code ngắn mỗi ý).
- Cấu trúc (`genai_check.py` kiểm khi bài `done`; lúc còn `doing` được push bản nháp): tiêu đề `# `; mục đầu tiên `## Từ viết tắt` (mỗi viết tắt một dòng:
  `- **LLM** (Large Language Model) — mô hình ngôn ngữ lớn: ...`); các mục nội dung; `## Nhìn hình trả lời`
  (một câu hỏi kiểm tra và đáp án trong `<details>`); `## Nguồn đối chiếu` có link `source_url` đã ghim và
  dòng ghi công: *Dựa trên bài NN của microsoft/generative-ai-for-beginners (MIT License, © Microsoft
  Corporation).*
- Không chép ảnh nguồn vào repo (thư mục bài chỉ có `lesson.md`, `deck.yaml`, `<id>.pptx`). Hình trong bài là
  Mermaid.

## Slide

Cùng họ thương hiệu với System Design 101 của owner, để hai bộ nhìn là biết của một nhà:

- Canvas `1920x1080`, category `slides`, không brand kit, chỉ vector (không sinh ảnh). Tên:
  `Generative AI cho người mới · Bài NN · <title_vi> (ga-NN)`. Gửi link editor ngay khi tạo.
- **10 đến 12 slide.** Font: **Bricolage Grotesque** 800 cho tiêu đề và số lớn, **Be Vietnam Pro** cho phần còn
  lại. Cỡ: tiêu đề bìa 108, tiêu đề slide 92–112, thân 34–40, nhãn 22–28; không gì dưới 22.
- Màu: kem `#F3EEE3`, mực `#14161C`, thẻ `#E8E0CF`, thẻ sơ đồ `#FBF8F2` (viền `#DDD5C1`), chữ phụ `#6B6A66`;
  nhấn: xanh `#1F3FD1`, hổ phách `#B45309`, xanh ngọc `#0F766E`, đỏ `#E8472B` (nhạt `#DDE3FA` `#F3DFB8`
  `#CFE8E2` `#F8D9D0`); nền tối `#14161C` (thẻ `#1E212B`) với `#7C93FF` `#FFB454` `#3DD6A0` `#FF6A4D`.
- **Xoay màu nhấn**: với n là số bài (`ga-04` → 4), khái niệm thứ k của bài (đếm từ 0) lấy màu nhấn số
  (n + k) mod 4 theo thứ tự xanh, hổ phách, xanh ngọc, đỏ; một khái niệm giữ một màu trên cả deck.
- Footer mọi slide trừ bìa: chấm tiến độ (chấm hiện tại màu đỏ) và `Generative AI cho người mới · Bài NN · 03/11`
  ở góc dưới trái. Góc dưới phải để trống (chỗ huy hiệu Moda).
- Thứ tự: **bìa** (tối: nhãn `GENERATIVE AI CHO NGƯỜI MỚI · BÀI NN`, tiêu đề, câu hỏi mở đầu, một dòng mỗi
  khái niệm chính) → bài này giúp bạn làm gì → một slide mỗi khái niệm, có sơ đồ → với bài kiểu `build`: một
  slide *Thử ngay* (các bước hoặc đoạn code ngắn ≤ 6 dòng, chữ mono ≥ 24) → câu hỏi kiểm tra + đáp án →
  **thuật ngữ và nguồn** cuối cùng (tối: `## Từ viết tắt` của bài và dòng ghi công nguồn MIT).
- Chữ trên slide chỉ lấy từ `lesson.md`. Tiếng Việt có dấu, không gạch ngang dài (—), tối đa 10 chữ mỗi gạch
  đầu dòng, 3 gạch mỗi thẻ; một slide đọc trong 5 giây.

### Bố cục (bảng `layouts`, script kiểm)

Mỗi slide đúng một trong 12 kiểu, theo thứ tự này (đếm từ 0): `sequence-diagram`, `flow`,
`two-column-comparison`, `2x2-matrix`, `lookup-table`, `card-grid`, `numbered-rows`, `connection-diagram`,
`layers`, `timeline`, `one-big-number`, `one-highlighted-sentence`.

- Một deck dùng **ít nhất 5 kiểu** và không bao giờ cùng kiểu ở hai slide liền nhau.
- **Kiểu chữ ký**: slide của khái niệm đầu tiên (`first_concept`) lấy kiểu ở vị trí n mod 12. Không thể hiện được
  nội dung bằng kiểu đó (ví dụ `one-big-number` mà bài không có con số) thì lấy kiểu kế tiếp làm được, và ghi
  từng kiểu bị bỏ qua kèm lý do vào `cannot`.
- Nền sáng/tối theo nội dung, không quá 3 slide liền nhau cùng nền (script không kiểm được; phản biện soi). Mỗi deck có một ý tưởng hình ảnh riêng lấy từ
  chính bài (bài embedding xoay quanh "bản đồ khoảng cách", bài agent xoay quanh "vòng lặp"): nói nó trong một
  dòng ở tin nhắn đầu tiên về deck.

## Phản biện (Claude subagent, thay cho Codex)

Sau khi dựng xong deck của một bài (trước khi ghi `done`), phiên làm việc gọi **một** agent phản biện
(`Agent`, `subagent_type: "general-purpose"`), đưa: đường dẫn `lesson.md`, `source_url`, id canvas Moda và
quy tắc trong file này. Agent chỉ đọc, không sửa; nó:

1. đối chiếu từng khẳng định của `lesson.md` với bài nguồn (sai, thêm điều nguồn không nói, bỏ sót ý chính);
2. đọc tiếng Việt như người mới (khó hiểu, viết tắt chưa giải thích, câu dịch máy);
3. chụp mọi slide (`canvas_screenshot`) và soi: chữ tràn/bị co, chữ < 22 px, góc dưới phải không trống, sai
   footer, sai màu khái niệm, quá 3 slide liền cùng nền, slide chép chữ không có trong `lesson.md`;
4. trả danh sách lỗi, mỗi lỗi ghi mức **P1** (sai sự thật, vỡ slide, thiếu phần bắt buộc) hoặc **P2/P3**.

Phiên làm việc kiểm từng lỗi, sửa lỗi đúng, ghi lý do khi bác lỗi sai. P1 sửa tới khi hết (gọi lại phản biện
cho riêng các lỗi P1 sau khi sửa). P2/P3 tối đa 2 vòng phản biện mỗi bài (tinh thần ADR 010); còn lại ghi
1 dòng vào mô tả PR. Xong thì ghi `review: passed`. Một bài một agent phản biện mỗi vòng: không gọi nhiều hơn.

## Mở PR

Một PR cho cả dải, từ nhánh của dải vào `main`, tiêu đề `genai slides: ga-NN..ga-MM`. Mô tả: bảng mỗi bài
(link editor Moda, số slide, bảng `layouts`, kết quả phản biện) và lỗi P2/P3 còn để lại. Kiểm trước khi mở:
`python3 scripts/genai_check.py`, `python3 scripts/genai_check.py scope`, `python3 -m pytest -q tests/test_genai_check.py`. Không merge; không đăng gì
lên Facebook.

## Prompt khởi động một phiên làm việc

> Làm dải `<range>` của bộ Generative AI cho người mới trong repo `vohoailinh90/agentic-coding-course`, nhánh
> `<branch>`. Đọc `docs/genai-slides.md` và làm đúng theo đó: claim dải bằng `scripts/genai_check.py`, viết
> `lesson.md` từ bài nguồn đã ghim, dựng deck trên Moda, chụp từng slide, xuất PPTX (giữ huy hiệu moda.app), gọi
> một agent phản biện cho mỗi bài, sửa lỗi, ghi `done`, mở một PR vào `main`. Không dùng Codex, không merge, không
> sửa file ngoài thư mục bài của dải mình.
