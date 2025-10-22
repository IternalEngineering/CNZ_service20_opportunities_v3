"""Get all cities with test@urbanzero.ai email."""
import asyncio
import asyncpg
from dotenv import load_dotenv
import os

load_dotenv()

async def get_cities():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    try:
        cities = await conn.fetch('''
            SELECT
                city,
                text_responses->>'country_code' as country_code,
                text_responses->>'success_criteria' as success_criteria,
                job_role,
                organization,
                created_at
            FROM service6_onboarding_voice
            WHERE email = 'test@urbanzero.ai'
            ORDER BY created_at DESC
        ''')

        print('Cities with test@urbanzero.ai:')
        print('=' * 80)
        for i, city in enumerate(cities, 1):
            print(f'{i}. {city["city"]}, {city["country_code"]}')
            print(f'   Organization: {city["organization"]}')
            print(f'   Role: {city["job_role"]}')
            print(f'   Goal: {city["success_criteria"][:100]}...' if city["success_criteria"] and len(city["success_criteria"]) > 100 else f'   Goal: {city["success_criteria"]}')
            print()

        return cities
    finally:
        await conn.close()

if __name__ == "__main__":
    cities = asyncio.run(get_cities())
