# Keiba Oracle Implementation Plan

## Overview
Build a Japanese horse racing analysis system with explicit AI reasoning transparency using LangGraph (Python), CopilotKit (AG-UI), and Next.js.

## Tech Decisions
- **LLM**: Gemini 3 Pro (via Google Generative AI SDK)
- **Skill Files**: Simple file read - load `.skill` markdown and inject into prompts
- **Error Handling**: Minimal (dev mode) - basic try/catch, console logging

---

## Phase 1: Backend Core (Python)

### 1.1 Update Dependencies
**File**: `agent/pyproject.toml`
```toml
dependencies = [
    "langgraph>=0.2.0",
    "langchain-core>=0.3.0",
    "google-genai>=1.0.0",
    "langchain-tavily>=0.1.0",
    "tavily-python>=0.5.0",
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "ag-ui-langgraph>=0.1.0",
    "pydantic>=2.10.0",
    "python-dotenv>=1.0.0",
    "httpx>=0.28.0",
]
```

### 1.2 Create State Model
**File**: `agent/state.py`
- `OracleState` Pydantic model with:
  - `active_node`: NodeType enum (scout/strategist/auditor/idle)
  - `reasoning_trace`: List[ReasoningStep] - **THE KEY EXPLICIT REQUIREMENT**
  - `scout_data`: Optional[ScoutData]
  - `strategy_draft`: Optional[StrategyDraft]
  - `risk_score`: float
  - `requires_backtrack`: bool
  - `tool_calls`: List[dict] - for ToolPulse component

### 1.3 Create Search Tool
**File**: `agent/tools/search.py`
- Tavily search configured for Japanese racing sites (jra.go.jp, netkeiba.com)
- LangChain `@tool` decorator for LangGraph integration

### 1.4 Create Scout Node (ReAct)
**File**: `agent/nodes/scout.py`
- Uses Gemini 3 Pro with tool binding
- Explicitly logs every thought/action/observation to `reasoning_trace`
- Logs tool calls to `tool_calls` list
- Outputs `ScoutData` with racecourse info

### 1.5 Create Strategist Node (CoT)
**File**: `agent/nodes/strategist.py`
- Uses Gemini 3 Pro with `thinkingLevel: HIGH`
- Captures extended thinking tokens and logs to `reasoning_trace`
- Outputs `StrategyDraft` with recommendation and kelly_fraction

### 1.6 Create Auditor Node (Negotiation)
**File**: `agent/nodes/auditor.py`
- Loads `kelly_criterion.skill` file into system prompt
- Calculates `risk_score`
- Returns `Command(goto="strategist")` if risk > 0.7 (backtrack)
- Sets `requires_backtrack` flag for UI visualization

### 1.7 Create Skill File
**File**: `agent/skills/kelly_criterion.skill`
- Markdown file with Kelly Criterion formula
- Risk thresholds and audit rules

### 1.8 Wire Up LangGraph
**File**: `agent/graph.py`
- StateGraph with Scout -> Strategist -> Auditor flow
- Conditional edge from Auditor back to Strategist (backtrack)
- Add max backtrack counter (3 attempts) to prevent infinite loops

### 1.9 Create FastAPI Entry Point
**File**: `agent/main.py`
- FastAPI app with CORS for localhost:3000
- `add_langgraph_fastapi_endpoint(app, graph, "/agent")`
- Health check endpoint

---

## Phase 2: CopilotKit Bridge

### 2.1 Create CopilotKit API Route
**File**: `web/app/api/copilotkit/route.ts`
- CopilotRuntime with remoteEndpoints pointing to `http://localhost:8000/agent`
- ExperimentalEmptyAdapter for pure LangGraph backend

### 2.2 Update Next.js Config
**File**: `web/next.config.ts`
- Add rewrites if needed for API proxy

---

## Phase 3: Frontend (Next.js)

### 3.1 Add Dependencies
**File**: `web/package.json`
```json
"dependencies": {
    "@copilotkit/react-core": "^1.50.0",
    "@copilotkit/react-ui": "^1.50.0",
    "framer-motion": "^12.0.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.5.0"
}
```

### 3.2 Create TypeScript Types
**File**: `web/lib/types.ts`
- Mirror Python OracleState interfaces in TypeScript

