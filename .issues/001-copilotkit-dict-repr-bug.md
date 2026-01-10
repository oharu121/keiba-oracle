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

## Issue 2: FastAPI trailing slash redirect

FastAPI's default `redirect_slashes=True` causes 307 redirect from `/copilotkit` to `/copilotkit/`. CopilotKit's runtime doesn't follow POST redirects, causing silent failures.

### Root Cause
- `POST /copilotkit` → 307 redirect to `/copilotkit/`
- CopilotKit runtime doesn't follow 307 redirects for POST requests (security behavior)
- Request fails silently, returning empty agents list

### Fix
Added `redirect_slashes=False` to FastAPI app constructor in `agent/app/main.py`.

### Status
- [x] Fix applied (v0.2.2)
