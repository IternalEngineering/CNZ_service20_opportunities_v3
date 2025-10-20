"""End-to-end test of Service20 alert system.

This script simulates a complete research completion flow and tests both
database and API alert creation.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv

load_dotenv()

# Color output
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class Fore:
        GREEN = RED = YELLOW = CYAN = MAGENTA = BLUE = WHITE = ""
    class Style:
        BRIGHT = RESET_ALL = ""


def print_header(text):
    """Print section header."""
    print(f"\n{Fore.CYAN}{'=' * 80}")
    print(f"{text}")
    print(f"{'=' * 80}{Style.RESET_ALL}\n")


def print_step(step_num, text):
    """Print test step."""
    print(f"{Fore.YELLOW}[Step {step_num}]{Style.RESET_ALL} {text}")


def print_success(text):
    """Print success message."""
    print(f"{Fore.GREEN}[OK] {text}{Style.RESET_ALL}")


def print_error(text):
    """Print error message."""
    print(f"{Fore.RED}[ERROR] {text}{Style.RESET_ALL}")


async def test_database_alert():
    """Test database alert creation."""
    print_step(1, "Testing Database Alert Creation")
    print("-" * 80)

    try:
        from open_deep_research.database_storage import create_service20_alert

        # Simulate research results
        research_results = {
            "research_id": f"test-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "opportunity_type": "investment",
            "research_brief": "Test research for Bristol renewable energy projects",
            "final_report": "This is a comprehensive test report. " * 50,
            "findings": [
                "Solar panel installation opportunities identified",
                "Wind energy potential in Bristol area",
                "Carbon reduction initiatives available",
                "Green building retrofit opportunities",
                "Electric vehicle charging infrastructure needs"
            ]
        }

        opportunity_data = {
            "title": "TEST: Bristol Green Energy Initiative",
            "location": "Bristol, UK",
            "investment_amount": 750000,
            "roi": 22.5,
            "city_id": "550e8400-e29b-41d4-a716-446655440001"
        }

        print(f"Research ID: {research_results['research_id']}")
        print(f"Opportunity: {opportunity_data['title']}")
        print(f"Findings: {len(research_results['findings'])}")
        print()

        # Create database alert
        alert_id = await create_service20_alert(
            research_results,
            opportunity_data,
            user_id="api-system-user"
        )

        if alert_id:
            print_success(f"Database alert created with ID: {alert_id}")
            return True, alert_id
        else:
            print_error("Failed to create database alert")
            return False, None

    except Exception as e:
        print_error(f"Database alert test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_api_alert():
    """Test API alert creation."""
    print_step(2, "Testing API Alert Creation")
    print("-" * 80)

    try:
        from create_alert_api import create_service20_research_alert

        research_id = f"test-api-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        print(f"Research ID: {research_id}")
        print(f"API URL: {os.getenv('CNZ_API_URL', 'https://stage-cnz.icmserver007.com/api/v2/alerts')}")
        print()

        # Create API alert
        result = create_service20_research_alert(
            research_id=research_id,
            opportunity_type="investment",
            title="TEST: London Sustainability Project",
            location="London, UK",
            findings_count=7,
            geoname_id="Q84",  # London geoname ID
            city_country_code="london-GB"
        )

        if result:
            print_success("API alert created successfully")
            print(f"Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print_error("Failed to create API alert")
            return False

    except Exception as e:
        print_error(f"API alert test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def verify_database_alert(alert_id):
    """Verify the database alert was created."""
    print_step(3, "Verifying Database Alert")
    print("-" * 80)

    try:
        import asyncpg

        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            print_error("DATABASE_URL not set")
            return False

        conn = await asyncpg.connect(database_url)

        # Query the alert
        query = """
            SELECT id, name, description, criteria, is_active, created_at
            FROM alerts
            WHERE id = $1;
        """

        row = await conn.fetchrow(query, alert_id)

        if row:
            print_success("Alert found in database")
            print(f"\nAlert Details:")
            print(f"  ID: {row['id']}")
            print(f"  Name: {row['name']}")
            print(f"  Description: {row['description']}")
            print(f"  Active: {row['is_active']}")
            print(f"  Created: {row['created_at']}")

            criteria = row['criteria']
            # Parse JSON if it's a string
            if isinstance(criteria, str):
                import json
                criteria = json.loads(criteria)

            print(f"\n  Criteria:")
            print(f"    Type: {criteria.get('type')}")
            print(f"    Research ID: {criteria.get('research_id')}")
            print(f"    Opportunity Type: {criteria.get('opportunity_type')}")
            print(f"    Findings Count: {criteria.get('findings_count')}")
            print(f"    Report Length: {criteria.get('report_length'):,} chars")

            await conn.close()
            return True
        else:
            print_error(f"Alert {alert_id} not found in database")
            await conn.close()
            return False

    except Exception as e:
        print_error(f"Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def check_alert_stats():
    """Check overall alert statistics."""
    print_step(4, "Checking Alert Statistics")
    print("-" * 80)

    try:
        from view_alerts import get_alert_stats
        await get_alert_stats()
        return True

    except Exception as e:
        print_error(f"Stats check failed: {e}")
        return False


async def view_service20_alerts():
    """View all Service20 alerts."""
    print_step(5, "Viewing Service20 Alerts")
    print("-" * 80)

    try:
        from view_alerts import get_service20_alerts
        alerts = await get_service20_alerts()

        if alerts:
            print_success(f"Found {len(alerts)} Service20 alert(s)")
            return True
        else:
            print(f"{Fore.YELLOW}No Service20 alerts found yet (this is normal for first run){Style.RESET_ALL}")
            return True

    except Exception as e:
        print_error(f"Alert viewing failed: {e}")
        return False


async def main():
    """Run all tests."""
    print_header("Service20 Alert System - End-to-End Test")

    print(f"Environment:")
    print(f"  DATABASE_URL: {'Set' if os.getenv('DATABASE_URL') else 'Not set'}")
    print(f"  CNZ_API_URL: {os.getenv('CNZ_API_URL', 'Using default')}")
    print(f"  CNZ_API_KEY: {'Set' if os.getenv('CNZ_API_KEY') else 'Using default'}")
    print()

    results = {}

    # Test 1: Database Alert
    db_success, alert_id = await test_database_alert()
    results['database_alert'] = db_success
    print()

    # Test 2: API Alert
    api_success = test_api_alert()
    results['api_alert'] = api_success
    print()

    # Test 3: Verify Database Alert
    if alert_id:
        verify_success = await verify_database_alert(alert_id)
        results['verification'] = verify_success
        print()

    # Test 4: Check Stats
    stats_success = await check_alert_stats()
    results['stats'] = stats_success
    print()

    # Test 5: View Service20 Alerts
    view_success = await view_service20_alerts()
    results['view_alerts'] = view_success
    print()

    # Summary
    print_header("Test Summary")

    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)

    for test_name, success in results.items():
        status = f"{Fore.GREEN}PASS" if success else f"{Fore.RED}FAIL"
        print(f"  {test_name.replace('_', ' ').title()}: {status}{Style.RESET_ALL}")

    print()
    print(f"Results: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print(f"\n{Fore.GREEN}{'=' * 80}")
        print(f"SUCCESS: All tests passed! Alert system is working correctly.")
        print(f"{'=' * 80}{Style.RESET_ALL}\n")
    else:
        print(f"\n{Fore.YELLOW}{'=' * 80}")
        print(f"WARNING: Some tests failed. Check the output above for details.")
        print(f"{'=' * 80}{Style.RESET_ALL}\n")

    # Cleanup instructions
    if alert_id:
        print(f"{Fore.CYAN}Cleanup:{Style.RESET_ALL}")
        print(f"  To delete the test alert, run:")
        print(f"  python -c \"import asyncio; from view_alerts import delete_alert; asyncio.run(delete_alert('{alert_id}'))\"")
        print()


if __name__ == "__main__":
    asyncio.run(main())
