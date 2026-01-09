"""
Tests for Scout node in app/nodes/scout.py
"""

import pytest
from unittest.mock import patch, MagicMock

from app.models import OracleState, NodeType, ScoutData
from app.nodes.scout import scout_node, get_timestamp


class TestGetTimestamp:
    """Tests for get_timestamp helper."""

    def test_returns_iso_format(self):
        """Test timestamp is in ISO format."""
        ts = get_timestamp()
        # Should be parseable as ISO format
        assert "T" in ts
        assert ts.endswith("Z") or "+" in ts


class TestScoutNodeBasics:
    """Basic tests for scout_node function."""

    def test_adds_entry_reasoning_step(self, state_with_query, mock_gemini_client, mock_gemini_text_response):
        """Test that scout_node adds an entry step to reasoning trace."""
        mock_gemini_client.models.generate_content.return_value = mock_gemini_text_response(
            "Analysis complete. Track looks good."
        )

        result = scout_node(state_with_query)

        assert len(result["reasoning_trace"]) >= 1
        first_step = result["reasoning_trace"][0]
        assert first_step.node == NodeType.SCOUT
        assert "Starting information gathering" in first_step.thought

    def test_transitions_to_strategist(self, state_with_query, mock_gemini_client, mock_gemini_text_response):
        """Test that scout_node sets active_node to STRATEGIST."""
        mock_gemini_client.models.generate_content.return_value = mock_gemini_text_response(
            "Information gathered successfully."
        )

        result = scout_node(state_with_query)

        assert result["active_node"] == NodeType.STRATEGIST

    def test_returns_scout_data(self, state_with_query, mock_gemini_client, mock_gemini_text_response):
        """Test that scout_node returns scout_data in result."""
        mock_gemini_client.models.generate_content.return_value = mock_gemini_text_response(
            "Tokyo Racecourse conditions are good and clear."
        )

        result = scout_node(state_with_query)

        assert "scout_data" in result
        assert isinstance(result["scout_data"], ScoutData)

    def test_preserves_original_state(self, state_with_query, mock_gemini_client, mock_gemini_text_response):
        """Test that original state's reasoning_trace is not mutated."""
        original_trace_len = len(state_with_query.reasoning_trace)
        mock_gemini_client.models.generate_content.return_value = mock_gemini_text_response("Test")

        scout_node(state_with_query)

        # Original state should be unchanged
        assert len(state_with_query.reasoning_trace) == original_trace_len


class TestScoutRacecourseExtraction:
    """Tests for racecourse extraction from query and results."""

    @pytest.mark.parametrize("racecourse,expected", [
        ("Tokyo", "Tokyo Racecourse"),
        ("Nakayama", "Nakayama Racecourse"),
        ("Kyoto", "Kyoto Racecourse"),
        ("Hanshin", "Hanshin Racecourse"),
        ("Chukyo", "Chukyo Racecourse"),
        ("Kokura", "Kokura Racecourse"),
        ("Niigata", "Niigata Racecourse"),
        ("Fukushima", "Fukushima Racecourse"),
        ("Sapporo", "Sapporo Racecourse"),
        ("Hakodate", "Hakodate Racecourse"),
    ])
    def test_extracts_racecourse_from_query(
        self, racecourse, expected, mock_gemini_client, mock_gemini_text_response
    ):
        """Test racecourse extraction from query."""
        state = OracleState(query=f"What are the conditions at {racecourse}?")
        mock_gemini_client.models.generate_content.return_value = mock_gemini_text_response(
            "Track conditions are favorable."
        )

        result = scout_node(state)

        assert result["scout_data"].racecourse == expected

    def test_unknown_racecourse_default(self, mock_gemini_client, mock_gemini_text_response):
        """Test fallback to 'Unknown' when racecourse not identified."""
        state = OracleState(query="What are the racing conditions?")
        mock_gemini_client.models.generate_content.return_value = mock_gemini_text_response(
            "General conditions are fine."
        )

        result = scout_node(state)

        assert result["scout_data"].racecourse == "Unknown"


