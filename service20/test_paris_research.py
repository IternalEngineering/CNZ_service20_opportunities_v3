"""Quick test script to trigger research for Paris Net Zero opportunities."""

import asyncio
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
load_dotenv()

from langchain_core.messages import HumanMessage
from open_deep_research.deep_researcher import deep_researcher
from open_deep_research.database_storage import create_service20_alert

# Color output
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class Fore:
        GREEN = RED = YELLOW = CYAN = MAGENTA = ""
    class Style:
        BRIGHT = RESET_ALL = ""


async def test_paris_research():
    """Run a quick research test for Paris solar energy opportunities."""

    print(f"\n{Fore.CYAN}{'=' * 80}")
    print(f"Service20 Research Test - Paris Solar Energy Opportunities")
    print(f"{'=' * 80}{Style.RESET_ALL}\n")

    # Research prompt for Paris
    research_prompt = """
    Research Net Zero investment opportunities in Paris, France, specifically focusing on:

    1. Solar panel installation projects for municipal buildings
    2. Investment amount range: €500,000 - €2,000,000
    3. Expected ROI and carbon reduction metrics
    4. Timeline for project implementation
    5. Any relevant funding opportunities or government incentives

    Provide a comprehensive analysis with specific project proposals that could be
    attractive to impact investors focused on urban sustainability.
    """

    print(f"{Fore.YELLOW}Starting deep research...{Style.RESET_ALL}")
    print(f"City: Paris, France")
    print(f"Sector: Solar Energy")
    print(f"Type: Investment Opportunity\n")

    try:
        # Run deep research
        result = await deep_researcher.ainvoke(
            {"messages": [HumanMessage(content=research_prompt)]},
            config={"configurable": {"thread_id": "paris-test-001"}}
        )

        # Extract results
        final_report = result.get("final_report", "")
        research_brief = result.get("research_brief", "")
        notes = result.get("notes", [])

        print(f"\n{Fore.GREEN}{'=' * 80}")
        print(f"Research Completed!")
        print(f"{'=' * 80}{Style.RESET_ALL}\n")

        print(f"{Fore.CYAN}Research Brief:{Style.RESET_ALL}")
        print(f"{research_brief}\n")

        print(f"{Fore.CYAN}Final Report Length:{Style.RESET_ALL} {len(final_report)} characters")
        print(f"{Fore.CYAN}Notes/Findings:{Style.RESET_ALL} {len(notes)} items\n")

        # Preview first 500 chars of report
        print(f"{Fore.CYAN}Report Preview:{Style.RESET_ALL}")
        print(f"{final_report[:500]}...\n")

        # Create alert with enhanced metadata
        print(f"{Fore.YELLOW}Creating Service20 alert with enhanced metadata...{Style.RESET_ALL}")

        research_results = {
            "research_id": "paris-solar-test-001",
            "opportunity_type": "investment",
            "research_brief": research_brief,
            "final_report": final_report,
            "findings": notes[:5] if len(notes) > 5 else notes  # Top 5 findings
        }

        opportunity_data = {
            # Basic info
            "title": "Paris Municipal Solar Panel Initiative",
            "location": "Paris, France",
            "investment_amount": 1500000,  # €1.5M
            "roi": 16.5,
            "city_id": None,  # Optional - will be null if not found

            # Enhanced metadata for matching
            "sector": "solar_energy",
            "subsector": "municipal",
            "sector_tags": ["rooftop", "public_buildings", "carbon_credits"],

            "city": "Paris",
            "country": "France",
            "region": "Europe",
            "geoname_id": "Q90",  # Wikidata ID for Paris
            "coordinates": [48.8566, 2.3522],

            "planning_start": "2025-Q3",
            "execution_start": "2026-Q1",
            "completion": "2027-Q1",
            "deadline": "2025-12-31",
            "urgency": "medium",

            "technology": "photovoltaic",
            "capacity_mw": 3.5,
            "maturity": "planning",
            "payback_years": 6,
            "currency": "EUR",
            "carbon_reduction": 200,  # tons/year

            "bundling_eligible": True,
            "minimum_bundle_size": 3000000,  # €3M
            "maximum_bundle_partners": 4,
            "compatibility_requirements": ["same_sector", "similar_timeline", "eu_region"]
        }

        alert_id = await create_service20_alert(research_results, opportunity_data)

        if alert_id:
            print(f"{Fore.GREEN}SUCCESS: Alert created successfully!{Style.RESET_ALL}")
            print(f"  Alert ID: {alert_id}")
            print(f"  Title: {opportunity_data['title']}")
            print(f"  Investment: EUR {opportunity_data['investment_amount']:,}")
            print(f"  ROI: {opportunity_data['roi']}%")
            print(f"  Carbon Reduction: {opportunity_data['carbon_reduction']} tons/year")
            print(f"  Bundling Eligible: Yes (min bundle: EUR {opportunity_data['minimum_bundle_size']:,})")
        else:
            print(f"{Fore.RED}ERROR: Failed to create alert{Style.RESET_ALL}")

        print(f"\n{Fore.GREEN}{'=' * 80}")
        print(f"Test completed successfully!")
        print(f"{'=' * 80}{Style.RESET_ALL}\n")

        print("Next steps:")
        print("  1. Check database for the alert: SELECT * FROM service20_alerts WHERE research_id = 'paris-solar-test-001';")
        print("  2. Run matching job to find compatible funders")
        print("  3. View results in matching_dashboard.html\n")

        return True

    except Exception as e:
        print(f"\n{Fore.RED}{'=' * 80}")
        print(f"Error during research: {e}")
        print(f"{'=' * 80}{Style.RESET_ALL}\n")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_paris_research())
    sys.exit(0 if success else 1)
