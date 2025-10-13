"""Main LangGraph implementation for funding research agent."""

from __future__ import annotations

import asyncio
import json
from typing import cast

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END

from funding_researcher.configuration import Configuration
from funding_researcher.state import ResearchState, FunderMetadata
from funding_researcher.prompts import (
    QUERY_GENERATOR_PROMPT,
    FUNDER_EXTRACTOR_PROMPT,
    REPORT_GENERATOR_PROMPT,
)
from funding_researcher.utils.search import (
    search_with_tavily,
    search_with_duckduckgo,
    search_with_exa,
    format_search_results_for_extraction,
)


async def initialize_research(
    state: ResearchState,
    config: RunnableConfig,
) -> dict:
    """Initialize the research process and set starting state."""
    configuration = Configuration.from_runnable_config(config)

    return {
        "current_level": "regional",
        "regional_funders": [],
        "national_funders": [],
        "global_funders": [],
        "search_queries": [],
        "search_results": [],
        "total_funders_found": 0,
        "messages": [
            SystemMessage(
                content="Starting funding research for Net Zero project. "
                f"Will search regional, national, and global funding opportunities."
            )
        ],
    }


async def generate_search_queries(
    state: ResearchState,
    config: RunnableConfig,
) -> dict:
    """Generate targeted search queries for the current research level."""
    configuration = Configuration.from_runnable_config(config)
    llm = configuration.get_model()

    level = state["current_level"]
    if level == "completed":
        return {}

    prompt = QUERY_GENERATOR_PROMPT.format(
        project_description=state["project_description"],
        project_location=state["project_location"],
        project_sectors=", ".join(state["project_sectors"]),
        funding_types=", ".join(state["funding_types"]),
        level=level,
    )

    response = await llm.ainvoke([HumanMessage(content=prompt)])

    try:
        queries = json.loads(response.content)
        if not isinstance(queries, list):
            queries = []
    except json.JSONDecodeError:
        # Fallback if LLM doesn't return valid JSON
        queries = [
            f"{level} net zero funding {state['project_location']}",
            f"{level} sustainability grants {state['project_location']}",
            f"{level} green energy investment {' '.join(state['project_sectors'])}",
        ]

    return {
        "search_queries": queries,
        "messages": [
            SystemMessage(
                content=f"Generated {len(queries)} search queries for {level} funding opportunities."
            )
        ],
    }


async def execute_searches(
    state: ResearchState,
    config: RunnableConfig,
) -> dict:
    """Execute parallel web searches using configured search API."""
    configuration = Configuration.from_runnable_config(config)

    queries = state["search_queries"]
    if not queries:
        return {"search_results": []}

    # Choose search method based on configuration
    search_api_value = configuration.search_api.value if hasattr(configuration.search_api, 'value') else configuration.search_api

    if search_api_value == "tavily" and configuration.tavily_api_key:
        results = await search_with_tavily(
            queries,
            configuration.tavily_api_key,
            configuration.max_results_per_query,
            configuration.max_concurrent_searches,
        )
    elif search_api_value == "exa" and configuration.exa_api_key:
        results = await search_with_exa(
            queries,
            configuration.exa_api_key,
            configuration.max_results_per_query,
            configuration.max_concurrent_searches,
        )
    else:
        # Fallback to DuckDuckGo (no API key required)
        results = await search_with_duckduckgo(
            queries,
            configuration.max_results_per_query,
            configuration.max_concurrent_searches,
        )

    return {
        "search_results": results,
        "messages": [
            SystemMessage(
                content=f"Executed {len(queries)} searches and retrieved {len(results)} results."
            )
        ],
    }


async def extract_funders(
    state: ResearchState,
    config: RunnableConfig,
) -> dict:
    """Extract structured funder information from search results."""
    configuration = Configuration.from_runnable_config(config)
    llm = configuration.get_model()

    level = state["current_level"]
    if level == "completed":
        return {}

    # Format search results for extraction
    formatted_results = format_search_results_for_extraction(state["search_results"])

    prompt = FUNDER_EXTRACTOR_PROMPT.format(
        project_description=state["project_description"],
        project_location=state["project_location"],
        project_sectors=", ".join(state["project_sectors"]),
        funding_types=", ".join(state["funding_types"]),
        level=level,
        search_results=formatted_results,
    )

    response = await llm.ainvoke([HumanMessage(content=prompt)])

    try:
        funders_data = json.loads(response.content)
        if not isinstance(funders_data, list):
            funders_data = []

        # Convert to FunderMetadata objects
        funders = [FunderMetadata(**funder) for funder in funders_data]
    except (json.JSONDecodeError, Exception) as e:
        print(f"Error extracting funders: {e}")
        funders = []

    # Store in appropriate level
    if level == "regional":
        return {
            "regional_funders": funders,
            "messages": [
                SystemMessage(
                    content=f"Extracted {len(funders)} regional funding opportunities."
                )
            ],
        }
    elif level == "national":
        return {
            "national_funders": funders,
            "messages": [
                SystemMessage(
                    content=f"Extracted {len(funders)} national funding opportunities."
                )
            ],
        }
    elif level == "global":
        return {
            "global_funders": funders,
            "messages": [
                SystemMessage(
                    content=f"Extracted {len(funders)} global funding opportunities."
                )
            ],
        }

    return {}