class TestScoutTrackConditionExtraction:
    """Tests for track condition extraction from search results."""

    @pytest.mark.parametrize("keyword,expected", [
        ("good", "Good"),
        ("firm", "Good"),
        ("soft", "Soft"),
        ("yielding", "Soft"),
        ("heavy", "Heavy"),
    ])
    def test_extracts_track_condition(
        self, keyword, expected, state_with_query, mock_gemini_client, mock_search_tools
    ):
        """Test track condition extraction from tool call results."""
        from tests.conftest import create_mock_gemini_response

        # Mock search tool to return result with track condition keyword
        mock_search_tools["racecourse"].invoke.return_value = f"Track condition: {keyword}. Weather: normal."

        # Gemini returns a tool call
        mock_gemini_client.models.generate_content.return_value = create_mock_gemini_response(
            function_calls=[{
                "name": "search_racecourse_conditions",
                "args": {"query": "Tokyo conditions"}
            }]
        )

        result = scout_node(state_with_query)

        assert result["scout_data"].track_condition == expected

    def test_unknown_track_condition_default(self, state_with_query, mock_gemini_client, mock_gemini_text_response):
        """Test fallback to 'Unknown' when track condition not identified."""
        mock_gemini_client.models.generate_content.return_value = mock_gemini_text_response(
            "The track is in standard condition."
        )

        result = scout_node(state_with_query)

        assert result["scout_data"].track_condition == "Unknown"


class TestScoutWeatherExtraction:
    """Tests for weather extraction from search results."""

    @pytest.mark.parametrize("keyword,expected", [
        ("clear", "Clear"),
        ("sunny", "Clear"),
        ("rain", "Rainy"),
        ("cloudy", "Cloudy"),
    ])
    def test_extracts_weather(
        self, keyword, expected, state_with_query, mock_gemini_client, mock_search_tools
    ):
        """Test weather extraction from tool call results."""
        from tests.conftest import create_mock_gemini_response

        # Mock search tool to return result with weather keyword
        mock_search_tools["racecourse"].invoke.return_value = f"Track: normal. Weather: {keyword}."

        # Gemini returns a tool call
        mock_gemini_client.models.generate_content.return_value = create_mock_gemini_response(
            function_calls=[{
                "name": "search_racecourse_conditions",
                "args": {"query": "Tokyo conditions"}
            }]
        )

        result = scout_node(state_with_query)

        assert result["scout_data"].weather == expected

    def test_unknown_weather_default(self, state_with_query, mock_gemini_client, mock_gemini_text_response):
        """Test fallback to 'Unknown' when weather not identified."""
        mock_gemini_client.models.generate_content.return_value = mock_gemini_text_response(
            "Weather conditions are normal."
        )

        result = scout_node(state_with_query)

        assert result["scout_data"].weather == "Unknown"


class TestScoutToolCalls:
    """Tests for tool call handling."""

    def test_processes_function_calls(self, state_with_query, mock_gemini_client, mock_search_tools):
        """Test that scout_node processes Gemini function calls."""
        from tests.conftest import create_mock_gemini_response

        # First call returns function call, second returns text
        mock_gemini_client.models.generate_content.return_value = create_mock_gemini_response(
            function_calls=[{
                "name": "search_racecourse_conditions",
                "args": {"query": "Tokyo racecourse conditions"}
            }]
        )

        result = scout_node(state_with_query)

        # Should have tool_calls in result
        assert "tool_calls" in result
        assert len(result["tool_calls"]) >= 1

    def test_logs_tool_calls(self, state_with_query, mock_gemini_client, mock_search_tools):
        """Test that tool calls are logged to tool_calls list."""
        from tests.conftest import create_mock_gemini_response

        mock_gemini_client.models.generate_content.return_value = create_mock_gemini_response(
            function_calls=[{
                "name": "search_racecourse_conditions",
                "args": {"query": "Tokyo"}
            }]
        )

        result = scout_node(state_with_query)

        assert len(result["tool_calls"]) >= 1
        tool_call = result["tool_calls"][0]
        assert tool_call.tool == "search_racecourse_conditions"
        assert tool_call.node == "scout"


