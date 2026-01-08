"use client";

/**
 * Dashboard Component - Main three-pane layout for Keiba Oracle.
 *
 * Layout:
 * - Header with title and query input
 * - Three-pane grid: NodeGraph | ReasoningTrace | ToolPulse
 * - Strategy output panel at bottom (when available)
 */

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { NodeGraph } from "./NodeGraph";
import { ReasoningTrace } from "./ReasoningTrace";
import { ToolPulse } from "./ToolPulse";
import { useKeibaOracle } from "@/hooks/useKeibaOracle";

export function Dashboard() {
  const {
    state,
    isLoading,
    isActive,
    sendQuery,
    reset,
    strategyDraft,
    riskScore,
    finalRecommendation,
    scoutData,
    backtrackCount,
  } = useKeibaOracle();

  const [queryInput, setQueryInput] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (queryInput.trim() && !isLoading) {
      await sendQuery(queryInput);
      setQueryInput("");
    }
  };

  return (
    <div className="h-screen flex flex-col bg-black p-4 gap-4">
      {/* Header */}
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <span className="text-3xl">🏇</span>
            Keiba Oracle
          </h1>
          <p className="text-zinc-400 text-sm">
            Japanese Horse Racing Analysis with Explicit AI Reasoning
          </p>
        </div>

        {/* Status indicator */}
        <div className="flex items-center gap-4">
          {isActive && (
            <span className="flex items-center gap-2 text-sm text-yellow-400">
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-yellow-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-yellow-500"></span>
              </span>
              Processing...
            </span>
          )}
          <button
            onClick={reset}
            className="text-sm text-zinc-400 hover:text-white px-3 py-1 rounded border border-zinc-700 hover:border-zinc-600 transition-colors"
          >
            Reset
          </button>
        </div>
      </header>

      {/* Query Input */}
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={queryInput}
          onChange={(e) => setQueryInput(e.target.value)}
          placeholder="Enter your racing query... (e.g., 'What are the conditions at Tokyo Racecourse today?')"
          className="flex-1 bg-zinc-800 text-white px-4 py-3 rounded-lg border border-zinc-700 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 placeholder-zinc-500"
          disabled={isLoading}
        />
        <button
          type="submit"
          disabled={isLoading || !queryInput.trim()}
          className="bg-blue-600 hover:bg-blue-700 disabled:bg-zinc-700 disabled:cursor-not-allowed text-white px-6 py-3 rounded-lg font-medium transition-colors flex items-center gap-2"
        >
          {isLoading ? (
            <>
              <svg
                className="animate-spin h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              Analyzing...
            </>
          ) : (
            <>
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
              Analyze
            </>
          )}
        </button>
      </form>

      {/* Three-Pane Layout */}
      <div className="flex-1 grid grid-cols-3 gap-4 min-h-0">
        {/* Pane A: Graph Visualization */}
        <div className="col-span-1 min-h-0">
          <NodeGraph />
        </div>

        {/* Pane B: Reasoning Trace */}
        <div className="col-span-1 min-h-0">
          <ReasoningTrace />
        </div>

        {/* Pane C: Tool Pulse */}
        <div className="col-span-1 min-h-0">
          <ToolPulse />
        </div>
      </div>

      {/* Strategy Output Panel */}
      <AnimatePresence>
        {(strategyDraft || finalRecommendation) && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="bg-zinc-900 rounded-lg p-4 border border-zinc-800"
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">
                Strategy Recommendation
              </h3>
              {backtrackCount > 0 && (
                <span className="text-xs bg-yellow-500/20 text-yellow-400 px-2 py-1 rounded">
                  Revised {backtrackCount}x
                </span>
              )}
            </div>

            {strategyDraft && (
              <div className="grid grid-cols-4 gap-4 mb-4">
                {/* Horse/Strategy */}
                <div className="bg-zinc-800 rounded p-3">
                  <span className="text-zinc-400 text-xs block mb-1">
                    Strategy
                  </span>
                  <p className="text-white font-medium text-sm">
                    {strategyDraft.recommended_horse}
                  </p>
                </div>

                {/* Confidence */}
                <div className="bg-zinc-800 rounded p-3">
                  <span className="text-zinc-400 text-xs block mb-1">
                    Confidence
                  </span>
                  <p className="text-white font-medium">
                    {(strategyDraft.confidence_score * 100).toFixed(1)}%
                  </p>
                  <div className="mt-1 h-1 bg-zinc-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500 rounded-full"
                      style={{
                        width: `${strategyDraft.confidence_score * 100}%`,
                      }}
                    />
                  </div>
                </div>

                {/* Kelly Fraction */}
                <div className="bg-zinc-800 rounded p-3">
                  <span className="text-zinc-400 text-xs block mb-1">
                    Kelly Fraction
                  </span>
                  <p className="text-white font-medium">
                    {strategyDraft.kelly_fraction
                      ? `${(strategyDraft.kelly_fraction * 100).toFixed(1)}%`
                      : "N/A"}
                  </p>
                </div>

                {/* Risk Score */}
                <div className="bg-zinc-800 rounded p-3">
                  <span className="text-zinc-400 text-xs block mb-1">
                    Risk Score
                  </span>
                  <p
                    className={`font-medium ${
                      riskScore > 0.7
                        ? "text-red-500"
                        : riskScore > 0.4
                          ? "text-yellow-500"
                          : "text-green-500"
                    }`}
                  >
                    {(riskScore * 100).toFixed(1)}%
                  </p>
                  <div className="mt-1 h-1 bg-zinc-700 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        riskScore > 0.7
                          ? "bg-red-500"
                          : riskScore > 0.4
                            ? "bg-yellow-500"
                            : "bg-green-500"
                      }`}
                      style={{ width: `${riskScore * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Scout Data Summary */}
            {scoutData && (
              <div className="mb-4 p-3 bg-zinc-800 rounded-lg">
                <span className="text-zinc-400 text-xs block mb-2">
                  Race Conditions
                </span>
                <div className="flex gap-4 text-sm">
                  <span className="text-white">
                    <span className="text-zinc-500">Venue:</span>{" "}
                    {scoutData.racecourse}
                  </span>
                  <span className="text-white">
                    <span className="text-zinc-500">Track:</span>{" "}
                    {scoutData.track_condition}
                  </span>
                  <span className="text-white">
                    <span className="text-zinc-500">Weather:</span>{" "}
                    {scoutData.weather}
                  </span>
                </div>
              </div>
            )}

            {/* Final Recommendation */}
            {finalRecommendation && (
              <div className="prose prose-invert prose-sm max-w-none">
                <pre className="whitespace-pre-wrap text-sm text-zinc-300 bg-zinc-800 rounded p-4 overflow-auto">
                  {finalRecommendation}
                </pre>
              </div>
            )}

            {/* Disclaimer */}
            <p className="text-xs text-zinc-500 mt-4 text-center">
              This recommendation is for educational purposes only. Always
              gamble responsibly.
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
