"""
Tests for Pydantic models in app/models/state.py
"""

import pytest
from pydantic import ValidationError
from datetime import datetime, timezone

from app.models import (
    OracleState,
    NodeType,
    ReasoningStep,
    ScoutData,
    StrategyDraft,
    ToolCall,
)


class TestNodeType:
    """Tests for NodeType enum."""

    def test_node_type_values(self):
        """Verify all node type values."""
        assert NodeType.SCOUT.value == "scout"
        assert NodeType.STRATEGIST.value == "strategist"
        assert NodeType.AUDITOR.value == "auditor"
        assert NodeType.IDLE.value == "idle"

    def test_node_type_is_string_enum(self):
        """Verify NodeType is a string enum."""
        assert isinstance(NodeType.SCOUT, str)
        assert NodeType.SCOUT == "scout"


class TestReasoningStep:
    """Tests for ReasoningStep model."""

    def test_required_fields(self):
        """Test that timestamp, node, and thought are required."""
        step = ReasoningStep(
            timestamp="2024-01-01T00:00:00Z",
            node=NodeType.SCOUT,
            thought="Test thought",
        )
        assert step.timestamp == "2024-01-01T00:00:00Z"
        assert step.node == NodeType.SCOUT
        assert step.thought == "Test thought"

    def test_optional_fields_default_none(self):
        """Test that action and observation default to None."""
        step = ReasoningStep(
            timestamp="2024-01-01T00:00:00Z",
            node=NodeType.SCOUT,
            thought="Test thought",
        )
        assert step.action is None
        assert step.observation is None

    def test_optional_fields_can_be_set(self):
        """Test that optional fields can be provided."""
        step = ReasoningStep(
            timestamp="2024-01-01T00:00:00Z",
            node=NodeType.SCOUT,
            thought="Test thought",
            action="Test action",
            observation="Test observation",
        )
        assert step.action == "Test action"
        assert step.observation == "Test observation"

    def test_missing_required_field_raises(self):
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError):
            ReasoningStep(  # type: ignore[call-arg]
                timestamp="2024-01-01T00:00:00Z",
                node=NodeType.SCOUT,
                # thought is missing - should raise
            )


class TestScoutData:
    """Tests for ScoutData model."""

    def test_all_fields_required(self):
        """Test that all ScoutData fields are required."""
        data = ScoutData(
            racecourse="Tokyo Racecourse",
            track_condition="Good",
            weather="Clear",
            horse_data=[],
            sources=[],
        )
        assert data.racecourse == "Tokyo Racecourse"
        assert data.track_condition == "Good"
        assert data.weather == "Clear"
        assert data.horse_data == []
        assert data.sources == []

    def test_with_horse_data(self):
        """Test ScoutData with horse data populated."""
        data = ScoutData(
            racecourse="Tokyo Racecourse",
            track_condition="Good",
            weather="Clear",
            horse_data=[{"name": "Deep Impact", "form": "1-1-1"}],
            sources=["https://jra.go.jp"],
        )
        assert len(data.horse_data) == 1
        assert data.horse_data[0]["name"] == "Deep Impact"

    def test_missing_field_raises(self):
        """Test that missing fields raise ValidationError."""
        with pytest.raises(ValidationError):
            ScoutData(  # type: ignore[call-arg]
                racecourse="Tokyo",
                track_condition="Good",
                weather="Clear",
                # horse_data and sources are missing
            )


class TestStrategyDraft:
    """Tests for StrategyDraft model."""

    def test_required_fields(self):
        """Test required fields for StrategyDraft."""
        draft = StrategyDraft(
            recommended_horse="Front-runner strategy",
            confidence_score=0.75,
            reasoning_summary="Good conditions favor front-runners",
        )
        assert draft.recommended_horse == "Front-runner strategy"
        assert draft.confidence_score == 0.75
        assert draft.reasoning_summary == "Good conditions favor front-runners"
        assert draft.kelly_fraction is None

    def test_kelly_fraction_optional(self):
        """Test that kelly_fraction is optional."""
        draft = StrategyDraft(
            recommended_horse="Test",
            confidence_score=0.5,
            reasoning_summary="Test",
            kelly_fraction=0.10,
        )
        assert draft.kelly_fraction == 0.10

    def test_confidence_score_bounds(self):
        """Test confidence_score must be between 0 and 1."""
        # Valid bounds
        StrategyDraft(
            recommended_horse="Test",
            confidence_score=0.0,
            reasoning_summary="Test",
        )
        StrategyDraft(
            recommended_horse="Test",
            confidence_score=1.0,
            reasoning_summary="Test",
        )

        # Invalid: below 0
        with pytest.raises(ValidationError):
            StrategyDraft(
                recommended_horse="Test",
                confidence_score=-0.1,
                reasoning_summary="Test",
            )

        # Invalid: above 1
        with pytest.raises(ValidationError):
            StrategyDraft(
                recommended_horse="Test",
                confidence_score=1.1,
                reasoning_summary="Test",
            )

    def test_kelly_fraction_bounds(self):
        """Test kelly_fraction must be between 0 and 1."""
        # Valid bounds
        StrategyDraft(
            recommended_horse="Test",
            confidence_score=0.5,
            reasoning_summary="Test",
            kelly_fraction=0.0,
        )
        StrategyDraft(
            recommended_horse="Test",
            confidence_score=0.5,
            reasoning_summary="Test",
            kelly_fraction=1.0,
        )

        # Invalid: below 0
        with pytest.raises(ValidationError):
            StrategyDraft(
                recommended_horse="Test",
                confidence_score=0.5,
                reasoning_summary="Test",
                kelly_fraction=-0.1,
            )

        # Invalid: above 1
        with pytest.raises(ValidationError):
            StrategyDraft(
                recommended_horse="Test",
                confidence_score=0.5,
                reasoning_summary="Test",
                kelly_fraction=1.1,
            )


