"""View research results from the service20_investment_opportunities table."""

import asyncio
import os
from dotenv import load_dotenv
import asyncpg

load_dotenv()

async def view_results():
    """View all research results from the database."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("[ERROR] DATABASE_URL not set")
        return

    conn = await asyncpg.connect(database_url)

    try:
        # Get all records
        rows = await conn.fetch("""
            SELECT id, query, tool_calls_count, database_tools_used,
                   web_tools_used, created_at,
                   LENGTH(final_report) as report_length
            FROM service20_investment_opportunities
            ORDER BY created_at DESC;
        """)

        if not rows:
            print("No research results found in the database.")
            return

        print("=" * 80)
        print(f"Found {len(rows)} research result(s) in the database:")
        print("=" * 80)
        print()

        for row in rows:
            print(f"ID: {row['id']}")
            print(f"Query: {row['query']}")
            print(f"Created: {row['created_at']}")
            print(f"Tool Calls: {row['tool_calls_count']}")
            print(f"Database Tools: {row['database_tools_used'] or '(none)'}")
            print(f"Web Tools: {row['web_tools_used'] or '(none)'}")
            print(f"Report Length: {row['report_length']} characters")
            print("-" * 80)
            print()

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(view_results())
