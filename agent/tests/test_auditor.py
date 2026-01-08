"""
Tests for Auditor node in app/nodes/auditor.py
"""

import pytest
from unittest.mock import patch, MagicMock
from typing import cast

from langgraph.types import Command

from app.models import OracleState, NodeType, ScoutData, StrategyDraft, ReasoningStep
from app.nodes.auditor import auditor_node, get_timestamp, load_kelly_skill


class TestGetTimestamp:
    """Tests for get_timestamp helper."""

    def test_returns_iso_format(self):
        """Test timestamp is in ISO format."""
        ts = get_timestamp()
        assert "T" in ts


class TestLoadKellySkill:
    """Tests for load_kelly_skill function."""

    def test_loads_skill_file(self):
        """Test that Kelly skill file is loaded."""
        skill = load_kelly_skill()
        assert isinstance(skill, str)
        assert len(skill) > 0

    def test_fallback_on_missing_file(self):
        """Test fallback content when file is missing."""
        with patch("builtins.open", side_effect=FileNotFoundError()):
            skill = load_kelly_skill()
            assert "Kelly Criterion" in skill
            assert "Fallback" in skill


class TestAuditorNodeBasics:
    """Basic tests for auditor_node function."""

    def test_adds_entry_reasoning_step(self, state_with_strategy: OracleState, mock_gemini_client: MagicMock, mock_gemini_text_response):
        """Test that auditor_node adds an entry step."""
        mock_gemini_client.models.generate_content.return_value = mock_gemini_text_response(
            "Risk assessment: acceptable. Approve the strategy."
        )

        result = auditor_node(state_with_strategy)
        assert isinstance(result, dict)

        entry_steps = [
            step for step in result["reasoning_trace"]
            if step.node == NodeType.AUDITOR and "risk assessment" in step.thought.lower()
        ]
        assert len(entry_steps) >= 1

    def test_returns_dict_on_approval(self, state_with_strategy: OracleState, mock_gemini_client: MagicMock, mock_gemini_text_response):
        """Test that approval returns a dict (not Command)."""
        mock_gemini_client.models.generate_content.return_value = mock_gemini_text_response(
            "Approve this strategy. Acceptable risk level."
        )

        result = auditor_node(state_with_strategy)

        assert isinstance(result, dict)
        assert result["active_node"] == NodeType.IDLE

    def test_returns_command_on_backtrack(self, state_high_risk_strategy: OracleState, mock_gemini_client: MagicMock, mock_gemini_text_response):
        """Test that high risk returns Command for backtrack."""
        mock_gemini_client.models.generate_content.return_value = mock_gemini_text_response(
            "High risk detected. Backtrack required. Reject this strategy."
        )

        result = auditor_node(state_high_risk_strategy)

        assert isinstance(result, Command)
        assert result.goto == "strategist"


class TestAuditorMissingStrategy:
    """Tests for handling missing strategy."""

    def test_handles_missing_strategy(self, mock_gemini_client: MagicMock):
        """Test behavior when strategy_draft is None."""
        state = OracleState(
            query="Test",
            scout_data=ScoutData(
                racecourse="Tokyo", track_condition="Good",
                weather="Clear", horse_data=[], sources=[]
            ),
            strategy_draft=None,
        )

        result = auditor_node(state)

        assert isinstance(result, dict)
        assert result["active_node"] == NodeType.IDLE
        assert result["risk_score"] == 1.0  # Max risk for missing strategy

    def test_logs_error_for_missing_strategy(self, mock_gemini_client: MagicMock):
        """Test error logged when strategy missing."""
        state = OracleState(query="Test", strategy_draft=None)

        result = auditor_node(state)
        assert isinstance(result, dict)

        error_steps = [
            step for step in result["reasoning_trace"]
            if "No strategy" in step.thought or (step.action and "missing" in step.action.lower())
        ]
        assert len(error_steps) >= 1


