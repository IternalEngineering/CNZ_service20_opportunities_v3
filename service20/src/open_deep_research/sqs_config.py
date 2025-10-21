"""AWS SQS configuration and message queue management for inter-agent communication.

This module provides SQS queue management for communication between the investment
opportunities agent and the funding opportunities agent in service20.
"""

import json
import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError

# Configure logging
logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """Message types for agent communication."""

    INVESTMENT_OPPORTUNITY = "investment_opportunity"
    FUNDING_OPPORTUNITY = "funding_opportunity"
    RESEARCH_REQUEST = "research_request"
    RESEARCH_COMPLETE = "research_complete"
    MATCH_REQUEST = "match_request"
    MATCH_RESULT = "match_result"
    MATCH_FOUND = "match_found"                      # NEW: Successful match proposal
    MATCH_APPROVAL_NEEDED = "match_approval_needed"  # NEW: Low/medium confidence matches
    MATCH_STATUS_CHANGE = "match_status_change"      # NEW: Match status updates


@dataclass
class QueueConfig:
    """Configuration for SQS queues."""

    # Queue URLs (set from environment or created dynamically)
    investment_queue_url: Optional[str] = None
    funding_queue_url: Optional[str] = None
    results_queue_url: Optional[str] = None
    match_requests_queue_url: Optional[str] = None   # NEW: Trigger matching
    match_results_queue_url: Optional[str] = None    # NEW: Match proposals
    match_approvals_queue_url: Optional[str] = None  # NEW: Matches needing approval

    # AWS configuration
    region: str = "eu-west-2"

    # Queue names (defaults)
    investment_queue_name: str = "service20-investment-opportunities"
    funding_queue_name: str = "service20-funding-opportunities"
    results_queue_name: str = "service20-research-results"
    match_requests_queue_name: str = "service20-match-requests"  # NEW
    match_results_queue_name: str = "service20-match-results"    # NEW
    match_approvals_queue_name: str = "service20-match-approvals"  # NEW

    # Message settings
    visibility_timeout: int = 300  # 5 minutes
    message_retention: int = 345600  # 4 days
    receive_wait_time: int = 20  # Long polling
    max_messages: int = 10


