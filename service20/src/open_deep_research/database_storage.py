"""Database storage functions for research results."""

import asyncpg
import logging
import os
from typing import Any, Dict, Optional, List

logger = logging.getLogger(__name__)


async def save_research_to_database(
    research_results: Dict[str, Any],
    opportunity_data: Optional[Dict[str, Any]] = None
) -> Optional[int]:
    """Save research results to PostgreSQL database.

    Args:
        research_results: Research results dictionary from deep researcher
        opportunity_data: Original opportunity data (optional)

    Returns:
        Database record ID if successful, None otherwise
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.warning("DATABASE_URL not set - skipping database storage")
        return None

    try:
        conn = await asyncpg.connect(database_url)

        # Extract fields from research results
        research_id = research_results.get('research_id', 'unknown')
        opportunity_type = research_results.get('opportunity_type', 'unknown')
        research_brief = research_results.get('research_brief', '')
        final_report = research_results.get('final_report', '')
        findings = research_results.get('findings', [])

        # Build query based on opportunity type
        if opportunity_data:
            if opportunity_type == 'investment':
                query_text = f"Investment Research: {opportunity_data.get('title', research_id)}"
            else:
                query_text = f"Funding Research: {opportunity_data.get('title', research_id)}"
        else:
            query_text = f"{opportunity_type.title()} Research: {research_id}"

        # Prepare metadata
        metadata = {
            'research_id': research_id,
            'opportunity_type': opportunity_type,
            'opportunity_data': opportunity_data or {},
            'findings_count': len(findings)
        }

        # Insert into database
        insert_query = """
            INSERT INTO service20_investment_opportunities (
                query,
                research_brief,
                final_report,
                research_iterations,
                tool_calls_count,
                metadata
            ) VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id;
        """

        record_id = await conn.fetchval(
            insert_query,
            query_text,
            research_brief,
            final_report,
            len(findings),  # research_iterations
            len(findings),  # tool_calls_count (approximate)
            metadata
        )

        logger.info(f"Saved research to database with ID: {record_id}")

        await conn.close()
        return record_id

    except Exception as e:
        logger.error(f"Failed to save research to database: {e}")
        return None


async def get_research_from_database(
    record_id: Optional[int] = None,
    research_id: Optional[str] = None,
    limit: int = 10
) -> list:
    """Retrieve research results from database.

    Args:
        record_id: Database record ID
        research_id: Research ID from metadata
        limit: Maximum records to return

    Returns:
        List of research records
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL not set")
        return []

    try:
        conn = await asyncpg.connect(database_url)

        if record_id:
            query = """
                SELECT * FROM service20_investment_opportunities
                WHERE id = $1;
            """
            row = await conn.fetchrow(query, record_id)
            results = [dict(row)] if row else []

        elif research_id:
            query = """
                SELECT * FROM service20_investment_opportunities
                WHERE metadata->>'research_id' = $1
                ORDER BY created_at DESC
                LIMIT $2;
            """
            rows = await conn.fetch(query, research_id, limit)
            results = [dict(row) for row in rows]

        else:
            query = """
                SELECT * FROM service20_investment_opportunities
                ORDER BY created_at DESC
                LIMIT $1;
            """
            rows = await conn.fetch(query, limit)
            results = [dict(row) for row in rows]

        await conn.close()
        return results

    except Exception as e:
        logger.error(f"Failed to retrieve research from database: {e}")
        return []


