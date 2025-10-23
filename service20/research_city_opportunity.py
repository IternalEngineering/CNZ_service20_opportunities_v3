"""City-specific investment opportunity research script.

This script researches Net Zero investment opportunities for a specific city.
It requires both city name and country code as inputs.
"""

import asyncio
import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
load_dotenv()

from langchain_core.messages import HumanMessage
from open_deep_research.deep_researcher import deep_researcher
from open_deep_research.database_storage import store_investment_research
from open_deep_research.tracing import initialize_tracing, get_tracer

# Color output
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class Fore:
        GREEN = RED = YELLOW = CYAN = MAGENTA = ""
    class Style:
        BRIGHT = RESET_ALL = ""


# ISO 3166-1 alpha-3 country codes mapping
COUNTRY_CODES = {
    'USA': 'United States',
    'GBR': 'United Kingdom',
    'FRA': 'France',
    'DEU': 'Germany',
    'ESP': 'Spain',
    'ITA': 'Italy',
    'NLD': 'Netherlands',
    'BEL': 'Belgium',
    'SWE': 'Sweden',
    'NOR': 'Norway',
    'DNK': 'Denmark',
    'FIN': 'Finland',
    'POL': 'Poland',
    'CZE': 'Czech Republic',
    'AUT': 'Austria',
    'CHE': 'Switzerland',
    'CAN': 'Canada',
    'AUS': 'Australia',
    'NZL': 'New Zealand',
    'JPN': 'Japan',
    'KOR': 'South Korea',
    'SGP': 'Singapore',
    'IND': 'India',
    'CHN': 'China',
    'BRA': 'Brazil',
    'MEX': 'Mexico',
    'ARG': 'Argentina',
    'CHL': 'Chile',
    'ZAF': 'South Africa',
    'ARE': 'United Arab Emirates',
    'SAU': 'Saudi Arabia',
}


def validate_country_code(country_code: str) -> str:
    """Validate and return country name from country code."""
    country_code = country_code.upper()
    if country_code not in COUNTRY_CODES:
        print(f"{Fore.RED}ERROR: Invalid country code '{country_code}'{Style.RESET_ALL}")
        print(f"\nSupported country codes:")
        for code, name in sorted(COUNTRY_CODES.items()):
            print(f"  {code}: {name}")
        sys.exit(1)
    return COUNTRY_CODES[country_code]


