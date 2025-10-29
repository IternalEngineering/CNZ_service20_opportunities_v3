"""Test the new opportunity term matcher with real database data and save results."""

import asyncio
import asyncpg
import os
from pathlib import Path
from dotenv import load_dotenv
import uuid
from datetime import datetime
import json

from opportunity_term_matcher_local import OpportunityTermMatcher, PDFDocument

load_dotenv()


async def get_opportunity(conn, opp_id: int):
    """Get opportunity from database."""
    result = await conn.fetchrow("""
        SELECT id, query, research_brief, final_report, city, country, sector
        FROM service20_investment_opportunities
        WHERE id = $1
    """, opp_id)
    return result


async def save_match_result(conn, result, council_doc, investor_doc, provider_doc):
    """Save match result to service20_matches table."""

    match_id = f"term-match-{result.opportunity_id}"

    # Build detailed match analysis text
    match_analysis = f"""LOCATION: {result.location} ({result.location_granularity})

MATCH REASONING:
{result.match_reasoning}

EXTRACTED DETAILS:
{result.extracted_details.get('text', 'None')}

COUNCIL TERMS:
{result.council_terms.get('raw_terms', 'Not available')[:500]}...

INVESTOR TERMS:
{result.investor_terms.get('raw_terms', 'Not available')[:500]}...

PROVIDER TERMS:
{result.provider_terms.get('raw_terms', 'Not available')[:500]}...
"""

    # Insert into database using the actual schema
    await conn.execute("""
        INSERT INTO service20_matches (
            match_id, bundle_name, bundle_description,
            opportunity_ids, opportunity_count,
            cities, countries, regions,
            primary_sector, sectors,
            total_investment, currency,
            match_metrics, criteria,
            council_doc_url, investor_doc_url, provider_doc_url,
            council_match_score, investor_match_score, provider_match_score,
            overall_match_score, compatibility_score,
            match_analysis, match_failed, created_at
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14,
            $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25
        )
    """,
        match_id,  # $1
        f"Term Match - Opp {result.opportunity_id}",  # $2 - bundle_name
        f"Location: {result.location} - Term-based match for investment opportunity",  # $3 - bundle_description
        [str(result.opportunity_id)],  # $4 - opportunity_ids (TEXT[])
        1,  # $5 - opportunity_count
        [result.location],  # $6 - cities
        ['Unknown'],  # $7 - countries
        ['Unknown'],  # $8 - regions
        'unknown',  # $9 - primary_sector
        ['unknown'],  # $10 - sectors
        0.0,  # $11 - total_investment
        'GBP',  # $12 - currency
        json.dumps({'location_granularity': result.location_granularity, 'confidence': result.overall_confidence}),  # $13 - match_metrics (JSONB)
        json.dumps({'extracted_details': result.extracted_details}),  # $14 - criteria (JSONB)
        council_doc.file_path,  # $15 - council_doc_url
        investor_doc.file_path,  # $16 - investor_doc_url
        provider_doc.file_path,  # $17 - provider_doc_url
        result.overall_confidence,  # $18 - council_match_score
        result.overall_confidence,  # $19 - investor_match_score
        result.overall_confidence,  # $20 - provider_match_score
        result.overall_confidence,  # $21 - overall_match_score
        result.overall_confidence,  # $22 - compatibility_score
        match_analysis,  # $23 - match_analysis
        False,  # $24 - match_failed
        datetime.utcnow()  # $25 - created_at
    )

    print(f"Saved match result to database: {match_id}")
    return match_id


async def test_single_opportunity():
    """Test matching with a single opportunity and save to database."""

    # Set up PDFs
    pdf_dir = Path(__file__).parent.parent / "terms" / "Example_pdfs"

    council_doc = PDFDocument(
        name="Manchester PPA",
        file_path=str(pdf_dir / "Manchester_PPA_Purchase.pdf"),
        type="council",
        description="Council procurement"
    )

    investor_doc = PDFDocument(
        name="ILPA Term Sheet",
        file_path=str(pdf_dir / "ILPA-Model-LPA-Term-Sheet-WOF-Version.pdf"),
        type="investor",
        description="Investor terms"
    )

    provider_doc = PDFDocument(
        name="EnergyREV Case Study",
        file_path=str(pdf_dir / "EnergyREV_Bunhill_Case_Study.pdf"),
        type="provider",
        description="Provider capabilities"
    )

    # Connect to database
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))

    try:
        # Get opportunity ID 2 (Bristol housing)
        opp = await get_opportunity(conn, 2)

        if not opp:
            print("Opportunity not found!")
            return

        print("\n" + "="*80)
        print("TESTING NEW OPPORTUNITY TERM MATCHER")
        print("="*80)
        print(f"Opportunity ID: {opp['id']}")
        print(f"Query: {opp['query']}")
        print(f"City: {opp['city']}")
        print(f"Country: {opp['country']}")
        print(f"Sector: {opp['sector']}")

        # Create matcher and run
        matcher = OpportunityTermMatcher()

        # Use the full report as opportunity description
        opportunity_description = f"""
        Query: {opp['query']}

        Research Brief: {opp['research_brief'] or 'Not available'}

        Final Report: {opp['final_report'] or 'Not available'}
        """

        print("\n" + "="*80)
        print("RUNNING MATCHING...")
        print("="*80)

        result = matcher.match_opportunity(
            opportunity_id=opp['id'],
            opportunity_description=opportunity_description,
            council_doc=council_doc,
            investor_doc=investor_doc,
            provider_doc=provider_doc
        )

        print("\n" + "="*80)
        print("MATCH RESULT")
        print("="*80)
        print(f"\nLocation: {result.location}")
        print(f"Granularity: {result.location_granularity}")
        print(f"Confidence: {result.overall_confidence}%")

        print(f"\nMatch Reasoning:")
        print("-" * 80)
        print(result.match_reasoning)

        print(f"\nExtracted Details:")
        print("-" * 80)
        print(result.extracted_details)

        # Save to database
        print("\n" + "="*80)
        print("SAVING TO DATABASE...")
        print("="*80)

        match_id = await save_match_result(conn, result, council_doc, investor_doc, provider_doc)

        print(f"\nSUCCESS: Match saved with ID {match_id}")

        # Verify it was saved
        saved = await conn.fetchrow("""
            SELECT match_id, opportunity_ids, overall_match_score, match_failed
            FROM service20_matches
            WHERE match_id = $1
        """, match_id)

        print(f"\nVerification:")
        print(f"  Match ID: {saved['match_id']}")
        print(f"  Opportunity IDs: {saved['opportunity_ids']}")
        print(f"  Overall Score: {saved['overall_match_score']}")
        print(f"  Failed: {saved['match_failed']}")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(test_single_opportunity())
