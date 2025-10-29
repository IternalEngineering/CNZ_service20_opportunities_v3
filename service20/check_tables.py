"""Check existing service20 tables in the database."""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()


async def check_tables():
    """List all service20 tables and their columns."""
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    try:
        # Get all service20 tables
        tables = await conn.fetch("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname='public' AND tablename LIKE '%service20%'
            ORDER BY tablename
        """)

        print(f"\nFound {len(tables)} service20 tables:\n")

        for table in tables:
            table_name = table['tablename']
            print(f"Table: {table_name}")

            # Get columns for this table
            columns = await conn.fetch("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = $1
                ORDER BY ordinal_position
                LIMIT 10
            """, table_name)

            for col in columns:
                print(f"  - {col['column_name']} ({col['data_type']})")

            print()

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(check_tables())
