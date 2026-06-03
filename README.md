# ARAM — Agentic Research Analysis Machine

ARAM is a workflow integration layer for financial multi-agent systems.

It preserves the original workflow structures of:

- **TradingAgents** — trading decision with bull/bear analyst debate, trader synthesis, and risk review.
- **FinRobot** — equity research and financial report generation via Data-CoT / Concept-CoT / Thesis-CoT pipeline.

Instead of rebuilding workflows from scratch, ARAM provides:

- Agent replacement adapters (prompt override, LLM override, API agent, tool agent)
- LLM provider routing (Ollama, llama.cpp, OpenAI-compatible remote, custom fine-tuned API)
- Tool adapters for external services (SBQ-Quant, FinGPT, RAG, news/filing clients)
- Unified output schemas with Pydantic validation
- Trace logging for every workflow run
- FastAPI service endpoints
- Streamlit UI for interactive analysis

---

## Architecture Overview

```
ARAM
├── TradingAgents Wrapper
│   └── fundamental → sentiment → technical → bull/bear debate → trader → risk manager
├── FinRobot Wrapper
│   └── data-CoT → concept-CoT → thesis-CoT → valuation → report writer
├── Adapter System
│   ├── prompt override / LLM override / API agent / tool agent
├── LLM Provider Router
│   ├── Ollama (default)
│   ├── llama.cpp
│   ├── OpenAI-compatible API
│   └── Custom fine-tuned model API
└── FastAPI + Streamlit surface
```

---

## Requirements

