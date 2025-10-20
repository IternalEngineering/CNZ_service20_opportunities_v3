"""Database storage functions for research results."""

import asyncpg
import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


async def save_research_to_database(
    research_results: Dict[str, Any],
    opportunity_data: Optional[Dict[str, Any]] = None
) -> Optional[int]:
    """Save research results to PostgreSQL database.

    Args:
        research_results: Research results dictionary from deep researcher
        opportunity_data: Original opportunity data (optional)

    Returns:
        Database record ID if successful, None otherwise
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.warning("DATABASE_URL not set - skipping database storage")
        return None

    try:
        conn = await asyncpg.connect(database_url)

        # Extract fields from research results
        research_id = research_results.get('research_id', 'unknown')
        opportunity_type = research_results.get('opportunity_type', 'unknown')
        research_brief = research_results.get('research_brief', '')
        final_report = research_results.get('final_report', '')
        findings = research_results.get('findings', [])

        # Build query based on opportunity type
        if opportunity_data:
            if opportunity_type == 'investment':
                query_text = f"Investment Research: {opportunity_data.get('title', research_id)}"
            else:
                query_text = f"Funding Research: {opportunity_data.get('title', research_id)}"
        else:
            query_text = f"{opportunity_type.title()} Research: {research_id}"

        # Prepare metadata
        metadata = {
            'research_id': research_id,
            'opportunity_type': opportunity_type,
            'opportunity_data': opportunity_data or {},
            'findings_count': len(findings)
        }

        # Insert into database
        insert_query = """
            INSERT INTO service20_investment_opportunities (
                query,
                research_brief,
                final_report,
                research_iterations,
                tool_calls_count,
                metadata
            ) VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id;
        """

        record_id = await conn.fetchval(
            insert_query,
            query_text,
            research_brief,
            final_report,
            len(findings),  # research_iterations
            len(findings),  # tool_calls_count (approximate)
            metadata
        )

        logger.info(f"Saved research to database with ID: {record_id}")

        await conn.close()
        return record_id

    except Exception as e:
        logger.error(f"Failed to save research to database: {e}")
        return None


async def get_research_from_database(
    record_id: Optional[int] = None,
    research_id: Optional[str] = None,
    limit: int = 10
) -> list:
    """Retrieve research results from database.

    Args:
        record_id: Database record ID
        research_id: Research ID from metadata
        limit: Maximum records to return

    Returns:
        List of research records
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL not set")
        return []

    try:
        conn = await asyncpg.connect(database_url)

        if record_id:
            query = """
                SELECT * FROM service20_investment_opportunities
                WHERE id = $1;
            """
            row = await conn.fetchrow(query, record_id)
            results = [dict(row)] if row else []

        elif research_id:
            query = """
                SELECT * FROM service20_investment_opportunities
                WHERE metadata->>'research_id' = $1
                ORDER BY created_at DESC
                LIMIT $2;
            """
            rows = await conn.fetch(query, research_id, limit)
            results = [dict(row) for row in rows]

        else:
            query = """
                SELECT * FROM service20_investment_opportunities
                ORDER BY created_at DESC
                LIMIT $1;
            """
            rows = await conn.fetch(query, limit)
            results = [dict(row) for row in rows]

        await conn.close()
        return results

    except Exception as e:
        logger.error(f"Failed to retrieve research from database: {e}")
        return []


async def search_research_by_keyword(
    keyword: str,
    limit: int = 10
) -> list:
    """Search research results by keyword.

    Args:
        keyword: Search keyword
        limit: Maximum records to return

    Returns:
        List of matching research records
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL not set")
        return []

    try:
        conn = await asyncpg.connect(database_url)

        query = """
            SELECT id, query, research_brief, created_at,
                   LENGTH(final_report) as report_length
            FROM service20_investment_opportunities
            WHERE query ILIKE $1
               OR research_brief ILIKE $1
               OR final_report ILIKE $1
            ORDER BY created_at DESC
            LIMIT $2;
        """

        rows = await conn.fetch(query, f'%{keyword}%', limit)
        results = [dict(row) for row in rows]

        await conn.close()
        return results

    except Exception as e:
        logger.error(f"Failed to search research: {e}")
        return []


async def create_service20_alert(
    research_results: Dict[str, Any],
    opportunity_data: Optional[Dict[str, Any]] = None,
    user_id: str = "api-system-user"
) -> Optional[int]:
    """Create an alert notification for completed Service20 research.

    Args:
        research_results: Research results dictionary from deep researcher
        opportunity_data: Original opportunity data (optional)
        user_id: User ID to create alert for (default: system user)

    Returns:
        Alert ID if successful, None otherwise
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.warning("DATABASE_URL not set - skipping alert creation")
        return None

    try:
        conn = await asyncpg.connect(database_url)

        # Extract fields from research results
        research_id = research_results.get('research_id', 'unknown')
        opportunity_type = research_results.get('opportunity_type', 'unknown')
        research_brief = research_results.get('research_brief', '')
        final_report = research_results.get('final_report', '')
        findings = research_results.get('findings', [])

        # Build alert name and description
        if opportunity_data:
            alert_name = f"New {opportunity_type.title()} Research: {opportunity_data.get('title', research_id)[:50]}"
            location = opportunity_data.get('location', 'Unknown location')
            alert_description = f"Research completed for {opportunity_type} opportunity in {location}. {len(findings)} findings discovered."
        else:
            alert_name = f"New {opportunity_type.title()} Research Completed"
            alert_description = f"Service20 completed research for {research_id}. {len(findings)} findings discovered."

        # Prepare alert criteria with research metadata
        alert_criteria = {
            "type": "service20_research",
            "research_id": research_id,
            "opportunity_type": opportunity_type,
            "findings_count": len(findings),
            "report_length": len(final_report),
            "opportunity_data": opportunity_data or {}
        }

        # Insert alert into database
        import json

        insert_query = """
            INSERT INTO alerts (
                user_id,
                name,
                description,
                criteria,
                is_active,
                last_triggered,
                city_id
            ) VALUES ($1, $2, $3, $4::jsonb, $5, $6, $7)
            RETURNING id;
        """

        # Extract city_id if available
        city_id = None
        if opportunity_data:
            city_id = opportunity_data.get('city_id')

        alert_id = await conn.fetchval(
            insert_query,
            user_id,
            alert_name,
            alert_description,
            json.dumps(alert_criteria),  # Convert dict to JSON string
            True,  # is_active
            None,  # last_triggered (initially null)
            city_id
        )

        logger.info(f"Created Service20 alert with ID: {alert_id} for research {research_id}")

        await conn.close()
        return alert_id

    except Exception as e:
        logger.error(f"Failed to create Service20 alert: {e}")
        return None