async def search_research_by_keyword(
    keyword: str,
    limit: int = 10
) -> list:
    """Search research results by keyword.

    Args:
        keyword: Search keyword
        limit: Maximum records to return

    Returns:
        List of matching research records
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL not set")
        return []

    try:
        conn = await asyncpg.connect(database_url)

        query = """
            SELECT id, query, research_brief, created_at,
                   LENGTH(final_report) as report_length
            FROM service20_investment_opportunities
            WHERE query ILIKE $1
               OR research_brief ILIKE $1
               OR final_report ILIKE $1
            ORDER BY created_at DESC
            LIMIT $2;
        """

        rows = await conn.fetch(query, f'%{keyword}%', limit)
        results = [dict(row) for row in rows]

        await conn.close()
        return results

    except Exception as e:
        logger.error(f"Failed to search research: {e}")
        return []


async def create_service20_alert(
    research_results: Dict[str, Any],
    opportunity_data: Optional[Dict[str, Any]] = None,
    user_id: str = "api-system-user"
) -> Optional[int]:
    """Create an alert notification for completed Service20 research.

    Args:
        research_results: Research results dictionary from deep researcher
        opportunity_data: Original opportunity data (optional)
        user_id: User ID to create alert for (default: system user)

    Returns:
        Alert ID if successful, None otherwise
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.warning("DATABASE_URL not set - skipping alert creation")
        return None

    try:
        conn = await asyncpg.connect(database_url)

        # Extract fields from research results
        research_id = research_results.get('research_id', 'unknown')
        opportunity_type = research_results.get('opportunity_type', 'unknown')
        research_brief = research_results.get('research_brief', '')
        final_report = research_results.get('final_report', '')
        findings = research_results.get('findings', [])

        # Build alert name and description
        if opportunity_data:
            alert_name = f"New {opportunity_type.title()} Research: {opportunity_data.get('title', research_id)[:50]}"
            location = opportunity_data.get('location', 'Unknown location')
            alert_description = f"Research completed for {opportunity_type} opportunity in {location}. {len(findings)} findings discovered."
        else:
            alert_name = f"New {opportunity_type.title()} Research Completed"
            alert_description = f"Service20 completed research for {research_id}. {len(findings)} findings discovered."

        # Prepare alert criteria with comprehensive metadata for matching
        alert_criteria = {
            "type": "service20_research",
            "research_id": research_id,
            "opportunity_type": opportunity_type,
            "findings_count": len(findings),
            "report_length": len(final_report),

            # Enhanced metadata for intelligent matching
            "sector": {
                "primary": opportunity_data.get('sector', 'unknown') if opportunity_data else 'unknown',
                "secondary": opportunity_data.get('subsector', '') if opportunity_data else '',
                "tags": opportunity_data.get('sector_tags', []) if opportunity_data else []
            },

            "financial": {
                "amount": opportunity_data.get('investment_amount') or opportunity_data.get('funding_amount', 0) if opportunity_data else 0,
                "minimum_required": opportunity_data.get('minimum_investment', 0) if opportunity_data else 0,
                "roi_expected": opportunity_data.get('roi', 0) if opportunity_data else 0,
                "payback_years": opportunity_data.get('payback_years', 0) if opportunity_data else 0,
                "currency": opportunity_data.get('currency', 'USD') if opportunity_data else 'USD',
                "carbon_reduction_tons_annually": opportunity_data.get('carbon_reduction', 0) if opportunity_data else 0
            },

            "location": {
                "city": opportunity_data.get('city', 'Unknown') if opportunity_data else 'Unknown',
                "country": opportunity_data.get('country', 'Unknown') if opportunity_data else 'Unknown',
                "region": opportunity_data.get('region', 'Unknown') if opportunity_data else 'Unknown',
                "geoname_id": opportunity_data.get('geoname_id', '') if opportunity_data else '',
                "coordinates": opportunity_data.get('coordinates', []) if opportunity_data else []
            },

            "timeline": {
                "planning_start": opportunity_data.get('planning_start', '') if opportunity_data else '',
                "execution_start": opportunity_data.get('execution_start', '') if opportunity_data else '',
                "completion": opportunity_data.get('completion', '') if opportunity_data else '',
                "deadline": opportunity_data.get('deadline', '') if opportunity_data else '',
                "urgency": opportunity_data.get('urgency', 'medium') if opportunity_data else 'medium'
            },

            "technical": {
                "technology": opportunity_data.get('technology', '') if opportunity_data else '',
                "capacity_mw": opportunity_data.get('capacity_mw', 0) if opportunity_data else 0,
                "maturity": opportunity_data.get('maturity', 'planning') if opportunity_data else 'planning'
            },

            "bundling": {
                "eligible": opportunity_data.get('bundling_eligible', True) if opportunity_data else True,
                "minimum_bundle_size": opportunity_data.get('minimum_bundle_size', 1000000) if opportunity_data else 1000000,
                "maximum_bundle_partners": opportunity_data.get('maximum_bundle_partners', 5) if opportunity_data else 5,
                "compatibility_requirements": opportunity_data.get('compatibility_requirements', ['same_sector']) if opportunity_data else ['same_sector']
            },

            # Keep backward compatibility
            "opportunity_data": opportunity_data or {}
        }

        # Insert alert into database
        import json

        insert_query = """
            INSERT INTO service20_alerts (
                research_id,
                user_id,
                alert_type,
                title,
                description,
                criteria
            ) VALUES ($1, $2, $3, $4, $5, $6::jsonb)
            RETURNING id;
        """

        alert_id = await conn.fetchval(
            insert_query,
            research_id,
            user_id,
            opportunity_type,
            alert_name,
            alert_description,
            json.dumps(alert_criteria)  # Convert dict to JSON string
        )

        logger.info(f"Created Service20 alert with ID: {alert_id} for research {research_id}")

        await conn.close()
        return alert_id

    except Exception as e:
        logger.error(f"Failed to create Service20 alert: {e}")
        return None


