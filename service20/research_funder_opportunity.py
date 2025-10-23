"""Funder-specific research script.

This script researches funding sources (investors, grants, development banks)
for Net Zero projects with specific parameters.
"""

import asyncio
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Optional

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
load_dotenv()

from langchain_core.messages import HumanMessage
from open_deep_research.deep_researcher import deep_researcher
from open_deep_research.database_storage import store_funding_research
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


# Funder types
FUNDER_TYPES = {
    'impact_investor': 'Impact Investors and ESG-focused funds',
    'development_bank': 'Development Banks (World Bank, EIB, regional banks)',
    'government_grant': 'Government Grant Programs',
    'private_equity': 'Private Equity and Green Infrastructure Funds',
    'green_bond': 'Green Bond Issuers',
    'corporate_fund': 'Corporate Sustainability Funds',
    'foundation': 'Foundations and Philanthropic Organizations',
    'venture_capital': 'Venture Capital focused on climate tech'
}

# Geographic scopes
GEOGRAPHIC_SCOPES = ['global', 'continental', 'multi_national', 'national', 'regional', 'city']

# Common sectors
SECTORS = [
    'renewable_energy', 'solar_energy', 'wind_energy', 'hydro_energy',
    'geothermal_energy', 'energy_storage', 'sustainable_transport',
    'ev_charging', 'public_transit', 'green_buildings', 'energy_efficiency',
    'waste_management', 'water_management', 'circular_economy',
    'sustainable_agriculture', 'carbon_capture', 'hydrogen'
]


def validate_funder_type(funder_type: str) -> bool:
    """Validate funder type."""
    if funder_type not in FUNDER_TYPES:
        print(f"{Fore.RED}ERROR: Invalid funder type '{funder_type}'{Style.RESET_ALL}")
        print(f"\nSupported funder types:")
        for key, desc in FUNDER_TYPES.items():
            print(f"  {key}: {desc}")
        return False
    return True


def validate_scope(scope: str) -> bool:
    """Validate geographic scope."""
    if scope not in GEOGRAPHIC_SCOPES:
        print(f"{Fore.RED}ERROR: Invalid scope '{scope}'{Style.RESET_ALL}")
        print(f"\nSupported scopes: {', '.join(GEOGRAPHIC_SCOPES)}")
        return False
    return True


