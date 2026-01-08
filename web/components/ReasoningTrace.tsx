"use client";

/**
 * ReasoningTrace Component - Real-time display of AI reasoning.
 *
 * Shows the reasoning_trace from OracleState as a scrolling list
 * with color-coded badges by node type and auto-scroll to latest.
 */

import { motion, AnimatePresence } from "framer-motion";
import { useEffect, useRef } from "react";
import { useKeibaOracle } from "@/hooks/useKeibaOracle";
import { NODE_COLORS, NODE_LABELS } from "@/lib/types";

export function ReasoningTrace() {
  const { reasoningTrace } = useKeibaOracle();
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to latest entry
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [reasoningTrace.length]);

  return (
    <div className="h-full flex flex-col bg-zinc-900 rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-white">Reasoning Trace</h2>
        <span className="text-sm text-zinc-400 bg-zinc-800 px-2 py-1 rounded">
          {reasoningTrace.length} steps
        </span>
      </div>

      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto space-y-3 pr-2 scrollbar-thin scrollbar-thumb-zinc-700 scrollbar-track-zinc-800"
      >
        <AnimatePresence initial={false}>
          {reasoningTrace.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-zinc-500">
              <svg
                className="w-12 h-12 mb-2 opacity-50"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                />
              </svg>
              <p className="text-sm">No reasoning steps yet</p>
              <p className="text-xs mt-1">Submit a query to see AI thinking</p>
            </div>
          ) : (
            reasoningTrace.map((step, index) => (
              <motion.div
                key={`${step.timestamp}-${index}`}
                initial={{ opacity: 0, y: 20, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.3 }}
                className="bg-zinc-800 rounded-lg p-3 border-l-4"
                style={{
                  borderLeftColor: NODE_COLORS[step.node] || NODE_COLORS.idle,
                }}
              >
                {/* Header with badge and timestamp */}
                <div className="flex items-center gap-2 mb-2">
                  <span
                    className="text-white text-xs px-2 py-0.5 rounded-full font-medium"
                    style={{
                      backgroundColor:
                        NODE_COLORS[step.node] || NODE_COLORS.idle,
                    }}
                  >
                    {NODE_LABELS[step.node] || step.node}
                  </span>
                  <span className="text-zinc-500 text-xs">
                    {formatTimestamp(step.timestamp)}
                  </span>
                  <span className="text-zinc-600 text-xs">#{index + 1}</span>
                </div>

                {/* Thought */}
                <p className="text-white text-sm leading-relaxed">
                  {step.thought}
                </p>

                {/* Action (if present) */}
                {step.action && (
                  <div className="mt-2 flex items-start gap-2">
                    <span className="text-blue-400 text-xs font-medium">
                      ACTION:
                    </span>
                    <p className="text-blue-300 text-xs">{step.action}</p>
                  </div>
                )}

                {/* Observation (if present) */}
                {step.observation && (
                  <div className="mt-2 flex items-start gap-2">
                    <span className="text-green-400 text-xs font-medium">
                      OBS:
                    </span>
                    <p className="text-green-300 text-xs line-clamp-3">
                      {step.observation}
                    </p>
                  </div>
                )}
              </motion.div>
            ))
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

/**
 * Format ISO timestamp to readable time.
 */
function formatTimestamp(isoString: string): string {
  try {
    const date = new Date(isoString);
    return date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return isoString;
  }
}
