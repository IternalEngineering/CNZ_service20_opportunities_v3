"""Check all columns in service20_matches table."""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()


async def check_columns():
    """List all columns in service20_matches."""
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    try:
        columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'service20_matches'
            ORDER BY ordinal_position
        """)

        print(f"\nservice20_matches table has {len(columns)} columns:\n")

        for col in columns:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            print(f"{col['column_name']:<40} {col['data_type']:<30} {nullable}")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(check_columns())