class TestAuditorRiskCalculation:
    """Tests for risk score calculation logic."""

    def test_base_risk_score(self, mock_gemini_client: MagicMock, mock_gemini_text_response):
        """Test base risk score is 0.3."""
        state = OracleState(
            query="Test",
            scout_data=ScoutData(
                racecourse="Tokyo", track_condition="Good",
                weather="Clear", horse_data=[], sources=[]
            ),
            strategy_draft=StrategyDraft(
                recommended_horse="Test",
                confidence_score=0.75,
                reasoning_summary="Test",
                kelly_fraction=0.08,
            ),
        )

        mock_gemini_client.models.generate_content.return_value = mock_gemini_text_response(
            "Standard assessment."
        )

        result = auditor_node(state)
        assert isinstance(result, dict)
        assert 0.25 <= result["risk_score"] <= 0.35

    def test_low_confidence_adds_risk(self, mock_gemini_client: MagicMock, mock_gemini_text_response):
        """Test confidence < 0.5 adds 0.3 to risk."""
        state = OracleState(
            query="Test",
            scout_data=ScoutData(
                racecourse="Tokyo", track_condition="Good",
                weather="Clear", horse_data=[], sources=[]
            ),
            strategy_draft=StrategyDraft(
                recommended_horse="Test",
                confidence_score=0.40,
                reasoning_summary="Test",
                kelly_fraction=0.05,
            ),
        )

        mock_gemini_client.models.generate_content.return_value = mock_gemini_text_response(
            "Standard assessment."
        )

        result = auditor_node(state)
        assert isinstance(result, dict)
        assert result["risk_score"] >= 0.55

    def test_medium_confidence_adds_risk(self, mock_gemini_client: MagicMock, mock_gemini_text_response):
        """Test 0.5 <= confidence < 0.7 adds 0.15 to risk."""
        state = OracleState(
            query="Test",
            scout_data=ScoutData(
                racecourse="Tokyo", track_condition="Good",
                weather="Clear", horse_data=[], sources=[]
            ),
            strategy_draft=StrategyDraft(
                recommended_horse="Test",
                confidence_score=0.60,
                reasoning_summary="Test",
                kelly_fraction=0.05,
            ),
        )

        mock_gemini_client.models.generate_content.return_value = mock_gemini_text_response(
            "Standard assessment."
        )

        result = auditor_node(state)
        assert isinstance(result, dict)
        assert 0.40 <= result["risk_score"] <= 0.50

    def test_high_kelly_adds_maximum_risk(self, mock_gemini_client: MagicMock, mock_gemini_text_response):
        """Test kelly > 0.20 adds 0.3 to risk."""
        state = OracleState(
            query="Test",
            scout_data=ScoutData(
                racecourse="Tokyo", track_condition="Good",
                weather="Clear", horse_data=[], sources=[]
            ),
            strategy_draft=StrategyDraft(
                recommended_horse="Test",
                confidence_score=0.80,
                reasoning_summary="Test",
                kelly_fraction=0.25,
            ),
        )

        mock_gemini_client.models.generate_content.return_value = mock_gemini_text_response(
            "Standard assessment."
        )

        result = auditor_node(state)
        assert isinstance(result, dict)
        assert result["risk_score"] >= 0.55

    def test_medium_kelly_adds_risk(self, mock_gemini_client: MagicMock, mock_gemini_text_response):
        """Test 0.15 < kelly <= 0.20 adds 0.2 to risk."""
        state = OracleState(
            query="Test",
            scout_data=ScoutData(
                racecourse="Tokyo", track_condition="Good",
                weather="Clear", horse_data=[], sources=[]
            ),
            strategy_draft=StrategyDraft(
                recommended_horse="Test",
                confidence_score=0.80,
                reasoning_summary="Test",
                kelly_fraction=0.18,
            ),
        )

        mock_gemini_client.models.generate_content.return_value = mock_gemini_text_response(
            "Standard assessment."
        )

        result = auditor_node(state)
        assert isinstance(result, dict)
        assert 0.45 <= result["risk_score"] <= 0.55

    def test_low_kelly_adds_small_risk(self, mock_gemini_client: MagicMock, mock_gemini_text_response):
        """Test 0.10 < kelly <= 0.15 adds 0.1 to risk."""
        state = OracleState(
            query="Test",
            scout_data=ScoutData(
                racecourse="Tokyo", track_condition="Good",
                weather="Clear", horse_data=[], sources=[]
            ),
            strategy_draft=StrategyDraft(
                recommended_horse="Test",
                confidence_score=0.80,
                reasoning_summary="Test",
                kelly_fraction=0.12,
            ),
        )

        mock_gemini_client.models.generate_content.return_value = mock_gemini_text_response(
            "Standard assessment."
        )

        result = auditor_node(state)
        assert isinstance(result, dict)
        assert 0.35 <= result["risk_score"] <= 0.45


