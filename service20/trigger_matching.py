"""Trigger matching job by sending a match request to SQS.

This script sends a match_request message to the SQS queue, which triggers
the matching agent to process alerts and create bundles.

Usage:
    python trigger_matching.py [--lookback DAYS]

Examples:
    python trigger_matching.py                    # Default 30 days
    python trigger_matching.py --lookback 7       # Last 7 days
    python trigger_matching.py --lookback 60      # Last 60 days
"""

import argparse
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
load_dotenv()

from open_deep_research.sqs_config import MessageType, get_sqs_manager

# Color output
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class Fore:
        GREEN = RED = YELLOW = CYAN = MAGENTA = ""
    class Style:
        BRIGHT = RESET_ALL = ""


def trigger_matching(lookback_days: int = 30):
    """Trigger a matching job via SQS.

    Args:
        lookback_days: How many days back to look for active alerts
    """
    print(f"\n{Fore.CYAN}{'=' * 80}")
    print(f"Triggering Matching Job")
    print(f"{'=' * 80}{Style.RESET_ALL}\n")

    print(f"{Fore.YELLOW}Parameters:{Style.RESET_ALL}")
    print(f"  Lookback Days: {lookback_days}")
    print()

    # Get SQS manager
    sqs_manager = get_sqs_manager()

    # Construct match request payload
    payload = {
        'lookback_days': lookback_days,
        'trigger_source': 'manual',
        'requested_at': sqs_manager._get_timestamp()
    }

    # Send match request message
    print(f"{Fore.YELLOW}Sending match request to SQS...{Style.RESET_ALL}")
    message_id = sqs_manager.send_message(
        sqs_manager.config.match_requests_queue_url,
        MessageType.MATCH_REQUEST,
        payload
    )

    if message_id:
        print(f"{Fore.GREEN}SUCCESS: Match request sent!{Style.RESET_ALL}")
        print(f"  Message ID: {message_id}")
        print(f"  Queue: {sqs_manager.config.match_requests_queue_url}")
        print()
        print(f"{Fore.CYAN}Next steps:{Style.RESET_ALL}")
        print(f"  1. Ensure matching agent is running: python matching_agent.py")
        print(f"  2. Check service20_bundles table for results")
        print(f"  3. Monitor SQS match_results queue for notifications")
        print()
        return True
    else:
        print(f"{Fore.RED}ERROR: Failed to send match request{Style.RESET_ALL}")
        return False


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Trigger matching job via SQS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python trigger_matching.py                    # Default 30 days lookback
  python trigger_matching.py --lookback 7       # Last 7 days
  python trigger_matching.py --lookback 60      # Last 60 days
        """
    )

    parser.add_argument(
        '--lookback',
        type=int,
        default=30,
        help='How many days back to look for active alerts (default: 30)'
    )

    args = parser.parse_args()

    # Trigger matching
    success = trigger_matching(lookback_days=args.lookback)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