class TestScoutSourceExtraction:
    """Tests for source URL extraction."""

    def test_extracts_sources_from_results(self, state_with_query, mock_gemini_client, mock_search_tools):
        """Test that sources are extracted from search results."""
        from tests.conftest import create_mock_gemini_response

        # Mock search tool to return results with sources
        mock_search_tools["racecourse"].invoke.return_value = """
## Results
Track is good.
Source: https://jra.go.jp/keiba/tokyo
Source: https://netkeiba.com/race/123
"""

        mock_gemini_client.models.generate_content.return_value = create_mock_gemini_response(
            function_calls=[{
                "name": "search_racecourse_conditions",
                "args": {"query": "Tokyo"}
            }]
        )

        result = scout_node(state_with_query)

        assert len(result["scout_data"].sources) >= 1

    def test_limits_sources_to_five(self, state_with_query, mock_gemini_client, mock_search_tools):
        """Test that sources are limited to 5."""
        from tests.conftest import create_mock_gemini_response

        # Return more than 5 sources
        mock_search_tools["racecourse"].invoke.return_value = "\n".join([
            f"Source: https://example.com/{i}" for i in range(10)
        ])

        mock_gemini_client.models.generate_content.return_value = create_mock_gemini_response(
            function_calls=[{
                "name": "search_racecourse_conditions",
                "args": {"query": "Tokyo"}
            }]
        )

        result = scout_node(state_with_query)

        assert len(result["scout_data"].sources) <= 5


class TestScoutErrorHandling:
    """Tests for error handling in scout_node."""

    def test_handles_gemini_error(self, state_with_query, mock_gemini_client):
        """Test fallback behavior when Gemini raises exception."""
        mock_gemini_client.models.generate_content.side_effect = Exception("API Error")

        result = scout_node(state_with_query)

        # Should still return valid result with fallback ScoutData
        assert result["active_node"] == NodeType.STRATEGIST
        assert result["scout_data"].racecourse == "Unknown Racecourse"
        assert result["scout_data"].track_condition == "Unknown"
        assert result["scout_data"].weather == "Unknown"

    def test_error_logged_to_reasoning_trace(self, state_with_query, mock_gemini_client):
        """Test that errors are logged to reasoning trace."""
        mock_gemini_client.models.generate_content.side_effect = Exception("API Error")

        result = scout_node(state_with_query)

        # Should have error step in trace
        error_steps = [
            step for step in result["reasoning_trace"]
            if "Error" in (step.thought or "") or "Error" in (step.action or "")
        ]
        assert len(error_steps) >= 1


class TestScoutReasoningTrace:
    """Tests for reasoning trace accumulation."""

    def test_appends_to_existing_trace(self, mock_gemini_client, mock_gemini_text_response):
        """Test that scout appends to existing reasoning trace."""
        from app.models import ReasoningStep

        existing_step = ReasoningStep(
            timestamp="2024-01-01T00:00:00Z",
            node=NodeType.IDLE,
            thought="Initial thought",
        )
        state = OracleState(
            query="Test query",
            reasoning_trace=[existing_step],
        )

        mock_gemini_client.models.generate_content.return_value = mock_gemini_text_response("Done")

        result = scout_node(state)

        # Should have more than original 1 step
        assert len(result["reasoning_trace"]) > 1
        # First step should be the existing one
        assert result["reasoning_trace"][0].thought == "Initial thought"

    def test_multiple_reasoning_steps_added(self, state_with_query, mock_gemini_client, mock_gemini_text_response):
        """Test that multiple reasoning steps are added during execution."""
        mock_gemini_client.models.generate_content.return_value = mock_gemini_text_response(
            "Analysis complete with detailed findings."
        )

        result = scout_node(state_with_query)

        # Should have entry step + analysis step + summary step at minimum
        assert len(result["reasoning_trace"]) >= 2
