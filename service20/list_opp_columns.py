"""List all columns in opportunities table."""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()


async def list_columns():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    try:
        cols = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'service20_investment_opportunities'
            ORDER BY ordinal_position
        """)

        print('service20_investment_opportunities columns:')
        print('-' * 80)
        for c in cols:
            print(f"{c['column_name']:30s} {c['data_type']:20s} {'NULL' if c['is_nullable'] == 'YES' else 'NOT NULL'}")

        # Get sample data
        print('\nFirst 3 opportunities:')
        print('-' * 80)
        opps = await conn.fetch("""
            SELECT * FROM service20_investment_opportunities
            ORDER BY id LIMIT 3
        """)
        for opp in opps:
            print(f"\nID {opp['id']}:")
            for key, value in dict(opp).items():
                if value is not None:
                    print(f"  {key}: {value}")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(list_columns())