- Python 3.11+
- [Ollama](https://ollama.com/) (default local LLM backend)
- Optional: llama.cpp server, SBQ-Quant API, FinGPT API, RAG service

---

## Installation

```bash
git clone https://github.com/hgvf/SBQ_ARAM.git
cd SBQ_ARAM

# Install dependencies
pip install -e .

# Copy and edit environment config
cp .env.example .env
```

---

## Configuration

### LLM Backend (`configs/config.yaml`)

```yaml
default_llm_provider: "ollama"   # ollama | llama_cpp | remote_api | custom_api
default_model: "default_reasoner"
```

### Model Registry (`configs/model_registry.yaml`)

Define model aliases used by agents and the UI:

```yaml
models:
  default_reasoner:
    provider: "ollama"
    base_url: "http://localhost:11434/v1"
    model: "qwen2.5:7b"

  custom_finetuned:
    provider: "custom_api"
    base_url: "http://localhost:8300/v1"
    model: "custom-finetuned-v1"
```

To add a new model, append an entry to `model_registry.yaml` — it will appear in the Streamlit UI's model selector automatically.

### External Services (`.env`)

```bash
SBQ_QUANT_BASE_URL=http://localhost:8001   # SBQ-Quant quantitative factor API
FINGPT_API_URL=http://localhost:8200       # FinGPT sentiment API
RAG_API_URL=http://localhost:8400          # RAG retrieval service
```

All external services are optional. Workflows degrade gracefully when unavailable.

---

## Quickstart

### 1. Start Ollama and pull a model

```bash
ollama serve
ollama pull qwen2.5:7b
```

### 2. Start the FastAPI server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Start the Streamlit UI

```bash
streamlit run ui/streamlit_app.py
```

Open http://localhost:8501 — enter a ticker, select a workflow and model, click **Run Analysis**.

---

## CLI / API Usage

### Health check

```bash
curl http://localhost:8000/health
# {"status":"ok","version":"0.2.0"}
```

### Run TradingAgents workflow

```bash
curl -X POST http://localhost:8000/workflows/tradingagents/run \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "NVDA",
    "date": "2026-06-03",
    "query": "Analyze NVDA and generate a risk-reviewed trading decision.",
    "model_alias": "default_reasoner",
    "save_trace": true
  }'
```

Response includes: `decision`, `confidence`, `bull_case`, `bear_case`, `sentiment`, `technical`, `fundamental`, `risk_assessment`, `trace_id`.

### Run FinRobot workflow

```bash
curl -X POST http://localhost:8000/workflows/finrobot/run \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "NVDA",
    "date": "2026-06-03",
    "query": "Generate an equity research report for NVDA.",
    "model_alias": "report_writer",
    "save_trace": true
  }'
```

Response includes: `rating_view`, `investment_thesis`, `key_risks`, `valuation_view`, `report_markdown`, `trace_id`.

### Auto-routed workflow

```bash
curl -X POST http://localhost:8000/workflows/run \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "NVDA",
    "query": "Give me a full research report and a trading decision.",
    "save_trace": true
  }'
```

The router selects FinRobot, TradingAgents, or both based on the query.

---

## Docker

```bash
cp .env.example .env
docker compose up --build
```

- FastAPI: http://localhost:8000
- Streamlit: http://localhost:8501

---

## Project Structure

```
ARAM/
├── app/                    # FastAPI service
│   ├── main.py
│   ├── routes/             # health, workflows endpoints
│   └── schemas/            # Pydantic request/response/trace schemas
├── workflows/
│   ├── tradingagents/      # TradingAgents workflow wrapper
│   └── finrobot/           # FinRobot workflow wrapper
├── adapters/
│   ├── llm/                # LLM provider router (Ollama, llama.cpp, custom)
│   ├── agents/             # Agent adapters (passthrough, prompt, llm, api)
│   ├── tools/              # Tool clients (SBQ-Quant, FinGPT, RAG, news)
│   └── parsers/            # Output parsers (JSON, trading decision, report)
├── prompts/
│   ├── tradingagents/      # 7 agent prompt YAML files
│   └── finrobot/           # 5 agent prompt YAML files
├── configs/
│   ├── config.yaml         # Master config (default model, provider)
│   ├── model_registry.yaml # All model aliases
│   ├── tool_registry.yaml  # External tool endpoints
│   ├── tradingagents_default.yaml
│   ├── finrobot_default.yaml
│   ├── agent_overrides.example.yaml
│   └── fallback_policy.yaml
├── storage/
│   ├── traces/             # Workflow trace JSON
│   ├── reports/            # Generated report Markdown
│   └── decisions/          # Trading decision JSON
├── supervisor/             # Retry policy, checkpoint stubs
├── ui/
│   └── streamlit_app.py    # Streamlit UI
└── tests/
```

---

## Switching LLM Backends

| Backend | Config |
|---|---|
| Ollama (default) | `default_llm_provider: ollama` + `OLLAMA_BASE_URL` |
| llama.cpp | `default_llm_provider: llama_cpp` + `LLAMA_CPP_BASE_URL` |
| Self-finetuned API | Add entry to `model_registry.yaml` with `provider: custom_api` |
| OpenAI-compatible | Add entry with `provider: remote_api` and `REMOTE_API_KEY` |

Agents can use different models — configure per-agent in `configs/agent_overrides.example.yaml`.

---

## Extending ARAM

**Add a new agent override** — edit or copy `configs/agent_overrides.example.yaml`:

```yaml
workflows:
  tradingagents:
    agents:
      sentiment_analyst:
        mode: api_agent
        api:
          endpoint: "http://localhost:8200/fingpt/sentiment"
          method: "POST"
```

**Add a new prompt** — create a YAML in `prompts/tradingagents/` or `prompts/finrobot/`:

```yaml
name: my_analyst
version: 1
system: |
  You are a custom analyst. Return JSON with keys: view, confidence.
```

**Add a new model** — append to `configs/model_registry.yaml`. No code changes needed.

**Connect SBQ-Quant** — set `SBQ_QUANT_BASE_URL` in `.env`. The workflow wrappers and Streamlit UI will automatically use available signals and factors.

---

## Running Tests

```bash
pip install -e ".[dev]"
pytest tests/
```

---

## Design Principles

- Preserve upstream TradingAgents and FinRobot workflow order — do not rewrite them.
- Replace individual agents through adapters, not by modifying workflow graphs.
- All prompts live in YAML files — never hard-coded in Python.
- Every workflow run produces a trace saved to `storage/traces/`.
- LLM backend is always replaceable via `configs/model_registry.yaml`.
- SBQ-Quant and other external services are treated as optional API clients.
