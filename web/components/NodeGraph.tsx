"use client";

/**
 * NodeGraph Component - SVG visualization of the agent graph.
 *
 * Displays Scout -> Strategist -> Auditor flow with:
 * - Glow effect on active node
 * - Pulse animation on node transitions
 * - Curved backtrack edge that turns red when active
 */

import { motion, AnimatePresence } from "framer-motion";
import { useEffect, useState } from "react";
import { useKeibaOracle } from "@/hooks/useKeibaOracle";
import { NODE_COLORS, type NodeType } from "@/lib/types";

// Node positions in the SVG viewBox
const NODE_POSITIONS = {
  scout: { x: 100, y: 120 },
  strategist: { x: 300, y: 120 },
  auditor: { x: 500, y: 120 },
} as const;

export function NodeGraph() {
  const { currentNode, pulsingNode, requiresBacktrack, onNodeChange } =
    useKeibaOracle();

  const [localPulse, setLocalPulse] = useState<NodeType | null>(null);

  // Subscribe to node changes for pulse animation
  useEffect(() => {
    const unsubscribe = onNodeChange((node) => {
      setLocalPulse(node);
      const timeout = setTimeout(() => setLocalPulse(null), 1000);
      return () => clearTimeout(timeout);
    });
    return unsubscribe;
  }, [onNodeChange]);

  const activePulse = localPulse || pulsingNode;

  return (
    <div className="h-full flex flex-col bg-zinc-900 rounded-lg p-4">
      <h2 className="text-lg font-semibold text-white mb-2">Agent Graph</h2>
      <p className="text-xs text-zinc-500 mb-4">
        Scout → Strategist → Auditor
      </p>

      <svg viewBox="0 0 600 240" className="w-full flex-1">
        {/* Background grid (subtle) */}
        <defs>
          <pattern
            id="grid"
            width="20"
            height="20"
            patternUnits="userSpaceOnUse"
          >
            <path
              d="M 20 0 L 0 0 0 20"
              fill="none"
              stroke="#27272a"
              strokeWidth="0.5"
            />
          </pattern>
        </defs>
        <rect width="600" height="240" fill="url(#grid)" />

        {/* Edges */}
        {/* Scout -> Strategist */}
        <line
          x1={NODE_POSITIONS.scout.x + 35}
          y1={NODE_POSITIONS.scout.y}
          x2={NODE_POSITIONS.strategist.x - 35}
          y2={NODE_POSITIONS.strategist.y}
          stroke="#4b5563"
          strokeWidth="2"
          markerEnd="url(#arrowhead)"
        />

        {/* Strategist -> Auditor */}
        <line
          x1={NODE_POSITIONS.strategist.x + 35}
          y1={NODE_POSITIONS.strategist.y}
          x2={NODE_POSITIONS.auditor.x - 35}
          y2={NODE_POSITIONS.auditor.y}
          stroke="#4b5563"
          strokeWidth="2"
          markerEnd="url(#arrowhead)"
        />

        {/* Backtrack edge (curved) - Auditor back to Strategist */}
        <path
          d={`M ${NODE_POSITIONS.auditor.x} ${NODE_POSITIONS.auditor.y + 40}
              Q ${NODE_POSITIONS.strategist.x + 100} ${NODE_POSITIONS.auditor.y + 90}
              ${NODE_POSITIONS.strategist.x} ${NODE_POSITIONS.strategist.y + 40}`}
          fill="none"
          stroke={requiresBacktrack ? "#ef4444" : "#4b5563"}
          strokeWidth={requiresBacktrack ? "3" : "2"}
          strokeDasharray={requiresBacktrack ? "none" : "5,5"}
          opacity={requiresBacktrack ? 1 : 0.5}
        />

        {/* Backtrack label */}
        <text
          x={NODE_POSITIONS.strategist.x + 100}
          y={NODE_POSITIONS.auditor.y + 95}
          textAnchor="middle"
          fill={requiresBacktrack ? "#ef4444" : "#6b7280"}
          className="text-xs"
          fontSize="10"
        >
          backtrack
        </text>

        {/* Arrow marker definition */}
        <defs>
          <marker
            id="arrowhead"
            markerWidth="10"
            markerHeight="7"
            refX="9"
            refY="3.5"
            orient="auto"
          >
            <polygon points="0 0, 10 3.5, 0 7" fill="#4b5563" />
          </marker>
        </defs>

        {/* Nodes */}
        {(["scout", "strategist", "auditor"] as const).map((node) => {
          const pos = NODE_POSITIONS[node];
          const isActive = currentNode === node;
          const isPulsing = activePulse === node;

          return (
            <g key={node}>
              {/* Glow effect when active or pulsing */}
              <AnimatePresence>
                {(isActive || isPulsing) && (
                  <motion.circle
                    cx={pos.x}
                    cy={pos.y}
                    r={50}
                    fill={NODE_COLORS[node]}
                    initial={{ opacity: 0.5, scale: 1 }}
                    animate={{
                      opacity: [0.5, 0.2, 0.5],
                      scale: [1, 1.3, 1],
                    }}
                    exit={{ opacity: 0, scale: 1 }}
                    transition={{
                      duration: isPulsing ? 0.5 : 1,
                      repeat: isPulsing ? 0 : Infinity,
                    }}
                    style={{ filter: "blur(15px)" }}
                  />
                )}
              </AnimatePresence>

              {/* Main node circle */}
              <motion.circle
                cx={pos.x}
                cy={pos.y}
                r={35}
                fill={isActive ? NODE_COLORS[node] : "#1f2937"}
                stroke={NODE_COLORS[node]}
                strokeWidth={isActive ? "4" : "2"}
                animate={{
                  scale: isActive ? 1.1 : 1,
                }}
                transition={{ duration: 0.2 }}
              />

              {/* Node icon/indicator */}
              <circle
                cx={pos.x}
                cy={pos.y - 10}
                r={5}
                fill={isActive ? "white" : NODE_COLORS[node]}
              />

              {/* Node label */}
              <text
                x={pos.x}
                y={pos.y + 8}
                textAnchor="middle"
                fill="white"
                className="text-sm font-medium"
                fontSize="12"
              >
                {node.charAt(0).toUpperCase() + node.slice(1)}
              </text>

              {/* Status indicator below node */}
              <text
                x={pos.x}
                y={pos.y + 60}
                textAnchor="middle"
                fill={isActive ? NODE_COLORS[node] : "#6b7280"}
                className="text-xs"
                fontSize="10"
              >
                {isActive ? "ACTIVE" : "waiting"}
              </text>
            </g>
          );
        })}

        {/* START indicator */}
        <g>
          <circle cx={30} cy={NODE_POSITIONS.scout.y} r={12} fill="#22c55e" />
          <text
            x={30}
            y={NODE_POSITIONS.scout.y + 4}
            textAnchor="middle"
            fill="white"
            fontSize="10"
            fontWeight="bold"
          >
            S
          </text>
          <line
            x1={42}
            y1={NODE_POSITIONS.scout.y}
            x2={65}
            y2={NODE_POSITIONS.scout.y}
            stroke="#22c55e"
            strokeWidth="2"
            markerEnd="url(#arrowhead-green)"
          />
        </g>

        {/* END indicator */}
        <g>
          <circle cx={570} cy={NODE_POSITIONS.auditor.y} r={12} fill="#6b7280" />
          <text
            x={570}
            y={NODE_POSITIONS.auditor.y + 4}
            textAnchor="middle"
            fill="white"
            fontSize="10"
            fontWeight="bold"
          >
            E
          </text>
          <line
            x1={NODE_POSITIONS.auditor.x + 35}
            y1={NODE_POSITIONS.auditor.y}
            x2={558}
            y2={NODE_POSITIONS.auditor.y}
            stroke="#6b7280"
            strokeWidth="2"
          />
        </g>

        <defs>
          <marker
            id="arrowhead-green"
            markerWidth="10"
            markerHeight="7"
            refX="9"
            refY="3.5"
            orient="auto"
          >
            <polygon points="0 0, 10 3.5, 0 7" fill="#22c55e" />
          </marker>
        </defs>
      </svg>
    </div>
  );
}
