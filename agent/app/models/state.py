"""
OracleState - Central state model for Keiba Oracle.

Every field is explicitly exposed - no black boxes.
The reasoning_trace is THE KEY requirement for explicit AI transparency.
"""

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from enum import Enum


class NodeType(str, Enum):
    """Types of nodes in the agent graph."""
    SCOUT = "scout"
    STRATEGIST = "strategist"
    AUDITOR = "auditor"
    IDLE = "idle"


class ReasoningStep(BaseModel):
    """
    Single step in the reasoning trace - explicitly visible to the UI.

    Every thought, action, and observation is captured here for full transparency.
    """
    timestamp: str
    node: NodeType
    thought: str
    action: Optional[str] = None
    observation: Optional[str] = None


class ScoutData(BaseModel):
    """Data gathered by Scout node from search operations."""
    racecourse: str
    track_condition: str
    weather: str
    horse_data: list[dict]
    sources: list[str]


class StrategyDraft(BaseModel):
    """Strategy output from Strategist node."""
    recommended_horse: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    reasoning_summary: str
    kelly_fraction: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class ToolCall(BaseModel):
    """Record of a tool invocation - displayed in ToolPulse component."""
    timestamp: str
    tool: str
    args: dict
    node: str


class OracleState(BaseModel):
    """
    Central state model for Keiba Oracle.

    Every field is explicitly exposed - no black boxes.
    This state is synchronized with the frontend via CopilotKit.
    """
    # Current execution state
    active_node: NodeType = NodeType.IDLE

    # Explicit reasoning trace (THE KEY REQUIREMENT)
    # Every node must append to this list - no hidden logic
    reasoning_trace: list[ReasoningStep] = Field(default_factory=list)

    # Data from Scout node
    scout_data: Optional[ScoutData] = None

    # Output from Strategist
    strategy_draft: Optional[StrategyDraft] = None

    # Risk assessment from Auditor
    risk_score: float = Field(default=0.0, ge=0.0, le=1.0)

    # Control flow flags
    requires_backtrack: bool = False
    backtrack_reason: Optional[str] = None
    backtrack_count: int = Field(default=0, ge=0, le=3)  # Max 3 backtracks

    # User query
    query: str = ""

    # Tool invocations log (for ToolPulse component)
    tool_calls: list[ToolCall] = Field(default_factory=list)

    # Final output
    final_recommendation: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True)