class SQSManager:
    """Manager for AWS SQS operations and message handling."""

    def __init__(self, config: Optional[QueueConfig] = None):
        """Initialize SQS manager with configuration.

        Args:
            config: Queue configuration, uses defaults if not provided
        """
        self.config = config or QueueConfig()

        # Initialize boto3 SQS client
        self.sqs_client = boto3.client(
            'sqs',
            region_name=self.config.region,
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )

        # Load queue URLs from environment or create queues
        self._initialize_queues()

    def _initialize_queues(self) -> None:
        """Initialize queue URLs from environment or create new queues."""
        # Try to get URLs from environment first
        self.config.investment_queue_url = os.getenv('SQS_INVESTMENT_QUEUE_URL')
        self.config.funding_queue_url = os.getenv('SQS_FUNDING_QUEUE_URL')
        self.config.results_queue_url = os.getenv('SQS_RESULTS_QUEUE_URL')
        self.config.match_requests_queue_url = os.getenv('SQS_MATCH_REQUESTS_QUEUE_URL')
        self.config.match_results_queue_url = os.getenv('SQS_MATCH_RESULTS_QUEUE_URL')
        self.config.match_approvals_queue_url = os.getenv('SQS_MATCH_APPROVALS_QUEUE_URL')

        # Create queues if URLs not provided
        if not self.config.investment_queue_url:
            self.config.investment_queue_url = self.create_queue(
                self.config.investment_queue_name
            )

        if not self.config.funding_queue_url:
            self.config.funding_queue_url = self.create_queue(
                self.config.funding_queue_name
            )

        if not self.config.results_queue_url:
            self.config.results_queue_url = self.create_queue(
                self.config.results_queue_name
            )

        if not self.config.match_requests_queue_url:
            self.config.match_requests_queue_url = self.create_queue(
                self.config.match_requests_queue_name
            )

        if not self.config.match_results_queue_url:
            self.config.match_results_queue_url = self.create_queue(
                self.config.match_results_queue_name
            )

        if not self.config.match_approvals_queue_url:
            self.config.match_approvals_queue_url = self.create_queue(
                self.config.match_approvals_queue_name
            )

        logger.info(f"Initialized SQS queues:")
        logger.info(f"  Investment: {self.config.investment_queue_url}")
        logger.info(f"  Funding: {self.config.funding_queue_url}")
        logger.info(f"  Results: {self.config.results_queue_url}")
        logger.info(f"  Match Requests: {self.config.match_requests_queue_url}")
        logger.info(f"  Match Results: {self.config.match_results_queue_url}")
        logger.info(f"  Match Approvals: {self.config.match_approvals_queue_url}")

    def create_queue(self, queue_name: str) -> str:
        """Create an SQS queue or get existing queue URL.

        Args:
            queue_name: Name of the queue to create

        Returns:
            Queue URL

        Raises:
            ClientError: If queue creation fails
        """
        try:
            response = self.sqs_client.create_queue(
                QueueName=queue_name,
                Attributes={
                    'VisibilityTimeout': str(self.config.visibility_timeout),
                    'MessageRetentionPeriod': str(self.config.message_retention),
                    'ReceiveMessageWaitTimeSeconds': str(self.config.receive_wait_time)
                }
            )
            queue_url = response['QueueUrl']
            logger.info(f"Created/Retrieved queue: {queue_name} -> {queue_url}")
            return queue_url

        except ClientError as e:
            logger.error(f"Failed to create queue {queue_name}: {e}")
            raise

    def send_message(
        self,
        queue_url: str,
        message_type: MessageType,
        payload: Dict[str, Any],
        delay_seconds: int = 0
    ) -> Optional[str]:
        """Send a message to an SQS queue.

        Args:
            queue_url: URL of the target queue
            message_type: Type of message being sent
            payload: Message payload dictionary
            delay_seconds: Delay before message becomes available (0-900 seconds)

        Returns:
            Message ID if successful, None otherwise
        """
        try:
            # Construct message with metadata
            message_body = {
                'type': message_type.value,
                'payload': payload,
                'timestamp': self._get_timestamp()
            }

            response = self.sqs_client.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps(message_body),
                DelaySeconds=delay_seconds,
                MessageAttributes={
                    'MessageType': {
                        'StringValue': message_type.value,
                        'DataType': 'String'
                    }
                }
            )

            message_id = response.get('MessageId')
            logger.info(f"Sent message {message_id} to queue {queue_url}")
            return message_id

        except (BotoCoreError, ClientError) as e:
            logger.error(f"Failed to send message to {queue_url}: {e}")
            return None

    def receive_messages(
        self,
        queue_url: str,
        max_messages: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Receive messages from an SQS queue.

        Args:
            queue_url: URL of the queue to receive from
            max_messages: Maximum number of messages to receive (1-10)

        Returns:
            List of message dictionaries
        """
        try:
            max_msgs = max_messages or self.config.max_messages

            response = self.sqs_client.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=min(max_msgs, 10),
                WaitTimeSeconds=self.config.receive_wait_time,
                MessageAttributeNames=['All']
            )

            messages = response.get('Messages', [])
            logger.info(f"Received {len(messages)} messages from {queue_url}")

            # Parse message bodies
            parsed_messages = []
            for msg in messages:
                try:
                    body = json.loads(msg['Body'])
                    parsed_messages.append({
                        'message_id': msg['MessageId'],
                        'receipt_handle': msg['ReceiptHandle'],
                        'type': body.get('type'),
                        'payload': body.get('payload'),
                        'timestamp': body.get('timestamp'),
                        'raw_message': msg
                    })
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse message {msg['MessageId']}: {e}")

            return parsed_messages

        except (BotoCoreError, ClientError) as e:
            logger.error(f"Failed to receive messages from {queue_url}: {e}")
            return []

    def delete_message(self, queue_url: str, receipt_handle: str) -> bool:
        """Delete a message from an SQS queue after processing.

        Args:
            queue_url: URL of the queue
            receipt_handle: Receipt handle from received message

        Returns:
            True if deletion successful, False otherwise
        """
        try:
            self.sqs_client.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=receipt_handle
            )
            logger.info(f"Deleted message from {queue_url}")
            return True

        except (BotoCoreError, ClientError) as e:
            logger.error(f"Failed to delete message from {queue_url}: {e}")
            return False

    def purge_queue(self, queue_url: str) -> bool:
        """Purge all messages from a queue (use with caution).

        Args:
            queue_url: URL of the queue to purge

        Returns:
            True if purge successful, False otherwise
        """
        try:
            self.sqs_client.purge_queue(QueueUrl=queue_url)
            logger.warning(f"Purged all messages from {queue_url}")
            return True

        except (BotoCoreError, ClientError) as e:
            logger.error(f"Failed to purge queue {queue_url}: {e}")
            return False

    def get_queue_attributes(self, queue_url: str) -> Dict[str, Any]:
        """Get queue attributes and statistics.

        Args:
            queue_url: URL of the queue

        Returns:
            Dictionary of queue attributes
        """
        try:
            response = self.sqs_client.get_queue_attributes(
                QueueUrl=queue_url,
                AttributeNames=['All']
            )
            return response.get('Attributes', {})

        except (BotoCoreError, ClientError) as e:
            logger.error(f"Failed to get queue attributes for {queue_url}: {e}")
            return {}

    @staticmethod
    def _get_timestamp() -> str:
        """Get current UTC timestamp in ISO format."""
        from datetime import datetime
        return datetime.utcnow().isoformat() + 'Z'

    # Convenience methods for specific queues

    def send_investment_opportunity(self, payload: Dict[str, Any]) -> Optional[str]:
        """Send investment opportunity to the investment queue."""
        return self.send_message(
            self.config.investment_queue_url,
            MessageType.INVESTMENT_OPPORTUNITY,
            payload
        )

    def send_funding_opportunity(self, payload: Dict[str, Any]) -> Optional[str]:
        """Send funding opportunity to the funding queue."""
        return self.send_message(
            self.config.funding_queue_url,
            MessageType.FUNDING_OPPORTUNITY,
            payload
        )

    def send_research_result(self, payload: Dict[str, Any]) -> Optional[str]:
        """Send research result to the results queue."""
        return self.send_message(
            self.config.results_queue_url,
            MessageType.RESEARCH_COMPLETE,
            payload
        )

    def receive_investment_opportunities(self) -> List[Dict[str, Any]]:
        """Receive investment opportunities from the queue."""
        return self.receive_messages(self.config.investment_queue_url)

    def receive_funding_opportunities(self) -> List[Dict[str, Any]]:
        """Receive funding opportunities from the queue."""
        return self.receive_messages(self.config.funding_queue_url)

    def receive_research_results(self) -> List[Dict[str, Any]]:
        """Receive research results from the queue."""
        return self.receive_messages(self.config.results_queue_url)


# Global SQS manager instance (lazy initialization)
_sqs_manager: Optional[SQSManager] = None


def get_sqs_manager() -> SQSManager:
    """Get or create the global SQS manager instance.

    Returns:
        SQSManager instance
    """
    global _sqs_manager
    if _sqs_manager is None:
        _sqs_manager = SQSManager()
    return _sqs_manager
