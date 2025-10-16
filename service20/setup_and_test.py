"""Setup database and run a quick test of the Service20 agents."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


async def setup_database():
    """Create the database table if it doesn't exist."""
    print("=" * 60)
    print("Step 1: Setting up PostgreSQL database table")
    print("=" * 60)
    print()

    from dotenv import load_dotenv
    load_dotenv()

    import os
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("⚠️  DATABASE_URL not set in .env file")
        print("   Research will only be saved to SQS, not PostgreSQL")
        print()
        return False

    # Run create table script
    from create_research_table import create_table
    try:
        await create_table()
        print()
        return True
    except Exception as e:
        print(f"❌ Failed to create table: {e}")
        print()
        return False


async def test_sqs_queues():
    """Test SQS queue connectivity."""
    print("=" * 60)
    print("Step 2: Testing SQS queue connectivity")
    print("=" * 60)
    print()

    from open_deep_research.sqs_config import get_sqs_manager

    try:
        sqs = get_sqs_manager()

        print(f"✓ Investment Queue: {sqs.config.investment_queue_url}")
        print(f"✓ Funding Queue: {sqs.config.funding_queue_url}")
        print(f"✓ Results Queue: {sqs.config.results_queue_url}")
        print()

        # Check queue status
        queues = [
            ("Investment", sqs.config.investment_queue_url),
            ("Funding", sqs.config.funding_queue_url),
            ("Results", sqs.config.results_queue_url),
        ]

        for name, url in queues:
            attrs = sqs.get_queue_attributes(url)
            available = attrs.get('ApproximateNumberOfMessages', 0)
            print(f"  {name} Queue: {available} messages available")

        print()
        return True

    except Exception as e:
        print(f"❌ SQS connection failed: {e}")
        print()
        return False


async def send_test_opportunity():
    """Send a single test opportunity."""
    print("=" * 60)
    print("Step 3: Sending test investment opportunity")
    print("=" * 60)
    print()

    from open_deep_research.sqs_config import get_sqs_manager

    sqs = get_sqs_manager()

    # Simple test opportunity
    opportunity = {
        "opportunity_id": "TEST-001",
        "title": "Test Solar Farm",
        "description": "Small test solar farm for validation",
        "location": "Test Location",
        "sector": "Solar Energy",
        "investment_amount": 1000000,
        "roi": 12.0
    }

    try:
        message_id = sqs.send_investment_opportunity(opportunity)
        print(f"✓ Sent test opportunity with message ID: {message_id}")
        print(f"  Title: {opportunity['title']}")
        print(f"  Investment: ${opportunity['investment_amount']:,}")
        print()
        return True

    except Exception as e:
        print(f"❌ Failed to send message: {e}")
        print()
        return False


async def run_quick_research():
    """Run research on the test opportunity."""
    print("=" * 60)
    print("Step 4: Running research (this will take 2-3 minutes)")
    print("=" * 60)
    print()

    from langchain_core.runnables import RunnableConfig
    from open_deep_research.sqs_integration import ResearchOrchestrator

    # Use cheaper model for testing
    config = RunnableConfig(
        configurable={
            "research_model": "gpt-4o-mini",
            "compression_model": "gpt-4o-mini",
            "max_concurrent_research_units": 1,
            "allow_clarification": False,
        }
    )

    orchestrator = ResearchOrchestrator(config)

    opportunity = {
        "id": "TEST-001",
        "title": "Test Solar Farm",
        "description": "Small test solar farm for validation",
        "location": "Test Location",
        "sector": "Solar Energy",
        "investment_amount": 1000000,
        "roi": 12.0
    }

    try:
        print("Starting research...")
        result = await orchestrator.conduct_research_for_opportunity(
            opportunity,
            opportunity_type="investment"
        )

        if result:
            print()
            print("✓ Research completed!")
            print(f"  Research ID: {result['research_id']}")
            print(f"  Report Length: {len(result['final_report']):,} characters")
            print(f"  Findings: {len(result['findings'])} items")

            if 'database_id' in result:
                print(f"  Database ID: {result['database_id']}")
                print("  ✓ Saved to PostgreSQL")
            else:
                print("  ⚠️  Not saved to PostgreSQL (DATABASE_URL not set)")

            print()

            # Send to results queue
            message_id = await orchestrator.send_research_results(result)
            print(f"✓ Sent to results queue: {message_id}")
            print()

            return True
        else:
            print("❌ Research failed")
            print()
            return False

    except Exception as e:
        print(f"❌ Research error: {e}")
        print()
        return False


async def verify_results():
    """Verify results are in both SQS and database."""
    print("=" * 60)
    print("Step 5: Verifying results")
    print("=" * 60)
    print()

    # Check SQS
    from open_deep_research.sqs_config import get_sqs_manager

    sqs = get_sqs_manager()
    messages = sqs.receive_research_results()

    print(f"SQS Results Queue: {len(messages)} message(s)")
    if messages:
        print("  ✓ Research results found in SQS")
    print()

    # Check database
    from open_deep_research.database_storage import get_research_from_database

    try:
        records = await get_research_from_database(limit=5)
        print(f"PostgreSQL Database: {len(records)} record(s)")
        if records:
            print("  ✓ Research results found in database")
            print()
            print("  Latest record:")
            latest = records[0]
            print(f"    ID: {latest['id']}")
            print(f"    Query: {latest['query']}")
            print(f"    Created: {latest['created_at']}")
        else:
            print("  ⚠️  No records in database")
        print()

    except Exception as e:
        print(f"  ⚠️  Could not query database: {e}")
        print()


async def main():
    """Run full setup and test."""
    print("\n" + "=" * 60)
    print("Service20 Setup and Quick Test")
    print("=" * 60)
    print()

    # Step 1: Setup database
    db_ok = await setup_database()

    # Step 2: Test SQS
    sqs_ok = await test_sqs_queues()

    if not sqs_ok:
        print("❌ Cannot continue without SQS connectivity")
        print("   Please check your AWS credentials in .env")
        return

    # Ask user if they want to run research
    print("Ready to run research test.")
    print("This will:")
    print("  1. Send a test investment opportunity to the queue")
    print("  2. Run deep research (takes 2-3 minutes)")
    print("  3. Save results to SQS and PostgreSQL")
    print("  4. Cost: ~$0.02-0.05 with gpt-4o-mini")
    print()

    response = input("Proceed with research test? (y/N): ").strip().lower()

    if response != 'y':
        print("\nTest cancelled. You can run research later with:")
        print("  python examples/sqs_research_integration_example.py")
        return

    print()

    # Step 3: Send test opportunity
    sent_ok = await send_test_opportunity()

    if not sent_ok:
        print("❌ Cannot continue without sending message")
        return

    # Step 4: Run research
    research_ok = await run_quick_research()

    if not research_ok:
        print("❌ Research failed")
        return

    # Step 5: Verify results
    await verify_results()

    print("=" * 60)
    print("✓ Setup and test complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. View results: python query_results.py")
    print("  2. Send more opportunities: python examples/sqs_basic_example.py")
    print("  3. Process queue: python examples/sqs_research_integration_example.py")
    print()


if __name__ == "__main__":
    asyncio.run(main())
