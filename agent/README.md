---
title: Keiba Oracle Backend API
emoji: 🏇
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 8000
---

# Keiba Oracle - Backend Agent

Python backend for Keiba Oracle using LangGraph, Gemini, and CopilotKit.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     LangGraph                           │
│                                                         │
│   ┌─────────┐      ┌─────────────┐      ┌─────────┐   │
│   │  Scout  │ ──▶  │ Strategist  │ ──▶  │ Auditor │   │
│   │ (ReAct) │      │   (CoT)     │      │ (Risk)  │   │
│   └─────────┘      └─────────────┘      └────┬────┘   │
│        │                  ▲                   │        │
│        │                  └───── backtrack ───┘        │
│        ▼                                               │
│   ┌─────────┐                                          │
│   │ Tavily  │  Search Tools                            │
│   └─────────┘                                          │
└─────────────────────────────────────────────────────────┘
                          │
                    FastAPI + CopilotKit
                          │
                      AG-UI Protocol
```

## Quick Start

```bash
# Setup environment
cp .env.example .env
# Edit .env with your API keys

# Install dependencies
uv sync

# Run server
uv run uvicorn app.main:app --reload --port 8000
```

## Project Structure

```
agent/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI entry point + CopilotKit endpoint
│   ├── graph.py             # LangGraph definition
│   ├── models/
│   │   ├── __init__.py
│   │   └── state.py         # OracleState Pydantic model
│   ├── nodes/
│   │   ├── __init__.py
│   │   ├── scout.py         # ReAct node with Tavily search
│   │   ├── strategist.py    # Chain-of-Thought with Gemini thinking
│   │   └── auditor.py       # Risk assessment + backtrack logic
│   ├── tools/
│   │   ├── __init__.py
│   │   └── search.py        # Tavily search tools for Japanese racing
│   └── skills/
│       ├── __init__.py
│       └── kelly_criterion.skill  # Kelly Criterion betting rules
├── pyproject.toml           # Dependencies
├── .env.example             # Environment template
└── README.md
```

## Nodes

### Scout (ReAct Pattern)
- Uses Gemini with tool binding
- Searches Japanese racing sites via Tavily (jra.go.jp, netkeiba.com)
- Logs every thought/action/observation to `reasoning_trace`
- Outputs `ScoutData` with racecourse conditions

### Strategist (Chain-of-Thought)
- Uses Gemini's extended thinking (`thinking_budget: 10000`)
- Captures internal reasoning explicitly
- Outputs `StrategyDraft` with confidence and Kelly fraction

### Auditor (Risk Assessment)
- Loads `kelly_criterion.skill` into system prompt
- Calculates risk score (0.0 - 1.0)
- Triggers **backtrack** to Strategist if risk > 0.7
- Maximum 3 backtracks to prevent infinite loops

## State Schema

```python
class OracleState(BaseModel):
    active_node: NodeType           # scout/strategist/auditor/idle
    reasoning_trace: list[ReasoningStep]  # THE KEY: explicit AI thoughts
    scout_data: Optional[ScoutData]
    strategy_draft: Optional[StrategyDraft]
    risk_score: float               # 0.0 - 1.0
    requires_backtrack: bool
    backtrack_count: int            # max 3
    tool_calls: list[ToolCall]      # for frontend ToolPulse
    query: str
    final_recommendation: Optional[str]
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API info and available endpoints |
| `/health` | GET | Health check with API key status |
| `/copilotkit` | POST | CopilotKit AG-UI endpoint |
| `/test` | POST | Direct agent test (bypass CopilotKit) |

## Environment Variables

```bash
# Required
GOOGLE_API_KEY=xxx      # Gemini API key
TAVILY_API_KEY=xxx      # Tavily search API key

# Optional
HOST=0.0.0.0
PORT=8000
```

## Testing

```bash
# Health check
curl http://localhost:8000/health

# Direct agent test
curl -X POST "http://localhost:8000/test?query=Tokyo%20racecourse%20conditions"
```

## Dependencies

- **langgraph** - Agent orchestration
- **langchain-core** - Tool abstractions
- **google-genai** - Gemini API client
- **tavily-python** - Search API
- **fastapi** - Web framework
- **uvicorn** - ASGI server
- **copilotkit** - AG-UI protocol bridge
- **pydantic** - Data validation

## Docker

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install uv && uv sync
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## License

MIT
