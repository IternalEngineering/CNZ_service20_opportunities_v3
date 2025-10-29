"""
Run batch matching using local PDFs via temporary HTTP server.

This script:
1. Starts a local HTTP server to serve PDFs from Example_pdfs/
2. Runs the three-way matcher on all investment opportunities
3. Saves results to service20_matches table
4. Shuts down the HTTP server when complete
"""

import asyncio
import os
import sys
import logging
import http.server
import socketserver
import threading
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv
import asyncpg

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from threeway_matcher import ThreeWayMatcher, PDFDocument

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

# Configuration
PDF_DIR = Path(__file__).parents[1] / "terms" / "Example_pdfs"
HTTP_PORT = 8888
BASE_URL = f"http://localhost:{HTTP_PORT}"

# PDF Document mapping
COUNCIL_PDFS = [
    "Manchester_PPA_Purchase.pdf",
    "Oldham_Green_New_Deal_Prospectus.pdf",
    "Islington_Bunhill_OM_Strategy.pdf",
    "TfGM_PPA_Tender.pdf"
]

INVESTOR_PDFS = [
    "ILPA-Model-LPA-Term-Sheet-WOF-Version.pdf",
    "cef-rrf-termsheet.pdf",
    "Pro-Forma-Investment-Term-Sheet.pdf",
    "Simpact_TEMPLATE_TS-1.pdf"
]

PROVIDER_PDFS = [
    "EnergyREV_Bunhill_Case_Study.pdf",
    "Cornwall_Insight_Financing_Options.pdf"
]


class PDFServer:
    """Simple HTTP server to serve PDF files."""

    def __init__(self, directory: Path, port: int):
        self.directory = directory
        self.port = port
        self.httpd = None
        self.thread = None

    def start(self):
        """Start the HTTP server in a background thread."""
        os.chdir(self.directory)

        Handler = http.server.SimpleHTTPRequestHandler
        self.httpd = socketserver.TCPServer(("", self.port), Handler)

        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

        logger.info(f"PDF Server started on http://localhost:{self.port}")
        logger.info(f"Serving files from: {self.directory}")

    def stop(self):
        """Stop the HTTP server."""
        if self.httpd:
            self.httpd.shutdown()
            logger.info("PDF Server stopped")


async def get_all_opportunities() -> List[Dict[str, Any]]:
    """Retrieve all investment opportunities from the database."""
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


