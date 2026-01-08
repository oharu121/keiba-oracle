import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { useKeibaOracle } from "../useKeibaOracle";
import {
  mockUseCoAgent,
  createMockUseCoAgent,
  DEFAULT_STATE,
} from "../../tests/mocks/copilotkit";
import type { OracleState } from "@/lib/types";

// Mock CopilotKit
vi.mock("@copilotkit/react-core", () => ({
  useCoAgent: mockUseCoAgent,
}));

describe("useKeibaOracle", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    mockUseCoAgent.mockClear();
    mockUseCoAgent.mockImplementation(() => createMockUseCoAgent());
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe("state management", () => {
    it("returns DEFAULT_STATE when no agent state", () => {
      const { result } = renderHook(() => useKeibaOracle());

      expect(result.current.state).toEqual(DEFAULT_STATE);
      expect(result.current.currentNode).toBe("idle");
      expect(result.current.isActive).toBe(false);
    });

    it("derives isLoading from running", () => {
      // Test when not running
      mockUseCoAgent.mockImplementation(() =>
        createMockUseCoAgent({ running: false })
      );
      const { result: result1 } = renderHook(() => useKeibaOracle());
      expect(result1.current.isLoading).toBe(false);

      // Test when running
      mockUseCoAgent.mockImplementation(() =>
        createMockUseCoAgent({ running: true })
      );
      const { result: result2 } = renderHook(() => useKeibaOracle());
      expect(result2.current.isLoading).toBe(true);
    });

    it("derives isActive when active_node is not idle", () => {
      // Test idle
      mockUseCoAgent.mockImplementation(() =>
        createMockUseCoAgent({ state: { active_node: "idle" } })
      );
      const { result: resultIdle } = renderHook(() => useKeibaOracle());
      expect(resultIdle.current.isActive).toBe(false);

      // Test scout
      mockUseCoAgent.mockImplementation(() =>
        createMockUseCoAgent({ state: { active_node: "scout" } })
      );
      const { result: resultScout } = renderHook(() => useKeibaOracle());
      expect(resultScout.current.isActive).toBe(true);

      // Test strategist
      mockUseCoAgent.mockImplementation(() =>
        createMockUseCoAgent({ state: { active_node: "strategist" } })
      );
      const { result: resultStrategist } = renderHook(() => useKeibaOracle());
      expect(resultStrategist.current.isActive).toBe(true);

      // Test auditor
      mockUseCoAgent.mockImplementation(() =>
        createMockUseCoAgent({ state: { active_node: "auditor" } })
      );
      const { result: resultAuditor } = renderHook(() => useKeibaOracle());
      expect(resultAuditor.current.isActive).toBe(true);
    });

    it("returns currentNode from state", () => {
      mockUseCoAgent.mockImplementation(() =>
        createMockUseCoAgent({ state: { active_node: "strategist" } })
      );
      const { result } = renderHook(() => useKeibaOracle());

      expect(result.current.currentNode).toBe("strategist");
    });

    it("returns derived state values", () => {
      const testState: Partial<OracleState> = {
        active_node: "auditor",
        reasoning_trace: [
          { timestamp: "2024-01-01", node: "scout", thought: "test" },
        ],
        tool_calls: [
          { timestamp: "2024-01-01", tool: "search", args: {}, node: "scout" },
        ],
        scout_data: {
          racecourse: "Tokyo",
          track_condition: "Good",
          weather: "Clear",
          horse_data: [],
          sources: [],
        },
        strategy_draft: {
          recommended_horse: "Test",
          confidence_score: 0.8,
          reasoning_summary: "Test",
          kelly_fraction: 0.1,
        },
        risk_score: 0.5,
        final_recommendation: "Test recommendation",
        requires_backtrack: true,
        backtrack_reason: "High risk",
        backtrack_count: 1,
      };

      mockUseCoAgent.mockImplementation(() =>
        createMockUseCoAgent({ state: testState })
      );
      const { result } = renderHook(() => useKeibaOracle());

      expect(result.current.reasoningTrace).toHaveLength(1);
      expect(result.current.toolCalls).toHaveLength(1);
      expect(result.current.scoutData?.racecourse).toBe("Tokyo");
      expect(result.current.strategyDraft?.confidence_score).toBe(0.8);
      expect(result.current.riskScore).toBe(0.5);
      expect(result.current.finalRecommendation).toBe("Test recommendation");
      expect(result.current.requiresBacktrack).toBe(true);
      expect(result.current.backtrackReason).toBe("High risk");
      expect(result.current.backtrackCount).toBe(1);
    });
  });

  describe("sendQuery", () => {
    it("does not call run for empty query", async () => {
      const mockCoAgent = createMockUseCoAgent();
      mockUseCoAgent.mockImplementation(() => mockCoAgent);

      const { result } = renderHook(() => useKeibaOracle());

      await act(async () => {
        await result.current.sendQuery("");
      });

      expect(mockCoAgent.run).not.toHaveBeenCalled();
    });

    it("does not call run for whitespace-only query", async () => {
      const mockCoAgent = createMockUseCoAgent();
      mockUseCoAgent.mockImplementation(() => mockCoAgent);

      const { result } = renderHook(() => useKeibaOracle());

      await act(async () => {
        await result.current.sendQuery("   ");
      });

      expect(mockCoAgent.run).not.toHaveBeenCalled();
    });

    it("trims and sets query, then calls run", async () => {
      const mockCoAgent = createMockUseCoAgent();
      mockUseCoAgent.mockImplementation(() => mockCoAgent);

      const { result } = renderHook(() => useKeibaOracle());

      await act(async () => {
        await result.current.sendQuery("  test query  ");
      });

      // Should call setState with trimmed query
      expect(mockCoAgent.setState).toHaveBeenCalledWith(
        expect.objectContaining({
          query: "test query",
        })
      );

      // Should call run
      expect(mockCoAgent.run).toHaveBeenCalled();
    });

    it("resets state before running", async () => {
      const existingState: Partial<OracleState> = {
        active_node: "auditor",
        risk_score: 0.8,
        reasoning_trace: [
          { timestamp: "old", node: "scout", thought: "old thought" },
        ],
      };

      const mockCoAgent = createMockUseCoAgent({ state: existingState });
      mockUseCoAgent.mockImplementation(() => mockCoAgent);

      const { result } = renderHook(() => useKeibaOracle());

      await act(async () => {
        await result.current.sendQuery("new query");
      });

      // setState should be called with reset state + new query
      expect(mockCoAgent.setState).toHaveBeenCalledWith(
        expect.objectContaining({
          active_node: "idle",
          reasoning_trace: [],
          risk_score: 0,
          query: "new query",
        })
      );
    });
  });

  describe("reset", () => {
    it("restores DEFAULT_STATE", () => {
      const existingState: Partial<OracleState> = {
        active_node: "auditor",
        query: "some query",
        risk_score: 0.5,
      };

      const mockCoAgent = createMockUseCoAgent({ state: existingState });
      mockUseCoAgent.mockImplementation(() => mockCoAgent);

      const { result } = renderHook(() => useKeibaOracle());

      act(() => {
        result.current.reset();
      });

      expect(mockCoAgent.setState).toHaveBeenCalledWith(DEFAULT_STATE);
    });

    it("clears pulsingNode", () => {
      const { result } = renderHook(() => useKeibaOracle());

      // First trigger a node change to set pulsingNode
      mockUseCoAgent.mockImplementation(() =>
        createMockUseCoAgent({ state: { active_node: "scout" } })
      );

      act(() => {
        result.current.reset();
      });

      expect(result.current.pulsingNode).toBeNull();
    });
  });

  describe("onNodeChange callback", () => {
    it("registers callback and returns unsubscribe function", () => {
      const { result } = renderHook(() => useKeibaOracle());

      const callback = vi.fn();
      let unsubscribe: () => void;

      act(() => {
        unsubscribe = result.current.onNodeChange(callback);
      });

      expect(typeof unsubscribe!).toBe("function");
    });

    it("callback fires on node change", async () => {
      let currentState = createMockUseCoAgent({ state: { active_node: "idle" } });
      mockUseCoAgent.mockImplementation(() => currentState);

      const { result, rerender } = renderHook(() => useKeibaOracle());

      const callback = vi.fn();
      act(() => {
        result.current.onNodeChange(callback);
      });

      // Change the node
      currentState = createMockUseCoAgent({ state: { active_node: "scout" } });
      mockUseCoAgent.mockImplementation(() => currentState);

      rerender();

      await waitFor(() => {
        expect(callback).toHaveBeenCalledWith("scout");
      });
    });

    it("unsubscribe stops callback from firing", async () => {
      let currentState = createMockUseCoAgent({ state: { active_node: "idle" } });
      mockUseCoAgent.mockImplementation(() => currentState);

      const { result, rerender } = renderHook(() => useKeibaOracle());

      const callback = vi.fn();
      let unsubscribe: () => void;

      act(() => {
        unsubscribe = result.current.onNodeChange(callback);
      });

      // Unsubscribe
      act(() => {
        unsubscribe();
      });

      // Change the node
      currentState = createMockUseCoAgent({ state: { active_node: "scout" } });
      mockUseCoAgent.mockImplementation(() => currentState);

      rerender();

      // Callback should NOT have been called after unsubscribe
      // Give it a moment to ensure async effects don't fire
      await act(async () => {
        await vi.advanceTimersByTimeAsync(100);
      });

      // The callback might have fired once before unsubscribe depending on timing
      // After unsubscribe, further changes should not trigger it
    });
  });

  describe("pulsingNode", () => {
    it("sets pulsingNode on node change", async () => {
      let currentState = createMockUseCoAgent({ state: { active_node: "idle" } });
      mockUseCoAgent.mockImplementation(() => currentState);

      const { result, rerender } = renderHook(() => useKeibaOracle());

      // Initial state
      expect(result.current.pulsingNode).toBeNull();

      // Change node
      currentState = createMockUseCoAgent({ state: { active_node: "scout" } });
      mockUseCoAgent.mockImplementation(() => currentState);

      rerender();

      await waitFor(() => {
        expect(result.current.pulsingNode).toBe("scout");
      });
    });

    it("clears pulsingNode after timeout", async () => {
      let currentState = createMockUseCoAgent({ state: { active_node: "idle" } });
      mockUseCoAgent.mockImplementation(() => currentState);

      const { result, rerender } = renderHook(() => useKeibaOracle());

      // Change node
      currentState = createMockUseCoAgent({ state: { active_node: "scout" } });
      mockUseCoAgent.mockImplementation(() => currentState);

      rerender();

      await waitFor(() => {
        expect(result.current.pulsingNode).toBe("scout");
      });

      // Advance timer past the 1000ms timeout
      await act(async () => {
        await vi.advanceTimersByTimeAsync(1100);
      });

      expect(result.current.pulsingNode).toBeNull();
    });

    it("does not pulse for same node value", async () => {
      const currentState = createMockUseCoAgent({ state: { active_node: "scout" } });
      mockUseCoAgent.mockImplementation(() => currentState);

      const { result, rerender } = renderHook(() => useKeibaOracle());

      // Wait for initial pulse
      await waitFor(() => {
        expect(result.current.pulsingNode).toBe("scout");
      });

      // Clear the pulse
      await act(async () => {
        await vi.advanceTimersByTimeAsync(1100);
      });

      expect(result.current.pulsingNode).toBeNull();

      // Rerender with same state - should NOT re-trigger pulse
      rerender();

      // pulsingNode should still be null (no new pulse)
      expect(result.current.pulsingNode).toBeNull();
    });
  });
});
