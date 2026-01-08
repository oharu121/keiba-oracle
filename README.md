# Keiba Oracle

Japanese Horse Racing Analysis with Explicit AI Reasoning.

A multi-agent system that demonstrates transparent AI decision-making using LangGraph, CopilotKit, and Next.js. Every thought, action, and observation is explicitly exposed to the user.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js)                       │
│  ┌──────────────┐  ┌─────────────────┐  ┌──────────────────┐   │
│  │  NodeGraph   │  │ ReasoningTrace  │  │    ToolPulse     │   │
│  │  (SVG+Glow)  │  │  (Live Stream)  │  │  (Capability Log)│   │
│  └──────────────┘  └─────────────────┘  └──────────────────┘   │
│                              │                                   │
│                     CopilotKit Bridge                           │
└─────────────────────────────────┬───────────────────────────────┘
                                  │ AG-UI Protocol
┌─────────────────────────────────┴───────────────────────────────┐
│                      Backend (Python/FastAPI)                    │
│                                                                  │
│   ┌─────────┐      ┌─────────────┐      ┌─────────┐            │
│   │  Scout  │ ──▶  │ Strategist  │ ──▶  │ Auditor │ ──▶ END   │
│   │ (ReAct) │      │   (CoT)     │      │ (Risk)  │            │
│   └─────────┘      └─────────────┘      └────┬────┘            │
│                           ▲                   │                  │
│                           └───── backtrack ───┘                  │
│                                                                  │
│                        LangGraph + Gemini                        │
└──────────────────────────────────────────────────────────────────┘
```

## Features

- **Explicit Reasoning**: Every AI thought is captured in `reasoning_trace` and displayed in real-time
- **Multi-Node Graph**: Scout → Strategist → Auditor pipeline with backtrack capability
- **Visual Feedback**: Nodes glow when active, pulse on transitions
- **Tool Transparency**: All tool invocations logged in the Capability Log
- **Risk Management**: Kelly Criterion skill file for bet sizing validation

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 16, React 19, Tailwind CSS 4, Framer Motion |
| Bridge | CopilotKit (AG-UI Protocol) |
| Backend | Python 3.12, FastAPI, LangGraph |
| Intelligence | Google Gemini (gemini-2.0-flash, gemini-2.0-flash-thinking-exp) |
| Search | Tavily API (Japanese racing sites) |

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+
- [uv](https://github.com/astral-sh/uv) (Python package manager)
- Google API Key (for Gemini)
- Tavily API Key (for search)

### 1. Clone and Setup

```bash
git clone <repo-url>
cd keiba-oracle
```

### 2. Backend Setup

```bash
cd agent

# Copy environment template
cp .env.example .env

# Add your API keys to .env:
# GOOGLE_API_KEY=your_key_here
# TAVILY_API_KEY=your_key_here

# Install dependencies
uv sync

# Run the server
uv run uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup

```bash
cd web

# Copy environment template
cp .env.local.example .env.local

# Install dependencies
npm install

# Run the dev server
npm run dev
```

### 4. Open the App

Navigate to http://localhost:3000

## Project Structure

```
keiba-oracle/
├── agent/                      # Python Backend
│   ├── app/
│   │   ├── main.py            # FastAPI + CopilotKit endpoint
│   │   ├── graph.py           # LangGraph definition
│   │   ├── models/
│   │   │   └── state.py       # OracleState Pydantic model
│   │   ├── nodes/
│   │   │   ├── scout.py       # ReAct node (search tools)
│   │   │   ├── strategist.py  # CoT node (extended thinking)
│   │   │   └── auditor.py     # Risk assessment + backtrack
│   │   ├── tools/
│   │   │   └── search.py      # Tavily search tools
│   │   └── skills/
│   │       └── kelly_criterion.skill  # Betting strategy rules
│   └── pyproject.toml         # Dependencies
│
├── web/                        # Next.js Frontend
│   ├── app/
│   │   ├── api/copilotkit/    # CopilotKit API route
│   │   ├── layout.tsx         # CopilotKit provider
│   │   └── page.tsx           # Dashboard entry
│   ├── components/
│   │   ├── Dashboard.tsx      # Three-pane layout
│   │   ├── NodeGraph.tsx      # SVG graph visualization
│   │   ├── ReasoningTrace.tsx # Real-time reasoning display
│   │   └── ToolPulse.tsx      # Tool invocation log
│   ├── hooks/
│   │   └── useKeibaOracle.ts  # Agent state hook
│   └── lib/
│       └── types.ts           # TypeScript interfaces
│
└── .plans/
    └── implementation-plan.md  # Development roadmap
```

## Agent Nodes

### Scout (ReAct Pattern)
- Gathers racecourse conditions using Tavily search
- Logs every tool call to `tool_calls` array
- Outputs structured `ScoutData`

### Strategist (Chain-of-Thought)
- Uses Gemini's extended thinking (`thinking_budget: 10000`)
- Captures internal reasoning in `reasoning_trace`
- Outputs `StrategyDraft` with confidence and Kelly fraction

### Auditor (Risk Assessment)
- Loads `kelly_criterion.skill` for validation rules
- Calculates risk score (0.0 - 1.0)
- Can trigger **backtrack** to Strategist if risk > 0.7
- Maximum 3 backtrack attempts to prevent infinite loops

## Key Design Decisions

1. **No Black Boxes**: Every node explicitly appends to `reasoning_trace`
2. **Pulse Animation**: `useKeibaOracle` hook tracks `active_node` changes
3. **Backtrack Visualization**: Curved edge turns red when `requires_backtrack` is true
4. **Type Safety**: Python Pydantic models mirrored in TypeScript

## Environment Variables

### Backend (`agent/.env`)
```bash
GOOGLE_API_KEY=xxx      # Required: Gemini API
TAVILY_API_KEY=xxx      # Required: Search API
```

### Frontend (`web/.env.local`)
```bash
AGENT_URL=http://localhost:8000/copilotkit  # Backend URL
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API info |
| `/health` | GET | Health check with API key status |
| `/copilotkit` | POST | CopilotKit AG-UI endpoint |
| `/test` | POST | Direct agent test (bypass UI) |

## Development

```bash
# Backend with hot reload
cd agent && uv run uvicorn app.main:app --reload

# Frontend with hot reload
cd web && npm run dev

# Test backend directly
curl -X POST "http://localhost:8000/test?query=Tokyo%20racecourse%20conditions"
```

## License

MIT

---

*This recommendation is for educational purposes. Always gamble responsibly.*
