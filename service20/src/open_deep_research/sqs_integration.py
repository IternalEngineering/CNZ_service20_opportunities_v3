"""Integration module for connecting deep researcher with SQS message queues.

This module provides integration between the LangGraph deep researcher workflow
and the SQS message queue system for inter-agent communication.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig

from open_deep_research.configuration import Configuration
from open_deep_research.deep_researcher import deep_researcher
from open_deep_research.database_storage import save_research_to_database
from open_deep_research.message_handlers import (
    NetZeroInvestmentOpportunityHandler,
    NetZeroFundingOpportunityHandler,
    ResearchResultHandler,
)
from open_deep_research.sqs_config import MessageType, get_sqs_manager

# Configure logging
logger = logging.getLogger(__name__)


class ResearchOrchestrator:
    """Orchestrates research tasks triggered by SQS messages."""

    def __init__(self, config: Optional[RunnableConfig] = None):
        """Initialize research orchestrator.

        Args:
            config: LangGraph runtime configuration
        """
        self.config = config or {}
        self.sqs = get_sqs_manager()

    async def conduct_research_for_opportunity(
        self,
        opportunity_data: Dict[str, Any],
        opportunity_type: str = "investment"
    ) -> Optional[Dict[str, Any]]:
        """Conduct deep research for an investment or funding opportunity.

        Args:
            opportunity_data: Dictionary containing opportunity details
            opportunity_type: Type of opportunity ('investment' or 'funding')

        Returns:
            Research results dictionary or None if failed
        """
        try:
            # Build research prompt from opportunity data
            research_prompt = self._build_research_prompt(
                opportunity_data,
                opportunity_type
            )

            logger.info(f"Starting deep research for {opportunity_type} opportunity")
            logger.info(f"Research prompt: {research_prompt[:200]}...")

            # Execute deep research workflow
            result = await deep_researcher.ainvoke(
                {"messages": [HumanMessage(content=research_prompt)]},
                config=self.config
            )

            # Extract research results
            final_report = result.get("final_report", "")
            research_brief = result.get("research_brief", "")
            notes = result.get("notes", [])

            logger.info(f"Research completed. Report length: {len(final_report)} chars")

            research_results = {
                "research_id": opportunity_data.get("id", "unknown"),
                "opportunity_type": opportunity_type,
                "research_brief": research_brief,
                "final_report": final_report,
                "findings": notes,
                "opportunity_data": opportunity_data
            }

            # Save to PostgreSQL database
            try:
                db_id = await save_research_to_database(research_results, opportunity_data)
                if db_id:
                    logger.info(f"Saved research to database with ID: {db_id}")
                    research_results["database_id"] = db_id
            except Exception as e:
                logger.error(f"Failed to save to database: {e}")

            return research_results

        except Exception as e:
            logger.error(f"Research failed for {opportunity_type} opportunity: {e}")
            return None

    def _build_research_prompt(
        self,
        opportunity_data: Dict[str, Any],
        opportunity_type: str
    ) -> str:
        """Build research prompt from opportunity data.

        Args:
            opportunity_data: Dictionary containing opportunity details
            opportunity_type: Type of opportunity ('investment' or 'funding')

        Returns:
            Research prompt string
        """
        if opportunity_type == "investment":
            return self._build_investment_research_prompt(opportunity_data)
        elif opportunity_type == "funding":
            return self._build_funding_research_prompt(opportunity_data)
        else:
            return f"Research the following opportunity: {opportunity_data}"

    def _build_investment_research_prompt(
        self,
        opportunity_data: Dict[str, Any]
    ) -> str:
        """Build research prompt for investment opportunity.

        Args:
            opportunity_data: Investment opportunity details

        Returns:
            Research prompt string
        """
        title = opportunity_data.get("title", "Unknown")
        description = opportunity_data.get("description", "No description")
        location = opportunity_data.get("location", "Unknown location")
        sector = opportunity_data.get("sector", "Unknown sector")
        investment_amount = opportunity_data.get("investment_amount", 0)

        prompt = f"""
Research the following Net Zero investment opportunity:

**Title:** {title}
**Location:** {location}
**Sector:** {sector}
**Investment Amount:** ${investment_amount:,.2f}

**Description:**
{description}

Please conduct comprehensive research on:
1. Market analysis for this sector in this location
2. Competitive landscape and similar projects
3. Regulatory environment and compliance requirements
4. Risk factors and mitigation strategies
5. Potential funding sources that might match this opportunity
6. Expected ROI and financial projections
7. Environmental impact and Net Zero contribution
8. Key stakeholders and partnerships

Provide a detailed report with evidence-based recommendations.
"""
        return prompt.strip()

    def _build_funding_research_prompt(
        self,
        opportunity_data: Dict[str, Any]
    ) -> str:
        """Build research prompt for funding opportunity.

        Args:
            opportunity_data: Funding opportunity details

        Returns:
            Research prompt string
        """
        title = opportunity_data.get("title", "Unknown")
        description = opportunity_data.get("description", "No description")
        funder = opportunity_data.get("funder", "Unknown funder")
        amount_available = opportunity_data.get("amount_available", 0)
        eligible_sectors = opportunity_data.get("eligible_sectors", [])
        deadline = opportunity_data.get("deadline", "Unknown")

        sectors_str = ", ".join(eligible_sectors) if eligible_sectors else "Not specified"

        prompt = f"""
Research the following Net Zero funding opportunity:

**Title:** {title}
**Funder:** {funder}
**Amount Available:** ${amount_available:,.2f}
**Application Deadline:** {deadline}
**Eligible Sectors:** {sectors_str}