class TestAuditorResponseSentiment:
    """Tests for response sentiment analysis."""

    def test_backtrack_keyword_adds_risk(self, mock_gemini_client: MagicMock, mock_gemini_text_response):
        """Test 'backtrack' in response adds 0.2 to risk."""
        state = OracleState(
            query="Test",
            scout_data=ScoutData(
                racecourse="Tokyo", track_condition="Good",
                weather="Clear", horse_data=[], sources=[]
            ),
            strategy_draft=StrategyDraft(
                recommended_horse="Test",
                confidence_score=0.75,
                reasoning_summary="Test",
                kelly_fraction=0.08,
            ),
        )

        mock_gemini_client.models.generate_content.return_value = mock_gemini_text_response(
            "Recommend backtrack to revise this strategy."
        )

        result = auditor_node(state)
        assert isinstance(result, dict)
        assert result["risk_score"] >= 0.45

    def test_reject_keyword_adds_risk(self, mock_gemini_client: MagicMock, mock_gemini_text_response):
        """Test 'reject' in response adds 0.2 to risk."""
        state = OracleState(
            query="Test",
            scout_data=ScoutData(
                racecourse="Tokyo", track_condition="Good",
                weather="Clear", horse_data=[], sources=[]
            ),
            strategy_draft=StrategyDraft(
                recommended_horse="Test",
                confidence_score=0.75,
                reasoning_summary="Test",
                kelly_fraction=0.08,
            ),
        )

        mock_gemini_client.models.generate_content.return_value = mock_gemini_text_response(
            "Reject this strategy due to concerns."
        )

        result = auditor_node(state)
        assert isinstance(result, dict)
        assert result["risk_score"] >= 0.45

    def test_high_risk_keyword_adds_risk(self, mock_gemini_client: MagicMock, mock_gemini_text_response):
        """Test 'high risk' in response adds 0.2 to risk."""
        state = OracleState(
            query="Test",
            scout_data=ScoutData(
                racecourse="Tokyo", track_condition="Good",
                weather="Clear", horse_data=[], sources=[]
            ),
            strategy_draft=StrategyDraft(
                recommended_horse="Test",
                confidence_score=0.75,
                reasoning_summary="Test",
                kelly_fraction=0.08,
            ),
        )

        mock_gemini_client.models.generate_content.return_value = mock_gemini_text_response(
            "This is a high risk proposition."
        )

        result = auditor_node(state)
        assert isinstance(result, dict)
        assert result["risk_score"] >= 0.45

    def test_approve_keyword_reduces_risk(self, mock_gemini_client: MagicMock, mock_gemini_text_response):
        """Test 'approve' in response reduces risk by 0.1."""
        state = OracleState(
            query="Test",
            scout_data=ScoutData(
                racecourse="Tokyo", track_condition="Good",
                weather="Clear", horse_data=[], sources=[]
            ),
            strategy_draft=StrategyDraft(
                recommended_horse="Test",
                confidence_score=0.75,
                reasoning_summary="Test",
                kelly_fraction=0.08,
            ),
        )

        mock_gemini_client.models.generate_content.return_value = mock_gemini_text_response(
            "Approve this strategy. It looks acceptable."
        )

        result = auditor_node(state)
        assert isinstance(result, dict)
        assert result["risk_score"] <= 0.25


class TestAuditorRiskClamping:
    """Tests for risk score clamping."""

    def test_risk_clamped_to_max_1(self, mock_gemini_client: MagicMock, mock_gemini_text_response):
        """Test risk score is clamped to maximum 1.0."""
        state = OracleState(
            query="Test",
            scout_data=ScoutData(
                racecourse="Tokyo", track_condition="Heavy",
                weather="Rainy", horse_data=[], sources=[]
            ),
            strategy_draft=StrategyDraft(
                recommended_horse="Test",
                confidence_score=0.30,
                reasoning_summary="Test",
                kelly_fraction=0.25,
            ),
        )

        mock_gemini_client.models.generate_content.return_value = mock_gemini_text_response(
            "High risk, recommend backtrack, reject this approach."
        )

        result = auditor_node(state)
        # Result could be dict or Command depending on risk
        if isinstance(result, dict):
            assert result["risk_score"] <= 1.0
        else:
            assert result.update["risk_score"] <= 1.0  # type: ignore[index]

    def test_risk_clamped_to_min_0(self, mock_gemini_client: MagicMock, mock_gemini_text_response):
        """Test risk score is clamped to minimum 0.0."""
        state = OracleState(
            query="Test",
            scout_data=ScoutData(
                racecourse="Tokyo", track_condition="Good",
                weather="Clear", horse_data=[], sources=[]
            ),
            strategy_draft=StrategyDraft(
                recommended_horse="Test",
                confidence_score=0.95,
                reasoning_summary="Test",
                kelly_fraction=0.02,
            ),
        )

        mock_gemini_client.models.generate_content.return_value = mock_gemini_text_response(
            "Approve. Acceptable. This is a great strategy."
        )

        result = auditor_node(state)
        assert isinstance(result, dict)
        assert result["risk_score"] >= 0.0


