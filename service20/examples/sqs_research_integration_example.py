"""Example of using SQS with deep research integration.

This script demonstrates how to use the enhanced handlers that automatically
trigger deep research for investment and funding opportunities.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from langchain_core.runnables import RunnableConfig

from open_deep_research.sqs_integration import (
    ResearchOrchestrator,
    run_enhanced_investment_handler,
    run_enhanced_funding_handler,
    run_enhanced_handlers_parallel,
)
from open_deep_research.sqs_config import get_sqs_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def manual_research_example():
    """Example of manually triggering research for an opportunity."""
    print("=" * 60)
    print("Manual Research Trigger Example")
    print("=" * 60)
    print()

    # Create research orchestrator
    config = RunnableConfig(
        configurable={
            "research_model": "gpt-4o",
            "compression_model": "gpt-4o-mini",
            "max_concurrent_research_units": 3,
            "allow_clarification": False,
        }
    )

    orchestrator = ResearchOrchestrator(config)

    # Example investment opportunity
    opportunity = {
        "id": "INV-TEST-001",
        "title": "Smart Grid Battery Storage System",
        "description": """
        Development of a 100MWh grid-scale battery storage system to support
        renewable energy integration. The system will store excess solar and wind
        energy during peak generation and release it during high demand periods.
        Located near major renewable energy installations in Scotland.
        """.strip(),
        "location": "Scotland, UK",
        "sector": "Energy Storage",
        "investment_amount": 45000000,
        "roi": 16.8,
        "risk_level": "medium",
    }

    print("Triggering deep research for investment opportunity...")
    print(f"Title: {opportunity['title']}")
    print(f"Investment: £{opportunity['investment_amount']:,.2f}")
    print()
    print("This will take 2-5 minutes depending on research complexity...")
    print()

    # Conduct research
    result = await orchestrator.conduct_research_for_opportunity(
        opportunity,
        opportunity_type="investment"
    )

    if result:
        print("\n" + "=" * 60)
        print("Research Completed!")
        print("=" * 60)
        print(f"\nResearch Brief:\n{result['research_brief']}\n")
        print(f"Report Length: {len(result['final_report'])} characters")
        print(f"Number of findings: {len(result['findings'])}")

        # Save report to file
        output_file = Path(__file__).parent / "research_output.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"# Research Report\n\n")
            f.write(f"## Opportunity: {opportunity['title']}\n\n")
            f.write(f"**Investment Amount:** £{opportunity['investment_amount']:,.2f}\n\n")
            f.write(f"**Location:** {opportunity['location']}\n\n")
            f.write(f"## Research Brief\n\n{result['research_brief']}\n\n")
            f.write(f"## Final Report\n\n{result['final_report']}\n")

        print(f"\n✓ Report saved to: {output_file}")
    else:
        print("\n✗ Research failed")

    print("\n" + "=" * 60)


async def enhanced_handler_example():
    """Example of running enhanced handler with automatic research."""
    print("=" * 60)
    print("Enhanced Handler Example (Automatic Research)")
    print("=" * 60)
    print()

    # Configure LangGraph
    config = RunnableConfig(
        configurable={
            "research_model": "gpt-4o",
            "compression_model": "gpt-4o-mini",
            "final_report_model": "gpt-4o",
            "max_concurrent_research_units": 2,
            "max_researcher_iterations": 10,
            "allow_clarification": False,
        }
    )

    print("Starting enhanced investment handler...")
    print("This will automatically research any investment opportunities in the queue.")
    print()
    print("Configuration:")
    print(f"  Research Model: gpt-4o")
    print(f"  Compression Model: gpt-4o-mini")
    print(f"  Max Research Units: 2")
    print()
    print("Press Ctrl+C to stop")
    print()

    try:
        # Run handler for 5 iterations
        await run_enhanced_investment_handler(config, max_iterations=5)
        print("\n✓ Completed processing")
    except KeyboardInterrupt:
        print("\nStopped by user")


async def parallel_handlers_example():
    """Example of running both handlers in parallel."""
    print("=" * 60)
    print("Parallel Enhanced Handlers Example")
    print("=" * 60)
    print()

    # Configure LangGraph
    config = RunnableConfig(
        configurable={
            "research_model": "gpt-4o-mini",  # Use cheaper model for demo
            "compression_model": "gpt-4o-mini",
            "max_concurrent_research_units": 2,
            "allow_clarification": False,
        }
    )

    print("Starting both investment and funding handlers in parallel...")
    print("Each will automatically trigger research for opportunities.")
    print()
    print("Press Ctrl+C to stop")
    print()

    try:
        # Run both handlers for up to 3 iterations each
        await run_enhanced_handlers_parallel(config, max_iterations=3)
        print("\n✓ Completed processing")
    except KeyboardInterrupt:
        print("\nStopped by user")


async def send_and_process_example():
    """Example of sending a message and immediately processing it."""
    print("=" * 60)
    print("Send and Process Example")
    print("=" * 60)
    print()

    sqs = get_sqs_manager()

    # Send test opportunity
    opportunity = {
        "opportunity_id": "INV-DEMO-001",
        "title": "Green Hydrogen Production Facility",
        "description": """
        Development of a 10MW green hydrogen production facility powered by
        renewable energy. The facility will produce hydrogen through electrolysis
        for use in transport and industry. Includes electrolyzer installation,
        renewable energy connection, hydrogen storage, and distribution infrastructure.
        """.strip(),
        "location": "North East England",
        "sector": "Hydrogen Energy",
        "investment_amount": 15000000,
        "roi": 14.2,
        "risk_level": "medium",
        "timeline": "30 months",
    }

    print("Sending investment opportunity to queue...")
    message_id = sqs.send_investment_opportunity(opportunity)
    print(f"✓ Sent with message ID: {message_id}")
    print()

    # Wait a moment for message to be available
    await asyncio.sleep(2)

    print("Now processing the message with enhanced handler...")
    print()

    # Configure and run handler
    config = RunnableConfig(
        configurable={
            "research_model": "gpt-4o",
            "compression_model": "gpt-4o-mini",
            "max_concurrent_research_units": 2,
            "allow_clarification": False,
        }
    )

    try:
        # Process just one message
        await run_enhanced_investment_handler(config, max_iterations=1)
        print("\n✓ Processing completed")
    except Exception as e:
        print(f"\n✗ Error: {e}")


async def monitor_results_queue_example():
    """Example of monitoring the research results queue."""
    print("=" * 60)
    print("Monitor Research Results Example")
    print("=" * 60)
    print()

    sqs = get_sqs_manager()

    print("Checking for research results...")
    messages = sqs.receive_research_results()

    if not messages:
        print("No research results available yet.")
        print()
        print("Tip: Run the enhanced handler example first to generate results.")
    else:
        print(f"Found {len(messages)} research result(s):\n")

        for idx, msg in enumerate(messages, 1):
            payload = msg['payload']

            print(f"Result {idx}:")
            print(f"  Research ID: {payload.get('research_id')}")
            print(f"  Type: {payload.get('opportunity_type')}")
            print(f"  Brief: {payload.get('research_brief', 'N/A')[:100]}...")
            print(f"  Report Length: {len(payload.get('final_report', ''))} chars")
            print()

            # Optionally delete the message
            # sqs.delete_message(sqs.config.results_queue_url, msg['receipt_handle'])

    print("=" * 60)


def main():
    """Main function with menu."""
    examples = {
        "1": ("Manual research trigger", manual_research_example),
        "2": ("Enhanced handler (auto research)", enhanced_handler_example),
        "3": ("Parallel handlers", parallel_handlers_example),
        "4": ("Send and process", send_and_process_example),
        "5": ("Monitor results queue", monitor_results_queue_example),
    }

    print("\n" + "=" * 60)
    print("SQS + Deep Research Integration Examples")
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
