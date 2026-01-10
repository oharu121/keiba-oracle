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

### Issue 2: FastAPI trailing slash redirect
FastAPI's default `redirect_slashes=True` caused 307 redirect from `/copilotkit` to `/copilotkit/`.

CopilotKit's `@copilotkit/runtime` doesn't follow 307 redirects for POST requests (standard HTTP security behavior), causing the request to fail silently and return empty agents.

**Debugging steps:**
1. Added GET endpoint to `/api/copilotkit` to confirm `AGENT_URL` env var was set
2. Tested backend directly: `POST /copilotkit` returned 307, `POST /copilotkit/` returned 200
3. Identified redirect as root cause

**Fix:** Added `redirect_slashes=False` to FastAPI app constructor.

## Files Modified

| File | Change |
|------|--------|
| `agent/app/main.py` | Added `PatchedLangGraphAGUIAgent` class, added `redirect_slashes=False` |
| `web/app/api/copilotkit/route.ts` | Added error handling for missing `AGENT_URL`, added GET debug endpoint |
| `.issues/001-copilotkit-dict-repr-bug.md` | Documented both issues |

## Verification

```bash
# Should return 200 with agents (no redirect)
curl -X POST "https://oharu121-keiba-oracle.hf.space/copilotkit" \
  -H "Content-Type: application/json" -d '{"method":"info"}'

# Expected response:
{"actions":[],"agents":[{"name":"keiba-oracle","description":"..."}],"sdkVersion":"0.1.74"}
```

## Lessons Learned

1. **Test backend endpoints directly** before assuming frontend/runtime issues
2. **Check for redirects** - many HTTP clients don't follow redirects for non-GET requests
3. **Add debug endpoints** to confirm environment variables are set in production
4. **FastAPI defaults** may not be API-friendly (`redirect_slashes=True` causes issues)

## Versions

- copilotkit Python SDK: 0.1.74
- ag-ui-langgraph: 0.0.22
- @copilotkit/*: ^1.50.0
- FastAPI: >=0.115.0