async def process_single_opportunity(
    matcher: ThreeWayMatcher,
    opportunity: Dict[str, Any],
    council_url: str,
    investor_url: str,
    provider_url: str
) -> Dict[str, Any]:
    """Process a single opportunity through the matcher."""
    opportunity_id = opportunity['id']
    city = opportunity['city']
    country = opportunity['country']
    sector = opportunity['sector']

    logger.info(f"Processing opportunity {opportunity_id}: {city}, {country} - {sector}")

    # Create PDFDocument objects
    council_doc = PDFDocument(
        name=f"Council Requirements ({Path(council_url).stem})",
        url=council_url,
        type="council",
        description="Council requirements and procurement"
    )

    investor_doc = PDFDocument(
        name=f"Investor Criteria ({Path(investor_url).stem})",
        url=investor_url,
        type="investor",
        description="Investment criteria and terms"
    )

    provider_doc = PDFDocument(
        name=f"Provider Capabilities ({Path(provider_url).stem})",
        url=provider_url,
        type="provider",
        description="Service provider capabilities"
    )

    try:
        result = await matcher.match_opportunity(
            opportunity_id=opportunity_id,
            council_doc=council_doc,
            investor_doc=investor_doc,
            provider_doc=provider_doc,
            save_to_db=True
        )

        return {
            'opportunity_id': opportunity_id,
            'city': city,
            'country': country,
            'sector': sector,
            'status': 'success',
            'overall_score': result.overall_score,
            'failed': result.overall_score < 40,
            'council_score': result.council_match.get('match_score', 0),
            'investor_score': result.investor_match.get('match_score', 0),
            'provider_score': result.provider_match.get('match_score', 0)
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


async def run_batch_matching():
    """Main batch processing function."""
    print("\n" + "="*80)
    print("LOCAL BATCH THREE-WAY MATCHING")
    print("="*80)
    print(f"\nUsing local PDFs from: {PDF_DIR}")
    print(f"HTTP Server: {BASE_URL}\n")

    # Check if PDF directory exists
    if not PDF_DIR.exists():
        print(f"ERROR: PDF directory not found: {PDF_DIR}")
        return

    # Start HTTP server
    server = PDFServer(PDF_DIR, HTTP_PORT)
    try:
        server.start()

        # Give server a moment to start
        await asyncio.sleep(1)

        # Initialize matcher
        try:
            matcher = ThreeWayMatcher()
        except Exception as e:
            logger.error(f"Failed to initialize matcher: {str(e)}")
            print(f"\nERROR: Could not initialize matcher - {str(e)}")
            return

        # Get all opportunities
        try:
            opportunities = await get_all_opportunities()
            total = len(opportunities)
            print(f"Found {total} investment opportunities to process\n")
        except Exception as e:
            logger.error(f"Failed to fetch opportunities: {str(e)}")
            print(f"\nERROR: Could not fetch opportunities - {str(e)}")
            return

        if total == 0:
            print("No opportunities found in database.")
            return

        # Process each opportunity
        results = []
        success_count = 0
        failed_match_count = 0
        error_count = 0

        print("Processing opportunities:")
        print("-" * 80)

        for i, opportunity in enumerate(opportunities, 1):
            # Use first document from each category (round-robin could be added)
            council_url = f"{BASE_URL}/{COUNCIL_PDFS[i % len(COUNCIL_PDFS)]}"
            investor_url = f"{BASE_URL}/{INVESTOR_PDFS[i % len(INVESTOR_PDFS)]}"
            provider_url = f"{BASE_URL}/{PROVIDER_PDFS[i % len(PROVIDER_PDFS)]}"

            result = await process_single_opportunity(
                matcher, opportunity, council_url, investor_url, provider_url
            )

            results.append(result)

            # Print progress
            status_symbol = "SUCCESS" if result['status'] == 'success' else "ERROR"
            match_status = "FAILED" if result.get('failed') else f"SCORE: {result.get('overall_score', 0):.1f}"

            scores_detail = ""
            if result['status'] == 'success' and not result.get('failed'):
                scores_detail = f" (C:{result.get('council_score', 0):.0f} I:{result.get('investor_score', 0):.0f} P:{result.get('provider_score', 0):.0f})"

            # Handle NULL values in city/country
            city_display = (result.get('city') or 'Unknown')[:20]
            print(f"[{i}/{total}] ID {result['opportunity_id']:3d} - {city_display:20s} | {status_symbol:7s} | {match_status}{scores_detail}")

            # Update counts
            if result['status'] == 'success':
                success_count += 1
                if result.get('failed'):
                    failed_match_count += 1
            else:
                error_count += 1

            # Small delay to avoid overwhelming the API
            await asyncio.sleep(2)

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
                    print(f"  - ID {result['opportunity_id']}: {result.get('error', 'Unknown error')[:100]}")

        # Print score distribution
        if success_count > 0:
            print("\nScore Distribution:")
            strong = sum(1 for r in results if r.get('overall_score', 0) >= 75)
            moderate = sum(1 for r in results if 60 <= r.get('overall_score', 0) < 75)
            weak = sum(1 for r in results if 40 <= r.get('overall_score', 0) < 60)
            failed = sum(1 for r in results if r.get('overall_score', 0) < 40)

            print(f"  Strong (75-100):   {strong}")
            print(f"  Moderate (60-74):  {moderate}")
            print(f"  Weak (40-59):      {weak}")
            print(f"  Failed (0-39):     {failed}")

        print("\n" + "="*80)
        print("All results saved to service20_matches table")
        print("="*80)

    finally:
        # Stop HTTP server
        server.stop()


async def main():
    """Main entry point."""
    try:
        await run_batch_matching()
    except KeyboardInterrupt:
        print("\n\nBatch processing interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        print(f"\nFATAL ERROR: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
