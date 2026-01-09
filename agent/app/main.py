"""
FastAPI Entry Point for Keiba Oracle Agent.

Exposes the LangGraph via CopilotKit's AG-UI protocol.
"""

import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, PlainTextResponse
from copilotkit.integrations.fastapi import add_fastapi_endpoint
from copilotkit import CopilotKitSDK, LangGraphAGUIAgent

from app.graph import graph
from app.models import OracleState


# Patch for CopilotKit bug #2891: Missing dict_repr method
# See: https://github.com/CopilotKit/CopilotKit/issues/2891
class PatchedLangGraphAGUIAgent(LangGraphAGUIAgent):
    """Patched agent class that adds missing dict_repr method."""

    def dict_repr(self):
        """Return dictionary representation for CopilotKit /info endpoint."""
        return {
            "name": self.name,
            "description": self.description or "",
        }

# Load environment variables
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    print("Keiba Oracle Agent starting up...")
    print(f"Google API Key configured: {'Yes' if os.getenv('GOOGLE_API_KEY') else 'No'}")
    print(f"Tavily API Key configured: {'Yes' if os.getenv('TAVILY_API_KEY') else 'No'}")
    yield
    print("Keiba Oracle Agent shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Keiba Oracle Agent",
    description="Japanese Horse Racing Analysis Agent with Explicit Reasoning",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://127.0.0.1:3000",
        "https://keiba-oracle.vercel.app",  # Vercel production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create CopilotKit SDK with patched LangGraph agent
sdk = CopilotKitSDK(
    agents=[
        PatchedLangGraphAGUIAgent(
            name="keiba-oracle",
            description="Japanese Horse Racing Analysis Agent with Scout, Strategist, and Auditor nodes",
            graph=graph,
        )
    ]
)

# Add CopilotKit endpoint
add_fastapi_endpoint(app, sdk, "/copilotkit")


@app.get("/")
async def root():
    """Redirect to API documentation."""
    return RedirectResponse(url="/docs")


@app.get("/healthz")
async def healthz():
    """Lightweight liveness probe for keep-alive pings."""
    return PlainTextResponse("ok")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "agent": "keiba-oracle",
        "google_api_configured": bool(os.getenv("GOOGLE_API_KEY")),
        "tavily_api_configured": bool(os.getenv("TAVILY_API_KEY")),
    }


@app.post("/test")
async def test_agent(query: str = "What are the conditions at Tokyo Racecourse today?"):
    """
    Test endpoint to run the agent directly (bypassing CopilotKit).

    Useful for debugging and development.
    """
    initial_state = OracleState(query=query)

    try:
        # Run the graph
        result = await graph.ainvoke(
            initial_state.model_dump(),
            config={"configurable": {"thread_id": "test-thread"}}
        )

        return {
            "success": True,
            "query": query,
            "final_recommendation": result.get("final_recommendation"),
            "risk_score": result.get("risk_score"),
            "reasoning_steps": len(result.get("reasoning_trace", [])),
            "tool_calls": len(result.get("tool_calls", [])),
            "backtracks": result.get("backtrack_count", 0),
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "query": query,
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
