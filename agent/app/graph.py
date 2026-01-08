"""
LangGraph Definition for Keiba Oracle.

Defines the agent workflow: Scout -> Strategist -> Auditor
with conditional backtrack from Auditor to Strategist.
"""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.models import OracleState, NodeType
from app.nodes import scout_node, strategist_node, auditor_node


def should_continue(state: OracleState) -> str:
    """
    Conditional edge: determine next step based on state.

    Routes based on:
    - active_node: which node should be next
    - requires_backtrack: if Auditor requested revision
    """
    # If backtrack is required, go back to strategist
    if state.requires_backtrack and state.backtrack_count < 3:
        return "strategist"

    # If we're done (active_node is IDLE), end the graph
    if state.active_node == NodeType.IDLE:
        return END

    # Otherwise, continue to the next node
    return END


def build_graph() -> StateGraph:
    """
    Build the Keiba Oracle agent graph.

    Flow:
    START -> Scout -> Strategist -> Auditor -> END
                         ^            |
                         |            | (backtrack if risk > 0.7)
                         +------------+
    """
    # Create the graph with OracleState
    builder = StateGraph(OracleState)

    # Add nodes
    builder.add_node("scout", scout_node)
    builder.add_node("strategist", strategist_node)
    builder.add_node("auditor", auditor_node)

    # Define edges
    # START -> Scout
    builder.add_edge(START, "scout")

    # Scout -> Strategist
    builder.add_edge("scout", "strategist")

    # Strategist -> Auditor
    builder.add_edge("strategist", "auditor")

    # Auditor -> conditional (END or backtrack to Strategist)
    # Note: The auditor_node itself returns a Command for backtrack
    # This edge handles the normal flow to END
    builder.add_conditional_edges(
        "auditor",
        should_continue,
        {
            "strategist": "strategist",
            END: END,
        }
    )

    return builder


def create_graph(checkpointer=None):
    """
    Create and compile the graph with optional checkpointer.

    Args:
        checkpointer: LangGraph checkpointer for state persistence.
                     If None, uses in-memory checkpointer.

    Returns:
        Compiled LangGraph ready for execution.
    """
    builder = build_graph()

    # Use provided checkpointer or create in-memory one
    if checkpointer is None:
        checkpointer = MemorySaver()

    # Compile with checkpointer for state persistence
    graph = builder.compile(checkpointer=checkpointer)

    return graph


# Default graph instance for import
graph = create_graph()


# Export for use by main.py
__all__ = ["graph", "create_graph", "build_graph"]
