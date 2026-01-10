# CopilotKit Integration Issues

## Issue 1: Missing dict_repr() method

`LangGraphAGUIAgent` missing `dict_repr()` method causes 500 error on `/copilotkit/info` endpoint.

### Upstream Issue
https://github.com/CopilotKit/CopilotKit/issues/2891

### Affected Versions
- copilotkit Python SDK: 0.1.74
- ag-ui-langgraph: 0.0.22
- @copilotkit/*: 1.50.x

### Workaround
Created `PatchedLangGraphAGUIAgent` subclass with `dict_repr()` method in `agent/app/main.py`.

### Status
- [x] Workaround applied
- [ ] Upstream fix released
- [ ] Workaround removed (when upstream fix is available)

---

## Issue 2: CopilotKit route registration requires trailing slash

CopilotKit's `add_fastapi_endpoint` registers routes as `/{prefix}/{path:path}`, which means:
- `/copilotkit/` works (path="" matches)
- `/copilotkit` returns 404 (no route match)

### Upstream Issue
https://github.com/CopilotKit/CopilotKit/issues/1907

### Root Cause
- CopilotKit SDK route pattern requires trailing slash
- FastAPI's `redirect_slashes=True` redirects `/copilotkit` → `/copilotkit/` (307)
- CopilotKit's `@copilotkit/runtime` doesn't follow 307 redirects for POST requests
- Result: empty agents list returned to frontend

### Fix
**AGENT_URL must include trailing slash:** `https://your-backend.com/copilotkit/`

This is documented in:
- `web/.env.local.example`
- `agent/app/main.py` (comment)

### Status
- [x] Documentation added (v0.2.2)
- [ ] Upstream fix released (CopilotKit SDK handles both URL formats)
