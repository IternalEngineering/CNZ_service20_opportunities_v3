"""List service20_matches table schema."""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()


async def list_schema():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    try:
        cols = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'service20_matches'
            ORDER BY ordinal_position
        """)

        print('service20_matches columns:')
        print('-' * 80)
        for c in cols:
            print(f"{c['column_name']:30s} {c['data_type']:20s} {'NULL' if c['is_nullable'] == 'YES' else 'NOT NULL'}")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(list_schema())
