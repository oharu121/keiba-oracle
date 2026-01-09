# CopilotKit dict_repr Bug

## Issue
`LangGraphAGUIAgent` missing `dict_repr()` method causes 500 error on `/copilotkit/info` endpoint.

## Upstream Issue
https://github.com/CopilotKit/CopilotKit/issues/2891

## Affected Versions
- copilotkit Python SDK: 0.1.74
- ag-ui-langgraph: 0.0.22
- @copilotkit/*: 1.50.x

## Workaround
Created `PatchedLangGraphAGUIAgent` subclass with `dict_repr()` method in `agent/app/main.py`.

## Status
- [x] Workaround applied
- [ ] Upstream fix released
- [ ] Workaround removed (when upstream fix is available)
