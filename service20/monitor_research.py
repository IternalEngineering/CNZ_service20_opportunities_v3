"""Monitor research progress and update tasklist.md."""
import asyncio
import asyncpg
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

# Map of cities to track
CITIES_TO_TRACK = {
    'Boston': ('USA', 'US'),
    'Austin': ('USA', 'US'),
    'Seattle': ('USA', 'US'),
    'San Francisco': ('USA', 'US'),
    'New York City': ('USA', 'US'),
    'Vancouver': ('CAN', 'CA'),
    'Birmingham': ('GBR', 'GB'),
    'Edinburgh': ('GBR', 'GB'),
    'Manchester': ('GBR', 'GB'),
    'Bristol': ('GBR', 'GB'),
    'Stockholm': ('SWE', 'SE'),
    'Copenhagen': ('DNK', 'DK'),
    'Melbourne': ('AUS', 'AU'),
    'Mumbai': ('IND', 'IN'),
    'Auckland': ('NZL', 'NZ'),
    'Dubai': ('ARE', 'AE'),
    'Tokyo': ('JPN', 'JP'),
    'Singapore': ('SGP', 'SG'),
    'Bogotá': ('COL', 'CO'),
    'São Paulo': ('BRA', 'BR'),
    'Cape Town': ('ZAF', 'ZA'),
}

async def check_research_status():
    """Check which cities have completed research."""
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    try:
        # Get all completed opportunities
        opportunities = await conn.fetch('''
            SELECT DISTINCT city, country
            FROM service20_investment_opportunities
            WHERE created_at >= CURRENT_DATE
            ORDER BY city
        ''')

        completed_cities = {(row['city'], row['country']) for row in opportunities}

        print('Research Progress Report')
        print('=' * 80)
        print(f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        print()

        completed_count = 0
        pending_count = 0

        for city, (country_code, country_short) in CITIES_TO_TRACK.items():
            # Check both possible country formats
            is_completed = (city, country_code) in completed_cities or (city, country_short) in completed_cities

            status = '[x]' if is_completed else '[ ]'
            status_text = 'COMPLETED' if is_completed else 'PENDING'

            print(f'{status} {city}, {country_short} - {status_text}')

            if is_completed:
                completed_count += 1
            else:
                pending_count += 1

        print()
        print(f'Summary: {completed_count}/{len(CITIES_TO_TRACK)} completed, {pending_count} pending')
        print()

        return completed_cities

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check_research_status())
