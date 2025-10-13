"""Example usage of the funding research agent."""

import asyncio
from funding_researcher.graph import graph
from funding_researcher.state import ResearchState


async def research_wind_farm_funding():
    """Example: Research funding for an offshore wind farm project."""

    # Define your project details
    initial_state: ResearchState = {
        "messages": [],
        "project_description": (
            "Offshore wind farm development with 100 turbines generating 500MW capacity. "
            "Project includes marine biodiversity protection, local supply chain development, "
            "and community investment program. Located 15km offshore. Total cost: £1.2B."
        ),
        "project_location": "North Sea, Scotland",
        "project_sectors": [
            "Energy",
            "Sustainability",
            "Manufacturing",
            "Infrastructure",
        ],
        "funding_types": ["grant", "loan", "equity", "tax credit"],
        "current_level": "regional",
        "regional_funders": [],
        "national_funders": [],
        "global_funders": [],
        "search_queries": [],
        "search_results": [],
        "final_report": "",
        "total_funders_found": 0,
    }

    # Configure the agent (optional - uses environment variables if not specified)
    config = {
        "configurable": {
            "model_provider": "openai",
            "model_name": "gpt-4o-mini",
            "temperature": 0.0,
            "max_tokens": 4000,
            "search_api": "tavily",
            "max_results_per_query": 10,
            "max_concurrent_searches": 3,
        }
    }

    print("🔍 Starting Funding Research Agent")
    print("=" * 80)
    print(f"\n📋 Project: {initial_state['project_description'][:150]}...")
    print(f"📍 Location: {initial_state['project_location']}")
    print(f"🏭 Sectors: {', '.join(initial_state['project_sectors'])}")
    print(f"💰 Funding Types: {', '.join(initial_state['funding_types'])}")
    print("\n" + "=" * 80 + "\n")

    # Run the research
    result = await graph.ainvoke(initial_state, config)

    # Display results
    print("\n" + "=" * 80)
    print("✅ RESEARCH COMPLETE")
    print("=" * 80)
    print(f"\n📊 Total funders found: {result['total_funders_found']}")
    print(f"   • Regional: {len(result['regional_funders'])}")
    print(f"   • National: {len(result['national_funders'])}")
    print(f"   • Global: {len(result['global_funders'])}")

    # Display detailed funder information
    if result["regional_funders"]:
        print("\n🌍 Regional Funders:")
        for funder in result["regional_funders"][:3]:  # Show first 3
            print(f"   • {funder.name} - {funder.award_range}")

    if result["national_funders"]:
        print("\n🇬🇧 National Funders:")
        for funder in result["national_funders"][:3]:
            print(f"   • {funder.name} - {funder.award_range}")

    if result["global_funders"]:
        print("\n🌐 Global Funders:")
        for funder in result["global_funders"][:3]:
            print(f"   • {funder.name} - {funder.award_range}")

    print("\n" + "=" * 80)
    print("📄 FINAL REPORT")
    print("=" * 80 + "\n")
    print(result["final_report"])

    # Optionally save the report
    with open("funding_report.md", "w") as f:
        f.write(result["final_report"])
    print("\n💾 Report saved to: funding_report.md")


async def research_building_retrofit_funding():
    """Example: Research funding for a commercial building retrofit project."""

    initial_state: ResearchState = {
        "messages": [],
        "project_description": (
            "Deep energy retrofit of 10 commercial office buildings totaling 500,000 sq ft. "
            "Includes heat pump installation, solar PV, advanced insulation, smart building "
            "controls, and net-zero carbon target. Estimated 75% energy reduction. Cost: £25M."
        ),
        "project_location": "Manchester, UK",
        "project_sectors": [
            "Infrastructure",
            "Energy",
            "Sustainability",
            "Manufacturing",
        ],
        "funding_types": ["grant", "loan", "tax incentive"],
        "current_level": "regional",
        "regional_funders": [],
        "national_funders": [],
        "global_funders": [],
        "search_queries": [],
        "search_results": [],
        "final_report": "",
        "total_funders_found": 0,
    }

    config = {
        "configurable": {
            "model_provider": "openai",
            "model_name": "gpt-4o-mini",
            "search_api": "tavily",
        }
    }

    print("🔍 Researching Building Retrofit Funding...")
    result = await graph.ainvoke(initial_state, config)

    print(f"\n✅ Found {result['total_funders_found']} funding opportunities")
    print(f"\nReport preview:\n{result['final_report'][:500]}...\n")


if __name__ == "__main__":
    print("Choose an example:")
    print("1. Offshore Wind Farm (detailed)")
    print("2. Building Retrofit (quick)")
    choice = input("\nEnter choice (1 or 2): ").strip()

    if choice == "2":
        asyncio.run(research_building_retrofit_funding())
    else:
        asyncio.run(research_wind_farm_funding())
