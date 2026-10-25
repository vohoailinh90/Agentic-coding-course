# Kích hoạt team VPS từ Claude Code trên web

Phiên Claude Code trên web chạy trong container cloud và **không có đường vào VPS**. Cửa duy nhất là GitHub:
workflow [`.github/workflows/team-dispatch.yml`](../.github/workflows/team-dispatch.yml) (chỉ `workflow_dispatch`)
chạy trên một runner đặt ở VPS và gọi `sudo -u team /usr/local/bin/team ...`, đúng cách Hermes gọi. Quy trình team
nói chung ở [TEAM.md](TEAM.md); cách cài phía VPS ở `docs/vps-team.md` (mục *Start a run from GitHub*) của repo
`vohoailinh90/claude-agent-routing-template`.

```text
Claude Code web ── actions_run_trigger ──▶ GitHub Actions ──▶ runner trên VPS (user team-dispatch)
                                                                   │ sudo -n -u team
                                                                   ▼
                                                  /usr/local/bin/team  (wrapper của root)
```

## Nó làm được gì, không làm được gì

| Làm được | Không làm được (do wrapper trên VPS chặn, không do workflow) |
|---|---|
| `status ID`, `queue` (chỉ đọc) | `new`, `work`, `push`, `dequeue`, `drain`, `--force`, `--wait` |
| `run ID [--from tester\|coder\|review\|pack\|verdict]` (luôn kèm `--queue`) | viết `spec.md`/`acceptance.md`, audit, mở PR |

Feature phải có sẵn trên VPS (`team new`, spec đã qua `team check-spec`). Phần thiết kế và audit vẫn do Claude
(hoặc Codex với `team-codex`) làm trên VPS; PR, review và merge theo [TEAM.md](TEAM.md).

## Cài một lần (phía VPS và GitHub)

1. Trên VPS, chạy lại `setup-vps-team.sh` của repo template với `--with-dispatch` (tạo user `team-dispatch`, không
   thuộc nhóm `docker`/`team`/`sudo`, và luật sudoers `team-dispatch ALL=(team) NOPASSWD: /usr/local/bin/<team>`).
2. Đăng ký **một runner riêng** dưới user `team-dispatch` (GitHub → Settings → Actions → Runners) với label riêng,
   ví dụ `team-dispatch`. Label đó phải khác `CI_SELF_HOSTED_LABEL` và `CI_PROBE_LABEL`
   ([ci-runner-mode.md](ci-runner-mode.md)): runner CI chạy mã của pull request, nó mà dùng chung thì mã đó chạm
   được luật sudo.
3. Đặt biến repo: `gh variable set TEAM_DISPATCH_LABEL --body team-dispatch`. Chưa đặt thì workflow không có job nào.
4. Unit systemd của runner không được đặt `NoNewPrivileges=yes`, nếu không `sudo` bị chặn.

## Dùng

Từ Claude Code web (công cụ GitHub MCP `actions_run_trigger`) hoặc từ tab Actions / `gh`:

```bash
gh workflow run team-dispatch.yml -f action=status -f feature=F12
gh workflow run team-dispatch.yml -f action=run    -f feature=F12                    # = team run F12 --queue
gh workflow run team-dispatch.yml -f action=run    -f feature=F12 -f from=verdict    # sau khi audit BLOCK
gh workflow run team-dispatch.yml -f team=team-codex -f action=queue
```

Kết quả (đầu ra của lệnh `team`) nằm ở log và *Summary* của lần chạy. Dispatch xong, đọc lại lần chạy:

- Job `dispatch` **`skipped`** nghĩa là `TEAM_DISPATCH_LABEL` chưa đặt: lượt chạy vẫn "xanh" nhưng **chưa chạy gì**.
  Chỉ coi là đã chạy khi job có kết luận `success`.
- `team queue` báo `runner: not running` khi còn run chờ: chạy `team drain --detach` trên VPS.

## Lưu ý an toàn

- Chỉ người có quyền ghi repo mới dispatch được; coi quyền đó là quyền bấm "chạy F12" (xếp một pipeline tốn quota
  model free). Đừng bật workflow này nếu repo nhận contributor lạ có quyền ghi.
- Label runner không phải bí mật: một workflow khác trong repo có `runs-on: <label>` (kể cả file mới đẩy lên một
  nhánh) cũng chạy với quyền shell của `team-dispatch`. Quyền đó vẫn bị wrapper chặn như bảng trên, nhưng rộng hơn
  "chỉ bấm dispatch". Worker miễn phí **ghi được vào repo**, nên đây là lý do giữ label riêng và không thêm workflow
  nào khác dùng nó.
- Workflow không checkout mã, không giữ quyền token (`permissions: {}`), không đưa input vào script (qua biến môi
  trường, đã kiểm hình dạng). `tests/test_team_dispatch.py` chạy chính đoạn shell đó với `sudo` giả, và
  `tests/mutations/team_dispatch.yaml` chứng minh các test ấy thật sự bắt lỗi.
- **Chưa kiểm trên máy thật** (cũng như ở repo template): đăng ký runner dưới `team-dispatch`, `sudo -n -u team` từ dịch
  vụ runner và một lần `gh workflow run` thật. Lần đầu nên thử `action=status` hoặc `queue` trước khi `run`.
