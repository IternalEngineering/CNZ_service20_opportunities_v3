"""Bundles service."""

import time
from typing import Optional, List, Dict, Any
from asyncpg import Connection
from opentelemetry import trace

tracer = trace.get_tracer(__name__)


class BundleService:
    """Service for querying bundles."""

    def __init__(self):
        self.tracer = tracer

    async def query_bundles(
        self,
        connection: Connection,
        bundle_type: Optional[str] = None,
        min_investment: Optional[int] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Query bundles with optional filters.

        Args:
            connection: Database connection
            bundle_type: Filter by bundle type (regional/sectoral/mixed)
            min_investment: Filter by minimum total investment amount
            limit: Maximum number of results

        Returns:
            List of bundle dictionaries
        """
        with self.tracer.start_as_current_span(
            "query_bundles",
            attributes={
                "bundle_type": bundle_type or "none",
                "min_investment": min_investment or "none",
                "limit": limit,
            },
        ):
            # Build dynamic query
            query_parts = ["SELECT * FROM service20_bundles WHERE 1=1"]
            params = []
            param_idx = 1

            if bundle_type:
                query_parts.append(f"AND bundle_type = ${param_idx}")
                params.append(bundle_type)
                param_idx += 1

            if min_investment is not None:
                query_parts.append(f"AND total_investment >= ${param_idx}")
                params.append(min_investment)
                param_idx += 1

            query_parts.append(f"ORDER BY created_at DESC LIMIT ${param_idx}")
            params.append(limit)

            query = " ".join(query_parts)

            rows = await connection.fetch(query, *params)
            return [dict(row) for row in rows]


# Singleton instance
bundle_service = BundleService()
