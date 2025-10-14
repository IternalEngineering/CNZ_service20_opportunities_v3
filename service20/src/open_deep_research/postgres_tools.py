"""PostgreSQL database tools for the Deep Research agent.

This module provides LangChain tools that allow the deep researcher to query
the UrbanZero PostgreSQL database for investment opportunities, ESG data,
risk assessments, and other relevant information.
"""

import os
from typing import Annotated, List, Optional

import asyncpg
from langchain_core.tools import InjectedToolArg, tool
from langchain_core.runnables import RunnableConfig


async def get_db_connection():
    """Create and return a database connection pool."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")

    return await asyncpg.connect(database_url)


@tool(description="Search for investment opportunities in the UrbanZero database based on location, ROI, risk level, or sustainability metrics.")
async def search_opportunities(
    location: Optional[str] = None,
    min_roi: Optional[float] = None,
    max_risk_level: Optional[int] = None,
    min_esg_score: Optional[float] = None,
    limit: int = 10,
    config: Annotated[RunnableConfig, InjectedToolArg] = None
) -> str:
    """Search for investment opportunities in the database.

    Args:
        location: Filter by location (city, country, or region)
        min_roi: Minimum ROI percentage
        max_risk_level: Maximum risk level (1-5, where 1 is lowest risk)
        min_esg_score: Minimum ESG score (0-100)
        limit: Maximum number of results to return (default 10)
        config: Runtime configuration

    Returns:
        Formatted string containing matching opportunities with key details
    """
    conn = await get_db_connection()

    try:
        # Build dynamic query based on filters
        query_parts = ["SELECT * FROM opportunities WHERE 1=1"]
        params = []
        param_count = 1

        if location:
            query_parts.append(f" AND (location ILIKE ${param_count} OR country ILIKE ${param_count} OR city ILIKE ${param_count})")
            params.append(f"%{location}%")
            param_count += 1

        if min_roi is not None:
            query_parts.append(f" AND roi >= ${param_count}")
            params.append(min_roi)
            param_count += 1

        if max_risk_level is not None:
            query_parts.append(f" AND risk_level <= ${param_count}")
            params.append(max_risk_level)
            param_count += 1

        if min_esg_score is not None:
            query_parts.append(f" AND esg_score >= ${param_count}")
            params.append(min_esg_score)
            param_count += 1

        query_parts.append(f" ORDER BY created_at DESC LIMIT ${param_count}")
        params.append(limit)

        query = "".join(query_parts)

        # Execute query
        rows = await conn.fetch(query, *params)

        if not rows:
            return "No investment opportunities found matching the specified criteria."

        # Format results
        results = []
        for row in rows:
            result = f"""
Opportunity ID: {row['id']}
Title: {row['title']}
Location: {row['location']} ({row['city']}, {row['country']})
ROI: {row['roi']}%
Risk Level: {row['risk_level']}/5
ESG Score: {row['esg_score']}/100
Investment Required: ${row['investment_required']:,.2f}
Payback Period: {row['payback_period_years']} years
Description: {row['description'][:200]}...
Created: {row['created_at']}
---"""
            results.append(result)

        return "\n".join(results)

    finally:
        await conn.close()


@tool(description="Get detailed information about a specific investment opportunity by ID.")
async def get_opportunity_details(
    opportunity_id: int,
    config: Annotated[RunnableConfig, InjectedToolArg] = None
) -> str:
    """Retrieve full details for a specific opportunity.

    Args:
        opportunity_id: The unique ID of the opportunity
        config: Runtime configuration

    Returns:
        Detailed information about the opportunity
    """
    conn = await get_db_connection()

    try:
        row = await conn.fetchrow(
            "SELECT * FROM opportunities WHERE id = $1",
            opportunity_id
        )

        if not row:
            return f"No opportunity found with ID {opportunity_id}"

        # Format comprehensive details
        details = f"""
=== Investment Opportunity Details ===

ID: {row['id']}
Title: {row['title']}
Type: {row['type']}

LOCATION
--------
Location: {row['location']}
City: {row['city']}
Country: {row['country']}
Coordinates: {row['latitude']}, {row['longitude']}

FINANCIAL METRICS
-----------------
ROI: {row['roi']}%
Investment Required: ${row['investment_required']:,.2f}
Annual Revenue: ${row['annual_revenue']:,.2f}
Payback Period: {row['payback_period_years']} years

RISK & ESG
----------
Risk Level: {row['risk_level']}/5
ESG Score: {row['esg_score']}/100
Carbon Reduction: {row['carbon_reduction_tons_per_year']:,.0f} tons/year

DESCRIPTION
-----------
{row['description']}

