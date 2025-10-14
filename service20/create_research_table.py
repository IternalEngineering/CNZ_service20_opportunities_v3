"""Create the service20_investment_opportunities table for storing research outputs."""

import asyncio
import os
from dotenv import load_dotenv
import asyncpg

load_dotenv()

async def create_table():
    """Create the service20_investment_opportunities table."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")

    conn = await asyncpg.connect(database_url)

    try:
        # Create table if it doesn't exist
        create_table_query = """
        CREATE TABLE IF NOT EXISTS service20_investment_opportunities (
            id SERIAL PRIMARY KEY,
            query TEXT NOT NULL,
            research_brief TEXT,
            final_report TEXT NOT NULL,
            research_iterations INTEGER,
            tool_calls_count INTEGER,
            database_tools_used TEXT[],
            web_tools_used TEXT[],
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            langfuse_trace_id TEXT,
            metadata JSONB
        );

        -- Create index on created_at for faster queries
        CREATE INDEX IF NOT EXISTS idx_service20_created_at
        ON service20_investment_opportunities(created_at DESC);

        -- Create index on query for text search
        CREATE INDEX IF NOT EXISTS idx_service20_query
        ON service20_investment_opportunities USING gin(to_tsvector('english', query));
        """

        await conn.execute(create_table_query)
        print("[OK] Table 'service20_investment_opportunities' created successfully")

        # Verify table exists
        table_check = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'service20_investment_opportunities'
            );
        """)

        if table_check:
            print("[OK] Table verification successful")

            # Show table schema
            schema = await conn.fetch("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'service20_investment_opportunities'
                ORDER BY ordinal_position;
            """)

            print("\nTable Schema:")
            for col in schema:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                print(f"  {col['column_name']}: {col['data_type']} {nullable}")
        else:
            print("[ERROR] Table verification failed")

    except Exception as e:
        print(f"[ERROR] Failed to create table: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_table())