async def research_city_opportunity(
    city: str,
    country_code: str,
    sector: str = "renewable_energy",
    investment_range: str = "500000-5000000"
):
    """
    Research Net Zero investment opportunities for a specific city.

    Args:
        city: City name (e.g., "Paris", "London", "New York")
        country_code: ISO 3166-1 alpha-3 country code (e.g., "FRA", "GBR", "USA")
        sector: Primary sector (default: "renewable_energy")
        investment_range: Investment range in USD (default: "500000-5000000")
    """

    country = validate_country_code(country_code)

    print(f"\n{Fore.CYAN}{'=' * 80}")
    print(f"Service20 City-Specific Research")
    print(f"{'=' * 80}{Style.RESET_ALL}\n")

    print(f"{Fore.YELLOW}Research Parameters:{Style.RESET_ALL}")
    print(f"  City: {city}")
    print(f"  Country: {country} ({country_code})")
    print(f"  Sector: {sector}")
    print(f"  Investment Range: ${investment_range}")
    print()

    # Build research prompt
    research_prompt = f"""
    Research Net Zero investment opportunities in {city}, {country}.

    Focus Areas:
    1. {sector.replace('_', ' ').title()} projects and initiatives
    2. Investment range: ${investment_range} USD
    3. Municipal and city-level projects
    4. Expected ROI and carbon reduction metrics
    5. Project timelines and implementation readiness
    6. Local government incentives and funding programs
    7. Partnership opportunities with local stakeholders

    Requirements:
    - Identify specific, actionable project proposals
    - Include financial projections (investment amount, ROI, payback period)
    - Quantify carbon reduction impact (tons CO2/year)
    - Assess technical feasibility and maturity
    - Evaluate timeline (planning, execution, completion)
    - Consider bundling potential with other regional projects

    Provide a comprehensive analysis with:
    - Executive summary
    - 3-5 specific project proposals
    - Financial analysis for each project
    - Carbon impact assessment
    - Implementation roadmap
    - Risk factors and mitigation strategies
    - Funding and partnership recommendations

    Reference official government sources, reputable environmental organizations,
    and recent (2023-2025) sustainability reports for {city}.
    """

    print(f"{Fore.YELLOW}Starting deep research...{Style.RESET_ALL}\n")

    # Get tracer for manual spans
    tracer = get_tracer(__name__)

    try:
        # Run deep research with tracing
        thread_id = f"{city.lower()}-{country_code.lower()}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        with tracer.start_as_current_span(
            name=f"City Research: {city}, {country}",
            attributes={
                "research.type": "city_opportunity",
                "research.city": city,
                "research.country": country,
                "research.country_code": country_code,
                "research.sector": sector,
                "research.investment_range": investment_range,
                "research.thread_id": thread_id,
            }
        ):
            result = await deep_researcher.ainvoke(
                {"messages": [HumanMessage(content=research_prompt)]},
                config={"configurable": {"thread_id": thread_id}}
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

        print(f"{Fore.CYAN}Statistics:{Style.RESET_ALL}")
        print(f"  Report Length: {len(final_report):,} characters")
        print(f"  Notes/Findings: {len(notes)} items\n")

        # Preview first 500 chars of report
        print(f"{Fore.CYAN}Report Preview:{Style.RESET_ALL}")
        print(f"{final_report[:500]}...\n")

        # Store in database
        print(f"{Fore.YELLOW}Storing research in database...{Style.RESET_ALL}")

        research_data = {
            "query": research_prompt,
            "research_brief": research_brief,
            "final_report": final_report,
            "notes": notes[:10] if len(notes) > 10 else notes,  # Top 10 findings
            "city": city,
            "country_code": country_code,
            "country": country,
            "sector": sector,
            "langfuse_trace_id": result.get("langfuse_trace_id")
        }

        research_id = await store_investment_research(research_data)

        if research_id:
            print(f"{Fore.GREEN}SUCCESS: Research stored successfully!{Style.RESET_ALL}")
            print(f"  Research ID: {research_id}")
            print(f"  City: {city}, {country}")
            print(f"  Sector: {sector}")
            print(f"  Database Table: service20_investment_opportunities")
        else:
            print(f"{Fore.RED}ERROR: Failed to store research in database{Style.RESET_ALL}")

        print(f"\n{Fore.GREEN}{'=' * 80}")
        print(f"Process completed successfully!")
        print(f"{'=' * 80}{Style.RESET_ALL}\n")

        print(f"Next steps:")
        print(f"  1. Review research: SELECT * FROM service20_investment_opportunities WHERE id = {research_id};")
        print(f"  2. Create alert for matching")
        print(f"  3. Run matching job to find compatible funders\n")

        return True

    except Exception as e:
        print(f"\n{Fore.RED}{'=' * 80}")
        print(f"Error during research: {e}")
        print(f"{'=' * 80}{Style.RESET_ALL}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Research Net Zero investment opportunities for a specific city",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python research_city_opportunity.py --city Paris --country FRA
  python research_city_opportunity.py --city London --country GBR --sector solar_energy
  python research_city_opportunity.py --city "New York" --country USA --sector wind_energy --range 1000000-10000000

Supported Sectors:
  - renewable_energy (default)
  - solar_energy
  - wind_energy
  - energy_storage
  - green_buildings
  - sustainable_transport
  - waste_management
  - water_management
        """
    )

    parser.add_argument(
        '--city',
        required=True,
        help='City name (e.g., "Paris", "London", "New York")'
    )

    parser.add_argument(
        '--country',
        required=True,
        help='ISO 3166-1 alpha-3 country code (e.g., FRA, GBR, USA)'
    )

    parser.add_argument(
        '--sector',
        default='renewable_energy',
        help='Primary sector (default: renewable_energy)'
    )

    parser.add_argument(
        '--range',
        default='500000-5000000',
        dest='investment_range',
        help='Investment range in USD (default: 500000-5000000)'
    )

    args = parser.parse_args()

    # Initialize tracing
    initialize_tracing("service20-city-research")

    # Run research
    success = asyncio.run(research_city_opportunity(
        city=args.city,
        country_code=args.country,
        sector=args.sector,
        investment_range=args.investment_range
    ))

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
