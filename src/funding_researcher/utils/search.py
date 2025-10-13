"""Search utilities for finding funding opportunities."""

from __future__ import annotations

import asyncio
from typing import Any

from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.utilities.duckduckgo_search import DuckDuckGoSearchAPIWrapper


async def search_with_tavily(
    queries: list[str],
    api_key: str,
    max_results: int = 10,
    max_concurrent: int = 3,
) -> list[dict[str, Any]]:
    """
    Perform parallel searches using Tavily API.

    Args:
        queries: List of search queries to execute
        api_key: Tavily API key
        max_results: Maximum results per query
        max_concurrent: Maximum concurrent searches

    Returns:
        List of search result dictionaries
    """
    tool = TavilySearchResults(
        api_key=api_key,
        max_results=max_results,
        search_depth="advanced",
        include_answer=True,
        include_raw_content=False,
        include_images=False,
    )

    semaphore = asyncio.Semaphore(max_concurrent)

    async def search_one(query: str) -> list[dict]:
        async with semaphore:
            try:
                results = await asyncio.to_thread(tool.invoke, {"query": query})
                if isinstance(results, list):
                    return results
                return []
            except Exception as e:
                print(f"Search error for query '{query}': {e}")
                return []

    tasks = [search_one(q) for q in queries]
    results = await asyncio.gather(*tasks)

    # Flatten results
    all_results = []
    for result_list in results:
        all_results.extend(result_list)

    return all_results


async def search_with_duckduckgo(
    queries: list[str],
    max_results: int = 10,
    max_concurrent: int = 3,
) -> list[dict[str, Any]]:
    """
    Perform parallel searches using DuckDuckGo.

    Args:
        queries: List of search queries to execute
        max_results: Maximum results per query
        max_concurrent: Maximum concurrent searches

    Returns:
        List of search result dictionaries
    """
    search = DuckDuckGoSearchAPIWrapper(max_results=max_results)

    semaphore = asyncio.Semaphore(max_concurrent)

    async def search_one(query: str) -> list[dict]:
        async with semaphore:
            try:
                results = await asyncio.to_thread(search.results, query, max_results)
                return results if results else []
            except Exception as e:
                print(f"Search error for query '{query}': {e}")
                return []

    tasks = [search_one(q) for q in queries]
    results = await asyncio.gather(*tasks)

    # Flatten and normalize results
    all_results = []
    for result_list in results:
        for result in result_list:
            # Normalize DuckDuckGo results to match Tavily format
            all_results.append({
                "url": result.get("link", ""),
                "content": result.get("snippet", ""),
                "title": result.get("title", ""),
            })

    return all_results


async def search_with_exa(
    queries: list[str],
    api_key: str,
    max_results: int = 10,
    max_concurrent: int = 3,
) -> list[dict[str, Any]]:
    """
    Perform parallel searches using Exa API.

    Args:
        queries: List of search queries to execute
        api_key: Exa API key
        max_results: Maximum results per query
        max_concurrent: Maximum concurrent searches

    Returns:
        List of search result dictionaries
    """
    try:
        from exa_py import Exa
    except ImportError:
        raise ImportError("exa_py is required for Exa search. Install with: pip install exa-py")

    client = Exa(api_key=api_key)
    semaphore = asyncio.Semaphore(max_concurrent)

    async def search_one(query: str) -> list[dict]:
        async with semaphore:
            try:
                results = await asyncio.to_thread(
                    client.search_and_contents,
                    query,
                    num_results=max_results,
                    text=True,
                )
                # Normalize Exa results
                return [
                    {
                        "url": result.url,
                        "content": result.text or "",
                        "title": result.title or "",
                    }
                    for result in results.results
                ]
            except Exception as e:
                print(f"Search error for query '{query}': {e}")
                return []

    tasks = [search_one(q) for q in queries]
    results = await asyncio.gather(*tasks)

    # Flatten results
    all_results = []
    for result_list in results:
        all_results.extend(result_list)

    return all_results


def format_search_results_for_extraction(results: list[dict[str, Any]]) -> str:
    """
    Format search results into a readable string for LLM extraction.

    Args:
        results: List of search result dictionaries

    Returns:
        Formatted string of search results
    """
    if not results:
        return "No search results found."

    formatted = []
    for i, result in enumerate(results, 1):
        title = result.get("title", "No title")
        url = result.get("url", "No URL")
        content = result.get("content", "No content")

        formatted.append(f"""
---
Result {i}:
Title: {title}
URL: {url}
Content: {content[:1000]}{'...' if len(content) > 1000 else ''}
---
""")

    return "\n".join(formatted)
