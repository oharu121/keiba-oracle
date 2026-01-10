# CopilotKit + Vercel Integration Fix

## Problem
Frontend on Vercel displayed runtime error:
```
Uncaught Error: useAgent: Agent 'default' not found after runtime sync (runtimeUrl=/api/copilotkit). No agents registered.
```

## Root Causes Found

### Issue 1: Missing dict_repr() method
**Bug:** [CopilotKit#2891](https://github.com/CopilotKit/CopilotKit/issues/2891)

`LangGraphAGUIAgent` class missing `dict_repr()` method caused 500 error on `/copilotkit/info` endpoint.

**Fix:** Created `PatchedLangGraphAGUIAgent` subclass in `agent/app/main.py`.

### Issue 2: CopilotKit route registration requires trailing slash
**Bug:** [CopilotKit#1907](https://github.com/CopilotKit/CopilotKit/issues/1907)

CopilotKit's `add_fastapi_endpoint` registers routes as `/{prefix}/{path:path}`, which means:
- `/copilotkit/` works (path="" matches)
- `/copilotkit` returns 404 (no route match)

FastAPI's `redirect_slashes=True` redirects `/copilotkit` → `/copilotkit/` (307), but CopilotKit's `@copilotkit/runtime` doesn't follow 307 redirects for POST requests.

**Debugging steps:**
1. Added GET endpoint to `/api/copilotkit` to confirm `AGENT_URL` env var was set
2. Tested backend directly: `POST /copilotkit` returned 307, `POST /copilotkit/` returned 200
3. Tried `redirect_slashes=False` - but then `/copilotkit` returned 404
4. Researched industry standard and CopilotKit issues
5. Found [CopilotKit#1907](https://github.com/CopilotKit/CopilotKit/issues/1907) documenting this exact issue

**Fix:** `AGENT_URL` must include trailing slash: `https://backend.com/copilotkit/`

## Files Modified

| File | Change |
|------|--------|
| `agent/app/main.py` | Added `PatchedLangGraphAGUIAgent` class, added comment about trailing slash |
| `web/app/api/copilotkit/route.ts` | Added error handling for missing `AGENT_URL`, added GET debug endpoint |
| `web/.env.local.example` | Documented trailing slash requirement |
| `.issues/001-copilotkit-dict-repr-bug.md` | Documented both issues |

## Verification

```bash
# Must use trailing slash
curl -X POST "https://oharu121-keiba-oracle.hf.space/copilotkit/" \
  -H "Content-Type: application/json" -d '{"method":"info"}'

# Expected response:
{"actions":[],"agents":[{"name":"keiba-oracle","description":"..."}],"sdkVersion":"0.1.74"}
```

## Lessons Learned

1. **Test backend endpoints directly** before assuming frontend/runtime issues
2. **Check for redirects** - many HTTP clients don't follow redirects for non-GET requests
3. **Add debug endpoints** to confirm environment variables are set in production
4. **Check upstream issues** - both bugs were known CopilotKit issues
5. **Trailing slashes matter** - CopilotKit SDK requires them due to route registration pattern

## Configuration Requirement

**AGENT_URL must include trailing slash:**
```
# Correct
AGENT_URL=https://your-backend.hf.space/copilotkit/

# Wrong (will fail)
AGENT_URL=https://your-backend.hf.space/copilotkit
```

## Versions

- copilotkit Python SDK: 0.1.74
- ag-ui-langgraph: 0.0.22
- @copilotkit/*: ^1.50.0
- FastAPI: >=0.115.0