METADATA
--------
Status: {row['status']}
Created: {row['created_at']}
Updated: {row['updated_at']}
User ID: {row['user_id']}
"""
        return details

    finally:
        await conn.close()


@tool(description="Query ESG (Environmental, Social, Governance) data and sustainability metrics from the database.")
async def query_esg_metrics(
    min_esg_score: Optional[float] = None,
    min_carbon_reduction: Optional[float] = None,
    location: Optional[str] = None,
    limit: int = 10,
    config: Annotated[RunnableConfig, InjectedToolArg] = None
) -> str:
    """Query ESG and sustainability metrics.

    Args:
        min_esg_score: Minimum ESG score (0-100)
        min_carbon_reduction: Minimum carbon reduction in tons per year
        location: Filter by location
        limit: Maximum number of results
        config: Runtime configuration

    Returns:
        ESG and sustainability data for matching opportunities
    """
    conn = await get_db_connection()

    try:
        query_parts = ["""
            SELECT id, title, location, esg_score, carbon_reduction_tons_per_year,
                   roi, investment_required, type
            FROM opportunities
            WHERE 1=1
        """]
        params = []
        param_count = 1

        if min_esg_score is not None:
            query_parts.append(f" AND esg_score >= ${param_count}")
            params.append(min_esg_score)
            param_count += 1

        if min_carbon_reduction is not None:
            query_parts.append(f" AND carbon_reduction_tons_per_year >= ${param_count}")
            params.append(min_carbon_reduction)
            param_count += 1

        if location:
            query_parts.append(f" AND location ILIKE ${param_count}")
            params.append(f"%{location}%")
            param_count += 1

        query_parts.append(f" ORDER BY esg_score DESC LIMIT ${param_count}")
        params.append(limit)

        query = "".join(query_parts)
        rows = await conn.fetch(query, *params)

        if not rows:
            return "No ESG data found matching the criteria."

        results = [f"Found {len(rows)} opportunities with ESG data:\n"]
        total_carbon = 0

        for row in rows:
            total_carbon += row['carbon_reduction_tons_per_year'] or 0
            result = f"""
ID: {row['id']} | {row['title']}
Type: {row['type']} | Location: {row['location']}
ESG Score: {row['esg_score']}/100
Carbon Reduction: {row['carbon_reduction_tons_per_year']:,.0f} tons/year
ROI: {row['roi']}% | Investment: ${row['investment_required']:,.0f}
---"""
            results.append(result)

        results.append(f"\nTotal Carbon Reduction Potential: {total_carbon:,.0f} tons/year")

        return "\n".join(results)

    finally:
        await conn.close()


@tool(description="Get database schema information for available tables and their columns.")
async def get_database_schema(
    table_name: Optional[str] = None,
    config: Annotated[RunnableConfig, InjectedToolArg] = None
) -> str:
    """Get schema information for database tables.

    Args:
        table_name: Specific table to get schema for (optional)
        config: Runtime configuration

    Returns:
        Schema information for the requested table(s)
    """
    conn = await get_db_connection()

    try:
        if table_name:
            # Get columns for specific table
            query = """
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = $1
                ORDER BY ordinal_position
            """
            rows = await conn.fetch(query, table_name)

            if not rows:
                return f"Table '{table_name}' not found"

            result = [f"Schema for table '{table_name}':\n"]
            for row in rows:
                nullable_text = 'NULL' if row['is_nullable'] == 'YES' else 'NOT NULL'
                default_text = f"DEFAULT {row['column_default']}" if row['column_default'] else ''
                result.append(
                    f"  {row['column_name']}: {row['data_type']} {nullable_text} {default_text}"
                )

            return "\n".join(result)
        else:
            # List all relevant tables
            query = """
                SELECT table_name,
                       (SELECT COUNT(*) FROM information_schema.columns
                        WHERE columns.table_name = tables.table_name) as column_count
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """
            rows = await conn.fetch(query)

            result = ["Available tables in the database:\n"]
            for row in rows:
                result.append(f"  {row['table_name']} ({row['column_count']} columns)")

            result.append("\nUse get_database_schema(table_name='<table>') to see column details.")

            return "\n".join(result)

    finally:
        await conn.close()


@tool(description="Execute a read-only SQL query against the UrbanZero database.")
async def execute_readonly_query(
    sql_query: str,
    config: Annotated[RunnableConfig, InjectedToolArg] = None
) -> str:
    """Execute a read-only SQL query.

    IMPORTANT: This tool only allows SELECT queries for safety.
    No INSERT, UPDATE, DELETE, DROP, or other modifying operations are permitted.

    Args:
        sql_query: The SELECT query to execute
        config: Runtime configuration

    Returns:
        Query results formatted as a string
    """
    # Safety check - only allow SELECT queries
    query_upper = sql_query.strip().upper()
    if not query_upper.startswith("SELECT"):
        return "ERROR: Only SELECT queries are allowed. No data modification permitted."

    # Block dangerous keywords
    dangerous_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "TRUNCATE"]
    for keyword in dangerous_keywords:
        if keyword in query_upper:
            return f"ERROR: Query contains forbidden keyword '{keyword}'. Only SELECT queries allowed."

    conn = await get_db_connection()

    try:
        # Set transaction to read-only
        await conn.execute("BEGIN TRANSACTION READ ONLY")

        # Execute query with a reasonable limit
        rows = await conn.fetch(sql_query)

        await conn.execute("COMMIT")

        if not rows:
            return "Query executed successfully but returned no results."

        # Format results
        if len(rows) > 100:
            result = [f"Query returned {len(rows)} rows (showing first 100):\n"]
            rows = rows[:100]
        else:
            result = [f"Query returned {len(rows)} rows:\n"]

        # Add column headers
        if rows:
            headers = " | ".join(rows[0].keys())
            result.append(headers)
            result.append("-" * len(headers))

            # Add data rows
            for row in rows:
                values = " | ".join(str(v) for v in row.values())
                result.append(values)

        return "\n".join(result)

    except Exception as e:
        await conn.execute("ROLLBACK")
        return f"Query execution error: {str(e)}"

    finally:
        await conn.close()


# Export all tools for easy import
POSTGRES_TOOLS = [
    search_opportunities,
    get_opportunity_details,
    query_esg_metrics,
    get_database_schema,
    execute_readonly_query
]
