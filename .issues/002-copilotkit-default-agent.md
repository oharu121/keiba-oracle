# CopilotKit Provider Default Agent Issue

## Summary

The `<CopilotKit>` React provider defaults the `agent` prop to `"default"`, causing
"Agent not found" errors when using custom agent names.

## Error Message

```
Uncaught Error: useAgent: Agent 'default' not found after runtime sync (runtimeUrl=/api/copilotkit). Known agents: [keiba-oracle]
```

## Root Cause

In `@copilotkit/react-core` (v1.50.0), the CopilotKit provider passes the agent ID to
the chat configuration context with a default of `"default"`:

```typescript
// node_modules/@copilotkit/react-core/src/components/copilot-provider/copilotkit.tsx:531
<CopilotChatConfigurationProvider agentId={props.agent ?? "default"} ...>
```

This causes internal hooks like `useAgent()` to look for an agent named `"default"`,
even when the runtime registers a differently-named agent.

## Solution

Explicitly set the `agent` prop on the `<CopilotKit>` provider to match your registered
agent name:

```tsx
// Before (broken)
<CopilotKit runtimeUrl="/api/copilotkit">
  {children}
</CopilotKit>

// After (working)
<CopilotKit runtimeUrl="/api/copilotkit" agent="keiba-oracle">
  {children}
</CopilotKit>
```

## Affected Versions

- @copilotkit/react-core: ^1.50.0
- @copilotkitnext/react: 0.0.33

## Files Modified

- `web/app/layout.tsx` - Added `agent="keiba-oracle"` prop

## Status

- [x] Fix applied (v0.2.4)
- [ ] Upstream documentation updated to clarify this requirement