**Description:**
{description}

Please conduct comprehensive research on:
1. Funder background, history, and previous funding patterns
2. Application requirements and success factors
3. Eligible project types and criteria
4. Competition analysis (how many typically apply, success rates)
5. Potential investment opportunities that match this funding
6. Strategic approach for applications
7. Similar past funding awards and their outcomes
8. Key contacts and networking opportunities

Provide a detailed report with actionable recommendations for matching investments.
"""
        return prompt.strip()

    async def send_research_results(
        self,
        research_results: Dict[str, Any]
    ) -> Optional[str]:
        """Send research results to the results queue.

        Args:
            research_results: Research results dictionary

        Returns:
            Message ID if successful, None otherwise
        """
        if not research_results:
            logger.warning("No research results to send")
            return None

        return self.sqs.send_research_result(research_results)


class EnhancedInvestmentHandler(NetZeroInvestmentOpportunityHandler):
    """Enhanced Net Zero investment handler with deep research integration."""

    def __init__(self, config: Optional[RunnableConfig] = None):
        """Initialize enhanced investment handler.

        Args:
            config: LangGraph runtime configuration
        """
        super().__init__()
        self.orchestrator = ResearchOrchestrator(config)

    async def handle_investment_opportunity(
        self,
        payload: Dict[str, Any],
        message: Dict[str, Any]
    ) -> None:
        """Handle investment opportunity with automatic research.

        Args:
            payload: Message payload containing opportunity details
            message: Full message dictionary
        """
        logger.info(f"Processing investment opportunity: {payload.get('opportunity_id')}")

        # Conduct deep research
        research_results = await self.orchestrator.conduct_research_for_opportunity(
            payload,
            opportunity_type="investment"
        )

        if research_results:
            # Send results to results queue
            message_id = await self.orchestrator.send_research_results(research_results)
            logger.info(f"Research results sent with message ID: {message_id}")

            # Check for potential funding matches
            await self._check_funding_matches(payload, research_results)
        else:
            logger.error("Research failed for investment opportunity")

    async def _check_funding_matches(
        self,
        opportunity_data: Dict[str, Any],
        research_results: Dict[str, Any]
    ) -> None:
        """Check for potential funding matches.

        Args:
            opportunity_data: Investment opportunity details
            research_results: Research results from deep researcher
        """
        # TODO: Implement matching logic
        # This could analyze research results to find compatible funding opportunities
        logger.info("Checking for funding matches (not yet implemented)")


class EnhancedFundingHandler(NetZeroFundingOpportunityHandler):
    """Enhanced Net Zero funding handler with deep research integration."""

    def __init__(self, config: Optional[RunnableConfig] = None):
        """Initialize enhanced funding handler.

        Args:
            config: LangGraph runtime configuration
        """
        super().__init__()
        self.orchestrator = ResearchOrchestrator(config)

    async def handle_funding_opportunity(
        self,
        payload: Dict[str, Any],
        message: Dict[str, Any]
    ) -> None:
        """Handle funding opportunity with automatic research.

        Args:
            payload: Message payload containing funding details
            message: Full message dictionary
        """
        logger.info(f"Processing funding opportunity: {payload.get('funding_id')}")

        # Conduct deep research
        research_results = await self.orchestrator.conduct_research_for_opportunity(
            payload,
            opportunity_type="funding"
        )

        if research_results:
            # Send results to results queue
            message_id = await self.orchestrator.send_research_results(research_results)
            logger.info(f"Research results sent with message ID: {message_id}")

            # Check for potential investment matches
            await self._check_investment_matches(payload, research_results)
        else:
            logger.error("Research failed for funding opportunity")

    async def _check_investment_matches(
        self,
        opportunity_data: Dict[str, Any],
        research_results: Dict[str, Any]
    ) -> None:
        """Check for potential investment matches.

        Args:
            opportunity_data: Funding opportunity details
            research_results: Research results from deep researcher
        """
        # TODO: Implement matching logic
        # This could analyze research results to find compatible investment opportunities
        logger.info("Checking for investment matches (not yet implemented)")


# Convenience functions for running enhanced handlers

async def run_enhanced_investment_handler(
    config: Optional[RunnableConfig] = None,
    max_iterations: Optional[int] = None
) -> None:
    """Run enhanced investment handler with deep research.

    Args:
        config: LangGraph runtime configuration
        max_iterations: Maximum polling iterations (None = infinite)
    """
    handler = EnhancedInvestmentHandler(config)
    await handler.poll_and_process(
        handler.sqs.config.investment_queue_url,
        max_iterations=max_iterations
    )


async def run_enhanced_funding_handler(
    config: Optional[RunnableConfig] = None,
    max_iterations: Optional[int] = None
) -> None:
    """Run enhanced funding handler with deep research.

    Args:
        config: LangGraph runtime configuration
        max_iterations: Maximum polling iterations (None = infinite)
    """
    handler = EnhancedFundingHandler(config)
    await handler.poll_and_process(
        handler.sqs.config.funding_queue_url,
        max_iterations=max_iterations
    )


async def run_enhanced_handlers_parallel(
    config: Optional[RunnableConfig] = None,
    max_iterations: Optional[int] = None
) -> None:
    """Run both enhanced handlers in parallel.

    Args:
        config: LangGraph runtime configuration
        max_iterations: Maximum polling iterations for each handler (None = infinite)
    """
    logger.info("Starting enhanced message handlers with deep research integration")

    tasks = [
        run_enhanced_investment_handler(config, max_iterations),
        run_enhanced_funding_handler(config, max_iterations),
    ]

    await asyncio.gather(*tasks)