class TestAuditorBacktrackDecision:
    """Tests for backtrack decision logic."""

    def test_backtrack_when_risk_exceeds_threshold(self, state_high_risk_strategy: OracleState, mock_gemini_client: MagicMock, mock_gemini_text_response):
        """Test backtrack triggered when risk > 0.7."""
        mock_gemini_client.models.generate_content.return_value = mock_gemini_text_response(
            "High risk detected. Backtrack recommended."
        )

        result = auditor_node(state_high_risk_strategy)

        assert isinstance(result, Command)
        assert result.goto == "strategist"

    def test_backtrack_increments_count(self, state_high_risk_strategy: OracleState, mock_gemini_client: MagicMock, mock_gemini_text_response):
        """Test backtrack_count is incremented on backtrack."""
        original_count = state_high_risk_strategy.backtrack_count
        mock_gemini_client.models.generate_content.return_value = mock_gemini_text_response(
            "High risk. Backtrack."
        )

        result = auditor_node(state_high_risk_strategy)

        assert isinstance(result, Command)
        assert result.update["backtrack_count"] == original_count + 1  # type: ignore[index]

    def test_backtrack_sets_reason(self, state_high_risk_strategy: OracleState, mock_gemini_client: MagicMock, mock_gemini_text_response):
        """Test backtrack_reason is set on backtrack."""
        mock_gemini_client.models.generate_content.return_value = mock_gemini_text_response(
            "High risk. Backtrack."
        )

        result = auditor_node(state_high_risk_strategy)

        assert isinstance(result, Command)
        update = result.update
        assert isinstance(update, dict)
        assert update["backtrack_reason"] is not None
        assert "Risk score" in update["backtrack_reason"]

    def test_backtrack_sets_requires_backtrack_flag(self, state_high_risk_strategy: OracleState, mock_gemini_client: MagicMock, mock_gemini_text_response):
        """Test requires_backtrack is set to True on backtrack."""
        mock_gemini_client.models.generate_content.return_value = mock_gemini_text_response(
            "High risk. Backtrack."
        )

        result = auditor_node(state_high_risk_strategy)

        assert isinstance(result, Command)
        update = result.update
        assert isinstance(update, dict)
        assert update["requires_backtrack"] is True


class TestAuditorMaxBacktrackLimit:
    """Tests for maximum backtrack limit enforcement."""

    def test_accepts_at_max_backtrack(self, state_at_max_backtrack: OracleState, mock_gemini_client: MagicMock, mock_gemini_text_response):
        """Test strategy accepted despite risk when at max backtracks."""
        mock_gemini_client.models.generate_content.return_value = mock_gemini_text_response(
            "High risk. Would normally backtrack."
        )

        result = auditor_node(state_at_max_backtrack)

        assert isinstance(result, dict)
        assert result["active_node"] == NodeType.IDLE

    def test_logs_limit_reached(self, state_at_max_backtrack: OracleState, mock_gemini_client: MagicMock, mock_gemini_text_response):
        """Test message logged when backtrack limit reached."""
        mock_gemini_client.models.generate_content.return_value = mock_gemini_text_response(
            "Assessment complete."
        )

        result = auditor_node(state_at_max_backtrack)
        assert isinstance(result, dict)

        limit_steps = [
            step for step in result["reasoning_trace"]
            if "Maximum backtrack" in step.thought or "limit" in step.thought.lower()
        ]
        assert len(limit_steps) >= 1


