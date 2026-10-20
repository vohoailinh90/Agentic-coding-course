# AI Agent cho người mới — tiếng Việt

Bộ 18 bài học tiếng Việt kèm slide Moda, dựa trên
[microsoft/ai-agents-for-beginners](https://github.com/microsoft/ai-agents-for-beginners)
(MIT License, © Microsoft Corporation), ghim ở commit `9923c54`. Quyết định:
[ADR 013](../../docs/decisions/013-ai-agents-for-beginners-slides.md); quy trình nhiều phiên, style slide và cách
nhận bài: [docs/agents-slides.md](../../docs/agents-slides.md).

- `source-map.json`: 18 bài nguồn (01 đến 18), đường dẫn và link đã ghim.
- `assignments.yaml`: dải bài nào giao cho nhánh nào (chỉ phiên điều phối sửa).
- `lessons/<id>/`: `lesson.md`, `deck.yaml` (nhận bài / kết quả deck), `<id>.pptx` (bản xuất Moda, còn huy hiệu).

Kiểm tra trước khi commit: `python3 scripts/agents_check.py`. Trạng thái từng bài:
`python3 scripts/agents_check.py status` (đọc mọi nhánh `origin/*`), không lặp lại ở đây.

| ID | Bài | Kiểu | Bài nguồn |
|---|---|---|---|
| `ag-01` | AI agent là gì và dùng vào việc gì | learn | [Introduction to AI Agents and Agent Use Cases](https://github.com/microsoft/ai-agents-for-beginners/blob/9923c54bcc2df67e7119945e12cd2d45944da2f6/01-intro-to-ai-agents/README.md) |
| `ag-02` | Khám phá các framework dựng AI agent | learn | [Explore AI Agent Frameworks](https://github.com/microsoft/ai-agents-for-beginners/blob/9923c54bcc2df67e7119945e12cd2d45944da2f6/02-explore-agentic-frameworks/README.md) |
| `ag-03` | Nguyên tắc thiết kế AI agent | learn | [AI Agentic Design Principles](https://github.com/microsoft/ai-agents-for-beginners/blob/9923c54bcc2df67e7119945e12cd2d45944da2f6/03-agentic-design-patterns/README.md) |
| `ag-04` | Mẫu thiết kế dùng công cụ | build | [Tool Use Design Pattern](https://github.com/microsoft/ai-agents-for-beginners/blob/9923c54bcc2df67e7119945e12cd2d45944da2f6/04-tool-use/README.md) |
| `ag-05` | Agentic RAG: agent tự đi tìm thông tin | build | [Agentic RAG](https://github.com/microsoft/ai-agents-for-beginners/blob/9923c54bcc2df67e7119945e12cd2d45944da2f6/05-agentic-rag/README.md) |
| `ag-06` | Xây AI agent đáng tin cậy | learn | [Building Trustworthy AI Agents](https://github.com/microsoft/ai-agents-for-beginners/blob/9923c54bcc2df67e7119945e12cd2d45944da2f6/06-building-trustworthy-agents/README.md) |
| `ag-07` | Mẫu thiết kế lập kế hoạch | learn | [Planning Design](https://github.com/microsoft/ai-agents-for-beginners/blob/9923c54bcc2df67e7119945e12cd2d45944da2f6/07-planning-design/README.md) |
| `ag-08` | Mẫu thiết kế nhiều agent | learn | [Multi-agent design patterns](https://github.com/microsoft/ai-agents-for-beginners/blob/9923c54bcc2df67e7119945e12cd2d45944da2f6/08-multi-agent/README.md) |
| `ag-09` | Siêu nhận thức: agent tự xem lại cách nghĩ | learn | [Metacognition in AI Agents](https://github.com/microsoft/ai-agents-for-beginners/blob/9923c54bcc2df67e7119945e12cd2d45944da2f6/09-metacognition/README.md) |
| `ag-10` | Đưa AI agent vào vận hành: quan sát và đánh giá | learn | [AI Agents in Production: Observability & Evaluation](https://github.com/microsoft/ai-agents-for-beginners/blob/9923c54bcc2df67e7119945e12cd2d45944da2f6/10-ai-agents-production/README.md) |
| `ag-11` | Giao thức cho agent: MCP, A2A và NLWeb | learn | [Using Agentic Protocols (MCP, A2A and NLWeb)](https://github.com/microsoft/ai-agents-for-beginners/blob/9923c54bcc2df67e7119945e12cd2d45944da2f6/11-agentic-protocols/README.md) |
| `ag-12` | Thiết kế ngữ cảnh cho AI agent | learn | [Context Engineering for AI Agents](https://github.com/microsoft/ai-agents-for-beginners/blob/9923c54bcc2df67e7119945e12cd2d45944da2f6/12-context-engineering/README.md) |
| `ag-13` | Bộ nhớ của AI agent | learn | [Memory for AI Agents](https://github.com/microsoft/ai-agents-for-beginners/blob/9923c54bcc2df67e7119945e12cd2d45944da2f6/13-agent-memory/README.md) |
| `ag-14` | Tìm hiểu Microsoft Agent Framework | build | [Exploring Microsoft Agent Framework](https://github.com/microsoft/ai-agents-for-beginners/blob/9923c54bcc2df67e7119945e12cd2d45944da2f6/14-microsoft-agent-framework/README.md) |
| `ag-15` | Xây agent điều khiển máy tính | build | [Building Computer Use Agents (CUA)](https://github.com/microsoft/ai-agents-for-beginners/blob/9923c54bcc2df67e7119945e12cd2d45944da2f6/15-browser-use/README.md) |
| `ag-16` | Triển khai agent mở rộng được với Microsoft Foundry | build | [Deploying Scalable Agents with Microsoft Foundry](https://github.com/microsoft/ai-agents-for-beginners/blob/9923c54bcc2df67e7119945e12cd2d45944da2f6/16-deploying-scalable-agents/README.md) |
| `ag-17` | Tạo AI agent chạy trên máy với Foundry Local và Qwen | build | [Creating Local AI Agents Using Microsoft Foundry Local and Qwen](https://github.com/microsoft/ai-agents-for-beginners/blob/9923c54bcc2df67e7119945e12cd2d45944da2f6/17-creating-local-ai-agents/README.md) |
| `ag-18` | Bảo mật AI agent bằng biên nhận mật mã | build | [Securing AI Agents with Cryptographic Receipts](https://github.com/microsoft/ai-agents-for-beginners/blob/9923c54bcc2df67e7119945e12cd2d45944da2f6/18-securing-ai-agents/README.md) |