### 3.3 Create Custom Hook
**File**: `web/hooks/useKeibaOracle.ts`
- Wraps `useAgent<OracleState>` from CopilotKit
- Tracks `previousNode` with useRef
- Exposes `onNodeChange` callback for pulse animations
- Provides `sendQuery` function

### 3.4 Create NodeGraph Component
**File**: `web/components/NodeGraph.tsx`
- SVG with three nodes (Scout, Strategist, Auditor)
- Lines connecting nodes + curved backtrack edge
- Framer Motion glow effect when `active_node` matches
- **KEY**: useEffect triggers pulse animation on node change

### 3.5 Create ReasoningTrace Component
**File**: `web/components/ReasoningTrace.tsx`
- Scrolling list rendering `reasoning_trace` entries
- Color-coded badges by node type
- Auto-scroll to latest entry
- Shows thought/action/observation for each step

### 3.6 Create ToolPulse Component
**File**: `web/components/ToolPulse.tsx`
- Displays `tool_calls` from state
- Green pulse animation on new tool invocation
- Shows tool name, args, and timestamp

### 3.7 Create Dashboard Component
**File**: `web/components/Dashboard.tsx`
- Three-pane grid layout (NodeGraph | ReasoningTrace | ToolPulse)
- Query input form at top
- Strategy output panel at bottom when available

### 3.8 Update Layout
**File**: `web/app/layout.tsx`
- Wrap children in `<CopilotKit runtimeUrl="/api/copilotkit" agent="keiba-oracle">`

### 3.9 Update Page
**File**: `web/app/page.tsx`
- Replace boilerplate with `<Dashboard />`

### 3.10 Add Animation Styles
**File**: `web/app/globals.css`
- Keyframes for pulse/glow animations if not using Framer Motion inline

---

## File Summary

### Files to Create
| Path | Purpose |
|------|---------|
| `.plans/implementation-plan.md` | Project documentation (this plan) |
| `agent/state.py` | OracleState Pydantic model |
| `agent/tools/__init__.py` | Package init |
| `agent/tools/search.py` | Tavily search tool |
| `agent/nodes/__init__.py` | Package init |
| `agent/nodes/scout.py` | Scout node (ReAct) |
| `agent/nodes/strategist.py` | Strategist node (CoT) |
| `agent/nodes/auditor.py` | Auditor node (negotiation) |
| `agent/skills/kelly_criterion.skill` | Betting strategy skill |
| `agent/graph.py` | LangGraph definition |
| `agent/.env.example` | Environment template |
| `web/app/api/copilotkit/route.ts` | CopilotKit API route |
| `web/lib/types.ts` | TypeScript interfaces |
| `web/hooks/useKeibaOracle.ts` | Custom agent hook |
| `web/components/NodeGraph.tsx` | SVG graph visualization |
| `web/components/ReasoningTrace.tsx` | Reasoning display |
| `web/components/ToolPulse.tsx` | Tool trigger log |
| `web/components/Dashboard.tsx` | Main layout |
| `web/.env.local.example` | Environment template |

### Files to Modify
| Path | Changes |
|------|---------|
| `agent/pyproject.toml` | Add dependencies |
| `agent/main.py` | FastAPI + AG-UI setup |
| `web/package.json` | Add dependencies |
| `web/next.config.ts` | API config |
| `web/app/layout.tsx` | CopilotKit provider |
| `web/app/page.tsx` | Dashboard component |

---

## Environment Variables Required
```bash
# agent/.env
GOOGLE_API_KEY=xxx
TAVILY_API_KEY=xxx

# web/.env.local
AGENT_URL=http://localhost:8000/agent
```

---

## Running the Project
```bash
# Terminal 1: Backend
cd agent && uv sync && uv run uvicorn main:app --reload --port 8000

# Terminal 2: Frontend
cd web && npm install && npm run dev
```

---

## Key Implementation Notes

1. **Explicit Reasoning**: Every node must append to `reasoning_trace` - no black box helpers
2. **Pulse Animation**: `useKeibaOracle` hook tracks `active_node` changes and triggers callbacks
3. **Backtrack Visualization**: Curved edge in NodeGraph turns red when `requires_backtrack` is true
4. **Max Backtracks**: Add counter in Auditor to prevent infinite loops (max 3)
5. **Gemini 3 Pro**: Use `google-genai` SDK with `thinkingLevel: HIGH` for Strategist
