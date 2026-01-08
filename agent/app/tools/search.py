"""
Tavily Search Tool for Japanese Horse Racing Data.

Configured for Japanese racing sites (JRA, netkeiba).
"""

import os
from langchain_core.tools import tool
from tavily import TavilyClient


def get_tavily_client() -> TavilyClient:
    """Get Tavily client with API key from environment."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY environment variable not set")
    return TavilyClient(api_key=api_key)


@tool
def search_racecourse_conditions(query: str) -> str:
    """
    Search for Japanese racecourse conditions and horse racing data.

    Uses Tavily optimized for Japanese racing sites like JRA and netkeiba.
    Returns formatted search results with source URLs.

    Args:
        query: Search query about racecourse, weather, track conditions, or horse info.
               Examples: "Tokyo racecourse weather today", "horse Racing results Nakayama"

    Returns:
        Formatted search results with content and source URLs.
    """
    client = get_tavily_client()

    # Execute search with Japanese racing site preferences
    results = client.search(
        query=query,
        search_depth="advanced",
        max_results=5,
        include_domains=["jra.go.jp", "netkeiba.com", "keiba.go.jp", "racing.yahoo.co.jp"],
    )

    # Format results for agent consumption
    formatted_results = []
    for result in results.get("results", []):
        formatted_results.append(
            f"**{result.get('title', 'No title')}**\n"
            f"Source: {result.get('url', 'No URL')}\n"
            f"Content: {result.get('content', 'No content')[:500]}...\n"
        )

    if not formatted_results:
        return "No results found for the query."

    return "\n---\n".join(formatted_results)


@tool
def search_horse_info(horse_name: str) -> str:
    """
    Search for specific horse information and racing history.

    Args:
        horse_name: Name of the horse to search for (Japanese or English).

    Returns:
        Information about the horse including past performance.
    """
    client = get_tavily_client()

    results = client.search(
        query=f"{horse_name} horse racing Japan performance history",
        search_depth="advanced",
        max_results=3,
        include_domains=["netkeiba.com", "jra.go.jp"],
    )

    formatted_results = []
    for result in results.get("results", []):
        formatted_results.append(
            f"**{result.get('title', 'No title')}**\n"
            f"Source: {result.get('url', 'No URL')}\n"
            f"Content: {result.get('content', 'No content')[:500]}...\n"
        )

    if not formatted_results:
        return f"No information found for horse: {horse_name}"

    return "\n---\n".join(formatted_results)
