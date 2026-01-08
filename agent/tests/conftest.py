"""
Shared test fixtures for Keiba Oracle Agent tests.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from app.models import (
    OracleState,
    NodeType,
    ReasoningStep,
    ScoutData,
    StrategyDraft,
    ToolCall,
)


# =============================================================================
# State Fixtures
# =============================================================================


@pytest.fixture
def default_state() -> OracleState:
    """Fresh OracleState with defaults."""
    return OracleState()


@pytest.fixture
def state_with_query() -> OracleState:
    """OracleState with a user query."""
    return OracleState(query="What are the conditions at Tokyo Racecourse today?")


@pytest.fixture
def state_with_scout_data() -> OracleState:
    """OracleState after Scout node completion."""
    return OracleState(
        active_node=NodeType.STRATEGIST,
        query="Tokyo racecourse conditions",
        scout_data=ScoutData(
            racecourse="Tokyo Racecourse",
            track_condition="Good",
            weather="Clear",
            horse_data=[],
            sources=["https://jra.go.jp/keiba/tokyo"],
        ),
        reasoning_trace=[
            ReasoningStep(
                timestamp=datetime.now(timezone.utc).isoformat(),
                node=NodeType.SCOUT,
                thought="Starting information gathering",
                action="Initializing Scout node",
            )
        ],
    )


@pytest.fixture
def state_with_strategy() -> OracleState:
    """OracleState after Strategist node completion."""
    return OracleState(
        active_node=NodeType.AUDITOR,
        query="Tokyo racecourse conditions",
        scout_data=ScoutData(
            racecourse="Tokyo Racecourse",
            track_condition="Good",
            weather="Clear",
            horse_data=[],
            sources=["https://jra.go.jp/keiba/tokyo"],
        ),
        strategy_draft=StrategyDraft(
            recommended_horse="Front-runner strategy recommended",
            confidence_score=0.75,
            reasoning_summary="Good track conditions favor front-runners",
            kelly_fraction=0.10,
        ),
        reasoning_trace=[
            ReasoningStep(
                timestamp=datetime.now(timezone.utc).isoformat(),
                node=NodeType.SCOUT,
                thought="Completed scouting",
                action="Scout phase complete",
            ),
            ReasoningStep(
                timestamp=datetime.now(timezone.utc).isoformat(),
                node=NodeType.STRATEGIST,
                thought="Strategy formulated",
                action="Passing to Auditor",
            ),
        ],
    )


@pytest.fixture
def state_high_risk_strategy() -> OracleState:
    """OracleState with a high-risk strategy that should trigger backtrack."""
    return OracleState(
        active_node=NodeType.AUDITOR,
        query="Tokyo racecourse conditions",
        scout_data=ScoutData(
            racecourse="Tokyo Racecourse",
            track_condition="Heavy",
            weather="Rainy",
            horse_data=[],
            sources=[],
        ),
        strategy_draft=StrategyDraft(
            recommended_horse="Aggressive bet on underdog",
            confidence_score=0.35,  # Low confidence adds risk
            reasoning_summary="Risky bet on uncertain conditions",
            kelly_fraction=0.25,  # High kelly adds risk
        ),
        reasoning_trace=[],
    )


@pytest.fixture
def state_at_max_backtrack() -> OracleState:
    """OracleState that has reached max backtrack count."""
    return OracleState(
        active_node=NodeType.AUDITOR,
        query="Tokyo racecourse conditions",
        scout_data=ScoutData(
            racecourse="Tokyo Racecourse",
            track_condition="Good",
            weather="Clear",
            horse_data=[],
            sources=[],
        ),
        strategy_draft=StrategyDraft(
            recommended_horse="Revised strategy",
            confidence_score=0.40,
            reasoning_summary="Third revision attempt",
            kelly_fraction=0.22,
        ),
        backtrack_count=3,  # Max backtracks reached
        reasoning_trace=[],
    )


# =============================================================================
# Gemini API Mocks
# =============================================================================


@pytest.fixture
def mock_gemini_client():
    """Mock the google.genai.Client."""
    with patch("google.genai.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        yield mock_client


def create_mock_gemini_response(
    text: str = "",
    function_calls: list[dict] | None = None,
    thinking_text: str | None = None,
):
    """
    Factory for creating mock Gemini API responses.

    Args:
        text: The text response from the model
        function_calls: List of dicts with 'name' and 'args' for function calls
        thinking_text: Extended thinking content (for thinking models)
    """
    mock_response = MagicMock()
    mock_candidate = MagicMock()
    mock_content = MagicMock()

    parts = []

    # Add thinking part if provided
    if thinking_text:
        thinking_part = MagicMock()
        thinking_part.thought = True
        thinking_part.text = thinking_text
        parts.append(thinking_part)

    # Add text response
    if text:
        text_part = MagicMock()
        text_part.thought = False
        text_part.text = text
        text_part.function_call = None
        parts.append(text_part)

    # Add function calls
    if function_calls:
        for fc in function_calls:
            fc_part = MagicMock()
            fc_part.thought = False
            fc_part.text = None
            fc_part.function_call = MagicMock()
            fc_part.function_call.name = fc.get("name")
            fc_part.function_call.args = fc.get("args", {})
            parts.append(fc_part)

    mock_content.parts = parts
    mock_candidate.content = mock_content
    mock_response.candidates = [mock_candidate]

    return mock_response


@pytest.fixture
def mock_gemini_text_response():
    """Factory fixture for text-only Gemini responses."""
    def _create(text: str):
        return create_mock_gemini_response(text=text)
    return _create


@pytest.fixture
def mock_gemini_tool_response():
    """Factory fixture for Gemini responses with tool calls."""
    def _create(function_calls: list[dict], text: str = ""):
        return create_mock_gemini_response(text=text, function_calls=function_calls)
    return _create


@pytest.fixture
def mock_gemini_thinking_response():
    """Factory fixture for Gemini thinking model responses."""
    def _create(text: str, thinking_text: str):
        return create_mock_gemini_response(text=text, thinking_text=thinking_text)
    return _create


# =============================================================================
# Tavily API Mocks
# =============================================================================


@pytest.fixture
def mock_tavily_client():
    """Mock the Tavily search client."""
    with patch("app.tools.search.get_tavily_client") as mock_get:
        mock_client = MagicMock()
        mock_get.return_value = mock_client
        yield mock_client


@pytest.fixture
def sample_tavily_racecourse_response():
    """Sample Tavily response for racecourse search."""
    return {
        "results": [
            {
                "title": "Tokyo Racecourse - Today's Conditions",
                "url": "https://jra.go.jp/keiba/tokyo",
                "content": "Track condition: Good to Firm. Weather: Clear skies. Temperature: 22C. Turf course in excellent condition.",
            },
            {
                "title": "JRA Racing Schedule",
                "url": "https://jra.go.jp/schedule",
                "content": "Tokyo Racecourse hosting Grade 1 race today. Expected attendance: 50,000.",
            },
        ]
    }


@pytest.fixture
def sample_tavily_horse_response():
    """Sample Tavily response for horse search."""
    return {
        "results": [
            {
                "title": "Deep Impact - Racing Record",
                "url": "https://netkeiba.com/horse/deep-impact",
                "content": "Deep Impact: 14 wins from 14 starts. Triple Crown winner. Excels on firm turf.",
            },
        ]
    }


# =============================================================================
# Tool Execution Mocks
# =============================================================================


@pytest.fixture
def mock_search_tools():
    """Mock the search tool functions."""
    with patch("app.nodes.scout.search_racecourse_conditions") as mock_racecourse, \
         patch("app.nodes.scout.search_horse_info") as mock_horse:

        mock_racecourse.invoke.return_value = """
## Tokyo Racecourse Conditions
Track: Good to Firm
Weather: Clear
Source: https://jra.go.jp/keiba/tokyo
"""
        mock_horse.invoke.return_value = """
## Horse Information
No specific horse data found.
Source: https://netkeiba.com
"""
        yield {
            "racecourse": mock_racecourse,
            "horse": mock_horse,
        }
