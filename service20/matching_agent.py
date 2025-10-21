"""Matching Agent - Discovers synergies and creates bundled opportunities.

This agent follows Service20's dual-agent SQS architecture to:
1. Listen for match requests on SQS
2. Analyze alerts from service20_alerts table
3. Create bundled opportunities in service20_bundles table
4. Send match notifications via SQS

Architecture:
- Triggered by match_request messages on SQS
- Uses CompatibilityScorer for weighted scoring
- Creates bundles when opportunities are too small for funders
- Stores results in service20_bundles table
- Sends notifications for high-confidence matches
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
load_dotenv()

import asyncpg

from open_deep_research.sqs_config import MessageType, get_sqs_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Color output
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class Fore:
        GREEN = RED = YELLOW = CYAN = MAGENTA = ""
    class Style:
        BRIGHT = RESET_ALL = ""


class CompatibilityScorer:
    """Calculates compatibility scores for opportunity-funder matches."""

    @staticmethod
    def calculate_score(
        funder: Dict[str, Any],
        opportunities: List[Dict[str, Any]]
    ) -> Tuple[float, List[str], List[str]]:
        """Calculate comprehensive compatibility score.

        Args:
            funder: Funder alert data with criteria
            opportunities: List of opportunity alert data

        Returns:
            Tuple of (score, criteria_met, warnings)
        """
        score = 0.0
        criteria_met = []
        warnings = []

        # Extract funder criteria
        funder_criteria = funder.get('criteria', {})
        funder_sector = funder_criteria.get('sector', {})
        funder_financial = funder_criteria.get('financial', {})
        funder_timeline = funder_criteria.get('timeline', {})

        # 1. Sector Alignment (30% weight)
        sector_score, sector_criteria = CompatibilityScorer._score_sector_alignment(
            funder_sector, opportunities
        )
        score += sector_score * 0.30
        criteria_met.extend(sector_criteria)

        # 2. Financial Fit (25% weight)
        financial_score, financial_criteria, financial_warnings = CompatibilityScorer._score_financial_fit(
            funder_financial, opportunities
        )
        score += financial_score * 0.25
        criteria_met.extend(financial_criteria)
        warnings.extend(financial_warnings)

        # 3. Timeline Compatibility (20% weight)
        timeline_score, timeline_criteria, timeline_warnings = CompatibilityScorer._score_timeline_compatibility(
            funder_timeline, opportunities
        )
        score += timeline_score * 0.20
        criteria_met.extend(timeline_criteria)
        warnings.extend(timeline_warnings)

        # 4. ROI Expectations (15% weight)
        roi_score, roi_criteria = CompatibilityScorer._score_roi_expectations(
            funder_financial, opportunities
        )
        score += roi_score * 0.15
        criteria_met.extend(roi_criteria)

        # 5. Technical Compatibility (10% weight)
        tech_score, tech_criteria = CompatibilityScorer._score_technical_compatibility(
            funder_criteria.get('technical', {}), opportunities
        )
        score += tech_score * 0.10
        criteria_met.extend(tech_criteria)

        return score, criteria_met, warnings

    @staticmethod
    def _score_sector_alignment(
        funder_sector: Dict[str, Any],
        opportunities: List[Dict[str, Any]]
    ) -> Tuple[float, List[str]]:
        """Score sector alignment."""
        criteria = []

        funder_primary = funder_sector.get('primary', '').lower()
        if not funder_primary:
            return 0.5, ['sector_unknown']

        # Get all opportunity sectors
        opp_sectors = []
        for opp in opportunities:
            sector = opp.get('sector', '').lower()
            if not sector:
                # Try to extract from criteria
                sector = opp.get('criteria', {}).get('sector', {}).get('primary', '').lower()
            opp_sectors.append(sector)

        # Check if all opportunities match funder's primary sector
        all_match = all(s == funder_primary for s in opp_sectors if s)

        if all_match:
            criteria.append('sector_perfect_match')
            return 1.0, criteria

        # Check if any match
        any_match = any(s == funder_primary for s in opp_sectors)

        if any_match:
            criteria.append('sector_partial_match')
            return 0.6, criteria

        # Check for related sectors (e.g., solar_energy matches renewable_energy)
        related_sectors = {
            'renewable_energy': ['solar_energy', 'wind_energy', 'energy_storage'],
            'solar_energy': ['renewable_energy'],
            'wind_energy': ['renewable_energy'],
            'energy_storage': ['renewable_energy', 'solar_energy', 'wind_energy']
        }

        if funder_primary in related_sectors:
            related = related_sectors[funder_primary]
            if any(s in related for s in opp_sectors):
                criteria.append('sector_related_match')
                return 0.7, criteria

        return 0.2, ['sector_mismatch']

    @staticmethod
    def _score_financial_fit(
        funder_financial: Dict[str, Any],
        opportunities: List[Dict[str, Any]]
    ) -> Tuple[float, List[str], List[str]]:
        """Score financial fit including scale requirements."""
        criteria = []
        warnings = []

        # Calculate total investment needed
        total_investment = sum(
            opp.get('criteria', {}).get('financial', {}).get('amount', 0)
            for opp in opportunities
        )

        # Get funder's minimum and available funding
        minimum_required = funder_financial.get('minimum_required', 0)
        funding_available = funder_financial.get('amount', 0)

        # Check if meets minimum scale
        if minimum_required > 0:
            if total_investment >= minimum_required:
                criteria.append('minimum_scale_met')
                score = 1.0
            elif total_investment >= minimum_required * 0.8:
                criteria.append('minimum_scale_nearly_met')
                warnings.append(f'Investment ${total_investment:,.0f} slightly below minimum ${minimum_required:,.0f}')
                score = 0.7
            else:
                warnings.append(f'Investment ${total_investment:,.0f} well below minimum ${minimum_required:,.0f}')
                score = 0.3
        else:
            score = 0.8  # No minimum specified

        # Check if within available funding
        if funding_available > 0:
            if total_investment <= funding_available:
                criteria.append('within_funding_capacity')
            elif total_investment <= funding_available * 1.2:
                warnings.append(f'Investment ${total_investment:,.0f} slightly exceeds available ${funding_available:,.0f}')
            else:
                warnings.append(f'Investment ${total_investment:,.0f} significantly exceeds available ${funding_available:,.0f}')
                score *= 0.7

        return score, criteria, warnings

    @staticmethod
    def _score_timeline_compatibility(
        funder_timeline: Dict[str, Any],
        opportunities: List[Dict[str, Any]]
    ) -> Tuple[float, List[str], List[str]]:
        """Score timeline compatibility."""
        criteria = []
        warnings = []

        # Extract timelines
        opp_timelines = [
            opp.get('criteria', {}).get('timeline', {})
            for opp in opportunities
        ]

        # Check if all opportunities have similar timelines (within 6 months)
        execution_starts = [
            t.get('execution_start', '') for t in opp_timelines if t.get('execution_start')
        ]

        if len(execution_starts) >= 2:
            # Check if timelines are aligned (simplified check)
            all_same_year = len(set(s[:4] for s in execution_starts if len(s) >= 4)) == 1
            if all_same_year:
                criteria.append('timeline_aligned')
                score = 1.0
            else:
                warnings.append('Project timelines span multiple years')
                score = 0.6
        else:
            score = 0.7  # Insufficient timeline data

        return score, criteria, warnings

    @staticmethod
    def _score_roi_expectations(
        funder_financial: Dict[str, Any],
        opportunities: List[Dict[str, Any]]
    ) -> Tuple[float, List[str]]:
        """Score ROI alignment."""
        criteria = []

        # Calculate blended ROI
        total_investment = 0
        weighted_roi = 0

        for opp in opportunities:
            opp_financial = opp.get('criteria', {}).get('financial', {})
            amount = opp_financial.get('amount', 0)
            roi = opp_financial.get('roi_expected', 0)

            total_investment += amount
            weighted_roi += amount * roi

        blended_roi = weighted_roi / total_investment if total_investment > 0 else 0

        # Compare with funder expectations
        funder_roi_min = funder_financial.get('roi_expected', 0)

        if blended_roi >= funder_roi_min:
            criteria.append('roi_acceptable')
            if blended_roi >= funder_roi_min * 1.2:
                criteria.append('roi_exceeds_expectations')
                return 1.0, criteria
            return 0.9, criteria
        elif blended_roi >= funder_roi_min * 0.8:
            criteria.append('roi_nearly_acceptable')
            return 0.6, criteria
        else:
            return 0.3, criteria

    @staticmethod
    def _score_technical_compatibility(
        funder_technical: Dict[str, Any],
        opportunities: List[Dict[str, Any]]
    ) -> Tuple[float, List[str]]:
        """Score technical compatibility."""
        criteria = []

        # Check if all opportunities use compatible technology
        technologies = [
            opp.get('criteria', {}).get('technical', {}).get('technology', '')
            for opp in opportunities
        ]

        unique_tech = set(t for t in technologies if t)
        if len(unique_tech) <= 1:
            criteria.append('technology_consistent')
            return 1.0, criteria
        else:
            criteria.append('mixed_technologies')
            return 0.7, criteria


class BundleAnalyzer:
    """Analyzes bundling feasibility and calculates bundle metrics."""

    @staticmethod
    def calculate_bundle_metrics(opportunities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate comprehensive bundle metrics.

        Args:
            opportunities: List of opportunities to bundle

        Returns:
            Dictionary of bundle metrics
        """
        total_investment = 0
        weighted_roi = 0
        total_carbon = 0
        total_capacity = 0
        countries = set()
        cities = set()
        sectors = set()
        technologies = set()

        earliest_start = None
        latest_completion = None

        for opp in opportunities:
            opp_criteria = opp.get('criteria', {})
            financial = opp_criteria.get('financial', {})
            location = opp_criteria.get('location', {})
            technical = opp_criteria.get('technical', {})
            timeline = opp_criteria.get('timeline', {})

            amount = financial.get('amount', 0)
            roi = financial.get('roi_expected', 0)
            carbon = financial.get('carbon_reduction_tons_annually', 0)
            capacity = technical.get('capacity_mw', 0)

            total_investment += amount
            weighted_roi += amount * roi
            total_carbon += carbon
            total_capacity += capacity

            # Location data
            country = opp.get('country', location.get('country', 'Unknown'))
            city = opp.get('city', location.get('city', 'Unknown'))
            countries.add(country)
            cities.add(city)

            # Sector data
            sector = opp.get('sector', opp_criteria.get('sector', {}).get('primary', 'Unknown'))
            sectors.add(sector)

            # Technology
            tech = technical.get('technology', '')
            if tech:
                technologies.add(tech)

            # Timeline
            start = timeline.get('execution_start', '')
            end = timeline.get('completion', '')

            if start:
                if not earliest_start or start < earliest_start:
                    earliest_start = start
            if end:
                if not latest_completion or end > latest_completion:
                    latest_completion = end

        blended_roi = weighted_roi / total_investment if total_investment > 0 else 0

        return {
            'total_investment': total_investment,
            'blended_roi': round(blended_roi, 2),
            'total_carbon_reduction': total_carbon,
            'average_carbon_per_project': total_carbon / len(opportunities) if opportunities else 0,
            'total_capacity_mw': total_capacity,
            'opportunity_count': len(opportunities),
            'countries': list(countries),
            'cities': list(cities),
            'sectors': list(sectors),
            'technologies': list(technologies),
            'geographic_spread': len(countries),
            'earliest_start_date': earliest_start,
            'latest_completion_date': latest_completion
        }


