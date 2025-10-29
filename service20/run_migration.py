"""Run database migration to rename bundles to matches."""

import asyncpg
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()


async def run_migration():
    """Execute the migration SQL."""
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    try:
        # Read migration SQL
        with open('migrate_bundles_to_matches.sql', 'r', encoding='utf-8') as f:
            sql = f.read()

        # Execute migration
        print('Running migration...')
        await conn.execute(sql)
        print('SUCCESS: Migration completed')

        # Verify table exists
        result = await conn.fetchval(
            "SELECT EXISTS (SELECT FROM pg_tables WHERE tablename = 'service20_matches')"
        )
        print(f'Table service20_matches exists: {result}')

        # Check new columns
        columns = await conn.fetch("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'service20_matches'
            AND column_name IN ('council_doc_url', 'investor_doc_url', 'provider_doc_url',
                               'overall_match_score', 'match_failed')
        """)

        print(f'New columns added: {len(columns)}')
        for col in columns:
            print(f'  - {col["column_name"]}')

    except Exception as e:
        print(f'ERROR: Migration failed - {str(e)}')
        raise
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(run_migration())
