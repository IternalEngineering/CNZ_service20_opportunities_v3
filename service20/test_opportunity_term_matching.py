"""Test the opportunity term matcher with real data."""

import asyncio
import asyncpg
import os
from pathlib import Path
from dotenv import load_dotenv
import http.server
import socketserver
import threading
import time

from opportunity_term_matcher import OpportunityTermMatcher, PDFDocument

load_dotenv()


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
        print(f"Started HTTP server on http://localhost:{self.port}")
        time.sleep(1)  # Give server time to start

    def stop(self):
        """Stop the HTTP server."""
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
            print("Stopped HTTP server")


async def get_opportunity(conn, opp_id: int):
    """Get opportunity from database."""
    result = await conn.fetchrow("""
        SELECT id, query, research_brief, final_report, city, country, sector
        FROM service20_investment_opportunities
        WHERE id = $1
    """, opp_id)
    return result


async def test_single_opportunity():
    """Test matching with a single opportunity."""

    # Start HTTP server for PDFs
    pdf_dir = Path(__file__).parent.parent / "terms" / "Example_pdfs"
    server = PDFServer(pdf_dir, 8888)
    server.start()

    try:
        # Connect to database
        conn = await asyncpg.connect(os.getenv('DATABASE_URL'))

        try:
            # Get opportunity ID 2 (Bristol housing)
            opp = await get_opportunity(conn, 2)

            if not opp:
                print("Opportunity not found!")
                return

            print("\n" + "="*80)
            print("OPPORTUNITY DATA")
            print("="*80)
            print(f"ID: {opp['id']}")
            print(f"Query: {opp['query']}")
            print(f"City: {opp['city']}")
            print(f"Country: {opp['country']}")
            print(f"Sector: {opp['sector']}")
            print(f"\nResearch Brief (first 500 chars):")
            print(opp['research_brief'][:500] if opp['research_brief'] else "None")
            print(f"\nFinal Report (first 500 chars):")
            print(opp['final_report'][:500] if opp['final_report'] else "None")

            # Set up PDFs
            council_doc = PDFDocument(
                name="Manchester PPA",
                url="http://localhost:8888/Manchester_PPA_Purchase.pdf",
                type="council",
                description="Council procurement"
            )

            investor_doc = PDFDocument(
                name="ILPA Term Sheet",
                url="http://localhost:8888/ILPA-Model-LPA-Term-Sheet-WOF-Version.pdf",
                type="investor",
                description="Investor terms"
            )

            provider_doc = PDFDocument(
                name="EnergyREV Case Study",
                url="http://localhost:8888/EnergyREV_Bunhill_Case_Study.pdf",
                type="provider",
                description="Provider capabilities"
            )

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

            print(f"\nCouncil Terms (first 500 chars):")
            print("-" * 80)
            print(str(result.council_terms.get('raw_terms', 'None'))[:500])

            print(f"\nInvestor Terms (first 500 chars):")
            print("-" * 80)
            print(str(result.investor_terms.get('raw_terms', 'None'))[:500])

            print(f"\nProvider Terms (first 500 chars):")
            print("-" * 80)
            print(str(result.provider_terms.get('raw_terms', 'None'))[:500])

        finally:
            await conn.close()

    finally:
        server.stop()


if __name__ == "__main__":
    asyncio.run(test_single_opportunity())
