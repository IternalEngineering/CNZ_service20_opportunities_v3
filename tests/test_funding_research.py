"""Test script for funding research agent."""

import asyncio
from funding_researcher.graph import graph
from funding_researcher.state import ResearchState


async def test_solar_farm_funding():
    """Test finding funding for a solar farm project in Scotland."""
    initial_state: ResearchState = {
        "messages": [],
        "project_description": (
            "Large-scale solar farm project to provide renewable energy to 5,000 homes. "
            "The project includes 50MW capacity with battery storage, community benefit sharing, "
            "and biodiversity enhancement measures. Total project cost: £40M."
        ),
        "project_location": "Scotland, UK",
        "project_sectors": ["Energy", "Sustainability", "Infrastructure"],
        "funding_types": ["grant", "loan", "equity", "tax incentive"],
        "current_level": "regional",
        "regional_funders": [],
        "national_funders": [],
        "global_funders": [],
        "search_queries": [],
        "search_results": [],
        "final_report": "",
        "total_funders_found": 0,
    }

    print("Starting funding research for solar farm project...")
    print(f"Project: {initial_state['project_description'][:100]}...")
    print(f"Location: {initial_state['project_location']}")
    print(f"Sectors: {', '.join(initial_state['project_sectors'])}")
    print("\n" + "=" * 80 + "\n")

    config = {
        "configurable": {
            "model_provider": "openai",
            "model_name": "gpt-4o-mini",
            "search_api": "tavily",
        }
    }

    result = await graph.ainvoke(initial_state, config)

    print("\n" + "=" * 80)
    print("RESEARCH COMPLETE")
    print("=" * 80 + "\n")
    print(f"Total funders found: {result['total_funders_found']}")
    print(f"- Regional: {len(result['regional_funders'])}")
    print(f"- National: {len(result['national_funders'])}")
    print(f"- Global: {len(result['global_funders'])}")
    print("\n" + "=" * 80)
    print("FINAL REPORT")
    print("=" * 80 + "\n")
    print(result["final_report"])


async def test_ev_charging_funding():
    """Test finding funding for an EV charging network project."""
    initial_state: ResearchState = {
        "messages": [],
        "project_description": (
            "Electric vehicle charging network deployment across urban areas. "
            "Plan to install 500 fast-charging stations with renewable energy integration. "
            "Focus on underserved communities and multi-unit dwellings. Total cost: £15M."
        ),
        "project_location": "London, UK",
        "project_sectors": ["Transport", "Energy", "Infrastructure", "Sustainability"],
        "funding_types": ["grant", "loan", "equity"],
        "current_level": "regional",
        "regional_funders": [],
        "national_funders": [],
        "global_funders": [],
        "search_queries": [],
        "search_results": [],
        "final_report": "",
        "total_funders_found": 0,
    }

    print("Starting funding research for EV charging network...")
    print(f"Project: {initial_state['project_description'][:100]}...")
    print(f"Location: {initial_state['project_location']}")
    print(f"Sectors: {', '.join(initial_state['project_sectors'])}")
    print("\n" + "=" * 80 + "\n")

    config = {
        "configurable": {
            "model_provider": "openai",
            "model_name": "gpt-4o-mini",
            "search_api": "duckduckgo",  # Test with different search API
        }
    }

    result = await graph.ainvoke(initial_state, config)

    print("\n" + "=" * 80)
    print("RESEARCH COMPLETE")
    print("=" * 80 + "\n")
    print(f"Total funders found: {result['total_funders_found']}")
    print(f"- Regional: {len(result['regional_funders'])}")
    print(f"- National: {len(result['national_funders'])}")
    print(f"- Global: {len(result['global_funders'])}")
    print("\n" + "=" * 80)
    print("FINAL REPORT")
    print("=" * 80 + "\n")
    print(result["final_report"])


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "ev":
        asyncio.run(test_ev_charging_funding())
    else:
        asyncio.run(test_solar_farm_funding())
