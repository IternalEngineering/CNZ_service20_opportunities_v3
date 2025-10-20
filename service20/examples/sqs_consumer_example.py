"""Example of consuming messages from SQS queues and processing them.

This script demonstrates how to set up message handlers to process
investment and funding opportunities from the queues.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from open_deep_research.message_handlers import (
    process_investment_opportunities_queue,
    process_funding_opportunities_queue,
    run_all_handlers_parallel,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def simple_consumer_example():
    """Simple example of consuming from a single queue."""
    print("=" * 60)
    print("Simple Consumer Example")
    print("=" * 60)
    print()
    print("Processing investment opportunities queue...")
    print("Press Ctrl+C to stop")
    print()

    try:
        # Process up to 5 iterations (or until no messages)
        await process_investment_opportunities_queue(max_iterations=5)
    except KeyboardInterrupt:
        print("\nStopped by user")


async def parallel_consumer_example():
    """Example of consuming from multiple queues in parallel."""
    print("=" * 60)
    print("Parallel Consumer Example")
    print("=" * 60)
    print()
    print("Processing all queues in parallel...")
    print("Press Ctrl+C to stop")
    print()

    try:
        # Process all queues simultaneously
        await run_all_handlers_parallel(max_iterations=10)
    except KeyboardInterrupt:
        print("\nStopped by user")


async def custom_handler_example():
    """Example of using custom message handlers."""
    from open_deep_research.message_handlers import InvestmentOpportunityHandler
    from open_deep_research.sqs_config import MessageType

    print("=" * 60)
    print("Custom Handler Example")
    print("=" * 60)
    print()

    # Create custom handler class
    class CustomInvestmentHandler(InvestmentOpportunityHandler):
        """Custom handler with additional processing."""

        async def handle_investment_opportunity(self, payload, message):
            """Custom handling for investment opportunities."""
            print(f"\n{'=' * 60}")
            print(f"Processing Investment Opportunity")
            print(f"{'=' * 60}")
            print(f"ID: {payload.get('opportunity_id')}")
            print(f"Title: {payload.get('title')}")
            print(f"Location: {payload.get('location')}")
            print(f"Investment: £{payload.get('investment_amount', 0):,.2f}")
            print(f"ROI: {payload.get('roi', 0)}%")

            # Extract net zero impact if available
            impact = payload.get('net_zero_impact', {})
            if impact:
                print(f"\nNet Zero Impact:")
                print(f"  CO2 Reduction: {impact.get('co2_reduction_tons_per_year', 0):,.0f} tons/year")
                if 'equivalent_homes_powered' in impact:
                    print(f"  Homes Powered: {impact.get('equivalent_homes_powered', 0):,.0f}")

            print(f"{'=' * 60}\n")

            # Add custom processing logic here
            # For example: score the opportunity, match with funding, etc.

    # Create and run custom handler
    handler = CustomInvestmentHandler()

    print("Processing with custom handler...")
    print("Press Ctrl+C to stop")
    print()

    try:
        await handler.poll_and_process(
            handler.sqs.config.investment_queue_url,
            max_iterations=5
        )
    except KeyboardInterrupt:
        print("\nStopped by user")


async def monitoring_example():
    """Example of monitoring queue status."""
    from open_deep_research.sqs_config import get_sqs_manager

    print("=" * 60)
    print("Queue Monitoring Example")
    print("=" * 60)
    print()

    sqs = get_sqs_manager()

    queues = [
        ("Investment Opportunities", sqs.config.investment_queue_url),
        ("Funding Opportunities", sqs.config.funding_queue_url),
        ("Research Results", sqs.config.results_queue_url),
    ]

    for queue_name, queue_url in queues:
        print(f"\n{queue_name}:")
        print(f"  URL: {queue_url}")

        attrs = sqs.get_queue_attributes(queue_url)
        print(f"  Messages Available: {attrs.get('ApproximateNumberOfMessages', 0)}")
        print(f"  Messages In Flight: {attrs.get('ApproximateNumberOfMessagesNotVisible', 0)}")
        print(f"  Oldest Message Age: {attrs.get('ApproximateAgeOfOldestMessage', 0)} seconds")

    print("\n" + "=" * 60)


async def receive_without_delete_example():
    """Example of receiving messages without deleting them."""
    from open_deep_research.sqs_config import get_sqs_manager

    print("=" * 60)
    print("Peek Messages Example (No Deletion)")
    print("=" * 60)
    print()

    sqs = get_sqs_manager()

    print("Peeking at investment opportunities queue...")
    messages = sqs.receive_messages(sqs.config.investment_queue_url, max_messages=3)

    if not messages:
        print("No messages available in queue")
    else:
        for idx, msg in enumerate(messages, 1):
            print(f"\nMessage {idx}:")
            print(f"  Type: {msg['type']}")
            print(f"  Timestamp: {msg['timestamp']}")

            payload = msg['payload']
            print(f"  Title: {payload.get('title', 'N/A')}")
            print(f"  ID: {payload.get('opportunity_id') or payload.get('funding_id', 'N/A')}")

            # Note: Messages will become visible again after visibility timeout
            print("  (Message NOT deleted - will reappear after visibility timeout)")

    print("\n" + "=" * 60)


def main():
    """Main function with menu."""
    examples = {
        "1": ("Simple consumer (single queue)", simple_consumer_example),
        "2": ("Parallel consumer (all queues)", parallel_consumer_example),
        "3": ("Custom handler", custom_handler_example),
        "4": ("Monitor queue status", monitoring_example),
        "5": ("Peek messages (no deletion)", receive_without_delete_example),
    }

    print("\n" + "=" * 60)
    print("SQS Consumer Examples")
    print("=" * 60)
    print("\nSelect an example to run:")
    print()
    for key, (desc, _) in examples.items():
        print(f"  {key}. {desc}")
    print("  q. Quit")
    print()

    choice = input("Enter choice: ").strip().lower()

    if choice == 'q':
        print("Goodbye!")
        return

    if choice in examples:
        _, example_func = examples[choice]
        print()
        asyncio.run(example_func())
    else:
        print("Invalid choice!")


if __name__ == "__main__":
    main()
