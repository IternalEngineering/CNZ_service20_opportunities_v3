"""Fetch real alerts data from database and generate JSON for dashboard."""

import asyncio
import asyncpg
import json
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()


async def fetch_alerts_data():
    """Fetch all alerts from the database."""

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set")
        return None

    try:
        conn = await asyncpg.connect(database_url)

        # Fetch all service20 alerts
        query = """
            SELECT
                id,
                research_id,
                user_id,
                alert_type,
                title,
                description,
                criteria,
                created_at,
                updated_at,
                status
            FROM service20_alerts
            ORDER BY created_at DESC;
        """

        rows = await conn.fetch(query)
        await conn.close()

        # Convert to JSON-serializable format
        alerts = []
        for row in rows:
            criteria = row['criteria'] if row['criteria'] else {}

            alert = {
                'id': str(row['id']),
                'research_id': row['research_id'],
                'type': row['alert_type'],
                'title': criteria.get('basic_info', {}).get('title', 'N/A'),
                'location': criteria.get('location', {}).get('city', 'Unknown'),
                'sector': criteria.get('sector', {}).get('primary', 'unknown'),
                'status': 'completed',
                'started': row['created_at'].strftime('%Y-%m-%d %H:%M:%S') if row['created_at'] else 'N/A',
                'duration': 'N/A',
                'alertCreated': True,
                'investment_amount': criteria.get('financial', {}).get('amount', 0),
                'roi': criteria.get('financial', {}).get('roi_expected', 0),
                'carbon_reduction': criteria.get('financial', {}).get('carbon_reduction_tons_annually', 0),
            }
            alerts.append(alert)

        print(f"Fetched {len(alerts)} alerts from database")
        return alerts

    except Exception as e:
        print(f"Error fetching alerts: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Main function to fetch data and save to JSON."""

    alerts = await fetch_alerts_data()

    if alerts:
        # Save to JSON file
        output_file = Path(__file__).parent / "dashboard_data.json"

        data = {
            'alerts': alerts,
            'generated_at': datetime.utcnow().isoformat()
        }

        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"\nData saved to: {output_file}")
        print(f"Total alerts: {len(alerts)}")

        # Print summary
        print("\nAlert Summary:")
        for alert in alerts[:5]:  # Show first 5
            print(f"  - {alert['title']} ({alert['location']}) - {alert['sector']}")

        if len(alerts) > 5:
            print(f"  ... and {len(alerts) - 5} more")
    else:
        print("No data to save")


if __name__ == "__main__":
    asyncio.run(main())
