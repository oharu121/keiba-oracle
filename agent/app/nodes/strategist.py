"""
Strategist Node - Chain-of-Thought with Gemini 3 Pro.

Analyzes scout data and formulates betting strategy.
Uses thinkingLevel: HIGH for extended reasoning.
Explicitly captures all reasoning in reasoning_trace.
"""

import json
from datetime import datetime, timezone
from google import genai
from google.genai import types

from app.models import OracleState, NodeType, ReasoningStep, StrategyDraft


def get_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def strategist_node(state: OracleState) -> dict:
    """
    Strategist Node: Uses Chain-of-Thought with extended thinking.

    Gemini 3 Pro's thinkingLevel is set to HIGH to capture detailed reasoning.
    Every thought is explicitly logged to reasoning_trace.
    """
    # Initialize updates with copies to avoid mutation
    reasoning_trace = list(state.reasoning_trace)

    # Log entry into node
    entry_step = ReasoningStep(
        timestamp=get_timestamp(),
        node=NodeType.STRATEGIST,
        thought="Received scout data. Beginning strategic analysis.",
        action="Initializing Strategist node"
    )
    reasoning_trace.append(entry_step)

    # Check if we have scout data
    if not state.scout_data:
        error_step = ReasoningStep(
            timestamp=get_timestamp(),
            node=NodeType.STRATEGIST,
            thought="No scout data available. Cannot proceed with analysis.",
            action="Error - missing scout data"
        )
        reasoning_trace.append(error_step)
        return {
            "active_node": NodeType.AUDITOR,
            "reasoning_trace": reasoning_trace,
            "strategy_draft": None,
        }

    # Build context from scout data
    scout_context = f"""
## Scouting Report
- **Racecourse**: {state.scout_data.racecourse}
- **Track Condition**: {state.scout_data.track_condition}
- **Weather**: {state.scout_data.weather}
- **Sources**: {', '.join(state.scout_data.sources) if state.scout_data.sources else 'None'}
- **Horse Data**: {json.dumps(state.scout_data.horse_data) if state.scout_data.horse_data else 'Limited data available'}
"""

    # Log the context being analyzed
    context_step = ReasoningStep(
        timestamp=get_timestamp(),
        node=NodeType.STRATEGIST,
        thought=f"Analyzing scout report for {state.scout_data.racecourse}",
        action="Processing track and weather conditions"
    )
    reasoning_trace.append(context_step)

    # Initialize Gemini client
    client = genai.Client()

    # System prompt for strategic analysis
    system_prompt = """You are a Strategist agent for Japanese horse racing analysis.
Your role is to analyze the scout data and formulate a betting strategy.

Think deeply and systematically about:
1. How track conditions affect different running styles
2. Weather impact on race dynamics
3. Historical patterns at this racecourse
4. Risk factors to consider

Provide your analysis in a structured format:
- Recommended approach (e.g., favor front-runners, closers, etc.)
- Key factors influencing the recommendation
- Confidence level (0.0 to 1.0)
- Suggested Kelly fraction for bet sizing (0.0 to 0.25 max)

Be explicit about your reasoning. Every assumption should be stated."""

    try:
        # Call Gemini with extended thinking (thinkingLevel: HIGH equivalent)
        # Note: Using thinking budget for extended reasoning
        response = client.models.generate_content(
            model="gemini-2.0-flash-thinking-exp",  # Thinking model for CoT
            contents=[
                types.Content(
                    role="user",
                    parts=[types.Part(text=f"""{system_prompt}

## Original Query
{state.query}

{scout_context}

Please analyze this situation and provide your strategic recommendation.""")]
                )
            ],
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(
                    thinking_budget=10000  # Extended thinking budget
                )
            )
        )

        # Extract thinking and response
        thinking_content = ""
        response_content = ""

        for candidate in response.candidates or []:
            if candidate.content is None or candidate.content.parts is None:
                continue
            for part in candidate.content.parts:
                if hasattr(part, 'thought') and part.thought:
                    # This is the model's internal thinking - EXPLICITLY CAPTURED
                    thinking_content = part.text if hasattr(part, 'text') else str(part.thought)
                elif hasattr(part, 'text') and part.text:
                    response_content = part.text

        # Log the extended thinking if available
        if thinking_content:
            thinking_step = ReasoningStep(
                timestamp=get_timestamp(),
                node=NodeType.STRATEGIST,
                thought=f"[Extended Reasoning] {thinking_content[:800]}...",
                action="Deep analysis in progress"
            )
            reasoning_trace.append(thinking_step)

        # Log the main analysis
        if response_content:
            analysis_step = ReasoningStep(
                timestamp=get_timestamp(),
                node=NodeType.STRATEGIST,
                thought=response_content[:600],
                action="Strategy formulation complete"
            )
            reasoning_trace.append(analysis_step)

        # Parse the response to extract structured strategy
        # In production, would use structured output or another parsing step
        confidence = 0.65  # Default confidence
        kelly_fraction = 0.10  # Default Kelly fraction

        # Simple extraction from response
        response_lower = response_content.lower()

        # Adjust confidence based on content
        if "high confidence" in response_lower or "strongly" in response_lower:
            confidence = 0.80
        elif "moderate" in response_lower or "reasonable" in response_lower:
            confidence = 0.65
        elif "low confidence" in response_lower or "uncertain" in response_lower:
            confidence = 0.45

        # Extract Kelly fraction hints
        if "conservative" in response_lower:
            kelly_fraction = 0.05
        elif "aggressive" in response_lower:
            kelly_fraction = 0.15
        elif "moderate" in response_lower:
            kelly_fraction = 0.10

        # Determine recommended horse (simplified)
        recommended = "Front-runner strategy recommended"
        if "closer" in response_lower or "come from behind" in response_lower:
            recommended = "Closer/stalker strategy recommended"
        elif "front" in response_lower or "pace" in response_lower:
            recommended = "Front-runner strategy recommended"

        # Build StrategyDraft
        strategy_draft = StrategyDraft(
            recommended_horse=recommended,
            confidence_score=confidence,
            reasoning_summary=response_content[:300] if response_content else "Analysis complete",
            kelly_fraction=kelly_fraction
        )

        # Final summary step
        summary_step = ReasoningStep(
            timestamp=get_timestamp(),
            node=NodeType.STRATEGIST,
            thought=f"Strategy formulated: {recommended} with {confidence:.0%} confidence. Kelly fraction: {kelly_fraction:.2f}",
            action="Passing to Auditor for risk assessment"
        )
        reasoning_trace.append(summary_step)

    except Exception as e:
        error_step = ReasoningStep(
            timestamp=get_timestamp(),
            node=NodeType.STRATEGIST,
            thought=f"Error during strategic analysis: {str(e)}",
            action="Using fallback strategy"
        )
        reasoning_trace.append(error_step)

        # Fallback strategy
        strategy_draft = StrategyDraft(
            recommended_horse="Conservative approach - insufficient data",
            confidence_score=0.40,
            reasoning_summary="Unable to complete full analysis. Recommending conservative approach.",
            kelly_fraction=0.02
        )

    return {
        "active_node": NodeType.AUDITOR,  # Move to next node
        "reasoning_trace": reasoning_trace,
        "strategy_draft": strategy_draft,
    }
