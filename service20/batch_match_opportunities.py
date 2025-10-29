"""
Batch Processing Script for Three-Way Matching.

This script runs the three-way matcher on all investment opportunities in the database.
It uses publicly accessible PDF documents for council, investor, and provider analysis.

IMPORTANT: Before running this script, you must upload your PDFs to a publicly
accessible location (AWS S3, GitHub, web server) and update the URLs below.
"""

import asyncio
import asyncpg
import logging
import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from threeway_matcher import ThreeWayMatcher, PDFDocument

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()


# CONFIGURE YOUR PDF DOCUMENTS HERE
# Replace these placeholder URLs with actual public URLs to your PDFs
COUNCIL_DOCS = [
    PDFDocument(
        name="Manchester PPA Purchase",
        url="https://example.com/pdfs/Manchester_PPA_Purchase.pdf",  # REPLACE WITH ACTUAL URL
        type="council",
        description="Manchester council PPA procurement requirements"
    ),
    PDFDocument(
        name="Oldham Green New Deal",
        url="https://example.com/pdfs/Oldham_Green_New_Deal_Prospectus.pdf",  # REPLACE WITH ACTUAL URL
        type="council",
        description="Oldham Green New Deal investment prospectus"
    ),
]

INVESTOR_DOCS = [
    PDFDocument(
        name="Clean Energy Fund Terms",
        url="https://example.com/pdfs/cef-rrf-termsheet.pdf",  # REPLACE WITH ACTUAL URL
        type="investor",
        description="Clean Energy Finance investment criteria"
    ),
    PDFDocument(
        name="ILPA Model Term Sheet",
        url="https://example.com/pdfs/ILPA-Model-LPA-Term-Sheet.pdf",  # REPLACE WITH ACTUAL URL
        type="investor",
        description="Standard LP investment term sheet"
    ),
]

PROVIDER_DOCS = [
    PDFDocument(
        name="EnergyREV Bunhill Case Study",
        url="https://example.com/pdfs/EnergyREV_Bunhill_Case_Study.pdf",  # REPLACE WITH ACTUAL URL
        type="provider",
        description="Renewable energy provider case study"
    ),
    PDFDocument(
        name="Cornwall Insight Financing",
        url="https://example.com/pdfs/Cornwall_Insight_Financing_Options.pdf",  # REPLACE WITH ACTUAL URL
        type="provider",
        description="Renewable energy financing options"
    ),
]


async def get_all_opportunities() -> List[Dict[str, Any]]:
    """
    Retrieve all investment opportunities from the database.

    Returns:
        List of opportunity records
    """
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    try:
        opportunities = await conn.fetch("""
            SELECT id, city, country, country_code, sector
            FROM service20_investment_opportunities
            ORDER BY id
        """)
        return [dict(opp) for opp in opportunities]
    finally:
        await conn.close()


async def process_opportunity(
    matcher: ThreeWayMatcher,
    opportunity: Dict[str, Any],
    council_doc: PDFDocument,
    investor_doc: PDFDocument,
    provider_doc: PDFDocument
) -> Dict[str, Any]:
    """
    Process a single opportunity through the three-way matcher.

    Args:
        matcher: ThreeWayMatcher instance
        opportunity: Opportunity record
        council_doc: Council requirements document
        investor_doc: Investor criteria document
        provider_doc: Service provider document

    Returns:
        Result summary dict
    """
    opportunity_id = opportunity['id']
    city = opportunity['city']
    country = opportunity['country']
    sector = opportunity['sector']

    logger.info(f"Processing opportunity {opportunity_id}: {city}, {country} - {sector}")

    try:
        result = await matcher.match_opportunity(
            opportunity_id=opportunity_id,
            council_doc=council_doc,
            investor_doc=investor_doc,
            provider_doc=provider_doc,
            save_to_db=True  # Always save results
        )

        return {
            'opportunity_id': opportunity_id,
            'city': city,
            'country': country,
            'sector': sector,
            'status': 'success',
            'overall_score': result.overall_score,
            'failed': result.overall_score < 40
        }

    except Exception as e:
        logger.error(f"Error processing opportunity {opportunity_id}: {str(e)}")
        return {
            'opportunity_id': opportunity_id,
            'city': city,
            'country': country,
            'sector': sector,
            'status': 'error',
            'error': str(e),
            'overall_score': 0,
            'failed': True
        }


