"""
Auditor Node - Risk Assessment with Backtrack Capability.

Evaluates the strategy using Kelly Criterion skill.
Can trigger backtrack to Strategist if risk is too high.
"""

import os
from datetime import datetime, timezone
from google import genai
from google.genai import types
from langgraph.types import Command

from app.models import OracleState, NodeType, ReasoningStep


def get_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def load_kelly_skill() -> str:
    """Load the Kelly Criterion skill file."""
    skill_path = os.path.join(os.path.dirname(__file__), "../skills/kelly_criterion.skill")
    try:
        with open(skill_path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return """# Kelly Criterion (Fallback)
f* = (bp - q) / b
Never bet more than 25% of bankroll.
Risk threshold: 0.7"""


def auditor_node(state: OracleState) -> dict | Command:
    """
    Auditor Node: Evaluates risk and can trigger backtrack.

    Uses Claude skill (Kelly Criterion) for validation.
    Returns Command(goto="strategist") if risk > 0.7.
    """
    # Initialize updates with copies to avoid mutation
    reasoning_trace = list(state.reasoning_trace)

    # Log entry into node
    entry_step = ReasoningStep(
        timestamp=get_timestamp(),
        node=NodeType.AUDITOR,
        thought="Beginning risk assessment of proposed strategy",
        action="Initializing Auditor node"
    )
    reasoning_trace.append(entry_step)

    # Check backtrack count to prevent infinite loops
    current_backtrack_count = state.backtrack_count
    if current_backtrack_count >= 3:
        limit_step = ReasoningStep(
            timestamp=get_timestamp(),
            node=NodeType.AUDITOR,
            thought="Maximum backtrack attempts reached (3). Accepting current strategy despite risk.",
            action="Backtrack limit enforced"
        )
        reasoning_trace.append(limit_step)

        return {
            "active_node": NodeType.IDLE,
            "reasoning_trace": reasoning_trace,
            "risk_score": state.risk_score,
            "requires_backtrack": False,
            "final_recommendation": f"Strategy accepted after {current_backtrack_count} revisions. Exercise caution.",
        }

    # Check if we have strategy to audit
    if not state.strategy_draft:
        error_step = ReasoningStep(
            timestamp=get_timestamp(),
            node=NodeType.AUDITOR,
            thought="No strategy to audit. Cannot proceed.",
            action="Error - missing strategy draft"
        )
        reasoning_trace.append(error_step)
        return {
            "active_node": NodeType.IDLE,
            "reasoning_trace": reasoning_trace,
            "risk_score": 1.0,  # Max risk due to missing strategy
            "final_recommendation": "No strategy available for recommendation.",
        }

    # Load Kelly Criterion skill
    kelly_skill = load_kelly_skill()

    skill_step = ReasoningStep(
        timestamp=get_timestamp(),
        node=NodeType.AUDITOR,
        thought="Loaded Kelly Criterion skill for risk evaluation",
        action="Applying risk assessment framework"
    )
    reasoning_trace.append(skill_step)

    # Build audit context
    strategy = state.strategy_draft
    audit_context = f"""
## Strategy Under Review
- **Recommendation**: {strategy.recommended_horse}
- **Confidence Score**: {strategy.confidence_score:.2%}
- **Kelly Fraction**: {strategy.kelly_fraction if strategy.kelly_fraction else 'Not specified'}
- **Reasoning Summary**: {strategy.reasoning_summary}

## Scout Data Context
- **Racecourse**: {state.scout_data.racecourse if state.scout_data else 'Unknown'}
- **Track Condition**: {state.scout_data.track_condition if state.scout_data else 'Unknown'}
- **Weather**: {state.scout_data.weather if state.scout_data else 'Unknown'}

## Kelly Criterion Guidelines
{kelly_skill}
"""

    # Initialize Gemini client
    client = genai.Client()

    # System prompt for risk assessment
    system_prompt = """You are an Auditor agent responsible for risk assessment.
Your role is to evaluate betting strategies using the Kelly Criterion and risk management principles.

Evaluate the strategy and return:
1. A risk score from 0.0 (very safe) to 1.0 (very risky)
2. Whether to APPROVE or BACKTRACK (request revision)
3. Specific concerns if any

BACKTRACK if:
- Kelly fraction exceeds 25%
- Confidence score is below 50% but Kelly fraction is high
- Risk score exceeds 0.7
- Critical information is missing

Be conservative - it's better to revise a risky strategy than to approve a bad one."""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                types.Content(
                    role="user",
                    parts=[types.Part(text=f"""{system_prompt}

{audit_context}

Please evaluate this strategy and provide your risk assessment.""")]
                )
            ]
        )

        response_text = ""
        for candidate in response.candidates:
            for part in candidate.content.parts:
                if hasattr(part, 'text') and part.text:
                    response_text = part.text

        # Log the audit analysis
        audit_analysis_step = ReasoningStep(
            timestamp=get_timestamp(),
            node=NodeType.AUDITOR,
            thought=response_text[:500] if response_text else "Audit analysis complete",
            action="Risk evaluation performed"
        )
        reasoning_trace.append(audit_analysis_step)

        # Calculate risk score based on strategy parameters and audit response
        risk_score = 0.3  # Base risk

        # Factor in confidence (lower confidence = higher risk)
        if strategy.confidence_score < 0.5:
            risk_score += 0.3
        elif strategy.confidence_score < 0.7:
            risk_score += 0.15

        # Factor in Kelly fraction (higher Kelly = higher risk)
        if strategy.kelly_fraction:
            if strategy.kelly_fraction > 0.20:
                risk_score += 0.3
            elif strategy.kelly_fraction > 0.15:
                risk_score += 0.2
            elif strategy.kelly_fraction > 0.10:
                risk_score += 0.1

        # Factor in response sentiment
        response_lower = response_text.lower()
        if "backtrack" in response_lower or "reject" in response_lower or "high risk" in response_lower:
            risk_score += 0.2
        if "approve" in response_lower or "acceptable" in response_lower:
            risk_score -= 0.1

        # Clamp risk score
        risk_score = max(0.0, min(1.0, risk_score))

        # Log calculated risk
        risk_step = ReasoningStep(
            timestamp=get_timestamp(),
            node=NodeType.AUDITOR,
            thought=f"Calculated risk score: {risk_score:.2%}",
            action=f"Risk threshold check: {'EXCEEDS' if risk_score > 0.7 else 'WITHIN'} limits"
        )
        reasoning_trace.append(risk_step)

    except Exception as e:
        error_step = ReasoningStep(
            timestamp=get_timestamp(),
            node=NodeType.AUDITOR,
            thought=f"Error during audit: {str(e)}",
            action="Using conservative risk estimate"
        )
        reasoning_trace.append(error_step)
        risk_score = 0.6  # Conservative fallback

    # Decision: Approve or Backtrack
    if risk_score > 0.7:
        # BACKTRACK to Strategist
        backtrack_step = ReasoningStep(
            timestamp=get_timestamp(),
            node=NodeType.AUDITOR,
            thought=f"Risk score {risk_score:.2%} exceeds threshold (70%). Requesting strategy revision.",
            action="BACKTRACK to Strategist"
        )
        reasoning_trace.append(backtrack_step)

        # Use LangGraph Command for conditional routing
        return Command(
            update={
                "active_node": NodeType.STRATEGIST,
                "reasoning_trace": reasoning_trace,
                "risk_score": risk_score,
                "requires_backtrack": True,
                "backtrack_reason": f"Risk score {risk_score:.2%} exceeds acceptable threshold",
                "backtrack_count": current_backtrack_count + 1,
            },
            goto="strategist"
        )

    # APPROVE - complete the workflow
    approval_step = ReasoningStep(
        timestamp=get_timestamp(),
        node=NodeType.AUDITOR,
        thought=f"Strategy approved with risk score {risk_score:.2%}. Within acceptable limits.",
        action="Audit complete - strategy approved"
    )
    reasoning_trace.append(approval_step)

    # Generate final recommendation
    final_rec = f"""
## Keiba Oracle Recommendation

**Strategy**: {strategy.recommended_horse}
**Confidence**: {strategy.confidence_score:.0%}
**Risk Score**: {risk_score:.0%}
**Suggested Position Size**: {(strategy.kelly_fraction or 0.05) * 100:.1f}% of bankroll

**Summary**: {strategy.reasoning_summary}

**Racecourse**: {state.scout_data.racecourse if state.scout_data else 'Unknown'}
**Conditions**: {state.scout_data.track_condition if state.scout_data else 'Unknown'} / {state.scout_data.weather if state.scout_data else 'Unknown'}

---
*This recommendation is for educational purposes. Always gamble responsibly.*
""".strip()

    return {
        "active_node": NodeType.IDLE,
        "reasoning_trace": reasoning_trace,
        "risk_score": risk_score,
        "requires_backtrack": False,
        "backtrack_reason": None,
        "final_recommendation": final_rec,
    }
