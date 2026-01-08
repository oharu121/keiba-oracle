/**
 * TypeScript types matching Python OracleState.
 *
 * These types mirror the Pydantic models in agent/state.py
 * for type-safe state synchronization.
 */

export type NodeType = "scout" | "strategist" | "auditor" | "idle";

export interface ReasoningStep {
  timestamp: string;
  node: NodeType;
  thought: string;
  action?: string;
  observation?: string;
}

export interface ScoutData {
  racecourse: string;
  track_condition: string;
  weather: string;
  horse_data: Record<string, unknown>[];
  sources: string[];
}

export interface StrategyDraft {
  recommended_horse: string;
  confidence_score: number;
  reasoning_summary: string;
  kelly_fraction: number | null;
}

export interface ToolCall {
  timestamp: string;
  tool: string;
  args: Record<string, unknown>;
  node: string;
}

export interface OracleState {
  active_node: NodeType;
  reasoning_trace: ReasoningStep[];
  scout_data: ScoutData | null;
  strategy_draft: StrategyDraft | null;
  risk_score: number;
  requires_backtrack: boolean;
  backtrack_reason: string | null;
  backtrack_count: number;
  query: string;
  tool_calls: ToolCall[];
  final_recommendation: string | null;
}

// Node colors for consistent styling
export const NODE_COLORS: Record<NodeType, string> = {
  scout: "#3b82f6", // blue-500
  strategist: "#8b5cf6", // purple-500
  auditor: "#ef4444", // red-500
  idle: "#6b7280", // gray-500
};

// Node labels for display
export const NODE_LABELS: Record<NodeType, string> = {
  scout: "Scout",
  strategist: "Strategist",
  auditor: "Auditor",
  idle: "Idle",
};
