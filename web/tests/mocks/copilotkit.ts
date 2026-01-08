import { vi } from "vitest";
import type { OracleState } from "@/lib/types";

/**
 * Default state matching the hook's DEFAULT_STATE
 */
export const DEFAULT_STATE: OracleState = {
  active_node: "idle",
  reasoning_trace: [],
  scout_data: null,
  strategy_draft: null,
  risk_score: 0,
  requires_backtrack: false,
  backtrack_reason: null,
  backtrack_count: 0,
  query: "",
  tool_calls: [],
  final_recommendation: null,
};

/**
 * Create a mock return value for useCoAgent
 */
export function createMockUseCoAgent(
  overrides: Partial<{
    state: Partial<OracleState>;
    running: boolean;
  }> = {}
) {
  const state = { ...DEFAULT_STATE, ...overrides.state };
  const setState = vi.fn();
  const run = vi.fn().mockResolvedValue(undefined);
  const start = vi.fn();
  const stop = vi.fn();

  return {
    name: "keiba-oracle",
    state,
    setState,
    run,
    start,
    stop,
    running: overrides.running ?? false,
    nodeName: undefined,
    threadId: undefined,
  };
}

/**
 * Mock function for useCoAgent that can be configured per test
 */
export const mockUseCoAgent = vi.fn(() => createMockUseCoAgent());

/**
 * Setup the CopilotKit mock - call this in beforeEach
 */
export function setupCopilotKitMock() {
  vi.mock("@copilotkit/react-core", () => ({
    useCoAgent: mockUseCoAgent,
  }));
}

/**
 * Reset the mock between tests
 */
export function resetCopilotKitMock() {
  mockUseCoAgent.mockClear();
  mockUseCoAgent.mockImplementation(() => createMockUseCoAgent());
}
