# Prototype — Vinschool Notification AI (Nhóm E06 · C401)

## Mô tả

Hệ thống AI hỗ trợ phụ huynh Vinschool xử lý thông báo thông minh theo mô hình Push 2 giai đoạn: **Pha 1 (Tự động)** — giáo viên gửi thông báo (có thể kèm file PDF/ảnh) → AI tự động trích xuất nội dung file, phân loại mức độ ưu tiên (Cao/Trung bình/Thấp) và tạo tóm tắt nhanh; **Pha 2 (Tương tác)** — phụ huynh bấm "Xem chi tiết" → AI tóm tắt chi tiết, trích xuất sự kiện/lịch hẹn, và thu nhận phản hồi (upvote/downvote) để cải thiện mô hình.

## Level: Working Prototype

- Streamlit UI đa trang với 5 view: Dashboard, Teacher Portal, AI Processing Workflow, Analytics, Evaluation Metrics
- LangGraph pipeline chạy thật end-to-end: `parse_attachment → prioritize → summarize_brief → summarize_detailed → feedback`
- AI call thật: GPT-4o-mini (Vision LLM cho OCR ảnh/PDF scan), DeepSeek / OpenRouter (prioritization + summarization)
- File upload thật: giáo viên upload PDF/ảnh → pdfplumber extract text (PDF chuẩn) hoặc PyMuPDF + Vision LLM (PDF scan/ảnh)

## Links

- **GitHub repo:** https://github.com/t1qnq/Hackathon_Day5_C401_E6
- **Chạy local:**
  ```bash
  pip install -r requirements.txt
  cp .env.example .env   # Điền API key vào .env
  streamlit run app.py
  ```

## Tools và API đã dùng

| Loại | Tool / API | Mục đích |
|------|-----------|----------|
| **Framework** | LangGraph ≥0.4.0 | Orchestrate pipeline AI dạng graph (nodes + edges + conditional routing) |
| **UI** | Streamlit ≥1.45.0 | Frontend đa trang: Dashboard, Teacher Portal, AI Workflow, Analytics, Evaluation |
| **File parsing** | pdfplumber 0.11.9 | Trích xuất text + bảng biểu từ PDF chuẩn (text-based) |
| **File parsing** | PyMuPDF 1.27.2 | Render PDF scan → ảnh PNG (fallback khi pdfplumber không đọc được text) |
| **Vision LLM** | OpenAI GPT-4o-mini | OCR ảnh và PDF scan → text (gọi qua Vision API) |
| **LLM Prioritization** | DeepSeek / OpenRouter (multi-provider chain) | Phân loại mức độ ưu tiên thông báo (Cao/TB/Thấp) + confidence score |
| **LLM Summarization** | OpenRouter (minimax-m2.5 / các model free) | Tóm tắt brief (3 bullet points) và detailed (1 đoạn văn) |
| **Visualization** | Plotly ≥6.0.0 + Pandas | Biểu đồ phân bố priority, category, latency trend trong Evaluation dashboard |
| **Testing** | Pytest ≥9.0.0 | Unit test cho file_parser và prioritizer |
| **AI coding assistant** | Google Antigravity / Claude | Scaffold kiến trúc SOLID, debug integration, viết test cases |

## Phân công

| Thành viên | Vai trò | Phân hệ | Output chính |
|-----------|---------|---------|-------------|
| **Quang** | Team Lead · LangGraph Architect | Backend · Core Agent | `graph.py` — thiết kế graph tổng thể, định nghĩa `AgentState`, kết nối nodes, review/merge code |
| **Tuấn** | AI Node Developer · Prioritization | Backend · LangGraph Node | `nodes/prioritizer.py` — node phân loại ưu tiên bằng rules + multi-provider LLM chain, `services/prioritization/rules.py`, unit test |
| **Hải** | AI Node · Summarizer | Backend · LangGraph Node | `nodes/summarizer.py`, `services/summarization/` — node tóm tắt brief + detailed, LLM client, formatter, fallback logic |
| **Long** | File Processing · OCR | Backend · File Handler | `nodes/file_parser.py` — node trích xuất text từ PDF/ảnh (pdfplumber → Vision LLM fallback), `docs/parse_attachment.md` (spec), `tests/test_file_parser.py` |
| **Dũng** | API Integration · Data Layer | Backend · API Trường | `api/data_loader.py` — mock API dữ liệu 300+ thông báo + student profile, `api/schemas.py`, eval metrics |
| **Thuận** | Feedback Loop · Learning Signal | Backend · Human-in-loop | `nodes/feedback.py` — node xử lý upvote/downvote, learning signal, `services/prioritization/feedback_learning.py` (keyword learning từ feedback) |
| **Huy** | Frontend · UI / Demo | Frontend · Demo | `app.py` (Streamlit) — 5 trang: Dashboard, Teacher Portal, AI Processing, Analytics, Evaluation; `ui/` components, styles, data_service |

