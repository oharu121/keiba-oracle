"""
Scout Node - ReAct Pattern with Gemini 3 Pro.

Gathers information about racecourse conditions using search tools.
Explicitly logs every thought, action, and observation to reasoning_trace.
"""

import json
from datetime import datetime, timezone
from google import genai
from google.genai import types

from app.models import OracleState, NodeType, ReasoningStep, ScoutData, ToolCall
from app.tools import search_racecourse_conditions, search_horse_info


def get_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def scout_node(state: OracleState) -> dict:
    """
    Scout Node: Uses ReAct pattern with Gemini 3 Pro.

    Explicitly logs every thought, action, and observation.
    No black box helpers - everything is transparent.
    """
    # Initialize updates with copies to avoid mutation
    reasoning_trace = list(state.reasoning_trace)
    tool_calls = list(state.tool_calls)

    # Log entry into node
    entry_step = ReasoningStep(
        timestamp=get_timestamp(),
        node=NodeType.SCOUT,
        thought=f"Starting information gathering for query: {state.query}",
        action="Initializing Scout node"
    )
    reasoning_trace.append(entry_step)

    # Initialize Gemini client
    client = genai.Client()

    # Define available tools for ReAct
    tools_schema = [
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="search_racecourse_conditions",
                    description="Search for Japanese racecourse conditions, weather, and track info",
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "query": types.Schema(
                                type=types.Type.STRING,
                                description="Search query about racecourse conditions"
                            )
                        },
                        required=["query"]
                    )
                ),
                types.FunctionDeclaration(
                    name="search_horse_info",
                    description="Search for specific horse information and racing history",
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "horse_name": types.Schema(
                                type=types.Type.STRING,
                                description="Name of the horse to search for"
                            )
                        },
                        required=["horse_name"]
                    )
                )
            ]
        )
    ]

    # ReAct prompt for the Scout
    system_prompt = """You are a Scout agent for Japanese horse racing analysis.
Your role is to gather information about racecourse conditions, weather, and horse data.

Use the available tools to search for information. Think step-by-step:
1. Analyze what information is needed based on the query
2. Use search tools to gather relevant data
3. Summarize your findings

Be thorough but efficient. Focus on:
- Current track conditions (turf/dirt, firmness)
- Weather conditions
- Recent race results at the venue
- Key horses mentioned in the query"""

    # Initial ReAct call to Gemini
    thinking_step = ReasoningStep(
        timestamp=get_timestamp(),
        node=NodeType.SCOUT,
        thought="Analyzing query to determine what searches are needed",
        action="Calling Gemini 3 Pro for initial analysis"
    )
    reasoning_trace.append(thinking_step)

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                types.Content(
                    role="user",
                    parts=[types.Part(text=f"{system_prompt}\n\nQuery: {state.query}")]
                )
            ],
            config=types.GenerateContentConfig(
                tools=tools_schema,
                tool_config=types.ToolConfig(
                    function_calling_config=types.FunctionCallingConfig(
                        mode=types.FunctionCallingConfigMode.AUTO
                    )
                )
            )
        )

        # Process response and handle tool calls
        search_results = []
        racecourse = "Unknown"
        track_condition = "Unknown"
        weather = "Unknown"
        sources = []

        for candidate in response.candidates:
            for part in candidate.content.parts:
                # Handle text response (thinking)
                if hasattr(part, 'text') and part.text:
                    thought_step = ReasoningStep(
                        timestamp=get_timestamp(),
                        node=NodeType.SCOUT,
                        thought=part.text[:500]  # Truncate for state
                    )
                    reasoning_trace.append(thought_step)

                # Handle function calls
                if hasattr(part, 'function_call') and part.function_call:
                    func_call = part.function_call
                    func_name = func_call.name
                    func_args = dict(func_call.args) if func_call.args else {}

                    # Log tool call
                    tool_call = ToolCall(
                        timestamp=get_timestamp(),
                        tool=func_name,
                        args=func_args,
                        node=NodeType.SCOUT.value
                    )
                    tool_calls.append(tool_call)

                    # Execute the tool
                    action_step = ReasoningStep(
                        timestamp=get_timestamp(),
                        node=NodeType.SCOUT,
                        thought=f"Executing tool: {func_name}",
                        action=f"Tool call: {func_name}({json.dumps(func_args)})"
                    )
                    reasoning_trace.append(action_step)

                    # Run the actual tool
                    if func_name == "search_racecourse_conditions":
                        result = search_racecourse_conditions.invoke(func_args.get("query", state.query))
                    elif func_name == "search_horse_info":
                        result = search_horse_info.invoke(func_args.get("horse_name", ""))
                    else:
                        result = "Unknown tool"

                    search_results.append(result)

                    # Log observation
                    observation_step = ReasoningStep(
                        timestamp=get_timestamp(),
                        node=NodeType.SCOUT,
                        thought="Received search results",
                        action=f"Processed {func_name}",
                        observation=result[:300] if result else "No results"
                    )
                    reasoning_trace.append(observation_step)

                    # Extract source URLs from results
                    if "Source:" in result:
                        for line in result.split("\n"):
                            if line.startswith("Source:"):
                                sources.append(line.replace("Source:", "").strip())

        # Parse results to extract structured data
        # This is a simplified extraction - in production, use another LLM call
        combined_results = "\n".join(search_results)

        # Try to identify racecourse from query
        racecourses = ["Tokyo", "Nakayama", "Kyoto", "Hanshin", "Chukyo", "Kokura", "Niigata", "Fukushima", "Sapporo", "Hakodate"]
        for rc in racecourses:
            if rc.lower() in state.query.lower() or rc.lower() in combined_results.lower():
                racecourse = f"{rc} Racecourse"
                break

        # Simple condition extraction (would be more sophisticated in production)
        if "good" in combined_results.lower() or "firm" in combined_results.lower():
            track_condition = "Good"
        elif "soft" in combined_results.lower() or "yielding" in combined_results.lower():
            track_condition = "Soft"
        elif "heavy" in combined_results.lower():
            track_condition = "Heavy"

        if "clear" in combined_results.lower() or "sunny" in combined_results.lower():
            weather = "Clear"
        elif "rain" in combined_results.lower():
            weather = "Rainy"
        elif "cloudy" in combined_results.lower():
            weather = "Cloudy"

        # Build ScoutData
        scout_data = ScoutData(
            racecourse=racecourse,
            track_condition=track_condition,
            weather=weather,
            horse_data=[],  # Would be populated with structured horse info
            sources=sources[:5]  # Limit to 5 sources
        )

        # Final summary step
        summary_step = ReasoningStep(
            timestamp=get_timestamp(),
            node=NodeType.SCOUT,
            thought=f"Completed scouting. Found: {racecourse}, {track_condition} track, {weather} weather. {len(sources)} sources collected.",
            action="Scout phase complete - handing off to Strategist"
        )
        reasoning_trace.append(summary_step)

    except Exception as e:
        error_step = ReasoningStep(
            timestamp=get_timestamp(),
            node=NodeType.SCOUT,
            thought=f"Error during scouting: {str(e)}",
            action="Error recovery - using default data"
        )
        reasoning_trace.append(error_step)

        # Fallback ScoutData
        scout_data = ScoutData(
            racecourse="Unknown Racecourse",
            track_condition="Unknown",
            weather="Unknown",
            horse_data=[],
            sources=[]
        )

    return {
        "active_node": NodeType.STRATEGIST,  # Move to next node
        "reasoning_trace": reasoning_trace,
        "tool_calls": tool_calls,
        "scout_data": scout_data,
    }
