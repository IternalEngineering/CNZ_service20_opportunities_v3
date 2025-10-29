"""Check primary_sector column constraint in service20_matches."""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()


async def check_constraint():
    """Check if primary_sector column allows NULL."""
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    try:
        # Check column constraints
        columns = await conn.fetch("""
            SELECT column_name, is_nullable, data_type
            FROM information_schema.columns
            WHERE table_name = 'service20_matches'
            AND column_name LIKE '%sector%'
            ORDER BY column_name
        """)

        print('Sector columns in service20_matches:')
        for col in columns:
            print(f"  {col['column_name']:30s} Nullable: {col['is_nullable']:5s} Type: {col['data_type']:20s}")

        # Also check opportunity table
        print('\nChecking service20_investment_opportunities for NULL sectors:')
        null_sectors = await conn.fetchval("""
            SELECT COUNT(*)
            FROM service20_investment_opportunities
            WHERE sector IS NULL
        """)
        print(f"  Opportunities with NULL sector: {null_sectors}")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(check_constraint())
