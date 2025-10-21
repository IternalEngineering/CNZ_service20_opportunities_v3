"""Monitor SQS queues using AWS CLI or boto3.

This script provides real-time monitoring of service20 SQS queues.
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional

try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


class QueueMonitor:
    """Monitor SQS queues using boto3 or AWS CLI."""

    def __init__(self, use_cli: bool = False):
        """Initialize queue monitor.

        Args:
            use_cli: Use AWS CLI instead of boto3
        """
        self.use_cli = use_cli or not HAS_BOTO3

        if not self.use_cli:
            # Get region from environment or default to eu-west-2
            region = os.getenv('AWS_REGION', 'eu-west-2')
            self.sqs = boto3.client('sqs', region_name=region)
        else:
            # Verify AWS CLI is installed
            try:
                subprocess.run(['aws', '--version'], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("Error: AWS CLI not found. Please install it first.")
                print("See AWS_CLI_SETUP.md for installation instructions.")
                sys.exit(1)

        self.queue_names = [
            'service20-investment-opportunities',
            'service20-funding-opportunities',
            'service20-research-results'
        ]

    def get_queue_url(self, queue_name: str) -> Optional[str]:
        """Get queue URL by name.

        Args:
            queue_name: Name of the queue

        Returns:
            Queue URL or None if not found
        """
        if not self.use_cli:
            try:
                response = self.sqs.get_queue_url(QueueName=queue_name)
                return response['QueueUrl']
            except (BotoCoreError, ClientError):
                return None
        else:
            try:
                result = subprocess.run(
                    ['aws', 'sqs', 'get-queue-url', '--queue-name', queue_name],
                    capture_output=True,
                    text=True,
                    check=True
                )
                data = json.loads(result.stdout)
                return data['QueueUrl']
            except (subprocess.CalledProcessError, json.JSONDecodeError):
                return None

    def get_queue_attributes(self, queue_url: str) -> Dict:
        """Get queue attributes.

        Args:
            queue_url: Queue URL

        Returns:
            Dictionary of queue attributes
        """
        if not self.use_cli:
            try:
                response = self.sqs.get_queue_attributes(
                    QueueUrl=queue_url,
                    AttributeNames=['All']
                )
                return response.get('Attributes', {})
            except (BotoCoreError, ClientError) as e:
                print(f"Error getting attributes: {e}")
                return {}
        else:
            try:
                result = subprocess.run(
                    ['aws', 'sqs', 'get-queue-attributes',
                     '--queue-url', queue_url,
                     '--attribute-names', 'All'],
                    capture_output=True,
                    text=True,
                    check=True
                )
                data = json.loads(result.stdout)
                return data.get('Attributes', {})
            except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
                print(f"Error getting attributes: {e}")
                return {}

    def format_queue_stats(self, queue_name: str, attrs: Dict) -> str:
        """Format queue statistics for display.

        Args:
            queue_name: Name of the queue
            attrs: Queue attributes

        Returns:
            Formatted string
        """
        available = int(attrs.get('ApproximateNumberOfMessages', 0))
        in_flight = int(attrs.get('ApproximateNumberOfMessagesNotVisible', 0))
        delayed = int(attrs.get('ApproximateNumberOfMessagesDelayed', 0))
        oldest = int(attrs.get('ApproximateAgeOfOldestMessage', 0))

        # Color coding
        status = "🟢"  # Green
        if available > 100:
            status = "🔴"  # Red
        elif available > 50:
            status = "🟡"  # Yellow

        output = [
            f"{status} {queue_name}",
            f"  Available: {available:,}",
            f"  In Flight: {in_flight:,}",
            f"  Delayed: {delayed:,}",
        ]

        if oldest > 0:
            age_mins = oldest // 60
            output.append(f"  Oldest Message: {age_mins} minutes ago")

        return "\n".join(output)

    def monitor_once(self) -> None:
        """Monitor all queues once."""
        print(f"\n{'=' * 60}")
        print(f"Queue Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'=' * 60}\n")

        for queue_name in self.queue_names:
            queue_url = self.get_queue_url(queue_name)

            if not queue_url:
                print(f"❌ {queue_name}: Queue not found")
                continue

            attrs = self.get_queue_attributes(queue_url)
            print(self.format_queue_stats(queue_name, attrs))
            print()

    def monitor_continuous(self, interval: int = 5) -> None:
        """Monitor queues continuously.

        Args:
            interval: Refresh interval in seconds
        """
        try:
            while True:
                # Clear screen
                os.system('cls' if os.name == 'nt' else 'clear')

                self.monitor_once()

                print(f"Refreshing every {interval} seconds... (Ctrl+C to stop)")
                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n\nMonitoring stopped.")

    def check_queue_health(self) -> bool:
        """Check health of all queues.

        Returns:
            True if all queues are healthy
        """
        all_healthy = True

        for queue_name in self.queue_names:
            queue_url = self.get_queue_url(queue_name)

            if not queue_url:
                print(f"❌ {queue_name}: Queue not found")
                all_healthy = False
                continue

            attrs = self.get_queue_attributes(queue_url)
            available = int(attrs.get('ApproximateNumberOfMessages', 0))
            oldest = int(attrs.get('ApproximateAgeOfOldestMessage', 0))

            # Health checks
            if available > 100:
                print(f"⚠️  {queue_name}: High queue depth ({available} messages)")
                all_healthy = False

            if oldest > 1800:  # 30 minutes
                age_mins = oldest // 60
                print(f"⚠️  {queue_name}: Old messages ({age_mins} minutes)")
                all_healthy = False

        if all_healthy:
            print("✅ All queues are healthy")

        return all_healthy

    def get_summary(self) -> Dict:
        """Get summary of all queues.

        Returns:
            Dictionary with queue statistics
        """
        summary = {
            'timestamp': datetime.now().isoformat(),
            'queues': {}
        }

        for queue_name in self.queue_names:
            queue_url = self.get_queue_url(queue_name)

            if not queue_url:
                summary['queues'][queue_name] = {'status': 'not_found'}
                continue

            attrs = self.get_queue_attributes(queue_url)
            summary['queues'][queue_name] = {
                'status': 'ok',
                'available': int(attrs.get('ApproximateNumberOfMessages', 0)),
                'in_flight': int(attrs.get('ApproximateNumberOfMessagesNotVisible', 0)),
                'delayed': int(attrs.get('ApproximateNumberOfMessagesDelayed', 0)),
                'oldest_age_seconds': int(attrs.get('ApproximateAgeOfOldestMessage', 0))
            }

        return summary


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(description='Monitor SQS queues')
    parser.add_argument(
        '--mode',
        choices=['once', 'continuous', 'health', 'json'],
        default='once',
        help='Monitoring mode'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=5,
        help='Refresh interval for continuous mode (seconds)'
    )
    parser.add_argument(
        '--use-cli',
        action='store_true',
        help='Use AWS CLI instead of boto3'
    )

    args = parser.parse_args()

    monitor = QueueMonitor(use_cli=args.use_cli)

    if args.mode == 'once':
        monitor.monitor_once()
    elif args.mode == 'continuous':
        monitor.monitor_continuous(interval=args.interval)
    elif args.mode == 'health':
        healthy = monitor.check_queue_health()
        sys.exit(0 if healthy else 1)
    elif args.mode == 'json':
        summary = monitor.get_summary()
        print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
