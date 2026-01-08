# Changelog

All notable changes to Keiba Oracle will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-01-07

### Added

#### Backend (Python/LangGraph)
- **OracleState** Pydantic model with explicit `reasoning_trace` for full AI transparency
- **Scout Node** (ReAct pattern) with Tavily search for Japanese racing sites (JRA, netkeiba)
- **Strategist Node** (Chain-of-Thought) using Gemini's extended thinking (`thinking_budget: 10000`)
- **Auditor Node** with risk assessment and backtrack capability to Strategist
- **Kelly Criterion skill file** (`kelly_criterion.skill`) for bet sizing validation
- **LangGraph definition** with Scout → Strategist → Auditor flow and conditional backtrack edge
- **FastAPI server** with CopilotKit AG-UI endpoint at `/copilotkit`
- Health check endpoint at `/health`
- Direct test endpoint at `/test` for debugging

#### Frontend (Next.js/CopilotKit)
- **Three-pane Dashboard** layout:
  - **NodeGraph**: SVG visualization with Framer Motion glow effects on active nodes
  - **ReasoningTrace**: Real-time scrolling display of AI thoughts with color-coded badges
  - **ToolPulse**: Capability log showing tool invocations with green pulse animation
- **useKeibaOracle hook** wrapping CopilotKit's `useCoAgent` with node change detection
- Query input form with loading states
- Strategy output panel showing recommendation, confidence, Kelly fraction, and risk score
- Scout data summary (racecourse, track condition, weather)
- Backtrack count indicator when strategy is revised
- CopilotKit provider integration in layout

#### Documentation
- Implementation plan at `.plans/implementation-plan.md`
- Environment example files for both backend and frontend
- Comprehensive README with architecture diagram

### Technical Details

#### Agent Flow
```
START → Scout → Strategist → Auditor → END
                    ↑           │
                    └─backtrack─┘ (if risk > 0.7)
```

#### State Schema
- `active_node`: Current executing node (scout/strategist/auditor/idle)
- `reasoning_trace`: List of ReasoningStep objects with timestamp, node, thought, action, observation
- `scout_data`: Racecourse, track condition, weather, horse data, sources
- `strategy_draft`: Recommended horse, confidence score, reasoning summary, Kelly fraction
- `risk_score`: Float 0.0-1.0 from Auditor assessment
- `tool_calls`: Log of all tool invocations for ToolPulse component
- `backtrack_count`: Number of strategy revisions (max 3)

#### Dependencies
- **Backend**: langgraph, langchain-core, google-genai, tavily-python, fastapi, uvicorn, copilotkit, pydantic
- **Frontend**: next 16, react 19, @copilotkit/react-core, @copilotkit/react-ui, framer-motion, tailwindcss 4

---

[0.1.0]: https://github.com/user/keiba-oracle/releases/tag/v0.1.0
