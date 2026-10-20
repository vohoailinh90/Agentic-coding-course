# Generative AI cho người mới — tiếng Việt

Bộ 21 bài học tiếng Việt kèm slide Moda, dựa trên
[microsoft/generative-ai-for-beginners](https://github.com/microsoft/generative-ai-for-beginners)
(MIT License, © Microsoft Corporation), ghim ở commit `c35bc19`. Quyết định:
[ADR 012](../../docs/decisions/012-genai-for-beginners-slides.md); quy trình nhiều phiên, style slide và cách
nhận bài: [docs/genai-slides.md](../../docs/genai-slides.md).

- `source-map.json`: 21 bài nguồn, đường dẫn và link đã ghim.
- `assignments.yaml`: dải bài nào giao cho nhánh nào (chỉ phiên điều phối sửa).
- `lessons/<id>/`: `lesson.md`, `deck.yaml` (nhận bài / kết quả deck), `<id>.pptx` (bản xuất Moda, còn huy hiệu).

Kiểm tra trước khi commit: `python3 scripts/genai_check.py`. Trạng thái từng bài:
`python3 scripts/genai_check.py status` (đọc mọi nhánh `origin/*`), không lặp lại ở đây.

| ID | Bài | Kiểu | Bài nguồn |
|---|---|---|---|
| `ga-01` | AI tạo sinh và mô hình ngôn ngữ lớn là gì | learn | [Introduction to Generative AI and LLMs](https://github.com/microsoft/generative-ai-for-beginners/blob/c35bc1950f9dc56af773d2c362dafce6f76e9a56/01-introduction-to-genai/README.md) |
| `ga-02` | Khám phá và so sánh các LLM | learn | [Exploring and comparing different LLMs](https://github.com/microsoft/generative-ai-for-beginners/blob/c35bc1950f9dc56af773d2c362dafce6f76e9a56/02-exploring-and-comparing-different-llms/README.md) |
| `ga-03` | Dùng AI tạo sinh có trách nhiệm | learn | [Using Generative AI Responsibly](https://github.com/microsoft/generative-ai-for-beginners/blob/c35bc1950f9dc56af773d2c362dafce6f76e9a56/03-using-generative-ai-responsibly/README.md) |
| `ga-04` | Nền tảng kỹ thuật viết prompt | learn | [Understanding Prompt Engineering Fundamentals](https://github.com/microsoft/generative-ai-for-beginners/blob/c35bc1950f9dc56af773d2c362dafce6f76e9a56/04-prompt-engineering-fundamentals/README.md) |
| `ga-05` | Viết prompt nâng cao | learn | [Creating Advanced Prompts](https://github.com/microsoft/generative-ai-for-beginners/blob/c35bc1950f9dc56af773d2c362dafce6f76e9a56/05-advanced-prompts/README.md) |
| `ga-06` | Xây ứng dụng sinh văn bản | build | [Building Text Generation Applications](https://github.com/microsoft/generative-ai-for-beginners/blob/c35bc1950f9dc56af773d2c362dafce6f76e9a56/06-text-generation-apps/README.md) |
| `ga-07` | Xây ứng dụng chat | build | [Building Chat Applications](https://github.com/microsoft/generative-ai-for-beginners/blob/c35bc1950f9dc56af773d2c362dafce6f76e9a56/07-building-chat-applications/README.md) |
| `ga-08` | Xây ứng dụng tìm kiếm bằng embedding | build | [Building Search Apps Vector Databases](https://github.com/microsoft/generative-ai-for-beginners/blob/c35bc1950f9dc56af773d2c362dafce6f76e9a56/08-building-search-applications/README.md) |
| `ga-09` | Xây ứng dụng tạo ảnh | build | [Building Image Generation Applications](https://github.com/microsoft/generative-ai-for-beginners/blob/c35bc1950f9dc56af773d2c362dafce6f76e9a56/09-building-image-applications/README.md) |
| `ga-10` | Xây ứng dụng AI low-code | build | [Building Low Code AI Applications](https://github.com/microsoft/generative-ai-for-beginners/blob/c35bc1950f9dc56af773d2c362dafce6f76e9a56/10-building-low-code-ai-applications/README.md) |
| `ga-11` | Gọi hàm để nối ứng dụng bên ngoài | build | [Integrating External Applications with Function Calling](https://github.com/microsoft/generative-ai-for-beginners/blob/c35bc1950f9dc56af773d2c362dafce6f76e9a56/11-integrating-with-function-calling/README.md) |
| `ga-12` | Thiết kế trải nghiệm cho ứng dụng AI | learn | [Designing UX for AI Applications](https://github.com/microsoft/generative-ai-for-beginners/blob/c35bc1950f9dc56af773d2c362dafce6f76e9a56/12-designing-ux-for-ai-applications/README.md) |
| `ga-13` | Bảo mật ứng dụng AI tạo sinh | learn | [Securing Your Generative AI Applications](https://github.com/microsoft/generative-ai-for-beginners/blob/c35bc1950f9dc56af773d2c362dafce6f76e9a56/13-securing-ai-applications/README.md) |
| `ga-14` | Vòng đời ứng dụng AI tạo sinh | learn | [The Generative AI Application Lifecycle](https://github.com/microsoft/generative-ai-for-beginners/blob/c35bc1950f9dc56af773d2c362dafce6f76e9a56/14-the-generative-ai-application-lifecycle/README.md) |
| `ga-15` | RAG và cơ sở dữ liệu vector | build | [Retrieval Augmented Generation (RAG) and Vector Databases](https://github.com/microsoft/generative-ai-for-beginners/blob/c35bc1950f9dc56af773d2c362dafce6f76e9a56/15-rag-and-vector-databases/README.md) |
| `ga-16` | Mô hình mã nguồn mở và Hugging Face | build | [Open Source Models and Hugging Face](https://github.com/microsoft/generative-ai-for-beginners/blob/c35bc1950f9dc56af773d2c362dafce6f76e9a56/16-open-source-models/README.md) |
| `ga-17` | AI agent | build | [AI Agents](https://github.com/microsoft/generative-ai-for-beginners/blob/c35bc1950f9dc56af773d2c362dafce6f76e9a56/17-ai-agents/README.md) |
| `ga-18` | Tinh chỉnh LLM | learn | [Fine-Tuning LLMs](https://github.com/microsoft/generative-ai-for-beginners/blob/c35bc1950f9dc56af773d2c362dafce6f76e9a56/18-fine-tuning/README.md) |
| `ga-19` | Làm việc với mô hình ngôn ngữ nhỏ | learn | [Building with SLMs](https://github.com/microsoft/generative-ai-for-beginners/blob/c35bc1950f9dc56af773d2c362dafce6f76e9a56/19-slm/README.md) |
| `ga-20` | Làm việc với họ mô hình Mistral | learn | [Building with Mistral Models](https://github.com/microsoft/generative-ai-for-beginners/blob/c35bc1950f9dc56af773d2c362dafce6f76e9a56/20-mistral/README.md) |
| `ga-21` | Làm việc với họ mô hình Meta | learn | [Building with Meta Models](https://github.com/microsoft/generative-ai-for-beginners/blob/c35bc1950f9dc56af773d2c362dafce6f76e9a56/21-meta/README.md) |