async def store_match_proposal(
    match_data: Dict[str, Any],
    requires_approval: bool = False
) -> Optional[str]:
    """Store a match proposal in the database.

    Args:
        match_data: Match proposal data including opportunities, funders, and metrics
        requires_approval: Whether match needs human approval before notification

    Returns:
        Match ID if successful, None otherwise
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.warning("DATABASE_URL not set - skipping match storage")
        return None

    try:
        conn = await asyncpg.connect(database_url)

        # Extract match details
        match_id = match_data.get('match_id')
        match_type = match_data.get('match_type', 'bundled')
        compatibility_score = match_data.get('compatibility_score', 0.0)
        confidence_level = match_data.get('confidence_level', 'medium')

        # Opportunity and funder IDs
        opportunity_alert_ids = [o.get('alert_id') for o in match_data.get('opportunities', [])]
        funder_alert_ids = [f.get('alert_id') for f in match_data.get('funders', [])]

        # Full participant data
        opportunities_data = match_data.get('opportunities', [])
        funders_data = match_data.get('funders', [])

        # Bundle metrics
        bundle_metrics = match_data.get('bundle_metrics', {})

        # Matching criteria
        criteria_met = match_data.get('criteria_met', [])
        criteria_warnings = match_data.get('criteria_warnings', [])

        import json

        insert_query = """
            INSERT INTO opportunity_matches (
                match_id,
                match_type,
                opportunity_alert_ids,
                funder_alert_ids,
                opportunities_data,
                funders_data,
                compatibility_score,
                confidence_level,
                bundle_metrics,
                criteria_met,
                criteria_warnings,
                requires_approval,
                status
            ) VALUES ($1, $2, $3::jsonb, $4::jsonb, $5::jsonb, $6::jsonb, $7, $8, $9::jsonb, $10, $11, $12, $13)
            RETURNING match_id;
        """

        stored_match_id = await conn.fetchval(
            insert_query,
            match_id,
            match_type,
            json.dumps(opportunity_alert_ids),
            json.dumps(funder_alert_ids),
            json.dumps(opportunities_data),
            json.dumps(funders_data),
            compatibility_score,
            confidence_level,
            json.dumps(bundle_metrics),
            criteria_met,
            criteria_warnings,
            requires_approval,
            'proposed'
        )

        logger.info(f"Stored match proposal {stored_match_id} ({match_type}, score: {compatibility_score:.2f})")

        await conn.close()
        return stored_match_id

    except Exception as e:
        logger.error(f"Failed to store match proposal: {e}")
        return None


async def get_match_proposals(
    match_type: Optional[str] = None,
    min_confidence: Optional[str] = None,
    limit: int = 50
) -> list:
    """Retrieve match proposals from database.

    Args:
        match_type: Filter by match type ('simple', 'bundled', 'syndicated')
        min_confidence: Minimum confidence level ('high', 'medium', 'low')
        limit: Maximum records to return

    Returns:
        List of match proposal records
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL not set")
        return []

    try:
        conn = await asyncpg.connect(database_url)

        # Build query based on filters
        conditions = []
        params = []
        param_count = 1

        if match_type:
            conditions.append(f"match_type = ${param_count}")
            params.append(match_type)
            param_count += 1

        if min_confidence:
            confidence_order = {'high': 3, 'medium': 2, 'low': 1}
            min_level = confidence_order.get(min_confidence, 1)
            if min_level == 3:
                conditions.append("confidence_level = 'high'")
            elif min_level == 2:
                conditions.append("confidence_level IN ('high', 'medium')")

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        query = f"""
            SELECT *
            FROM opportunity_matches
            {where_clause}
            ORDER BY compatibility_score DESC, created_at DESC
            LIMIT ${param_count};
        """
        params.append(limit)

        rows = await conn.fetch(query, *params)
        results = [dict(row) for row in rows]

        await conn.close()
        return results

    except Exception as e:
        logger.error(f"Failed to retrieve match proposals: {e}")
        return []


