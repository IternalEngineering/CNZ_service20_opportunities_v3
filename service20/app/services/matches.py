"""Opportunity matches service."""

import time
from typing import Optional, List, Dict, Any
from asyncpg import Connection
from opentelemetry import trace

tracer = trace.get_tracer(__name__)


class MatchService:
    """Service for querying opportunity matches."""

    def __init__(self):
        self.tracer = tracer

    async def query_matches(
        self,
        connection: Connection,
        match_type: Optional[str] = None,
        confidence_level: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Query opportunity matches with optional filters.

        Args:
            connection: Database connection
            match_type: Filter by match type (single/bundled)
            confidence_level: Filter by confidence level (high/medium/low)
            status: Filter by status (proposed/reviewed/accepted/rejected)
            limit: Maximum number of results

        Returns:
            List of match dictionaries
        """
        with self.tracer.start_as_current_span(
            "query_matches",
            attributes={
                "match_type": match_type or "none",
                "confidence_level": confidence_level or "none",
                "status": status or "none",
                "limit": limit,
            },
        ):
            # Build dynamic query
            query_parts = ["SELECT * FROM opportunity_matches WHERE 1=1"]
            params = []
            param_idx = 1

            if match_type:
                query_parts.append(f"AND match_type = ${param_idx}")
                params.append(match_type)
                param_idx += 1

            if confidence_level:
                query_parts.append(f"AND confidence_level = ${param_idx}")
                params.append(confidence_level)
                param_idx += 1

            if status:
                query_parts.append(f"AND status = ${param_idx}")
                params.append(status)
                param_idx += 1

            query_parts.append(f"ORDER BY created_at DESC LIMIT ${param_idx}")
            params.append(limit)

            query = " ".join(query_parts)

            rows = await connection.fetch(query, *params)
            return [dict(row) for row in rows]


# Singleton instance
match_service = MatchService()
