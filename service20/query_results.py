"""Query and view results from Service20 agents.

This script provides multiple ways to query results:
1. Query SQS Results Queue (latest research outputs)
2. Query PostgreSQL Database (historical research)
3. Monitor Queue Status (check what's pending)
4. View specific opportunity details
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


async def query_sqs_results():
    """Query the SQS results queue for recent research outputs."""
    from open_deep_research.sqs_config import get_sqs_manager

    print_header("SQS Results Queue", Fore.CYAN)

    sqs = get_sqs_manager()

    print(f"Queue URL: {sqs.config.results_queue_url}")
    print()

    # Get queue attributes
    attrs = sqs.get_queue_attributes(sqs.config.results_queue_url)
    available = int(attrs.get('ApproximateNumberOfMessages', 0))
    in_flight = int(attrs.get('ApproximateNumberOfMessagesNotVisible', 0))

    print(f"Messages Available: {available}")
    print(f"Messages In Flight: {in_flight}")
    print()

    if available == 0:
        print(f"{Fore.YELLOW}No research results available in the queue.")
        print("Tip: Results appear here after agents complete research.{Style.RESET_ALL}")
        return

    # Receive messages
    print(f"Fetching up to {min(available, 10)} results...")
    messages = sqs.receive_messages(sqs.config.results_queue_url, max_messages=10)

    if not messages:
        print(f"{Fore.YELLOW}No messages retrieved (they may be in flight).{Style.RESET_ALL}")
        return

    print(f"\n{Fore.GREEN}Found {len(messages)} research result(s):{Style.RESET_ALL}\n")

    for idx, msg in enumerate(messages, 1):
        payload = msg['payload']

        print_section(f"Result {idx}: {payload.get('research_id', 'N/A')}", Fore.MAGENTA)

        print(f"{Fore.WHITE}Research ID:{Style.RESET_ALL} {payload.get('research_id', 'N/A')}")
        print(f"{Fore.WHITE}Type:{Style.RESET_ALL} {payload.get('opportunity_type', 'N/A')}")
        print(f"{Fore.WHITE}Timestamp:{Style.RESET_ALL} {msg.get('timestamp', 'N/A')}")
        print()

        # Research brief
        brief = payload.get('research_brief', '')
        if brief:
            print(f"{Fore.WHITE}Research Brief:{Style.RESET_ALL}")
            print(brief[:300] + ('...' if len(brief) > 300 else ''))
            print()

        # Report stats
        report = payload.get('final_report', '')
        findings = payload.get('findings', [])

        print(f"{Fore.WHITE}Report Length:{Style.RESET_ALL} {len(report):,} characters")
        print(f"{Fore.WHITE}Findings Count:{Style.RESET_ALL} {len(findings)}")
        print()

        # Show first 500 chars of report
        if report:
            print(f"{Fore.WHITE}Report Preview:{Style.RESET_ALL}")
            print(report[:500] + ('...' if len(report) > 500 else ''))
            print()

        # Option to save
        save = input(f"{Fore.CYAN}Save full report to file? (y/N): {Style.RESET_ALL}").strip().lower()
        if save == 'y':
            filename = f"research_{payload.get('research_id', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            filepath = Path(__file__).parent / "research_results" / filename
            filepath.parent.mkdir(exist_ok=True)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# Research Report\n\n")
                f.write(f"**Research ID:** {payload.get('research_id')}\n")
                f.write(f"**Type:** {payload.get('opportunity_type')}\n")
                f.write(f"**Timestamp:** {msg.get('timestamp')}\n\n")
                f.write(f"## Research Brief\n\n{brief}\n\n")
                f.write(f"## Final Report\n\n{report}\n\n")

                if findings:
                    f.write(f"## Findings\n\n")
                    for i, finding in enumerate(findings, 1):
                        f.write(f"### Finding {i}\n\n{finding}\n\n")

            print(f"{Fore.GREEN}✓ Saved to: {filepath}{Style.RESET_ALL}")

        # Option to delete
        delete = input(f"{Fore.CYAN}Delete this message from queue? (y/N): {Style.RESET_ALL}").strip().lower()
        if delete == 'y':
            sqs.delete_message(sqs.config.results_queue_url, msg['receipt_handle'])
            print(f"{Fore.GREEN}✓ Message deleted{Style.RESET_ALL}")

        print()


async def query_database_results():
    """Query PostgreSQL database for historical research results."""
    import asyncpg

    print_header("PostgreSQL Database Results", Fore.CYAN)

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print(f"{Fore.RED}ERROR: DATABASE_URL not set in .env file{Style.RESET_ALL}")
        return

    try:
        conn = await asyncpg.connect(database_url)

        # Get all records
        rows = await conn.fetch("""
            SELECT id, query, tool_calls_count, database_tools_used,
                   web_tools_used, created_at,
                   LENGTH(final_report) as report_length
            FROM service20_investment_opportunities
            ORDER BY created_at DESC
            LIMIT 20;
        """)

        if not rows:
            print(f"{Fore.YELLOW}No research results found in database.{Style.RESET_ALL}")
            await conn.close()
            return

        print(f"{Fore.GREEN}Found {len(rows)} research result(s) in database:{Style.RESET_ALL}\n")

        for idx, row in enumerate(rows, 1):
            print_section(f"Result {idx}: {row['query'][:50]}...", Fore.MAGENTA)

            print(f"{Fore.WHITE}ID:{Style.RESET_ALL} {row['id']}")
            print(f"{Fore.WHITE}Query:{Style.RESET_ALL} {row['query']}")
            print(f"{Fore.WHITE}Created:{Style.RESET_ALL} {row['created_at']}")
            print(f"{Fore.WHITE}Tool Calls:{Style.RESET_ALL} {row['tool_calls_count']}")
            print(f"{Fore.WHITE}Database Tools:{Style.RESET_ALL} {row['database_tools_used'] or '(none)'}")
            print(f"{Fore.WHITE}Web Tools:{Style.RESET_ALL} {row['web_tools_used'] or '(none)'}")
            print(f"{Fore.WHITE}Report Length:{Style.RESET_ALL} {row['report_length']:,} characters")
            print()

        # Option to view full report
        view_id = input(f"{Fore.CYAN}Enter ID to view full report (or press Enter to skip): {Style.RESET_ALL}").strip()
        if view_id:
            row = await conn.fetchrow("""
                SELECT id, query, final_report, created_at
                FROM service20_investment_opportunities
                WHERE id = $1;
            """, int(view_id))

            if row:
                print_section(f"Full Report - ID {row['id']}", Fore.BLUE)
                print(f"{Fore.WHITE}Query:{Style.RESET_ALL} {row['query']}")
                print(f"{Fore.WHITE}Created:{Style.RESET_ALL} {row['created_at']}")
                print()
                print(row['final_report'])
                print()

                # Option to save
                save = input(f"{Fore.CYAN}Save report to file? (y/N): {Style.RESET_ALL}").strip().lower()
                if save == 'y':
                    filename = f"database_report_{row['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                    filepath = Path(__file__).parent / "research_results" / filename
                    filepath.parent.mkdir(exist_ok=True)

                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(f"# Research Report (Database)\n\n")
                        f.write(f"**ID:** {row['id']}\n")
                        f.write(f"**Query:** {row['query']}\n")
                        f.write(f"**Created:** {row['created_at']}\n\n")
                        f.write(row['final_report'])

                    print(f"{Fore.GREEN}✓ Saved to: {filepath}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}No record found with ID {view_id}{Style.RESET_ALL}")

        await conn.close()

    except Exception as e:
        print(f"{Fore.RED}Error querying database: {e}{Style.RESET_ALL}")


async def monitor_queue_status():
    """Monitor the status of all SQS queues."""
    from open_deep_research.sqs_config import get_sqs_manager

    print_header("Queue Status Monitor", Fore.CYAN)

    sqs = get_sqs_manager()

    queues = [
        ("Investment Opportunities", sqs.config.investment_queue_url),
        ("Funding Opportunities", sqs.config.funding_queue_url),
        ("Research Results", sqs.config.results_queue_url),
    ]

    for queue_name, queue_url in queues:
        print_section(queue_name, Fore.YELLOW)
        print(f"{Fore.WHITE}URL:{Style.RESET_ALL} {queue_url}")

        attrs = sqs.get_queue_attributes(queue_url)
        available = int(attrs.get('ApproximateNumberOfMessages', 0))
        in_flight = int(attrs.get('ApproximateNumberOfMessagesNotVisible', 0))
        oldest_age = int(attrs.get('ApproximateAgeOfOldestMessage', 0))

        print(f"{Fore.WHITE}Messages Available:{Style.RESET_ALL} {available}")
        print(f"{Fore.WHITE}Messages In Flight:{Style.RESET_ALL} {in_flight}")

        if oldest_age > 0:
            minutes = oldest_age // 60
            seconds = oldest_age % 60
            print(f"{Fore.WHITE}Oldest Message Age:{Style.RESET_ALL} {minutes}m {seconds}s")

        print()


async def peek_queues():
    """Peek at messages in queues without deleting them."""
    from open_deep_research.sqs_config import get_sqs_manager

    print_header("Peek Queue Messages", Fore.CYAN)

    sqs = get_sqs_manager()

    queues = [
        ("Investment Opportunities", sqs.config.investment_queue_url),
        ("Funding Opportunities", sqs.config.funding_queue_url),
    ]

    for queue_name, queue_url in queues:
        print_section(queue_name, Fore.YELLOW)

        messages = sqs.receive_messages(queue_url, max_messages=5)

        if not messages:
            print(f"{Fore.YELLOW}No messages in queue{Style.RESET_ALL}")
            print()
            continue

        print(f"{Fore.GREEN}Found {len(messages)} message(s):{Style.RESET_ALL}\n")

        for idx, msg in enumerate(messages, 1):
            payload = msg['payload']
            msg_type = msg['type']

            print(f"{Fore.WHITE}{idx}. {msg_type}{Style.RESET_ALL}")

            if 'opportunity_id' in payload:
                print(f"   ID: {payload['opportunity_id']}")
                print(f"   Title: {payload.get('title', 'N/A')}")
                print(f"   Location: {payload.get('location', 'N/A')}")
                print(f"   Investment: £{payload.get('investment_amount', 0):,.2f}")
                print(f"   ROI: {payload.get('roi', 0)}%")
            elif 'funding_id' in payload:
                print(f"   ID: {payload['funding_id']}")
                print(f"   Title: {payload.get('title', 'N/A')}")
                print(f"   Funder: {payload.get('funder', 'N/A')}")
                print(f"   Amount: £{payload.get('amount_available', 0):,.2f}")
                print(f"   Deadline: {payload.get('deadline', 'N/A')}")

            print()

        print(f"{Fore.CYAN}Note: Messages were NOT deleted and will be visible again after timeout.{Style.RESET_ALL}")
        print()


async def search_by_keyword():
    """Search database results by keyword."""
    import asyncpg

    print_header("Search Database by Keyword", Fore.CYAN)

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print(f"{Fore.RED}ERROR: DATABASE_URL not set{Style.RESET_ALL}")
        return

    keyword = input(f"{Fore.CYAN}Enter search keyword: {Style.RESET_ALL}").strip()
    if not keyword:
        print(f"{Fore.RED}No keyword provided{Style.RESET_ALL}")
        return

    try:
        conn = await asyncpg.connect(database_url)

        rows = await conn.fetch("""
            SELECT id, query, created_at, LENGTH(final_report) as report_length
            FROM service20_investment_opportunities
            WHERE query ILIKE $1 OR final_report ILIKE $1
            ORDER BY created_at DESC
            LIMIT 10;
        """, f'%{keyword}%')

        if not rows:
            print(f"{Fore.YELLOW}No results found for '{keyword}'{Style.RESET_ALL}")
        else:
            print(f"{Fore.GREEN}Found {len(rows)} result(s):{Style.RESET_ALL}\n")

            for idx, row in enumerate(rows, 1):
                print(f"{idx}. ID {row['id']}: {row['query']}")
                print(f"   Created: {row['created_at']} | Report: {row['report_length']:,} chars")
                print()

        await conn.close()

    except Exception as e:
        print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")


def main():
    """Main menu."""
    options = {
        "1": ("Query SQS Results Queue", query_sqs_results),
        "2": ("Query PostgreSQL Database", query_database_results),
        "3": ("Monitor Queue Status", monitor_queue_status),
        "4": ("Peek Queue Messages", peek_queues),
        "5": ("Search by Keyword", search_by_keyword),
    }

    print_header("Service20 Query Tool", Fore.GREEN)

    print("Select query type:")
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
