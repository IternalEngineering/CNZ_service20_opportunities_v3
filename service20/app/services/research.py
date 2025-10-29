"""Research service for running deep research agents."""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

from langchain_core.messages import HumanMessage
from open_deep_research.deep_researcher import deep_researcher
from open_deep_research.database_storage import store_investment_research
from open_deep_research.tracing import get_tracer

logger = logging.getLogger(__name__)


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


class ResearchService:
    """Service for managing research operations."""

    @staticmethod
    def validate_country_code(country_code: str) -> Optional[str]:
        """
        Validate and return country name from country code.

        Args:
            country_code: ISO 3166-1 alpha-3 country code

        Returns:
            Country name if valid, None otherwise
        """
        country_code = country_code.upper()
        return COUNTRY_CODES.get(country_code)

    @staticmethod
    async def run_city_research(
        city: str,
        country_code: str,
        sector: str = "renewable_energy",
        investment_range: str = "500000-5000000"
    ) -> dict:
        """
        Run deep research for a city investment opportunity.

        This method runs the AI research agent to generate a comprehensive
        investment opportunity report for the specified city.

        Args:
            city: City name (e.g., "Paris", "London")
            country_code: ISO 3166-1 alpha-3 code (e.g., "FRA", "GBR")
            sector: Primary sector (default: "renewable_energy")
            investment_range: Investment range in USD (default: "500000-5000000")

        Returns:
            Dictionary with research results and metadata

        Raises:
            ValueError: If country code is invalid
            Exception: If research fails
        """
        # Validate country code
        country = ResearchService.validate_country_code(country_code)
        if not country:
            raise ValueError(
                f"Invalid country code '{country_code}'. "
                f"Supported codes: {', '.join(sorted(COUNTRY_CODES.keys()))}"
            )

        logger.info(
            f"Starting research for city={city}, country={country} ({country_code}), "
            f"sector={sector}, range={investment_range}"
        )

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

        # Get tracer for manual spans
        tracer = get_tracer(__name__)

        try:
            # Generate thread ID
            thread_id = f"{city.lower()}-{country_code.lower()}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

            # Run deep research with tracing
            with tracer.start_as_current_span(
                name=f"API City Research: {city}, {country}",
                attributes={
                    "research.type": "city_opportunity",
                    "research.city": city,
                    "research.country": country,
                    "research.country_code": country_code,
                    "research.sector": sector,
                    "research.investment_range": investment_range,
                    "research.thread_id": thread_id,
                    "research.trigger": "api"
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

            logger.info(
                f"Research completed for {city}, {country}. "
                f"Report length: {len(final_report)} chars, "
                f"Notes: {len(notes)} items"
            )

            # Store in database
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

            if not research_id:
                raise Exception("Failed to store research in database")

            logger.info(
                f"Research stored successfully with ID={research_id} for "
                f"city={city}, country={country}"
            )

            return {
                "success": True,
                "research_id": research_id,
                "city": city,
                "country": country,
                "country_code": country_code,
                "sector": sector,
                "report_length": len(final_report),
                "notes_count": len(notes),
                "langfuse_trace_id": result.get("langfuse_trace_id"),
                "thread_id": thread_id
            }

        except Exception as e:
            logger.error(
                f"Error during research for {city}, {country}: {str(e)}",
                exc_info=True
            )
            raise

    @staticmethod
    def generate_job_id(city: str, country_code: str) -> str:
        """
        Generate a unique job ID for research tracking.

        Args:
            city: City name
            country_code: Country code

        Returns:
            Unique job identifier
        """
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        return f"{city.lower().replace(' ', '-')}-{country_code.lower()}-{timestamp}"
