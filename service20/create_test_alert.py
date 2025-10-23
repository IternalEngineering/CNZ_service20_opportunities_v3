"""Quick script to create a test alert to demonstrate dashboard."""

import asyncio
import asyncpg
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


async def create_test_alert():
    """Create a simple test alert in service20_alerts table."""

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set")
        return False

    try:
        conn = await asyncpg.connect(database_url)

        # Create test alert with enhanced metadata
        criteria = {
            "basic_info": {
                "title": "Bristol Solar Energy Initiative",
                "description": "Solar panel installation for municipal buildings",
                "project_type": "solar_energy"
            },
            "sector": {
                "primary": "solar_energy",
                "subsector": "municipal",
                "tags": ["rooftop", "public_buildings"]
            },
            "location": {
                "city": "Bristol",
                "country": "UK",
                "region": "Europe",
                "geoname_id": "Q23154",
                "coordinates": [-2.5879, 51.4545]
            },
            "financial": {
                "amount": 1200000,
                "currency": "GBP",
                "roi_expected": 14.5,
                "payback_years": 7,
                "carbon_reduction_tons_annually": 180
            },
            "timeline": {
                "planning_start": "2025-Q2",
                "execution_start": "2025-Q4",
                "completion": "2026-Q3",
                "deadline": "2025-06-30",
                "urgency": "medium"
            },
            "technical": {
                "technology": "photovoltaic",
                "capacity_mw": 2.8,
                "maturity": "planning"
            },
            "bundling": {
                "eligible": True,
                "minimum_bundle_size": 2500000,
                "maximum_bundle_partners": 3,
                "compatibility_requirements": ["same_sector", "similar_timeline", "europe_region"]
            }
        }

        insert_query = """
            INSERT INTO service20_alerts (
                research_id,
                user_id,
                alert_type,
                title,
                description,
                criteria
            ) VALUES ($1, $2, $3, $4, $5, $6::jsonb)
            RETURNING id;
        """

        alert_id = await conn.fetchval(
            insert_query,
            "bristol-solar-test-001",
            "api-system-user",
            "investment",
            "Bristol Solar Energy Initiative",
            "Solar panel installation project for municipal buildings in Bristol",
            json.dumps(criteria)
        )

        print(f"SUCCESS: Created test alert with ID: {alert_id}")
        print(f"  Research ID: bristol-solar-test-001")
        print(f"  City: Bristol, UK")
        print(f"  Sector: Solar Energy")
        print(f"  Investment: GBP 1,200,000")
        print(f"  ROI: 14.5%")
        print(f"  Carbon Reduction: 180 tons/year")

        await conn.close()
        return True

    except Exception as e:
        print(f"ERROR: Failed to create test alert: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(create_test_alert())
    exit(0 if success else 1)