class TestToolCall:
    """Tests for ToolCall model."""

    def test_all_fields(self):
        """Test ToolCall with all fields."""
        tool_call = ToolCall(
            timestamp="2024-01-01T00:00:00Z",
            tool="search_racecourse_conditions",
            args={"query": "Tokyo conditions"},
            node="scout",
        )
        assert tool_call.timestamp == "2024-01-01T00:00:00Z"
        assert tool_call.tool == "search_racecourse_conditions"
        assert tool_call.args == {"query": "Tokyo conditions"}
        assert tool_call.node == "scout"

    def test_empty_args(self):
        """Test ToolCall with empty args dict."""
        tool_call = ToolCall(
            timestamp="2024-01-01T00:00:00Z",
            tool="test_tool",
            args={},
            node="scout",
        )
        assert tool_call.args == {}


class TestOracleState:
    """Tests for OracleState model."""

    def test_defaults(self):
        """Test OracleState default values."""
        state = OracleState()
        assert state.active_node == NodeType.IDLE
        assert state.reasoning_trace == []
        assert state.scout_data is None
        assert state.strategy_draft is None
        assert state.risk_score == 0.0
        assert state.requires_backtrack is False
        assert state.backtrack_reason is None
        assert state.backtrack_count == 0
        assert state.query == ""
        assert state.tool_calls == []
        assert state.final_recommendation is None

    def test_active_node_enum_values(self):
        """Test that active_node accepts all NodeType values."""
        for node_type in NodeType:
            state = OracleState(active_node=node_type)
            assert state.active_node == node_type

    def test_risk_score_bounds(self):
        """Test risk_score must be between 0 and 1."""
        OracleState(risk_score=0.0)
        OracleState(risk_score=1.0)

        with pytest.raises(ValidationError):
            OracleState(risk_score=-0.1)

        with pytest.raises(ValidationError):
            OracleState(risk_score=1.1)

    def test_backtrack_count_bounds(self):
        """Test backtrack_count must be between 0 and 3."""
        OracleState(backtrack_count=0)
        OracleState(backtrack_count=3)

        with pytest.raises(ValidationError):
            OracleState(backtrack_count=-1)

        with pytest.raises(ValidationError):
            OracleState(backtrack_count=4)

    def test_reasoning_trace_append(self):
        """Test appending to reasoning_trace."""
        state = OracleState()
        step = ReasoningStep(
            timestamp="2024-01-01T00:00:00Z",
            node=NodeType.SCOUT,
            thought="Test",
        )
        state.reasoning_trace.append(step)
        assert len(state.reasoning_trace) == 1

    def test_serialization(self):
        """Test OracleState can be serialized to dict."""
        state = OracleState(
            active_node=NodeType.SCOUT,
            query="Test query",
            risk_score=0.5,
        )
        data = state.model_dump()
        assert isinstance(data, dict)
        assert data["active_node"] == "scout"  # use_enum_values=True
        assert data["query"] == "Test query"
        assert data["risk_score"] == 0.5

    def test_use_enum_values_config(self):
        """Test that Config.use_enum_values=True works."""
        state = OracleState(active_node=NodeType.STRATEGIST)
        data = state.model_dump()
        # With use_enum_values=True, enum is serialized as string
        assert data["active_node"] == "strategist"

    def test_full_state_with_all_fields(self):
        """Test OracleState with all fields populated."""
        state = OracleState(
            active_node=NodeType.AUDITOR,
            reasoning_trace=[
                ReasoningStep(
                    timestamp="2024-01-01T00:00:00Z",
                    node=NodeType.SCOUT,
                    thought="Test",
                )
            ],
            scout_data=ScoutData(
                racecourse="Tokyo",
                track_condition="Good",
                weather="Clear",
                horse_data=[],
                sources=[],
            ),
            strategy_draft=StrategyDraft(
                recommended_horse="Test",
                confidence_score=0.7,
                reasoning_summary="Test",
                kelly_fraction=0.1,
            ),
            risk_score=0.5,
            requires_backtrack=True,
            backtrack_reason="High risk",
            backtrack_count=1,
            query="Test query",
            tool_calls=[
                ToolCall(
                    timestamp="2024-01-01T00:00:00Z",
                    tool="test",
                    args={},
                    node="scout",
                )
            ],
            final_recommendation="Test recommendation",
        )
        assert state.active_node == NodeType.AUDITOR
        assert len(state.reasoning_trace) == 1
        assert state.scout_data is not None
        assert state.scout_data.racecourse == "Tokyo"
        assert state.strategy_draft is not None
        assert state.strategy_draft.confidence_score == 0.7
        assert state.risk_score == 0.5
        assert state.requires_backtrack is True
        assert state.backtrack_reason == "High risk"
        assert state.backtrack_count == 1
        assert state.query == "Test query"
        assert len(state.tool_calls) == 1
        assert state.final_recommendation == "Test recommendation"
