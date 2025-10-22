"""Scheduled jobs for Service20 matching and maintenance tasks.

This module provides scheduled job functions that can be triggered by:
- Cron jobs (Linux)
- AWS EventBridge rules
- Manual execution for testing
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


async def run_daily_matching_job(lookback_days: int = 30) -> Dict[str, Any]:
    """Run daily matching job to find opportunities and create alerts.

    This job:
    1. Fetches active alerts from last N days
    2. Runs matching engine to find compatible combinations
    3. Stores match proposals in database
    4. Creates alerts for high-confidence matches (auto-notify)
    5. Queues medium-confidence matches for approval

    Args:
        lookback_days: How many days back to look for active alerts (default: 30)

    Returns:
        Dictionary with job execution summary
    """
    logger.info(f"Starting daily matching job at {datetime.utcnow().isoformat()}")
    start_time = datetime.utcnow()

    try:
        # Import here to avoid circular dependencies
        from open_deep_research.matching_engine import MatchMakerEngine
        from open_deep_research.database_storage import (
            store_match_proposal,
            create_match_alert
        )
        from open_deep_research.sqs_config import get_sqs_manager, MessageType

        # Initialize matching engine
        engine = MatchMakerEngine()
        logger.info("Initialized matching engine")

        # Run matching
        all_matches = await engine.run_matching(lookback_days=lookback_days)
        logger.info(f"Found {len(all_matches)} potential matches")

        # Separate by confidence level
        high_confidence = [m for m in all_matches if m['confidence_level'] == 'high']
        medium_confidence = [m for m in all_matches if m['confidence_level'] == 'medium']
        low_confidence = [m for m in all_matches if m['confidence_level'] == 'low']

        logger.info(f"Confidence breakdown: {len(high_confidence)} high, {len(medium_confidence)} medium, {len(low_confidence)} low")

        # Process high-confidence matches (auto-notify)
        high_confidence_processed = 0
        for match in high_confidence:
            try:
                # Store in database
                match_id = await store_match_proposal(match, requires_approval=False)

                if match_id:
                    # Create alerts for all participants (auto-notify)
                    alert_ids = await create_match_alert(match, auto_notify=True)
                    if alert_ids:
                        high_confidence_processed += 1
                        logger.info(f"Processed high-confidence match {match_id}: created {len(alert_ids)} alerts")
                    else:
                        logger.warning(f"Failed to create alerts for match {match_id}")
                else:
                    logger.warning(f"Failed to store match proposal")

            except Exception as e:
                logger.error(f"Error processing high-confidence match: {e}")

        # Process medium-confidence matches (queue for approval)
        medium_confidence_queued = 0
        sqs = get_sqs_manager()

        for match in medium_confidence:
            try:
                # Store in database (marked as requires_approval)
                match_id = await store_match_proposal(match, requires_approval=True)

                if match_id:
                    # Create alerts but don't auto-notify (just store in DB)
                    alert_ids = await create_match_alert(match, auto_notify=False)

                    # Send to approval queue
                    message_id = sqs.send_message(
                        sqs.config.match_approvals_queue_url,
                        MessageType.MATCH_APPROVAL_NEEDED,
                        {
                            'match_id': match_id,
                            'match_type': match['match_type'],
                            'compatibility_score': match['compatibility_score'],
                            'opportunities_count': len(match['opportunities']),
                            'funders_count': len(match['funders']),
                            'total_investment': match['bundle_metrics'].get('total_investment'),
                            'created_at': datetime.utcnow().isoformat()
                        }
                    )

                    if message_id:
                        medium_confidence_queued += 1
                        logger.info(f"Queued medium-confidence match {match_id} for approval")
                else:
                    logger.warning(f"Failed to store medium-confidence match")

            except Exception as e:
                logger.error(f"Error processing medium-confidence match: {e}")

        # Low-confidence matches are just logged, not processed
        logger.info(f"Skipped {len(low_confidence)} low-confidence matches (below notification threshold)")

        # Calculate execution time
        end_time = datetime.utcnow()
        duration_seconds = (end_time - start_time).total_seconds()

        # Job summary
        summary = {
            'job': 'daily_matching',
            'status': 'completed',
            'started_at': start_time.isoformat(),
            'completed_at': end_time.isoformat(),
            'duration_seconds': duration_seconds,
            'lookback_days': lookback_days,
            'statistics': {
                'total_matches_found': len(all_matches),
                'high_confidence': len(high_confidence),
                'medium_confidence': len(medium_confidence),
                'low_confidence': len(low_confidence),
                'high_confidence_processed': high_confidence_processed,
                'medium_confidence_queued': medium_confidence_queued
            }
        }

        logger.info(f"Daily matching job completed in {duration_seconds:.2f} seconds")
        logger.info(f"Summary: {summary}")

        return summary

    except Exception as e:
        logger.error(f"Daily matching job failed: {e}")
        import traceback
        traceback.print_exc()

        return {
            'job': 'daily_matching',
            'status': 'failed',
            'error': str(e),
            'started_at': start_time.isoformat(),
            'completed_at': datetime.utcnow().isoformat()
        }


async def cleanup_old_matches(days_old: int = 90) -> Dict[str, Any]:
    """Clean up old match proposals from database.

    Args:
        days_old: Remove matches older than this many days (default: 90)

    Returns:
        Dictionary with cleanup summary
    """
    logger.info(f"Starting cleanup job for matches older than {days_old} days")

    try:
        import asyncpg
        import os
        from datetime import timedelta

        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            logger.error("DATABASE_URL not set")
            return {'status': 'failed', 'error': 'DATABASE_URL not set'}

        conn = await asyncpg.connect(database_url)

        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        # Delete old matches
        delete_query = """
            DELETE FROM opportunity_matches
            WHERE created_at < $1
            RETURNING match_id;
        """

        deleted_rows = await conn.fetch(delete_query, cutoff_date)
        deleted_count = len(deleted_rows)

        await conn.close()

        logger.info(f"Cleanup job completed: deleted {deleted_count} old matches")

        return {
            'job': 'cleanup_old_matches',
            'status': 'completed',
            'days_old': days_old,
            'cutoff_date': cutoff_date.isoformat(),
            'deleted_count': deleted_count
        }

    except Exception as e:
        logger.error(f"Cleanup job failed: {e}")
        return {
            'job': 'cleanup_old_matches',
            'status': 'failed',
            'error': str(e)
        }


if __name__ == "__main__":
    """Allow running jobs directly for testing."""
    import sys

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Check command line args
    if len(sys.argv) > 1:
        job_name = sys.argv[1]

        if job_name == "matching":
            lookback = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            result = asyncio.run(run_daily_matching_job(lookback_days=lookback))
            print(f"\nJob Result: {result}")

        elif job_name == "cleanup":
            days_old = int(sys.argv[2]) if len(sys.argv) > 2 else 90
            result = asyncio.run(cleanup_old_matches(days_old=days_old))
            print(f"\nJob Result: {result}")

        else:
            print(f"Unknown job: {job_name}")
            print("Available jobs: matching, cleanup")
            sys.exit(1)
    else:
        print("Service20 Scheduled Jobs")
        print("=" * 60)
        print("Usage:")
        print("  python scheduled_jobs.py matching [lookback_days]")
        print("  python scheduled_jobs.py cleanup [days_old]")
        print("\nExamples:")
        print("  python scheduled_jobs.py matching 30")
        print("  python scheduled_jobs.py cleanup 90")
