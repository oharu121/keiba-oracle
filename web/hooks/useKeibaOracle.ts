"use client";

/**
 * Custom hook for Keiba Oracle agent state.
 *
 * Wraps CopilotKit's useCoAgent with node change detection
 * for triggering pulse animations in the UI.
 */

import { useCoAgent } from "@copilotkit/react-core";
import { useEffect, useRef, useCallback, useState } from "react";
import type { OracleState, NodeType } from "@/lib/types";

// Default initial state
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

export function useKeibaOracle() {
  // Connect to the CopilotKit agent
  const { state, setState, run, running } = useCoAgent<OracleState>({
    name: "keiba-oracle",
    initialState: DEFAULT_STATE,
  });

  // Track previous node for change detection
  const previousNode = useRef<NodeType | null>(null);

  // Callbacks for node change events (used by NodeGraph for pulse animation)
  const onNodeChangeCallbacks = useRef<Set<(node: NodeType) => void>>(
    new Set()
  );

  // Local state for pulse animation
  const [pulsingNode, setPulsingNode] = useState<NodeType | null>(null);

  // Detect node changes and trigger callbacks
  useEffect(() => {
    const currentNode = state?.active_node || "idle";

    if (currentNode !== previousNode.current) {
      previousNode.current = currentNode;

      // Trigger pulse animation
      setPulsingNode(currentNode);
      const timeout = setTimeout(() => setPulsingNode(null), 1000);

      // Notify all registered callbacks
      onNodeChangeCallbacks.current.forEach((callback) => {
        callback(currentNode);
      });

      return () => clearTimeout(timeout);
    }
  }, [state?.active_node]);

  // Register a callback for node changes
  const onNodeChange = useCallback((callback: (node: NodeType) => void) => {
    onNodeChangeCallbacks.current.add(callback);

    // Return unsubscribe function
    return () => {
      onNodeChangeCallbacks.current.delete(callback);
    };
  }, []);

  // Send a query to the agent
  const sendQuery = useCallback(
    async (query: string) => {
      if (!query.trim()) return;

      // Update state with query and reset for new run
      setState({
        ...DEFAULT_STATE,
        query: query.trim(),
      });

      // Run the agent
      await run();
    },
    [setState, run]
  );

  // Reset the agent state
  const reset = useCallback(() => {
    setState(DEFAULT_STATE);
    previousNode.current = null;
    setPulsingNode(null);
  }, [setState]);

  return {
    // State
    state: state || DEFAULT_STATE,
    isLoading: running,

    // Derived state
    isActive: (state?.active_node || "idle") !== "idle",
    currentNode: state?.active_node || "idle",
    pulsingNode,

    // Reasoning data
    reasoningTrace: state?.reasoning_trace || [],
    toolCalls: state?.tool_calls || [],

    // Results
    scoutData: state?.scout_data || null,
    strategyDraft: state?.strategy_draft || null,
    riskScore: state?.risk_score || 0,
    finalRecommendation: state?.final_recommendation || null,

    // Backtrack info
    requiresBacktrack: state?.requires_backtrack || false,
    backtrackReason: state?.backtrack_reason || null,
    backtrackCount: state?.backtrack_count || 0,

    // Actions
    sendQuery,
    reset,
    onNodeChange,
  };
}

export type UseKeibaOracleReturn = ReturnType<typeof useKeibaOracle>;
