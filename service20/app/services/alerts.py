"""Alerts service."""

import time
from typing import Optional, List, Dict, Any
from asyncpg import Connection
from opentelemetry import trace

tracer = trace.get_tracer(__name__)


class AlertService:
    """Service for querying alerts."""

    def __init__(self):
        self.tracer = tracer

    async def query_alerts(
        self,
        connection: Connection,
        user_id: Optional[int] = None,
        alert_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Query alerts with optional filters.

        Args:
            connection: Database connection
            user_id: Filter by user ID
            alert_type: Filter by alert type
            status: Filter by status (active/paused/expired)
            limit: Maximum number of results

        Returns:
            List of alert dictionaries
        """
        with self.tracer.start_as_current_span(
            "query_alerts",
            attributes={
                "user_id": user_id or "none",
                "alert_type": alert_type or "none",
                "status": status or "none",
                "limit": limit,
            },
        ):
            # Build dynamic query
            query_parts = ["SELECT * FROM service20_alerts WHERE 1=1"]
            params = []
            param_idx = 1

            if user_id is not None:
                query_parts.append(f"AND user_id = ${param_idx}")
                params.append(user_id)
                param_idx += 1

            if alert_type:
                query_parts.append(f"AND alert_type = ${param_idx}")
                params.append(alert_type)
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
alert_service = AlertService()
