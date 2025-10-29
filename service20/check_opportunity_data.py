"""Check what data is in the investment opportunities table."""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()


async def check_opportunities():
    """Check opportunity data."""
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    try:
        # Get first 10 opportunities
        opps = await conn.fetch("""
            SELECT id, city, country, country_code, sector,
                   estimated_cost, roi_percentage, risk_level
            FROM service20_investment_opportunities
            ORDER BY id
            LIMIT 10
        """)

        print('First 10 investment opportunities:')
        print('-' * 120)
        for opp in opps:
            print(f"ID {opp['id']:3d}: "
                  f"City={opp['city'] or 'NULL':20s} "
                  f"Country={opp['country'] or 'NULL':20s} "
                  f"Sector={opp['sector'] or 'NULL':20s} "
                  f"Cost={opp['estimated_cost'] or 0:10.0f} "
                  f"ROI={opp['roi_percentage'] or 0:5.1f}% "
                  f"Risk={opp['risk_level'] or 'NULL':10s}")

        # Count NULL values
        null_counts = await conn.fetch("""
            SELECT
                COUNT(*) FILTER (WHERE city IS NULL) as null_city,
                COUNT(*) FILTER (WHERE country IS NULL) as null_country,
                COUNT(*) FILTER (WHERE sector IS NULL) as null_sector,
                COUNT(*) FILTER (WHERE estimated_cost IS NULL) as null_cost,
                COUNT(*) as total
            FROM service20_investment_opportunities
        """)

        print('\nNULL value counts:')
        print('-' * 120)
        nc = null_counts[0]
        print(f"Total opportunities: {nc['total']}")
        print(f"NULL city: {nc['null_city']} ({nc['null_city']/nc['total']*100:.1f}%)")
        print(f"NULL country: {nc['null_country']} ({nc['null_country']/nc['total']*100:.1f}%)")
        print(f"NULL sector: {nc['null_sector']} ({nc['null_sector']/nc['total']*100:.1f}%)")
        print(f"NULL cost: {nc['null_cost']} ({nc['null_cost']/nc['total']*100:.1f}%)")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(check_opportunities())