## Kiến trúc hệ thống

```
Hackathon_Day5_C401_E6/
│
├── graph.py                         ← LangGraph pipeline (AgentState + nodes + edges)
├── app.py                           ← Streamlit UI (5 trang)
│
├── nodes/                           ← LangGraph nodes
│   ├── file_parser.py               ← parse_attachment (PDF/ảnh → text)
│   ├── prioritizer.py               ← prioritize_notification (rules + LLM)
│   ├── summarizer.py                ← summarize_brief + summarize_detailed
│   └── feedback.py                  ← handle_feedback (upvote/downvote)
│
├── services/                        ← Business logic tách riêng
│   ├── prioritization/              ← Rules engine, feedback learning
│   └── summarization/               ← LLM client, formatter, IO utils
│
├── ui/                              ← UI components cho Streamlit
│   ├── components.py                ← Các widget: notification card, priority badge, timeline
│   ├── graph_runner.py              ← Runner kết nối UI ↔ LangGraph (mock + real mode)
│   ├── data_service.py              ← Load dữ liệu cho UI
│   └── styles.py                    ← Custom CSS
│
├── api/                             ← Data layer
│   ├── data_loader.py               ← Mock API 300+ thông báo + student profile
│   └── schemas.py                   ← Schema validation
│
├── config/                          ← Runtime config
│   ├── prioritization_runtime.json  ← Tunable weights, thresholds, keyword confidence
│   └── provider_config.py           ← Multi-provider LLM config (DeepSeek, OpenRouter, OpenAI)
│
├── core/                            ← Shared constants + types
│   ├── constants/                   ← Keywords, categories, tone profiles
│   └── types/                       ← TypedDict definitions
│
├── utils/                           ← Utilities
│   ├── llm_providers.py             ← Multi-provider LLM chain (fallback giữa các provider)
│   └── prompt_loader.py             ← Load system prompt từ file / env
│
├── tests/                           ← Unit tests
│   ├── test_file_parser.py          ← Test parse PDF/ảnh/edge cases
│   └── test_prioritizer.py          ← Test classification logic
│
├── docs/                            ← Technical specs
│   └── parse_attachment.md          ← Input/Output schema, error codes
│
├── static/                          ← Assets (logo)
├── GROUP_REPORT/                    ← SPEC + prototype readme + demo slides
└── INVIDUAL_REPORT/                 ← Reflection + feedback cá nhân
```

## Luồng xử lý (LangGraph Pipeline)

```
                    ┌─────────────┐
                    │    START    │
                    └──────┬──────┘
                           │
                    router_start()
                    ┌──────┴──────┐
                    │ Có file?    │
              Có    │             │  Không
           ┌────────┤             ├────────┐
           ▼        └─────────────┘        ▼
  ┌────────────────┐              ┌────────────────────┐
  │parse_attachment│              │prioritize_notification│
  │ (PDF/ảnh→text) │──────────────▶│ (rules + LLM)        │
  └────────────────┘              └─────────┬──────────┘
                                            │
                                  router_after_prioritize()
                                  ┌─────────┴──────────┐
                                  │ Confidence thấp?   │
                            Có    │                    │  Đủ
                         ┌────────┤                    ├────────┐
                         ▼        └────────────────────┘        ▼
                ┌──────────────────┐                   ┌──────────┐
                │teacher_intervention│                   │ scheduler │
                │(human-in-loop)    │───────────────────▶│(trích lịch)│
                └──────────────────┘                   └─────┬────┘
                                                              │
                                                    ┌─────────▼──────────┐
                                                    │  summarize_brief   │
                                                    │(3 bullet points)   │
                                                    └─────────┬──────────┘
                                                              │
                                                    router_after_brief()
                                                    ┌─────────┴──────────┐
                                                    │ Xem chi tiết?      │
                                              Có    │                    │  Không
                                           ┌────────┤                    ├───▶ END
                                           ▼        └────────────────────┘
                                  ┌──────────────────────┐
                                  │  summarize_detailed   │
                                  │(1 đoạn văn + entities)│
                                  └──────────┬───────────┘
                                             │
                                  ┌──────────▼───────────┐
                                  │   handle_feedback     │
                                  │(upvote/downvote/learn)│
                                  └──────────┬───────────┘
                                             │
                                            END
```
