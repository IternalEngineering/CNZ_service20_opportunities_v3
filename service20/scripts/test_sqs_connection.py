"""Test SQS connection and queue access."""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
from open_deep_research.sqs_config import get_sqs_manager

load_dotenv()


def test_connection():
    """Test SQS connectivity and queue access."""
    print("=" * 60)
    print("Testing SQS Connection")
    print("=" * 60)
    print()

    # Check credentials
    access_key = os.getenv('AWS_ACCESS_KEY_ID')
    if not access_key:
        print("❌ AWS_ACCESS_KEY_ID not set in .env")
        return False

    print(f"✓ AWS_ACCESS_KEY_ID: {access_key[:8]}...")
    print(f"✓ AWS_REGION: {os.getenv('AWS_REGION', 'eu-west-2')}")
    print()

    # Test queue access
    try:
        print("Testing queue access...")
        sqs = get_sqs_manager()

        queues = [
            ("Investment", sqs.config.investment_queue_url),
            ("Funding", sqs.config.funding_queue_url),
            ("Results", sqs.config.results_queue_url),
        ]

        print()
        for name, url in queues:
            print(f"{name} Queue:")
            print(f"  URL: {url}")

            # Get queue attributes
            attrs = sqs.get_queue_attributes(url)
            available = attrs.get('ApproximateNumberOfMessages', '0')
            in_flight = attrs.get('ApproximateNumberOfMessagesNotVisible', '0')

            print(f"  Messages Available: {available}")
            print(f"  Messages In Flight: {in_flight}")
            print(f"  ✓ Queue accessible")
            print()

        print("=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print()
        print("Troubleshooting:")
        print("  1. Check AWS credentials in .env")
        print("  2. Verify queue URLs are correct")
        print("  3. Ensure IAM policy is attached to your user")
        print("  4. Check AWS region matches queue region")
        return False


if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