async def advance_research_level(
    state: ResearchState,
    config: RunnableConfig,
) -> dict:
    """Move to the next research level or complete the research."""
    current = state["current_level"]

    if current == "regional":
        next_level = "national"
    elif current == "national":
        next_level = "global"
    else:
        next_level = "completed"

    return {
        "current_level": next_level,
        "search_queries": [],  # Reset for next level
        "search_results": [],
        "messages": [
            SystemMessage(
                content=f"Advancing from {current} to {next_level} research level."
            )
        ],
    }


async def generate_final_report(
    state: ResearchState,
    config: RunnableConfig,
) -> dict:
    """Generate comprehensive funding research report."""
    configuration = Configuration.from_runnable_config(config)
    llm = configuration.get_model()

    # Format funders for report
    def format_funder_list(funders: list[FunderMetadata]) -> str:
        if not funders:
            return "No funding opportunities found at this level."

        formatted = []
        for i, funder in enumerate(funders, 1):
            formatted.append(f"""
{i}. **{funder.name}**
   - Organization: {funder.organization}
   - Type: {funder.opportunity_type}
   - Award: {funder.award_range}
   - Location: {funder.location}
   - Sectors: {', '.join(funder.sectors)}
   - Registration: {funder.registration_details}
   - Eligibility: {funder.eligibility}
   - Website: {funder.website}
   - Contact: {funder.contact_info}
   - Source: {funder.source_url}
""")
        return "\n".join(formatted)

    regional_funders = state.get("regional_funders", [])
    national_funders = state.get("national_funders", [])
    global_funders = state.get("global_funders", [])

    prompt = REPORT_GENERATOR_PROMPT.format(
        project_description=state["project_description"],
        project_location=state["project_location"],
        project_sectors=", ".join(state["project_sectors"]),
        funding_types=", ".join(state["funding_types"]),
        regional_count=len(regional_funders),
        regional_funders=format_funder_list(regional_funders),
        national_count=len(national_funders),
        national_funders=format_funder_list(national_funders),
        global_count=len(global_funders),
        global_funders=format_funder_list(global_funders),
    )

    response = await llm.ainvoke([HumanMessage(content=prompt)])

    total_funders = len(regional_funders) + len(national_funders) + len(global_funders)

    return {
        "final_report": response.content,
        "total_funders_found": total_funders,
        "messages": [
            SystemMessage(
                content=f"Generated final report with {total_funders} total funding opportunities."
            )
        ],
    }


def should_continue_research(state: ResearchState) -> str:
    """Determine if research should continue or generate final report."""
    if state["current_level"] == "completed":
        return "generate_report"
    return "continue"


# Build the graph
workflow = StateGraph(ResearchState, config_schema=Configuration)

# Add nodes
workflow.add_node("initialize", initialize_research)
workflow.add_node("generate_queries", generate_search_queries)
workflow.add_node("execute_searches", execute_searches)
workflow.add_node("extract_funders", extract_funders)
workflow.add_node("advance_level", advance_research_level)
workflow.add_node("generate_report", generate_final_report)

# Define edges
workflow.set_entry_point("initialize")
workflow.add_edge("initialize", "generate_queries")
workflow.add_edge("generate_queries", "execute_searches")
workflow.add_edge("execute_searches", "extract_funders")
workflow.add_edge("extract_funders", "advance_level")

# Conditional edge after advancing level
workflow.add_conditional_edges(
    "advance_level",
    should_continue_research,
    {
        "continue": "generate_queries",
        "generate_report": "generate_report",
    },
)

workflow.add_edge("generate_report", END)

# Compile the graph
graph = workflow.compile()
