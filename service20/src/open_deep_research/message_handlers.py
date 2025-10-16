"""Message handlers for processing investment and funding opportunities.

This module provides handlers for processing messages from SQS queues, including
investment opportunities, funding opportunities, and research requests.
"""

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional

from open_deep_research.sqs_config import (
    MessageType,
    SQSManager,
    get_sqs_manager,
)

# Configure logging
logger = logging.getLogger(__name__)


class MessageHandler:
    """Base class for handling SQS messages."""

    def __init__(self, sqs_manager: Optional[SQSManager] = None):
        """Initialize message handler.

        Args:
            sqs_manager: SQS manager instance, creates new if not provided
        """
        self.sqs = sqs_manager or get_sqs_manager()
        self.handlers: Dict[MessageType, Callable] = {}

    def register_handler(
        self,
        message_type: MessageType,
        handler: Callable
    ) -> None:
        """Register a handler function for a message type.

        Args:
            message_type: Type of message to handle
            handler: Async function to handle the message
        """
        self.handlers[message_type] = handler
        logger.info(f"Registered handler for {message_type.value}")

    async def process_message(self, message: Dict[str, Any]) -> bool:
        """Process a single message.

        Args:
            message: Message dictionary from SQS

        Returns:
            True if processing successful, False otherwise
        """
        try:
            message_type = MessageType(message.get('type'))
            payload = message.get('payload', {})

            # Find and execute handler
            handler = self.handlers.get(message_type)
            if handler:
                logger.info(f"Processing {message_type.value} message: {message.get('message_id')}")
                await handler(payload, message)
                return True
            else:
                logger.warning(f"No handler registered for {message_type.value}")
                return False

        except Exception as e:
            logger.error(f"Error processing message {message.get('message_id')}: {e}")
            return False

    async def poll_and_process(
        self,
        queue_url: str,
        max_iterations: Optional[int] = None,
        delete_after_processing: bool = True
    ) -> None:
        """Poll a queue and process messages.

        Args:
            queue_url: URL of the queue to poll
            max_iterations: Maximum number of polling iterations (None = infinite)
            delete_after_processing: Whether to delete messages after successful processing
        """
        iteration = 0
        logger.info(f"Starting message polling for queue: {queue_url}")

        while max_iterations is None or iteration < max_iterations:
            try:
                # Receive messages
                messages = self.sqs.receive_messages(queue_url)

                if not messages:
                    logger.debug("No messages received, continuing...")
                    iteration += 1
                    continue

                # Process each message
                for message in messages:
                    success = await self.process_message(message)

                    # Delete message if processing successful
                    if success and delete_after_processing:
                        self.sqs.delete_message(
                            queue_url,
                            message['receipt_handle']
                        )

                iteration += 1

            except KeyboardInterrupt:
                logger.info("Polling interrupted by user")
                break
            except Exception as e:
                logger.error(f"Error during polling: {e}")
                await asyncio.sleep(5)  # Wait before retrying
                iteration += 1


class NetZeroInvestmentOpportunityHandler(MessageHandler):
    """Handler for Net Zero investment opportunity messages.

    This agent identifies and analyzes potential Net Zero investment opportunities,
    conducts deep research on their feasibility, and attempts to match them with
    available funding sources.
    """

    def __init__(self, sqs_manager: Optional[SQSManager] = None):
        """Initialize investment opportunity handler."""
        super().__init__(sqs_manager)

        # Register default handlers
        self.register_handler(
            MessageType.INVESTMENT_OPPORTUNITY,
            self.handle_investment_opportunity
        )
        self.register_handler(
            MessageType.RESEARCH_REQUEST,
            self.handle_research_request
        )

    async def handle_investment_opportunity(
        self,
        payload: Dict[str, Any],
        message: Dict[str, Any]
    ) -> None:
        """Handle investment opportunity message.

        Args:
            payload: Message payload containing opportunity details
            message: Full message dictionary
        """
        logger.info(f"Processing investment opportunity: {payload.get('opportunity_id')}")

        # Extract opportunity details
        opportunity_id = payload.get('opportunity_id')
        title = payload.get('title')
        description = payload.get('description')
        location = payload.get('location')
        investment_amount = payload.get('investment_amount')
        roi = payload.get('roi')

        logger.info(f"Opportunity: {title}")
        logger.info(f"Location: {location}")
        logger.info(f"Investment: ${investment_amount:,.2f}")
        logger.info(f"Expected ROI: {roi}%")

        # TODO: Implement matching logic with funding opportunities
        # This could trigger a research task or funding search

    async def handle_research_request(
        self,
        payload: Dict[str, Any],
        message: Dict[str, Any]
    ) -> None:
        """Handle research request for an investment opportunity.

        Args:
            payload: Message payload containing research request
            message: Full message dictionary
        """
        logger.info(f"Processing research request: {payload.get('request_id')}")

        research_topic = payload.get('topic')
        context = payload.get('context', {})

        logger.info(f"Research topic: {research_topic}")

        # TODO: Trigger deep research workflow
        # This would integrate with the deep_researcher.py workflow


