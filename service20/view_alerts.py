"""View and manage Service20 alerts.

This script allows you to view, filter, and manage alerts created by Service20
research completion notifications.
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
import asyncpg

load_dotenv()

# Color output for terminal
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False
    class Fore:
        GREEN = RED = YELLOW = CYAN = MAGENTA = BLUE = WHITE = ""
    class Style:
        BRIGHT = RESET_ALL = ""


def print_header(text, color=Fore.CYAN):
    """Print a formatted header."""
    print(f"\n{color}{'=' * 80}")
    print(f"{text}")
    print(f"{'=' * 80}{Style.RESET_ALL}\n")


def print_section(text, color=Fore.YELLOW):
    """Print a section header."""
    print(f"\n{color}{'-' * 80}")
    print(f"{text}")
    print(f"{'-' * 80}{Style.RESET_ALL}")


async def get_all_alerts(user_id: str = "api-system-user"):
    """Get all alerts for a specific user."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print(f"{Fore.RED}ERROR: DATABASE_URL not set in .env file{Style.RESET_ALL}")
        return []

    try:
        conn = await asyncpg.connect(database_url)

        query = """
            SELECT id, user_id, name, description, criteria, is_active,
                   last_triggered, created_at, city_id
            FROM alerts
            WHERE user_id = $1
            ORDER BY created_at DESC;
        """

        rows = await conn.fetch(query, user_id)
        alerts = [dict(row) for row in rows]

        await conn.close()
        return alerts

    except Exception as e:
        print(f"{Fore.RED}Error fetching alerts: {e}{Style.RESET_ALL}")
        return []


async def get_service20_alerts():
    """Get all Service20 research alerts."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print(f"{Fore.RED}ERROR: DATABASE_URL not set in .env file{Style.RESET_ALL}")
        return []

    try:
        conn = await asyncpg.connect(database_url)

        query = """
            SELECT id, user_id, name, description, criteria, is_active,
                   last_triggered, created_at, city_id
            FROM alerts
            WHERE criteria->>'type' = 'service20_research'
            ORDER BY created_at DESC;
        """

        rows = await conn.fetch(query)
        alerts = [dict(row) for row in rows]

        await conn.close()
        return alerts

    except Exception as e:
        print(f"{Fore.RED}Error fetching Service20 alerts: {e}{Style.RESET_ALL}")
        return []


async def view_all_alerts():
    """View all alerts in the system."""
    print_header("All Alerts", Fore.CYAN)

    alerts = await get_all_alerts()

    if not alerts:
        print(f"{Fore.YELLOW}No alerts found.{Style.RESET_ALL}")
        return

    print(f"{Fore.GREEN}Found {len(alerts)} alert(s):{Style.RESET_ALL}\n")

    for idx, alert in enumerate(alerts, 1):
        criteria = alert.get('criteria', {})
        alert_type = criteria.get('type', 'unknown')

        print_section(f"Alert {idx}: {alert['name'][:60]}", Fore.MAGENTA)

        print(f"{Fore.WHITE}ID:{Style.RESET_ALL} {alert['id']}")
        print(f"{Fore.WHITE}User ID:{Style.RESET_ALL} {alert['user_id']}")
        print(f"{Fore.WHITE}Type:{Style.RESET_ALL} {alert_type}")
        print(f"{Fore.WHITE}Active:{Style.RESET_ALL} {'Yes' if alert['is_active'] else 'No'}")
        print(f"{Fore.WHITE}Created:{Style.RESET_ALL} {alert['created_at']}")

        if alert['description']:
            print(f"{Fore.WHITE}Description:{Style.RESET_ALL} {alert['description']}")

        if alert['last_triggered']:
            print(f"{Fore.WHITE}Last Triggered:{Style.RESET_ALL} {alert['last_triggered']}")
        else:
            print(f"{Fore.WHITE}Last Triggered:{Style.RESET_ALL} Never")

        if alert_type == 'service20_research':
            research_id = criteria.get('research_id')
            opportunity_type = criteria.get('opportunity_type')
            findings_count = criteria.get('findings_count')
            report_length = criteria.get('report_length')

            print(f"\n{Fore.CYAN}Service20 Research Details:{Style.RESET_ALL}")
            print(f"  Research ID: {research_id}")
            print(f"  Opportunity Type: {opportunity_type}")
            print(f"  Findings Count: {findings_count}")
            print(f"  Report Length: {report_length:,} characters")

        print()


async def view_service20_alerts():
    """View Service20 research alerts only."""
    print_header("Service20 Research Alerts", Fore.CYAN)

    alerts = await get_service20_alerts()

    if not alerts:
        print(f"{Fore.YELLOW}No Service20 research alerts found.{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Alerts will be created automatically when Service20 agents complete research.{Style.RESET_ALL}")
        return

    print(f"{Fore.GREEN}Found {len(alerts)} Service20 alert(s):{Style.RESET_ALL}\n")

    for idx, alert in enumerate(alerts, 1):
        criteria = alert.get('criteria', {})

        print_section(f"Research Alert {idx}", Fore.MAGENTA)

        print(f"{Fore.WHITE}ID:{Style.RESET_ALL} {alert['id']}")
        print(f"{Fore.WHITE}Name:{Style.RESET_ALL} {alert['name']}")
        print(f"{Fore.WHITE}Active:{Style.RESET_ALL} {'Yes' if alert['is_active'] else 'No'}")
        print(f"{Fore.WHITE}Created:{Style.RESET_ALL} {alert['created_at']}")
        print(f"\n{Fore.WHITE}Description:{Style.RESET_ALL}")
        print(f"{alert['description']}\n")

        # Research details
        research_id = criteria.get('research_id')
        opportunity_type = criteria.get('opportunity_type')
        findings_count = criteria.get('findings_count', 0)
        report_length = criteria.get('report_length', 0)
        opportunity_data = criteria.get('opportunity_data', {})

        print(f"{Fore.CYAN}Research Details:{Style.RESET_ALL}")
        print(f"  Research ID: {research_id}")
        print(f"  Type: {opportunity_type}")
        print(f"  Findings: {findings_count}")
        print(f"  Report Size: {report_length:,} chars")

        if opportunity_data:
            print(f"\n{Fore.CYAN}Opportunity Data:{Style.RESET_ALL}")
            if 'title' in opportunity_data:
                print(f"  Title: {opportunity_data['title']}")
            if 'location' in opportunity_data:
                print(f"  Location: {opportunity_data['location']}")
            if 'investment_amount' in opportunity_data:
                print(f"  Investment: £{opportunity_data['investment_amount']:,.2f}")
            if 'roi' in opportunity_data:
                print(f"  ROI: {opportunity_data['roi']}%")

        print()


async def delete_alert(alert_id: str):
    """Delete an alert by ID."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print(f"{Fore.RED}ERROR: DATABASE_URL not set{Style.RESET_ALL}")
        return False

    try:
        conn = await asyncpg.connect(database_url)

        query = "DELETE FROM alerts WHERE id = $1 RETURNING id;"
        result = await conn.fetchval(query, alert_id)

        await conn.close()

        if result:
            print(f"{Fore.GREEN}✓ Alert {alert_id} deleted successfully{Style.RESET_ALL}")
            return True
        else:
            print(f"{Fore.RED}Alert {alert_id} not found{Style.RESET_ALL}")
            return False

    except Exception as e:
        print(f"{Fore.RED}Error deleting alert: {e}{Style.RESET_ALL}")
        return False


