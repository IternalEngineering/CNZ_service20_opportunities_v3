"""Funding opportunities service."""

import time
from typing import Optional, List, Dict, Any
from asyncpg import Connection
from opentelemetry import trace

tracer = trace.get_tracer(__name__)


class FundingService:
    """Service for querying funding opportunities."""

    def __init__(self):
        self.tracer = tracer

    async def query_funding_opportunities(
        self,
        connection: Connection,
        funder_type: Optional[str] = None,
        scope: Optional[str] = None,
        country: Optional[str] = None,
        sector: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Query funding opportunities with optional filters.

        Args:
            connection: Database connection
            funder_type: Filter by funder type
            scope: Filter by geographic scope
            country: Filter by country
            sector: Filter by sector
            limit: Maximum number of results

        Returns:
            List of funding opportunity dictionaries
        """
        with self.tracer.start_as_current_span(
            "query_funding_opportunities",
            attributes={
                "funder_type": funder_type or "none",
                "scope": scope or "none",
                "country": country or "none",
                "sector": sector or "none",
                "limit": limit,
            },
        ):
            # Build dynamic query
            query_parts = ["SELECT * FROM service20_funding_opportunities WHERE 1=1"]
            params = []
            param_idx = 1

            if funder_type:
                query_parts.append(f"AND funder_type = ${param_idx}")
                params.append(funder_type)
                param_idx += 1

            if scope:
                query_parts.append(f"AND scope = ${param_idx}")
                params.append(scope)
                param_idx += 1

            if country:
                query_parts.append(f"AND ${param_idx} = ANY(countries)")
                params.append(country)
                param_idx += 1

            if sector:
                query_parts.append(f"AND ${param_idx} = ANY(sectors)")
                params.append(sector)
                param_idx += 1

            query_parts.append(f"ORDER BY created_at DESC LIMIT ${param_idx}")
            params.append(limit)

            query = " ".join(query_parts)

            rows = await connection.fetch(query, *params)
            return [dict(row) for row in rows]


# Singleton instance
funding_service = FundingService()