async def research_funder_opportunity(
    funder_type: str,
    scope: str = "global",
    continents: Optional[List[str]] = None,
    countries: Optional[List[str]] = None,
    regions: Optional[List[str]] = None,
    cities: Optional[List[str]] = None,
    sectors: Optional[List[str]] = None,
    min_investment: Optional[int] = None,
    max_investment: Optional[int] = None,
    project_stages: Optional[List[str]] = None
):
    """
    Research funding opportunities for Net Zero projects.

    Args:
        funder_type: Type of funder (impact_investor, development_bank, etc.)
        scope: Geographic scope (global, continental, national, etc.)
        continents: List of continents (for continental scope)
        countries: List of countries
        regions: List of regions
        cities: List of cities (for city scope)
        sectors: List of sectors to focus on
        min_investment: Minimum investment amount (USD)
        max_investment: Maximum investment amount (USD)
        project_stages: Preferred project stages
    """

    # Validate inputs
    if not validate_funder_type(funder_type):
        sys.exit(1)
    if not validate_scope(scope):
        sys.exit(1)

    # Default values
    if not sectors:
        sectors = ['renewable_energy', 'sustainable_transport']
    if not project_stages:
        project_stages = ['all']
    if not min_investment:
        min_investment = 500000
    if not max_investment:
        max_investment = 50000000

    print(f"\n{Fore.CYAN}{'=' * 80}")
    print(f"Service20 Funder Research")
    print(f"{'=' * 80}{Style.RESET_ALL}\n")

    print(f"{Fore.YELLOW}Research Parameters:{Style.RESET_ALL}")
    print(f"  Funder Type: {FUNDER_TYPES[funder_type]}")
    print(f"  Geographic Scope: {scope}")
    if continents:
        print(f"  Continents: {', '.join(continents)}")
    if countries:
        print(f"  Countries: {', '.join(countries)}")
    if regions:
        print(f"  Regions: {', '.join(regions)}")
    if cities:
        print(f"  Cities: {', '.join(cities)}")
    print(f"  Sectors: {', '.join(sectors)}")
    print(f"  Investment Range: ${min_investment:,} - ${max_investment:,}")
    print(f"  Project Stages: {', '.join(project_stages)}")
    print()

    # Build geographic description
    geo_parts = []
    if scope == 'global':
        geo_parts.append("operating globally")
    elif scope == 'continental' and continents:
        geo_parts.append(f"operating in {', '.join(continents)}")
    elif scope == 'national' and countries:
        geo_parts.append(f"operating in {', '.join(countries)}")
    elif scope == 'regional' and regions:
        geo_parts.append(f"operating in {', '.join(regions)}")
    elif scope == 'city' and cities:
        geo_parts.append(f"operating in {', '.join(cities)}")

    if countries and scope != 'national':
        geo_parts.append(f"with focus on {', '.join(countries)}")

    geographic_desc = ' '.join(geo_parts) if geo_parts else "with unspecified geography"

    # Build sector description
    sector_desc = ', '.join([s.replace('_', ' ') for s in sectors])

    # Build research prompt
    research_prompt = f"""
Research {FUNDER_TYPES[funder_type]} for Net Zero projects {geographic_desc}.

GEOGRAPHIC SCOPE: {scope.upper()}
{f"Continents: {', '.join(continents)}" if continents else ''}
{f"Countries: {', '.join(countries)}" if countries else ''}
{f"Regions: {', '.join(regions)}" if regions else ''}
{f"Cities: {', '.join(cities)}" if cities else ''}

SECTOR FOCUS: {sector_desc}

INVESTMENT CRITERIA:
- Minimum Investment: ${min_investment:,} USD
- Maximum Investment: ${max_investment:,} USD
- Project Stages: {', '.join(project_stages)}

REQUIRED INFORMATION FOR EACH FUNDER:

1. IDENTIFICATION
   - Official name and organization type
   - Funder type and subtype
   - Website and contact information (email, phone)

2. GEOGRAPHIC COVERAGE
   - Geographic scope (global/continental/national/regional/city)
   - Specific continents, countries, regions, or cities covered
   - Any geographic restrictions or preferences

3. SECTOR FOCUS
   - Primary sectors funded
   - Specific subsectors or technologies
   - Sectors explicitly excluded

4. FINANCIAL CRITERIA
   - Total fund size or assets under management
   - Minimum and maximum investment amounts
   - Typical ticket size
   - Investment types (equity/debt/grant/blended)
   - Financial instruments used

5. RETURN EXPECTATIONS
   - Minimum ROI required (if applicable)
   - Target ROI range
   - Willing to accept below-market returns?
   - Concessional finance available?

6. PROJECT REQUIREMENTS
   - Preferred project stages (early/development/construction/operational)
   - Technology maturity requirements
   - Carbon reduction metrics required?
   - Impact measurement requirements
   - Co-financing requirements

7. APPLICATION PROCESS
   - How to apply (detailed process description)
   - Application URL or portal
   - Contact email and phone
   - Typical decision timeline
   - Next call for proposals date (if applicable)
   - Current deadline (if applicable)

8. TRACK RECORD
   - Number of active projects
   - Total projects funded historically
   - Average deal size
   - 2-3 recent deal examples with details (project name, location, amount, type, year)

9. CURRENT STATUS
   - Currently accepting applications? (yes/no)
   - Fund status (active/closed/fundraising/deploying)
   - Next fundraising round date (if applicable)

DELIVERABLES:

Provide a comprehensive analysis with:

1. Executive Summary (200-300 words)
   - Overview of {funder_type} landscape in specified geography
   - Total funding available
   - Key trends and opportunities
   - Success rate and typical timelines

2. Detailed Funder Profiles (5-10 funders minimum)
   For each funder, provide all information listed above in structured format:
   - Complete contact details and application URLs
   - Recent deal examples with project details and terms
   - Application strategy and tips
   - Likelihood of success rating (high/medium/low)

3. Comparison Matrix
   - Side-by-side comparison of key criteria
   - Best matches for different project types
   - Geographic coverage comparison
   - Investment range and terms comparison

4. Application Strategy
   - Recommended approach for each funder
   - Timeline for applications
   - Required documentation checklist
   - Common success factors
   - Tips for increasing approval chances

5. Red Flags and Exclusions
   - Common reasons for rejection
   - Projects they explicitly won't fund
   - Geographic or sector restrictions
   - Minimum requirements that are deal-breakers

IMPORTANT:
- Only include ACTIVE funders currently accepting applications OR with upcoming calls
- Verify all information is current (2024-2025)
- Include specific contact information and application URLs
- Cite sources for all claims
- Flag any uncertain information
- For development banks, include both headquarters and regional offices

Reference official websites, recent annual reports, reputable financial databases,
and government funding portals.
"""

    print(f"{Fore.YELLOW}Starting deep research...{Style.RESET_ALL}\n")

    # Get tracer for manual spans
    tracer = get_tracer(__name__)

    try:
        # Generate thread ID
        funder_slug = funder_type.replace('_', '-')
        geo_slug = scope
        if countries and len(countries) == 1:
            geo_slug = countries[0].lower().replace(' ', '-')
        elif continents and len(continents) == 1:
            geo_slug = continents[0].lower().replace(' ', '-')

        thread_id = f"funder-{funder_slug}-{geo_slug}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        # Run deep research with tracing
        print(f"{Fore.CYAN}Thread ID: {thread_id}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Starting research iterations...{Style.RESET_ALL}\n")

        with tracer.start_as_current_span(
            name=f"Funder Research: {funder_type}",
            attributes={
                "research.type": "funder_opportunity",
                "research.funder_type": funder_type,
                "research.scope": scope,
                "research.countries": ','.join(countries) if countries else None,
                "research.continents": ','.join(continents) if continents else None,
                "research.sectors": ','.join(sectors) if sectors else None,
                "research.min_investment": min_investment,
                "research.max_investment": max_investment,
                "research.thread_id": thread_id,
            }
        ):
            result = await deep_researcher.ainvoke(
                {"messages": [HumanMessage(content=research_prompt)]},
                config={"configurable": {"thread_id": thread_id}}
            )

        # Extract results
        final_report = None
        research_brief = None
        notes = []

        for message in result.get("messages", []):
            if hasattr(message, 'content'):
                content = message.content
                if isinstance(content, str):
                    if len(content) > 1000:  # Likely the final report
                        final_report = content
                    elif len(content) > 100:  # Likely research brief or notes
                        if not research_brief:
                            research_brief = content
                        else:
                            notes.append(content)

        if not final_report:
            print(f"{Fore.RED}ERROR: No final report generated{Style.RESET_ALL}")
            return

        print(f"\n{Fore.GREEN}{'=' * 80}")
        print(f"Research Complete!")
        print(f"{'=' * 80}{Style.RESET_ALL}\n")

        print(f"{Fore.YELLOW}Final Report Length: {len(final_report)} characters{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Research Iterations: {len(result.get('messages', []))}{Style.RESET_ALL}\n")

        # Store in database
        print(f"{Fore.CYAN}Storing results in database...{Style.RESET_ALL}")

        research_data = {
            "query": research_prompt,
            "research_brief": research_brief,
            "final_report": final_report,
            "notes": notes,
            "funder_type": funder_type,
            "geographic_scope": scope,
            "continent": continents,
            "countries": countries,
            "regions": regions,
            "cities": cities,
            "sectors": sectors,
            "min_investment": min_investment,
            "max_investment": max_investment,
            "project_stages": project_stages,
            "research_iterations": len(result.get('messages', [])),
            "metadata": {
                "thread_id": thread_id,
                "funder_type_description": FUNDER_TYPES[funder_type],
                "sectors_description": sector_desc,
                "geographic_description": geographic_desc
            }
        }

        research_id = await store_funding_research(research_data)

        print(f"{Fore.GREEN}[OK] Research stored with ID: {research_id}{Style.RESET_ALL}\n")

        # Display summary
        print(f"{Fore.CYAN}{'=' * 80}")
        print(f"Research Summary")
        print(f"{'=' * 80}{Style.RESET_ALL}\n")

        print(f"{Fore.YELLOW}Funder Type:{Style.RESET_ALL} {FUNDER_TYPES[funder_type]}")
        print(f"{Fore.YELLOW}Geographic Scope:{Style.RESET_ALL} {geographic_desc}")
        print(f"{Fore.YELLOW}Sectors:{Style.RESET_ALL} {sector_desc}")
        print(f"{Fore.YELLOW}Investment Range:{Style.RESET_ALL} ${min_investment:,} - ${max_investment:,}")
        print(f"{Fore.YELLOW}Research ID:{Style.RESET_ALL} {research_id}")
        print()

        # Preview first 500 characters of report
        print(f"{Fore.CYAN}Report Preview:{Style.RESET_ALL}")
        print(f"{final_report[:500]}...")
        print()

        print(f"{Fore.GREEN}[OK] Funder research completed successfully!{Style.RESET_ALL}\n")

        return research_id

    except Exception as e:
        print(f"\n{Fore.RED}{'=' * 80}")
        print(f"Error during research: {e}")
        print(f"{'=' * 80}{Style.RESET_ALL}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Research funding sources for Net Zero projects",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # European impact investors for solar energy
  python research_funder_opportunity.py impact_investor --scope continental --continents Europe --sectors solar_energy,energy_storage --min 1000000 --max 20000000

  # US development banks for sustainable transport
  python research_funder_opportunity.py development_bank --scope national --countries "United States" --sectors sustainable_transport --min 10000000

  # French government grants for renewable energy
  python research_funder_opportunity.py government_grant --scope national --countries France --sectors renewable_energy,green_buildings

  # Global green bond funds
  python research_funder_opportunity.py green_bond --scope global --sectors renewable_energy --min 50000000
        """
    )

    parser.add_argument('funder_type', type=str, choices=list(FUNDER_TYPES.keys()),
                        help='Type of funder to research')
    parser.add_argument('--scope', type=str, default='global', choices=GEOGRAPHIC_SCOPES,
                        help='Geographic scope (default: global)')
    parser.add_argument('--continents', type=str, help='Comma-separated list of continents')
    parser.add_argument('--countries', type=str, help='Comma-separated list of countries')
    parser.add_argument('--regions', type=str, help='Comma-separated list of regions')
    parser.add_argument('--cities', type=str, help='Comma-separated list of cities')
    parser.add_argument('--sectors', type=str, default='renewable_energy',
                        help='Comma-separated list of sectors (default: renewable_energy)')
    parser.add_argument('--min', dest='min_investment', type=int, default=500000,
                        help='Minimum investment amount in USD (default: 500000)')
    parser.add_argument('--max', dest='max_investment', type=int, default=50000000,
                        help='Maximum investment amount in USD (default: 50000000)')
    parser.add_argument('--stages', type=str, default='all',
                        help='Comma-separated list of project stages (default: all)')

    args = parser.parse_args()

    # Parse comma-separated lists
    continents = [c.strip() for c in args.continents.split(',')] if args.continents else None
    countries = [c.strip() for c in args.countries.split(',')] if args.countries else None
    regions = [r.strip() for r in args.regions.split(',')] if args.regions else None
    cities = [c.strip() for c in args.cities.split(',')] if args.cities else None
    sectors = [s.strip() for s in args.sectors.split(',')]
    stages = [s.strip() for s in args.stages.split(',')]

    # Initialize tracing
    initialize_tracing("service20-funder-research")

    # Run research
    asyncio.run(research_funder_opportunity(
        funder_type=args.funder_type,
        scope=args.scope,
        continents=continents,
        countries=countries,
        regions=regions,
        cities=cities,
        sectors=sectors,
        min_investment=args.min_investment,
        max_investment=args.max_investment,
        project_stages=stages
    ))


if __name__ == "__main__":
    main()
