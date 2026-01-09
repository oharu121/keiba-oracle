import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import type { OracleState } from "@/lib/types";

// Default state matching the hook's DEFAULT_STATE
const DEFAULT_STATE: OracleState = {
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

// Create mock functions at module level
const mockSetState = vi.fn();
const mockRun = vi.fn().mockResolvedValue(undefined);
const mockStart = vi.fn();
const mockStop = vi.fn();

// Track mock state that can be changed per test
let mockState: OracleState = { ...DEFAULT_STATE };
let mockRunning = false;

// Mock CopilotKit - must be before any imports that use it
vi.mock("@copilotkit/react-core", () => ({
  useCoAgent: vi.fn(() => ({
    name: "keiba-oracle",
    state: mockState,
    setState: mockSetState,
    run: mockRun,
    start: mockStart,
    stop: mockStop,
    running: mockRunning,
    nodeName: undefined,
    threadId: undefined,
  })),
}));

// Import the hook after mocking
import { useKeibaOracle } from "../useKeibaOracle";

describe("useKeibaOracle", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    // Reset mock state
    mockState = { ...DEFAULT_STATE };
    mockRunning = false;
    // Clear mock call history
    mockSetState.mockClear();
    mockRun.mockClear();
    mockStart.mockClear();
    mockStop.mockClear();
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
      mockRunning = false;
      const { result: result1 } = renderHook(() => useKeibaOracle());
      expect(result1.current.isLoading).toBe(false);
    });

    it("derives isLoading as true when running", () => {
      mockRunning = true;
      const { result } = renderHook(() => useKeibaOracle());
      expect(result.current.isLoading).toBe(true);
    });

    it("derives isActive when active_node is not idle", () => {
      // Test idle
      mockState = { ...DEFAULT_STATE, active_node: "idle" };
      const { result: resultIdle } = renderHook(() => useKeibaOracle());
      expect(resultIdle.current.isActive).toBe(false);
    });

    it("derives isActive as true for scout node", () => {
      mockState = { ...DEFAULT_STATE, active_node: "scout" };
      const { result } = renderHook(() => useKeibaOracle());
      expect(result.current.isActive).toBe(true);
    });

    it("derives isActive as true for strategist node", () => {
      mockState = { ...DEFAULT_STATE, active_node: "strategist" };
      const { result } = renderHook(() => useKeibaOracle());
      expect(result.current.isActive).toBe(true);
    });

    it("derives isActive as true for auditor node", () => {
      mockState = { ...DEFAULT_STATE, active_node: "auditor" };
      const { result } = renderHook(() => useKeibaOracle());
      expect(result.current.isActive).toBe(true);
    });

    it("returns currentNode from state", () => {
      mockState = { ...DEFAULT_STATE, active_node: "strategist" };
      const { result } = renderHook(() => useKeibaOracle());
      expect(result.current.currentNode).toBe("strategist");
    });

    it("returns derived state values", () => {
      mockState = {
        ...DEFAULT_STATE,
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
      const { result } = renderHook(() => useKeibaOracle());

      await act(async () => {
        await result.current.sendQuery("");
      });

      expect(mockRun).not.toHaveBeenCalled();
    });

    it("does not call run for whitespace-only query", async () => {
      const { result } = renderHook(() => useKeibaOracle());

      await act(async () => {
        await result.current.sendQuery("   ");
      });

      expect(mockRun).not.toHaveBeenCalled();
    });

    it("trims and sets query, then calls run", async () => {
      const { result } = renderHook(() => useKeibaOracle());

      await act(async () => {
        await result.current.sendQuery("  test query  ");
      });

      // Should call setState with trimmed query
      expect(mockSetState).toHaveBeenCalledWith(
        expect.objectContaining({
          query: "test query",
        })
      );

      // Should call run
      expect(mockRun).toHaveBeenCalled();
    });

    it("resets state before running", async () => {
      mockState = {
        ...DEFAULT_STATE,
        active_node: "auditor",
        risk_score: 0.8,
        reasoning_trace: [
          { timestamp: "old", node: "scout", thought: "old thought" },
        ],
      };

      const { result } = renderHook(() => useKeibaOracle());

      await act(async () => {
        await result.current.sendQuery("new query");
      });

      // setState should be called with reset state + new query
      expect(mockSetState).toHaveBeenCalledWith(
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
      mockState = {
        ...DEFAULT_STATE,
        active_node: "auditor",
        query: "some query",
        risk_score: 0.5,
      };

      const { result } = renderHook(() => useKeibaOracle());

      act(() => {
        result.current.reset();
      });

      expect(mockSetState).toHaveBeenCalledWith(DEFAULT_STATE);
    });

    it("clears pulsingNode", () => {
      const { result } = renderHook(() => useKeibaOracle());

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
  });

  describe("pulsingNode", () => {
    it("is set to current node on initial render", () => {
      const { result } = renderHook(() => useKeibaOracle());
      // On initial render, pulsingNode is set to the active_node
      expect(result.current.pulsingNode).toBe("idle");
    });

    it("clears after timeout", async () => {
      const { result } = renderHook(() => useKeibaOracle());

      // Initially set to idle
      expect(result.current.pulsingNode).toBe("idle");

      // Advance timer past 1000ms timeout
      await act(async () => {
        await vi.advanceTimersByTimeAsync(1100);
      });

      expect(result.current.pulsingNode).toBeNull();
    });
  });
});
