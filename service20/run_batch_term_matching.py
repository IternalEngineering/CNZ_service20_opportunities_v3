"""Batch process opportunities with the new term matcher."""

import asyncio
import asyncpg
import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import json
import time

from opportunity_term_matcher_local import OpportunityTermMatcher, PDFDocument

load_dotenv()


async def get_opportunities(conn, limit: int = 10):
    """Get opportunities from database."""
    results = await conn.fetch("""
        SELECT id, query, research_brief, final_report, city, country, sector
        FROM service20_investment_opportunities
        ORDER BY id
        LIMIT $1
    """, limit)
    return results


async def save_match_result(conn, result, council_doc, investor_doc, provider_doc):
    """Save match result to service20_matches table."""

    match_id = f"term-match-{result.opportunity_id}"

    # Build detailed match analysis text
    match_analysis = f"""LOCATION: {result.location} ({result.location_granularity})

MATCH REASONING:
{result.match_reasoning}

EXTRACTED DETAILS:
{result.extracted_details.get('text', 'None')}

COUNCIL TERMS (excerpt):
{result.council_terms.get('raw_terms', 'Not available')[:500]}...

INVESTOR TERMS (excerpt):
{result.investor_terms.get('raw_terms', 'Not available')[:500]}...

PROVIDER TERMS (excerpt):
{result.provider_terms.get('raw_terms', 'Not available')[:500]}...
"""

    try:
        # Insert into database
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
            ON CONFLICT (match_id) DO UPDATE SET
                bundle_name = EXCLUDED.bundle_name,
                bundle_description = EXCLUDED.bundle_description,
                cities = EXCLUDED.cities,
                overall_match_score = EXCLUDED.overall_match_score,
                match_analysis = EXCLUDED.match_analysis,
                updated_at = NOW()
        """,
            match_id,  # $1
            f"Term Match - Opp {result.opportunity_id}",  # $2
            f"Location: {result.location} - Term-based match",  # $3
            [str(result.opportunity_id)],  # $4
            1,  # $5
            [result.location],  # $6
            ['Unknown'],  # $7
            ['Unknown'],  # $8
            'unknown',  # $9
            ['unknown'],  # $10
            0.0,  # $11
            'GBP',  # $12
            json.dumps({'location_granularity': result.location_granularity, 'confidence': result.overall_confidence}),  # $13
            json.dumps({'extracted_details': result.extracted_details}),  # $14
            council_doc.file_path,  # $15
            investor_doc.file_path,  # $16
            provider_doc.file_path,  # $17
            result.overall_confidence,  # $18
            result.overall_confidence,  # $19
            result.overall_confidence,  # $20
            result.overall_confidence,  # $21
            result.overall_confidence,  # $22
            match_analysis,  # $23
            False,  # $24
            datetime.utcnow()  # $25
        )
        return match_id, None
    except Exception as e:
        return None, str(e)


async def run_batch_matching(limit: int = 10):
    """Run batch matching on first N opportunities."""

    print("="*80)
    print("BATCH OPPORTUNITY TERM MATCHING")
    print("="*80)
    print(f"Processing first {limit} opportunities")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

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
        # Get opportunities
        opportunities = await get_opportunities(conn, limit)
        total = len(opportunities)
        print(f"\nFound {total} opportunities to process\n")

        # Create matcher
        matcher = OpportunityTermMatcher()

        # Process each opportunity
        success_count = 0
        failed_count = 0

        for i, opp in enumerate(opportunities, 1):
            print(f"\n[{i}/{total}] Processing Opportunity {opp['id']}")
            print(f"  Query: {opp['query'][:80]}...")

            try:
                # Build opportunity description
                opportunity_description = f"""
                Query: {opp['query']}

                Research Brief: {opp['research_brief'] or 'Not available'}

                Final Report: {opp['final_report'] or 'Not available'}
                """

                # Match opportunity
                start_time = time.time()
                result = matcher.match_opportunity(
                    opportunity_id=opp['id'],
                    opportunity_description=opportunity_description,
                    council_doc=council_doc,
                    investor_doc=investor_doc,
                    provider_doc=provider_doc
                )
                elapsed = time.time() - start_time

                # Save to database
                match_id, error = await save_match_result(conn, result, council_doc, investor_doc, provider_doc)

                if error:
                    print(f"  ERROR saving: {error}")
                    failed_count += 1
                else:
                    print(f"  SUCCESS: Location={result.location}, Confidence={result.overall_confidence}%, Time={elapsed:.1f}s")
                    success_count += 1

            except Exception as e:
                print(f"  ERROR: {str(e)}")
                failed_count += 1

            # Small delay between requests
            if i < total:
                time.sleep(1)

        # Summary
        print("\n" + "="*80)
        print("BATCH PROCESSING COMPLETE")
        print("="*80)
        print(f"Total processed: {total}")
        print(f"Successful: {success_count}")
        print(f"Failed: {failed_count}")
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)

    finally:
        await conn.close()


if __name__ == "__main__":
    # Default to 10, can be changed via command line
    import sys
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    asyncio.run(run_batch_matching(limit))
