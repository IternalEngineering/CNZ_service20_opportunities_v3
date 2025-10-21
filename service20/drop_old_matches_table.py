"""Drop the old opportunity_matches table (no longer needed).

The matching system now uses service20_bundles table instead.
This script safely drops the old opportunity_matches table if it exists.
"""

import asyncio
import asyncpg
import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

# Color output
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class Fore:
        GREEN = RED = YELLOW = CYAN = MAGENTA = ""
    class Style:
        BRIGHT = RESET_ALL = ""


async def drop_old_table():
    """Drop opportunity_matches table if it exists."""

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print(f"{Fore.RED}ERROR: DATABASE_URL not set{Style.RESET_ALL}")
        return False

    try:
        conn = await asyncpg.connect(database_url)

        # Check if table exists
        exists_query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'opportunity_matches'
            );
        """

        table_exists = await conn.fetchval(exists_query)

        if table_exists:
            print(f"{Fore.YELLOW}Found opportunity_matches table{Style.RESET_ALL}")

            # Check if there's any data
            count_query = "SELECT COUNT(*) FROM opportunity_matches;"
            count = await conn.fetchval(count_query)

            if count > 0:
                print(f"{Fore.YELLOW}Table contains {count} records{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}WARNING: This data will be permanently deleted!{Style.RESET_ALL}")
                print()
                response = input(f"Type 'YES' to confirm deletion: ")

                if response != 'YES':
                    print(f"{Fore.YELLOW}Aborted. Table not dropped.{Style.RESET_ALL}")
                    await conn.close()
                    return False

            # Drop the table
            drop_query = "DROP TABLE IF EXISTS opportunity_matches CASCADE;"
            await conn.execute(drop_query)

            print(f"{Fore.GREEN}SUCCESS: opportunity_matches table dropped{Style.RESET_ALL}")
            print(f"  The matching system now uses service20_bundles table")
            print()
        else:
            print(f"{Fore.CYAN}INFO: opportunity_matches table does not exist (already removed){Style.RESET_ALL}")

        await conn.close()
        return True

    except Exception as e:
        print(f"{Fore.RED}ERROR: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print(f"\n{Fore.CYAN}{'=' * 80}")
    print(f"Drop Old Opportunity Matches Table")
    print(f"{'=' * 80}{Style.RESET_ALL}\n")

    print(f"{Fore.YELLOW}This script will drop the old opportunity_matches table.{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}The new matching system uses service20_bundles table instead.{Style.RESET_ALL}")
    print()

    success = asyncio.run(drop_old_table())

    if success:
        print(f"\n{Fore.GREEN}{'=' * 80}")
        print(f"Migration Complete!")
        print(f"{'=' * 80}{Style.RESET_ALL}\n")
        print(f"Next steps:")
        print(f"  1. Use matching_agent.py for all matching operations")
        print(f"  2. Query service20_bundles table for match results")
        print(f"  3. Trigger matching with: python trigger_matching.py")
        print()

    exit(0 if success else 1)
