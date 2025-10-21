"""Setup database schema for Service20."""

import asyncio
import asyncpg
import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()


async def setup_database():
    """Create database tables for Service20."""

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set")
        return False

    try:
        conn = await asyncpg.connect(database_url)

        # Read and execute alerts schema
        alerts_schema_file = Path(__file__).parent / "database_schema_alerts.sql"
        with open(alerts_schema_file, 'r') as f:
            alerts_schema = f.read()

        print("Creating service20_alerts table...")
        await conn.execute(alerts_schema)
        print("SUCCESS: service20_alerts table created successfully")

        # Read and execute matches schema
        matches_schema_file = Path(__file__).parent / "database_schema_matches.sql"
        if matches_schema_file.exists():
            with open(matches_schema_file, 'r') as f:
                matches_schema = f.read()

            print("\nCreating opportunity_matches table...")
            await conn.execute(matches_schema)
            print("SUCCESS: opportunity_matches table created successfully")

        # Read and execute bundles schema
        bundles_schema_file = Path(__file__).parent / "database_schema_bundles.sql"
        if bundles_schema_file.exists():
            with open(bundles_schema_file, 'r') as f:
                bundles_schema = f.read()

            print("\nCreating service20_bundles table...")
            await conn.execute(bundles_schema)
            print("SUCCESS: service20_bundles table created successfully")

        await conn.close()

        print("\n" + "=" * 60)
        print("Database setup completed successfully!")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"Error setting up database: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(setup_database())
    exit(0 if success else 1)