class NetZeroFundingOpportunityHandler(MessageHandler):
    """Handler for Net Zero funding opportunity messages.

    This agent identifies and analyzes available funding sources for Net Zero projects,
    conducts deep research on funder requirements and priorities, and attempts to match
    them with suitable investment opportunities.
    """

    def __init__(self, sqs_manager: Optional[SQSManager] = None):
        """Initialize funding opportunity handler."""
        super().__init__(sqs_manager)

        # Register default handlers
        self.register_handler(
            MessageType.FUNDING_OPPORTUNITY,
            self.handle_funding_opportunity
        )
        self.register_handler(
            MessageType.MATCH_REQUEST,
            self.handle_match_request
        )

    async def handle_funding_opportunity(
        self,
        payload: Dict[str, Any],
        message: Dict[str, Any]
    ) -> None:
        """Handle funding opportunity message.

        Args:
            payload: Message payload containing funding details
            message: Full message dictionary
        """
        logger.info(f"Processing funding opportunity: {payload.get('funding_id')}")

        # Extract funding details
        funding_id = payload.get('funding_id')
        title = payload.get('title')
        description = payload.get('description')
        funder = payload.get('funder')
        amount_available = payload.get('amount_available')
        deadline = payload.get('deadline')
        eligible_sectors = payload.get('eligible_sectors', [])

        logger.info(f"Funding: {title}")
        logger.info(f"Funder: {funder}")
        logger.info(f"Amount: ${amount_available:,.2f}")
        logger.info(f"Deadline: {deadline}")
        logger.info(f"Sectors: {', '.join(eligible_sectors)}")

        # TODO: Implement matching logic with investment opportunities
        # This could trigger a research task or investment search

    async def handle_match_request(
        self,
        payload: Dict[str, Any],
        message: Dict[str, Any]
    ) -> None:
        """Handle request to match funding with investments.

        Args:
            payload: Message payload containing match criteria
            message: Full message dictionary
        """
        logger.info(f"Processing match request: {payload.get('request_id')}")

        criteria = payload.get('criteria', {})
        source_type = payload.get('source_type')  # 'investment' or 'funding'

        logger.info(f"Match criteria: {criteria}")
        logger.info(f"Source type: {source_type}")

        # TODO: Implement matching algorithm
        # This would search for compatible opportunities and send results


class ResearchResultHandler(MessageHandler):
    """Handler for research result messages."""

    def __init__(self, sqs_manager: Optional[SQSManager] = None):
        """Initialize research result handler."""
        super().__init__(sqs_manager)

        # Register default handlers
        self.register_handler(
            MessageType.RESEARCH_COMPLETE,
            self.handle_research_complete
        )
        self.register_handler(
            MessageType.MATCH_RESULT,
            self.handle_match_result
        )

    async def handle_research_complete(
        self,
        payload: Dict[str, Any],
        message: Dict[str, Any]
    ) -> None:
        """Handle research completion message.

        Args:
            payload: Message payload containing research results
            message: Full message dictionary
        """
        logger.info(f"Processing research results: {payload.get('research_id')}")

        research_id = payload.get('research_id')
        research_brief = payload.get('research_brief')
        findings = payload.get('findings')
        final_report = payload.get('final_report')

        logger.info(f"Research: {research_brief}")
        logger.info(f"Report length: {len(final_report) if final_report else 0} chars")

        # TODO: Store research results in database
        # This could update the opportunities table or create reports

    async def handle_match_result(
        self,
        payload: Dict[str, Any],
        message: Dict[str, Any]
    ) -> None:
        """Handle matching result message.

        Args:
            payload: Message payload containing match results
            message: Full message dictionary
        """
        logger.info(f"Processing match results: {payload.get('match_id')}")

        matches = payload.get('matches', [])
        confidence_scores = payload.get('confidence_scores', [])

        logger.info(f"Found {len(matches)} potential matches")

        for idx, match in enumerate(matches):
            confidence = confidence_scores[idx] if idx < len(confidence_scores) else 0
            logger.info(f"  Match {idx + 1}: {match.get('title')} (confidence: {confidence:.2%})")

        # TODO: Store match results and notify relevant parties


# Convenience functions for common operations

async def process_investment_opportunities_queue(
    handler: Optional[NetZeroInvestmentOpportunityHandler] = None,
    max_iterations: Optional[int] = None
) -> None:
    """Process investment opportunities from the queue.

    Args:
        handler: Custom handler instance, creates default if not provided
        max_iterations: Maximum polling iterations (None = infinite)
    """
    handler = handler or NetZeroInvestmentOpportunityHandler()
    sqs = handler.sqs

    await handler.poll_and_process(
        sqs.config.investment_queue_url,
        max_iterations=max_iterations
    )


async def process_funding_opportunities_queue(
    handler: Optional[NetZeroFundingOpportunityHandler] = None,
    max_iterations: Optional[int] = None
) -> None:
    """Process funding opportunities from the queue.

    Args:
        handler: Custom handler instance, creates default if not provided
        max_iterations: Maximum polling iterations (None = infinite)
    """
    handler = handler or NetZeroFundingOpportunityHandler()
    sqs = handler.sqs

    await handler.poll_and_process(
        sqs.config.funding_queue_url,
        max_iterations=max_iterations
    )


async def process_research_results_queue(
    handler: Optional[ResearchResultHandler] = None,
    max_iterations: Optional[int] = None
) -> None:
    """Process research results from the queue.

    Args:
        handler: Custom handler instance, creates default if not provided
        max_iterations: Maximum polling iterations (None = infinite)
    """
    handler = handler or ResearchResultHandler()
    sqs = handler.sqs

    await handler.poll_and_process(
        sqs.config.results_queue_url,
        max_iterations=max_iterations
    )


async def run_all_handlers_parallel(max_iterations: Optional[int] = None) -> None:
    """Run all message handlers in parallel.

    Args:
        max_iterations: Maximum polling iterations for each handler (None = infinite)
    """
    logger.info("Starting all message handlers in parallel")

    # Create tasks for each handler
    tasks = [
        process_investment_opportunities_queue(max_iterations=max_iterations),
        process_funding_opportunities_queue(max_iterations=max_iterations),
        process_research_results_queue(max_iterations=max_iterations),
    ]

    # Run all handlers concurrently
    await asyncio.gather(*tasks)
