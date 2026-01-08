"use client";

/**
 * ToolPulse Component - Capability log showing tool invocations.
 *
 * Displays tool_calls from OracleState with green pulse animation
 * on new invocations. Shows tool name, arguments, and timestamp.
 */

import { motion, AnimatePresence } from "framer-motion";
import { useKeibaOracle } from "@/hooks/useKeibaOracle";
import { NODE_LABELS } from "@/lib/types";

export function ToolPulse() {
  const { toolCalls } = useKeibaOracle();

  return (
    <div className="h-full flex flex-col bg-zinc-900 rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-white">Capability Log</h2>
        <span className="text-sm text-zinc-400 bg-zinc-800 px-2 py-1 rounded">
          {toolCalls.length} calls
        </span>
      </div>

      <div className="flex-1 overflow-y-auto space-y-2 pr-2">
        <AnimatePresence initial={false}>
          {toolCalls.length === 0 ? (
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
                  d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                />
              </svg>
              <p className="text-sm">No tools invoked yet</p>
              <p className="text-xs mt-1">Tools appear here when agents use them</p>
            </div>
          ) : (
            toolCalls.map((call, index) => (
              <motion.div
                key={`${call.timestamp}-${index}`}
                initial={{ opacity: 0, scale: 0.9, x: -20 }}
                animate={{ opacity: 1, scale: 1, x: 0 }}
                exit={{ opacity: 0, scale: 0.9 }}
                transition={{ duration: 0.2 }}
                className="relative"
              >
                {/* Pulse ring animation on mount */}
                <motion.div
                  className="absolute inset-0 bg-green-500 rounded-lg"
                  initial={{ opacity: 0.5 }}
                  animate={{ opacity: 0 }}
                  transition={{ duration: 0.5 }}
                />

                <div className="bg-zinc-800 rounded-lg p-3 border border-green-500/30">
                  {/* Tool header */}
                  <div className="flex items-center gap-2 mb-2">
                    <span className="relative flex h-2 w-2">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                    </span>
                    <span className="text-green-400 font-mono text-sm font-medium">
                      {call.tool}
                    </span>
                  </div>

                  {/* Arguments */}
                  <pre className="text-zinc-400 text-xs overflow-x-auto bg-zinc-900 rounded p-2 mb-2">
                    {formatArgs(call.args)}
                  </pre>

                  {/* Footer with node and timestamp */}
                  <div className="flex justify-between items-center text-xs text-zinc-500">
                    <span className="flex items-center gap-1">
                      <svg
                        className="w-3 h-3"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                        />
                      </svg>
                      {NODE_LABELS[call.node as keyof typeof NODE_LABELS] ||
                        call.node}
                    </span>
                    <span>{formatTimestamp(call.timestamp)}</span>
                  </div>
                </div>
              </motion.div>
            ))
          )}
        </AnimatePresence>
      </div>

      {/* Legend */}
      <div className="mt-4 pt-4 border-t border-zinc-800">
        <p className="text-xs text-zinc-500 mb-2">Available Tools:</p>
        <div className="flex flex-wrap gap-2">
          <span className="text-xs bg-zinc-800 text-zinc-400 px-2 py-1 rounded">
            search_racecourse_conditions
          </span>
          <span className="text-xs bg-zinc-800 text-zinc-400 px-2 py-1 rounded">
            search_horse_info
          </span>
        </div>
      </div>
    </div>
  );
}

/**
 * Format arguments object for display.
 */
function formatArgs(args: Record<string, unknown>): string {
  try {
    return JSON.stringify(args, null, 2);
  } catch {
    return String(args);
  }
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