class MatchingAgent:
    """Main matching agent that processes match requests via SQS."""

    def __init__(self):
        """Initialize matching agent."""
        self.scorer = CompatibilityScorer()
        self.analyzer = BundleAnalyzer()
        self.sqs_manager = get_sqs_manager()
        self.max_bundle_size = 5
        logger.info("Initialized Matching Agent")

    async def get_active_alerts(self, lookback_days: int = 30) -> Tuple[List[Dict], List[Dict]]:
        """Fetch active alerts from service20_alerts table.

        Args:
            lookback_days: How many days back to look for alerts

        Returns:
            Tuple of (investment_alerts, funding_alerts)
        """
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            logger.error("DATABASE_URL not set")
            return [], []

        conn = await asyncpg.connect(database_url)

        # Fetch active alerts
        cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)

        query = """
            SELECT id, alert_id, alert_type, research_id, criteria,
                   status, created_at, updated_at
            FROM service20_alerts
            WHERE status = 'active'
            AND created_at >= $1
            ORDER BY created_at DESC;
        """

        rows = await conn.fetch(query, cutoff_date)

        investment_alerts = []
        funding_alerts = []

        for row in rows:
            alert = {
                'id': row['id'],
                'alert_id': row['alert_id'],
                'alert_type': row['alert_type'],
                'research_id': row['research_id'],
                'criteria': row['criteria'],
                'status': row['status'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            }

            # Also fetch city/country from research if available
            if row['research_id']:
                research_query = """
                    SELECT city, country, country_code, sector
                    FROM service20_investment_opportunities
                    WHERE id = $1
                    LIMIT 1;
                """
                research_row = await conn.fetchrow(research_query, row['research_id'])
                if research_row:
                    alert['city'] = research_row['city']
                    alert['country'] = research_row['country']
                    alert['country_code'] = research_row['country_code']
                    alert['sector'] = research_row['sector']

            if row['alert_type'] == 'investment':
                investment_alerts.append(alert)
            elif row['alert_type'] == 'funding':
                funding_alerts.append(alert)

        await conn.close()

        logger.info(f"Found {len(investment_alerts)} investment alerts and {len(funding_alerts)} funding alerts")
        return investment_alerts, funding_alerts

    async def create_bundle(
        self,
        opportunities: List[Dict[str, Any]],
        funder: Dict[str, Any],
        compatibility_score: float,
        criteria_met: List[str],
        warnings: List[str]
    ) -> Optional[str]:
        """Create a bundle record in service20_bundles table.

        Args:
            opportunities: List of opportunities to bundle
            funder: Funder alert data
            compatibility_score: Overall compatibility score
            criteria_met: List of criteria that were met
            warnings: List of warnings from scoring

        Returns:
            Bundle ID if successful, None otherwise
        """
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            logger.error("DATABASE_URL not set")
            return None

        # Calculate bundle metrics
        bundle_metrics = self.analyzer.calculate_bundle_metrics(opportunities)

        # Generate bundle ID
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        bundle_id = f"bundle-{timestamp}-{len(opportunities)}opp"

        # Extract data for bundle record
        opportunity_ids = [str(opp.get('research_id', opp.get('id', ''))) for opp in opportunities]
        cities = bundle_metrics['cities']
        countries = bundle_metrics['countries']
        sectors = bundle_metrics['sectors']
        technologies = bundle_metrics['technologies']

        # Primary sector (most common)
        primary_sector = sectors[0] if sectors else 'unknown'

        # Regions (simplified - derive from countries)
        regions = list(set(self._get_region(c) for c in countries))

        # Generate bundle name and description
        city_str = ', '.join(cities[:3])
        if len(cities) > 3:
            city_str += f' +{len(cities)-3} more'

        bundle_name = f"{primary_sector.title()} Portfolio - {city_str}"
        bundle_description = f"Bundle of {len(opportunities)} {primary_sector} projects across {len(cities)} cities"

        # Confidence level
        if compatibility_score >= 0.80:
            confidence_level = 'high'
        elif compatibility_score >= 0.60:
            confidence_level = 'medium'
        else:
            confidence_level = 'low'

        # Bundling rationale
        bundling_rationale = f"Geographic diversification across {len(countries)} countries. " + \
                             f"Blended ROI: {bundle_metrics['blended_roi']}%. " + \
                             f"Total carbon reduction: {bundle_metrics['total_carbon_reduction']:,.0f} tons/year. " + \
                             f"Criteria met: {', '.join(criteria_met[:5])}"

        # Calculate ROI range
        roi_values = [
            opp.get('criteria', {}).get('financial', {}).get('roi_expected', 0)
            for opp in opportunities
        ]
        roi_range_min = min(roi_values) if roi_values else 0
        roi_range_max = max(roi_values) if roi_values else 0

        # Store in database
        conn = await asyncpg.connect(database_url)

        insert_query = """
            INSERT INTO service20_bundles (
                bundle_id, bundle_name, bundle_description,
                opportunity_ids, opportunity_count,
                cities, countries, regions,
                primary_sector, sectors,
                total_investment, blended_roi, roi_range_min, roi_range_max,
                total_carbon_reduction, average_carbon_per_project,
                earliest_start_date, latest_completion_date,
                technologies, total_capacity_mw,
                bundle_metrics, compatibility_score, confidence_level,
                bundling_rationale, status, criteria,
                matched_funder_id, match_date, created_by
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                $11, $12, $13, $14, $15, $16, $17, $18, $19, $20,
                $21::jsonb, $22, $23, $24, $25, $26::jsonb, $27, $28, $29
            )
            RETURNING id;
        """

        try:
            record_id = await conn.fetchval(
                insert_query,
                bundle_id, bundle_name, bundle_description,
                opportunity_ids, len(opportunities),
                cities, countries, regions,
                primary_sector, list(sectors),
                bundle_metrics['total_investment'],
                bundle_metrics['blended_roi'],
                roi_range_min, roi_range_max,
                bundle_metrics['total_carbon_reduction'],
                bundle_metrics['average_carbon_per_project'],
                bundle_metrics.get('earliest_start_date'),
                bundle_metrics.get('latest_completion_date'),
                technologies, bundle_metrics.get('total_capacity_mw', 0),
                json.dumps(bundle_metrics), compatibility_score, confidence_level,
                bundling_rationale, 'proposed',
                json.dumps({'criteria_met': criteria_met, 'warnings': warnings}),
                funder.get('research_id', funder.get('id')),
                datetime.utcnow(),
                'matching-agent'
            )

            await conn.close()

            logger.info(f"Created bundle {bundle_id} with {len(opportunities)} opportunities (ID: {record_id})")
            return bundle_id

        except Exception as e:
            logger.error(f"Failed to create bundle: {e}")
            await conn.close()
            return None

    def _get_region(self, country: str) -> str:
        """Get region from country name."""
        europe = ['France', 'Germany', 'United Kingdom', 'Spain', 'Italy', 'Netherlands',
                  'Belgium', 'Sweden', 'Norway', 'Denmark', 'Finland', 'Poland',
                  'Czech Republic', 'Austria', 'Switzerland']
        north_america = ['United States', 'Canada', 'Mexico']
        asia_pacific = ['Japan', 'South Korea', 'Singapore', 'Australia', 'New Zealand',
                        'China', 'India']
        latin_america = ['Brazil', 'Argentina', 'Chile']
        middle_east = ['United Arab Emirates', 'Saudi Arabia']
        africa = ['South Africa']

        if country in europe:
            return 'Europe'
        elif country in north_america:
            return 'North America'
        elif country in asia_pacific:
            return 'Asia Pacific'
        elif country in latin_america:
            return 'Latin America'
        elif country in middle_east:
            return 'Middle East'
        elif country in africa:
            return 'Africa'
        else:
            return 'Other'

    async def find_matches(
        self,
        investment_alerts: List[Dict[str, Any]],
        funding_alerts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Find matches between investment and funding alerts.

        Args:
            investment_alerts: List of investment opportunity alerts
            funding_alerts: List of funding opportunity alerts

        Returns:
            List of match/bundle records created
        """
        matches_created = []

        # Group investment opportunities by sector
        opportunities_by_sector = {}
        for opp in investment_alerts:
            sector = opp.get('sector',
                           opp.get('criteria', {}).get('sector', {}).get('primary', 'unknown')).lower()
            if sector not in opportunities_by_sector:
                opportunities_by_sector[sector] = []
            opportunities_by_sector[sector].append(opp)

        logger.info(f"Grouped opportunities into {len(opportunities_by_sector)} sectors")

        # Process each funder
        for funder in funding_alerts:
            logger.info(f"Processing funder: {funder.get('alert_id', funder.get('id'))}")

            funder_criteria = funder.get('criteria', {})
            funder_sector = funder_criteria.get('sector', {}).get('primary', '').lower()
            minimum_investment = funder_criteria.get('financial', {}).get('minimum_required', 0)

            # Get opportunities in funder's sector
            sector_opportunities = opportunities_by_sector.get(funder_sector, [])

            if not sector_opportunities:
                logger.info(f"No opportunities found for sector: {funder_sector}")
                continue

            # Try to find single matches first
            for opp in sector_opportunities:
                score, criteria_met, warnings = self.scorer.calculate_score(funder, [opp])

                if score >= 0.60:
                    # Single opportunity meets threshold
                    bundle_id = await self.create_bundle(
                        [opp], funder, score, criteria_met, warnings
                    )
                    if bundle_id:
                        matches_created.append({
                            'bundle_id': bundle_id,
                            'type': 'simple',
                            'opportunities': 1,
                            'score': score,
                            'confidence': 'high' if score >= 0.80 else 'medium'
                        })

            # Try bundled matches if funder has minimum requirement
            if minimum_investment > 0 and len(sector_opportunities) >= 2:
                logger.info(f"Trying bundled matches for minimum ${minimum_investment:,.0f}")

                # Try different combinations
                for size in range(2, min(len(sector_opportunities) + 1, self.max_bundle_size + 1)):
                    best_bundle = None
                    best_score = 0

                    for combo in combinations(sector_opportunities, size):
                        # Calculate total investment
                        total = sum(
                            opp.get('criteria', {}).get('financial', {}).get('amount', 0)
                            for opp in combo
                        )

                        # Check if bundle meets minimum investment
                        if total < minimum_investment * 0.8:
                            continue

                        # Score the bundle
                        score, criteria_met, warnings = self.scorer.calculate_score(
                            funder, list(combo)
                        )

                        if score >= 0.60 and score > best_score:
                            best_score = score
                            best_bundle = {
                                'opportunities': list(combo),
                                'score': score,
                                'criteria_met': criteria_met,
                                'warnings': warnings
                            }

                    # Create best bundle for this size
                    if best_bundle:
                        bundle_id = await self.create_bundle(
                            best_bundle['opportunities'],
                            funder,
                            best_bundle['score'],
                            best_bundle['criteria_met'],
                            best_bundle['warnings']
                        )
                        if bundle_id:
                            matches_created.append({
                                'bundle_id': bundle_id,
                                'type': 'bundled',
                                'opportunities': len(best_bundle['opportunities']),
                                'score': best_bundle['score'],
                                'confidence': 'high' if best_bundle['score'] >= 0.80 else 'medium'
                            })

        logger.info(f"Created {len(matches_created)} bundles/matches")
        return matches_created

    async def process_match_request(self, message: Dict[str, Any]) -> bool:
        """Process a match request from SQS.

        Args:
            message: SQS message containing match request

        Returns:
            True if processed successfully, False otherwise
        """
        payload = message.get('payload', {})
        lookback_days = payload.get('lookback_days', 30)

        logger.info(f"Processing match request (lookback: {lookback_days} days)")

        # Fetch active alerts
        investment_alerts, funding_alerts = await self.get_active_alerts(lookback_days)

        if not funding_alerts:
            logger.warning("No active funding alerts found")
            return True  # Not an error, just nothing to do

        if not investment_alerts:
            logger.warning("No active investment alerts found")
            return True

        # Find matches
        matches = await self.find_matches(investment_alerts, funding_alerts)

        # Send notifications for high-confidence matches
        high_confidence_count = 0
        for match in matches:
            if match['confidence'] == 'high':
                # Send notification via SQS
                notification_payload = {
                    'bundle_id': match['bundle_id'],
                    'opportunities': match['opportunities'],
                    'score': match['score'],
                    'type': match['type']
                }

                self.sqs_manager.send_message(
                    self.sqs_manager.config.match_results_queue_url,
                    MessageType.MATCH_FOUND,
                    notification_payload
                )
                high_confidence_count += 1

        logger.info(f"Sent {high_confidence_count} high-confidence match notifications")

        # Send result message
        result_payload = {
            'total_matches': len(matches),
            'high_confidence': high_confidence_count,
            'medium_confidence': len([m for m in matches if m['confidence'] == 'medium']),
            'investment_alerts_processed': len(investment_alerts),
            'funding_alerts_processed': len(funding_alerts)
        }

        self.sqs_manager.send_message(
            self.sqs_manager.config.results_queue_url,
            MessageType.MATCH_RESULT,
            result_payload
        )

        return True

    async def run(self, poll_interval: int = 20):
        """Run the matching agent (listen for SQS messages).

        Args:
            poll_interval: Seconds to wait between polls (default: 20 for long polling)
        """
        logger.info(f"{Fore.CYAN}{'=' * 80}")
        logger.info(f"Matching Agent Started")
        logger.info(f"{'=' * 80}{Style.RESET_ALL}")
        logger.info(f"Listening for match requests on SQS...")
        logger.info(f"Queue: {self.sqs_manager.config.match_requests_queue_url}")

        while True:
            try:
                # Receive messages from match requests queue
                messages = self.sqs_manager.receive_messages(
                    self.sqs_manager.config.match_requests_queue_url
                )

                for message in messages:
                    logger.info(f"{Fore.YELLOW}Received match request: {message['message_id']}{Style.RESET_ALL}")

                    # Process the request
                    success = await self.process_match_request(message)

                    # Delete message if processed successfully
                    if success:
                        self.sqs_manager.delete_message(
                            self.sqs_manager.config.match_requests_queue_url,
                            message['receipt_handle']
                        )
                        logger.info(f"{Fore.GREEN}Match request processed successfully{Style.RESET_ALL}")
                    else:
                        logger.error(f"{Fore.RED}Failed to process match request{Style.RESET_ALL}")

                # Sleep briefly before next poll (SQS long polling handles most of the wait)
                await asyncio.sleep(1)

            except KeyboardInterrupt:
                logger.info(f"\n{Fore.YELLOW}Shutting down matching agent...{Style.RESET_ALL}")
                break
            except Exception as e:
                logger.error(f"{Fore.RED}Error in matching agent: {e}{Style.RESET_ALL}")
                import traceback
                traceback.print_exc()
                await asyncio.sleep(poll_interval)


async def main():
    """Main entry point for matching agent."""
    agent = MatchingAgent()
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
