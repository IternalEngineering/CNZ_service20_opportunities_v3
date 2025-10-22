"""Check service6_onboarding_voice schema."""
import asyncio
import asyncpg
from dotenv import load_dotenv
import os

load_dotenv()

async def check_schema():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    try:
        # Get column names
        columns = await conn.fetch('''
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'service6_onboarding_voice'
            ORDER BY ordinal_position
        ''')

        print('service6_onboarding_voice columns:')
        print('=' * 80)
        for col in columns:
            print(f'{col["column_name"]}: {col["data_type"]}')
        print()

        # Get sample data
        sample = await conn.fetchrow('SELECT * FROM service6_onboarding_voice LIMIT 1')
        if sample:
            print('Sample record:')
            print('=' * 80)
            for key in sample.keys():
                print(f'{key}: {sample[key]}')
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check_schema())