async def batch_process_all_opportunities():
    """
    Main batch processing function.

    Processes all investment opportunities through the three-way matcher
    and saves results to the service20_matches table.
    """
    print("\n" + "="*80)
    print("BATCH THREE-WAY MATCHING - PROCESSING ALL INVESTMENT OPPORTUNITIES")
    print("="*80)

    # Check if URLs are configured
    if any("example.com" in doc.url for doc in COUNCIL_DOCS + INVESTOR_DOCS + PROVIDER_DOCS):
        print("\n⚠️  WARNING: Placeholder URLs detected!")
        print("Please update the PDF URLs in this script before running.")
        print("Google URL Context API requires publicly accessible URLs.")
        print("\nTo upload PDFs:")
        print("  1. Upload to AWS S3: aws s3 cp Example_pdfs/ s3://your-bucket/pdfs/ --recursive --acl public-read")
        print("  2. Or upload to GitHub and use raw URLs")
        print("  3. Update COUNCIL_DOCS, INVESTOR_DOCS, PROVIDER_DOCS in this script")
        print("\nExiting...")
        return

    # Initialize matcher
    try:
        matcher = ThreeWayMatcher()
    except Exception as e:
        logger.error(f"Failed to initialize matcher: {str(e)}")
        print(f"\n❌ Error: Could not initialize matcher - {str(e)}")
        return

    # Get all opportunities
    try:
        opportunities = await get_all_opportunities()
        total = len(opportunities)
        print(f"\nFound {total} investment opportunities to process\n")
    except Exception as e:
        logger.error(f"Failed to fetch opportunities: {str(e)}")
        print(f"\n❌ Error: Could not fetch opportunities - {str(e)}")
        return

    if total == 0:
        print("No opportunities found in database. Exiting.")
        return

    # Process each opportunity
    results = []
    success_count = 0
    failed_match_count = 0
    error_count = 0

    print("Processing opportunities:")
    print("-" * 80)

    for i, opportunity in enumerate(opportunities, 1):
        # Use first document from each category (you can implement round-robin or other logic)
        council_doc = COUNCIL_DOCS[0]
        investor_doc = INVESTOR_DOCS[0]
        provider_doc = PROVIDER_DOCS[0]

        result = await process_opportunity(
            matcher, opportunity, council_doc, investor_doc, provider_doc
        )

        results.append(result)

        # Print progress
        status_symbol = "✓" if result['status'] == 'success' else "✗"
        match_status = "FAILED" if result.get('failed') else f"SCORE: {result.get('overall_score', 0):.1f}"

        print(f"{status_symbol} [{i}/{total}] ID {result['opportunity_id']:3d} - {result['city']:20s} | {match_status}")

        # Update counts
        if result['status'] == 'success':
            success_count += 1
            if result.get('failed'):
                failed_match_count += 1
        else:
            error_count += 1

        # Add a small delay to avoid rate limiting
        await asyncio.sleep(1)

    # Print summary
    print("\n" + "="*80)
    print("BATCH PROCESSING COMPLETE")
    print("="*80)
    print(f"\nTotal Opportunities: {total}")
    print(f"Successfully Processed: {success_count}")
    print(f"  - Successful Matches: {success_count - failed_match_count}")
    print(f"  - Failed Matches: {failed_match_count}")
    print(f"Errors: {error_count}")

    if error_count > 0:
        print("\nOpportunities with errors:")
        for result in results:
            if result['status'] == 'error':
                print(f"  - ID {result['opportunity_id']}: {result.get('error', 'Unknown error')}")

    print("\n" + "="*80)
    print("All results saved to service20_matches table")
    print("="*80)


async def main():
    """Main entry point."""
    try:
        await batch_process_all_opportunities()
    except KeyboardInterrupt:
        print("\n\nBatch processing interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        print(f"\n❌ Fatal error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
