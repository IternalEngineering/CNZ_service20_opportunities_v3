"""Clear all results from service20_matches table."""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()


async def clear_matches():
    """Clear all rows from service20_matches table."""
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    try:
        # Count before
        count_before = await conn.fetchval("SELECT COUNT(*) FROM service20_matches")
        print(f"Rows before clearing: {count_before}")

        # Clear table
        await conn.execute("DELETE FROM service20_matches")

        # Count after
        count_after = await conn.fetchval("SELECT COUNT(*) FROM service20_matches")
        print(f"Rows after clearing: {count_after}")
        print("✓ Table cleared successfully")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(clear_matches())