async def toggle_alert(alert_id: str):
    """Toggle an alert's active status."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print(f"{Fore.RED}ERROR: DATABASE_URL not set{Style.RESET_ALL}")
        return False

    try:
        conn = await asyncpg.connect(database_url)

        # Get current status
        current = await conn.fetchval(
            "SELECT is_active FROM alerts WHERE id = $1",
            alert_id
        )

        if current is None:
            print(f"{Fore.RED}Alert {alert_id} not found{Style.RESET_ALL}")
            await conn.close()
            return False

        # Toggle status
        new_status = not current
        await conn.execute(
            "UPDATE alerts SET is_active = $1, updated_at = $2 WHERE id = $3",
            new_status,
            datetime.now(),
            alert_id
        )

        await conn.close()

        status_text = "activated" if new_status else "deactivated"
        print(f"{Fore.GREEN}✓ Alert {alert_id} {status_text}{Style.RESET_ALL}")
        return True

    except Exception as e:
        print(f"{Fore.RED}Error toggling alert: {e}{Style.RESET_ALL}")
        return False


async def get_alert_stats():
    """Get statistics about alerts."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print(f"{Fore.RED}ERROR: DATABASE_URL not set{Style.RESET_ALL}")
        return

    try:
        conn = await asyncpg.connect(database_url)

        # Get total counts
        total = await conn.fetchval("SELECT COUNT(*) FROM alerts")
        active = await conn.fetchval("SELECT COUNT(*) FROM alerts WHERE is_active = true")
        service20 = await conn.fetchval(
            "SELECT COUNT(*) FROM alerts WHERE criteria->>'type' = 'service20_research'"
        )
        triggered = await conn.fetchval(
            "SELECT COUNT(*) FROM alerts WHERE last_triggered IS NOT NULL"
        )

        await conn.close()

        print_header("Alert Statistics", Fore.CYAN)
        print(f"{Fore.WHITE}Total Alerts:{Style.RESET_ALL} {total}")
        print(f"{Fore.WHITE}Active Alerts:{Style.RESET_ALL} {active}")
        print(f"{Fore.WHITE}Service20 Alerts:{Style.RESET_ALL} {service20}")
        print(f"{Fore.WHITE}Triggered Alerts:{Style.RESET_ALL} {triggered}")
        print()

    except Exception as e:
        print(f"{Fore.RED}Error fetching stats: {e}{Style.RESET_ALL}")


def main():
    """Main menu."""
    options = {
        "1": ("View All Alerts", view_all_alerts),
        "2": ("View Service20 Alerts Only", view_service20_alerts),
        "3": ("Alert Statistics", get_alert_stats),
        "4": ("Delete Alert", lambda: delete_alert(input("Enter alert ID: ").strip())),
        "5": ("Toggle Alert Status", lambda: toggle_alert(input("Enter alert ID: ").strip())),
    }

    print_header("Service20 Alert Manager", Fore.GREEN)

    print("Select an option:")
    print()
    for key, (desc, _) in options.items():
        print(f"  {key}. {desc}")
    print("  q. Quit")
    print()

    choice = input(f"{Fore.CYAN}Enter choice: {Style.RESET_ALL}").strip().lower()

    if choice == 'q':
        print("Goodbye!")
        return

    if choice in options:
        _, func = options[choice]
        asyncio.run(func())
    else:
        print(f"{Fore.RED}Invalid choice!{Style.RESET_ALL}")


if __name__ == "__main__":
    main()
