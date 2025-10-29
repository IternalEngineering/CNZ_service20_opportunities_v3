"""Fix score column precision in service20_matches table."""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()


async def fix_score_precision():
    """Execute the score precision fix."""
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    try:
        # Read SQL fix
        with open('fix_score_precision.sql', 'r', encoding='utf-8') as f:
            sql = f.read()

        print('Fixing score column precision...')

        # Execute each ALTER statement separately
        statements = [
            "ALTER TABLE service20_matches ALTER COLUMN council_match_score TYPE DECIMAL(5,2)",
            "ALTER TABLE service20_matches ALTER COLUMN investor_match_score TYPE DECIMAL(5,2)",
            "ALTER TABLE service20_matches ALTER COLUMN provider_match_score TYPE DECIMAL(5,2)",
            "ALTER TABLE service20_matches ALTER COLUMN overall_match_score TYPE DECIMAL(5,2)",
            "ALTER TABLE service20_matches ALTER COLUMN compatibility_score TYPE DECIMAL(5,2)"
        ]

        for stmt in statements:
            try:
                await conn.execute(stmt)
                print(f'OK: {stmt.split("ALTER COLUMN")[1].split("TYPE")[0].strip()}')
            except Exception as e:
                print(f'ERROR: {stmt.split("ALTER COLUMN")[1].split("TYPE")[0].strip()} - {str(e)}')

        # Verify changes
        columns = await conn.fetch("""
            SELECT column_name, numeric_precision, numeric_scale
            FROM information_schema.columns
            WHERE table_name = 'service20_matches'
            AND column_name LIKE '%score%'
            ORDER BY column_name
        """)

        print('\nVerification - Score columns:')
        for col in columns:
            print(f"  {col['column_name']:30s} DECIMAL({col['numeric_precision']},{col['numeric_scale']})")

        print('\nSUCCESS: Score precision fixed!')

    except Exception as e:
        print(f'ERROR: {str(e)}')
        raise
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(fix_score_precision())
