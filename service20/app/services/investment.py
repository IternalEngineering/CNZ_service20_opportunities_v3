"""Business logic for investment opportunity queries."""

import logging
import sys
from pathlib import Path
from typing import Optional
from asyncpg import Connection

# Add src directory to path for tracing import
sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

from open_deep_research.tracing import get_tracer

logger = logging.getLogger(__name__)


class InvestmentService:
    """Service for querying investment opportunities."""

    def __init__(self):
        """Initialize investment service."""
        self.tracer = get_tracer(__name__)

    async def get_latest_opportunity(
        self,
        connection: Connection,
        city: str,
        country_code: str
    ) -> Optional[dict]:
        """
        Retrieve the most recent investment opportunity for a city and country.

        Args:
            connection: Database connection
            city: City name
            country_code: ISO 3166-1 alpha-3 country code

        Returns:
            Dictionary with opportunity data or None if not found
        """
        with self.tracer.start_as_current_span(
            "get_latest_opportunity",
            attributes={
                "db.operation": "SELECT",
                "db.table": "service20_investment_opportunities",
                "city": city,
                "country_code": country_code
            }
        ):
            query = """
                SELECT
                    id,
                    query,
                    research_brief,
                    final_report,
                    notes,
                    city,
                    country_code,
                    country,
                    region,
                    sector,
                    subsectors,
                    research_iterations,
                    tool_calls_count,
                    metadata,
                    langfuse_trace_id,
                    created_at,
                    updated_at
                FROM service20_investment_opportunities
                WHERE
                    LOWER(city) = LOWER($1) AND
                    UPPER(country_code) = UPPER($2)
                ORDER BY created_at DESC
                LIMIT 1;
            """

            try:
                row = await connection.fetchrow(query, city, country_code)

                if row is None:
                    logger.info(f"No opportunity found for city='{city}', country_code='{country_code}'")
                    return None

                # Convert row to dict
                opportunity = dict(row)
                logger.info(f"Found opportunity id={opportunity['id']} for city='{city}', country_code='{country_code}'")

                return opportunity

            except Exception as e:
                logger.error(f"Error querying investment opportunities: {str(e)}")
                raise