async def create_match_alert(
    match_data: Dict[str, Any],
    auto_notify: bool = True
) -> Optional[List[str]]:
    """Create alert notifications for all participants in a match.

    Args:
        match_data: Match proposal data
        auto_notify: Whether to send API alerts immediately (default: True for high confidence)

    Returns:
        List of created alert IDs if successful, None otherwise
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.warning("DATABASE_URL not set - skipping match alert creation")
        return None

    try:
        alert_ids = []

        # Create alert for each opportunity (city perspective)
        opportunities = match_data.get('opportunities', [])
        funders = match_data.get('funders', [])
        bundle_metrics = match_data.get('bundle_metrics', {})
        match_id = match_data.get('match_id')
        match_type = match_data.get('match_type')
        compatibility_score = match_data.get('compatibility_score', 0)

        for opp in opportunities:
            # Build alert for this opportunity
            partner_cities = [o.get('city') for o in opportunities if o != opp]

            alert_name = f"Match Found: {opp.get('city')} Project"
            if match_type == 'bundled':
                alert_description = f"Your {opp.get('sector')} project in {opp.get('city')} can be bundled with {len(partner_cities)} other cities to attract funding from {funders[0].get('research_id', 'investor')}."
            else:
                alert_description = f"Your {opp.get('sector')} project in {opp.get('city')} matches with funding opportunity {funders[0].get('research_id', 'investor')}."

            alert_criteria = {
                "type": "service20_match",
                "match_id": match_id,
                "match_type": match_type,
                "role": "opportunity_provider",

                "your_project": {
                    "city": opp.get('city'),
                    "sector": opp.get('sector'),
                    "investment_amount": opp.get('investment_amount'),
                    "roi": opp.get('roi'),
                    "carbon_reduction": opp.get('carbon_reduction')
                },

                "match_details": {
                    "compatibility_score": compatibility_score,
                    "confidence": match_data.get('confidence_level'),
                    "partner_cities": partner_cities if match_type == 'bundled' else [],
                    "funder": funders[0].get('research_id') if funders else 'Unknown',
                    "criteria_met": match_data.get('criteria_met', [])
                },

                "bundle_metrics": {
                    "total_investment": bundle_metrics.get('total_investment'),
                    "blended_roi": bundle_metrics.get('blended_roi'),
                    "total_carbon_reduction": bundle_metrics.get('total_carbon_reduction'),
                    "project_count": bundle_metrics.get('project_count')
                } if match_type == 'bundled' else {},

                "next_steps": [
                    "Review the match details and compatibility score",
                    "Contact partner cities if bundled" if match_type == 'bundled' else "Contact the funder directly",
                    "Prepare project documentation and financial projections",
                    "Schedule introduction call with funder"
                ]
            }

            # Create database alert
            import json
            conn = await asyncpg.connect(database_url)

            insert_query = """
                INSERT INTO alerts (
                    user_id,
                    name,
                    description,
                    criteria,
                    is_active,
                    last_triggered,
                    city_id
                ) VALUES ($1, $2, $3, $4::jsonb, $5, $6, $7)
                RETURNING id;
            """

            alert_id = await conn.fetchval(
                insert_query,
                "api-system-user",  # Can be customized per opportunity
                alert_name,
                alert_description,
                json.dumps(alert_criteria),
                True,
                None,
                None  # Could extract from opp data
            )

            alert_ids.append(alert_id)
            logger.info(f"Created match alert {alert_id} for opportunity {opp.get('city')}")

            await conn.close()

            # Create API alert if auto_notify
            if auto_notify:
                try:
                    import sys
                    from pathlib import Path
                    parent_dir = Path(__file__).parent.parent.parent
                    if str(parent_dir) not in sys.path:
                        sys.path.insert(0, str(parent_dir))

                    from create_alert_api import create_alert_via_api

                    api_result = create_alert_via_api(
                        name=alert_name,
                        criteria={
                            "type": "service20_match",
                            "conditions": {
                                "match_id": match_id,
                                "role": "opportunity",
                                "compatibility_score": compatibility_score
                            }
                        }
                    )

                    if api_result:
                        logger.info(f"Created API alert for opportunity {opp.get('city')}")

                except Exception as e:
                    logger.error(f"Failed to create API alert: {e}")

        # Create alert for each funder
        for funder in funders:
            alert_name = f"Match Found: {funder.get('sector_interest', 'Investment')} Opportunities"

            if match_type == 'bundled':
                cities_list = ", ".join([o.get('city') for o in opportunities])
                alert_description = f"Found bundled investment opportunity: {len(opportunities)} {opportunities[0].get('sector')} projects in {cities_list} totaling ${bundle_metrics.get('total_investment'):,.0f}."
            else:
                alert_description = f"Found matching {opportunities[0].get('sector')} project in {opportunities[0].get('city')} seeking ${opportunities[0].get('investment_amount'):,.0f} investment."

            alert_criteria = {
                "type": "service20_match",
                "match_id": match_id,
                "match_type": match_type,
                "role": "funder",

                "matched_opportunities": [
                    {
                        "city": o.get('city'),
                        "country": o.get('country'),
                        "sector": o.get('sector'),
                        "investment_amount": o.get('investment_amount'),
                        "roi": o.get('roi'),
                        "carbon_reduction": o.get('carbon_reduction')
                    }
                    for o in opportunities
                ],

                "match_details": {
                    "compatibility_score": compatibility_score,
                    "confidence": match_data.get('confidence_level'),
                    "criteria_met": match_data.get('criteria_met', []),
                    "warnings": match_data.get('criteria_warnings', [])
                },

                "bundle_metrics": bundle_metrics if match_type == 'bundled' else {},

                "next_steps": [
                    "Review project details and financial projections",
                    "Assess combined risk profile" if match_type == 'bundled' else "Assess project risk",
                    "Contact project lead(s) for more information",
                    "Schedule due diligence review"
                ]
            }

            # Create database alert
            conn = await asyncpg.connect(database_url)

            alert_id = await conn.fetchval(
                insert_query,
                "api-system-user",
                alert_name,
                alert_description,
                json.dumps(alert_criteria),
                True,
                None,
                None
            )

            alert_ids.append(alert_id)
            logger.info(f"Created match alert {alert_id} for funder {funder.get('research_id')}")

            await conn.close()

            # Create API alert if auto_notify
            if auto_notify:
                try:
                    from create_alert_api import create_alert_via_api

                    api_result = create_alert_via_api(
                        name=alert_name,
                        criteria={
                            "type": "service20_match",
                            "conditions": {
                                "match_id": match_id,
                                "role": "funder",
                                "compatibility_score": compatibility_score,
                                "opportunity_count": len(opportunities)
                            }
                        }
                    )

                    if api_result:
                        logger.info(f"Created API alert for funder {funder.get('research_id')}")

                except Exception as e:
                    logger.error(f"Failed to create API alert: {e}")

        logger.info(f"Created {len(alert_ids)} alerts for match {match_id}")
        return alert_ids

    except Exception as e:
        logger.error(f"Failed to create match alerts: {e}")
        import traceback
        traceback.print_exc()
        return None


async def store_investment_research(research_data: Dict[str, Any]) -> Optional[int]:
    """Store investment opportunity research in database.

    Args:
        research_data: Dictionary containing:
            - query: Research query/prompt
            - research_brief: Brief summary
            - final_report: Full research report
            - notes: List of findings/notes
            - city: City name
            - country_code: ISO 3166-1 alpha-3 country code
            - country: Country name
            - sector: Primary sector
            - langfuse_trace_id: Optional trace ID

    Returns:
        Database record ID if successful, None otherwise
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.warning("DATABASE_URL not set - skipping database storage")
        return None

    try:
        conn = await asyncpg.connect(database_url)

        # Extract fields
        query = research_data.get('query', '')
        research_brief = research_data.get('research_brief', '')
        final_report = research_data.get('final_report', '')
        notes = research_data.get('notes', [])
        city = research_data.get('city', '')
        country_code = research_data.get('country_code', '')
        country = research_data.get('country', '')
        sector = research_data.get('sector', 'renewable_energy')
        langfuse_trace_id = research_data.get('langfuse_trace_id')

        # Prepare metadata
        metadata = {
            'has_research_brief': bool(research_brief),
            'notes_count': len(notes),
            'report_length': len(final_report),
            'city': city,
            'country': country,
            'country_code': country_code,
            'sector': sector
        }

        # Insert into database
        insert_query = """
            INSERT INTO service20_investment_opportunities (
                query,
                research_brief,
                final_report,
                metadata,
                city,
                country_code,
                country,
                sector,
                langfuse_trace_id
            ) VALUES ($1, $2, $3, $4::jsonb, $5, $6, $7, $8, $9)
            RETURNING id;
        """

        import json
        record_id = await conn.fetchval(
            insert_query,
            query,
            research_brief,
            final_report,
            json.dumps(metadata),
            city,
            country_code,
            country,
            sector,
            langfuse_trace_id
        )

        await conn.close()

        logger.info(f"Stored investment research with ID: {record_id} for {city}, {country}")
        return record_id

    except Exception as e:
        logger.error(f"Failed to store investment research: {e}")
        import traceback
        traceback.print_exc()
        return None