class TestAuditorApproval:
    """Tests for strategy approval."""

    def test_approval_ends_at_idle(self, state_with_strategy: OracleState, mock_gemini_client: MagicMock, mock_gemini_text_response):
        """Test approved strategy ends at IDLE state."""
        mock_gemini_client.models.generate_content.return_value = mock_gemini_text_response(
            "Approve this strategy. Acceptable risk."
        )

        result = auditor_node(state_with_strategy)

        assert isinstance(result, dict)
        assert result["active_node"] == NodeType.IDLE

    def test_approval_generates_recommendation(self, state_with_strategy: OracleState, mock_gemini_client: MagicMock, mock_gemini_text_response):
        """Test final_recommendation is generated on approval."""
        mock_gemini_client.models.generate_content.return_value = mock_gemini_text_response(
            "Approve. Acceptable risk level."
        )

        result = auditor_node(state_with_strategy)
        assert isinstance(result, dict)

        assert result["final_recommendation"] is not None
        assert len(result["final_recommendation"]) > 0

    def test_recommendation_includes_strategy(self, state_with_strategy: OracleState, mock_gemini_client: MagicMock, mock_gemini_text_response):
        """Test recommendation includes strategy details."""
        mock_gemini_client.models.generate_content.return_value = mock_gemini_text_response(
            "Approve."
        )

        result = auditor_node(state_with_strategy)
        assert isinstance(result, dict)

        assert state_with_strategy.strategy_draft is not None
        assert result["final_recommendation"] is not None
        assert ("Front-runner" in result["final_recommendation"] or
                state_with_strategy.strategy_draft.recommended_horse in result["final_recommendation"])

    def test_approval_clears_backtrack_flag(self, state_with_strategy: OracleState, mock_gemini_client: MagicMock, mock_gemini_text_response):
        """Test requires_backtrack is False on approval."""
        mock_gemini_client.models.generate_content.return_value = mock_gemini_text_response(
            "Approve."
        )

        result = auditor_node(state_with_strategy)
        assert isinstance(result, dict)

        assert result["requires_backtrack"] is False


class TestAuditorErrorHandling:
    """Tests for error handling in auditor_node."""

    def test_handles_gemini_error(self, state_with_strategy: OracleState, mock_gemini_client: MagicMock):
        """Test fallback when Gemini raises exception."""
        mock_gemini_client.models.generate_content.side_effect = Exception("API Error")

        result = auditor_node(state_with_strategy)

        assert isinstance(result, dict)
        assert result["risk_score"] == 0.6

    def test_error_logged_to_trace(self, state_with_strategy: OracleState, mock_gemini_client: MagicMock):
        """Test error is logged to reasoning trace."""
        mock_gemini_client.models.generate_content.side_effect = Exception("API Error")

        result = auditor_node(state_with_strategy)
        assert isinstance(result, dict)

        error_steps = [
            step for step in result["reasoning_trace"]
            if "Error" in (step.thought or "") or "conservative" in (step.action or "").lower()
        ]
        assert len(error_steps) >= 1


class TestAuditorReasoningTrace:
    """Tests for reasoning trace accumulation."""

    def test_appends_to_existing_trace(self, mock_gemini_client: MagicMock, mock_gemini_text_response):
        """Test auditor appends to existing trace."""
        existing_step = ReasoningStep(
            timestamp="2024-01-01T00:00:00Z",
            node=NodeType.STRATEGIST,
            thought="Strategy complete",
        )
        state = OracleState(
            query="Test",
            scout_data=ScoutData(
                racecourse="Tokyo", track_condition="Good",
                weather="Clear", horse_data=[], sources=[]
            ),
            strategy_draft=StrategyDraft(
                recommended_horse="Test",
                confidence_score=0.75,
                reasoning_summary="Test",
                kelly_fraction=0.10,
            ),
            reasoning_trace=[existing_step],
        )

        mock_gemini_client.models.generate_content.return_value = mock_gemini_text_response(
            "Approve."
        )

        result = auditor_node(state)
        assert isinstance(result, dict)

        assert len(result["reasoning_trace"]) > 1
        assert result["reasoning_trace"][0].node == NodeType.STRATEGIST

    def test_logs_risk_calculation(self, state_with_strategy: OracleState, mock_gemini_client: MagicMock, mock_gemini_text_response):
        """Test risk calculation is logged."""
        mock_gemini_client.models.generate_content.return_value = mock_gemini_text_response(
            "Approve."
        )

        result = auditor_node(state_with_strategy)
        assert isinstance(result, dict)

        risk_steps = [
            step for step in result["reasoning_trace"]
            if "risk" in step.thought.lower() and "%" in step.thought
        ]
        assert len(risk_steps) >= 1
