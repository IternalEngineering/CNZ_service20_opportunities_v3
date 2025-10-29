"""
Test script for three-way matching with publicly accessible URLs.

Note: Google URL Context API requires publicly accessible URLs.
Local PDFs need to be uploaded to a web server or cloud storage first.
"""

import asyncio
import logging
from threeway_matcher import ThreeWayMatcher, PDFDocument

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_threeway_match():
    """
    Test three-way matching with example opportunity and documents.

    For this test to work, you need to:
    1. Upload the Example_pdfs to a publicly accessible location (S3, GitHub, etc.)
    2. Update the URLs below with the public URLs
    """

    # Example: Using publicly accessible documents
    # Replace these with actual public URLs to your PDFs

    council_doc = PDFDocument(
        name="Council Requirements Example",
        url="https://example.com/council_requirements.pdf",  # REPLACE WITH ACTUAL URL
        type="council",
        description="Council renewable energy procurement requirements"
    )

    investor_doc = PDFDocument(
        name="Investor Term Sheet Example",
        url="https://example.com/investor_terms.pdf",  # REPLACE WITH ACTUAL URL
        type="investor",
        description="Investment fund term sheet and criteria"
    )

    provider_doc = PDFDocument(
        name="Service Provider Capabilities",
        url="https://example.com/provider_capabilities.pdf",  # REPLACE WITH ACTUAL URL
        type="provider",
        description="Renewable energy service provider capabilities"
    )

    # Initialize matcher
    matcher = ThreeWayMatcher()

    # Get opportunity from database (assuming ID 1 exists)
    opportunity_id = 1

    print("\n" + "="*80)
    print("TESTING THREE-WAY MATCHER")
    print("="*80)

    print(f"\nFetching opportunity {opportunity_id} from database...")
    opportunity = await matcher.get_opportunity_from_db(opportunity_id)

    print(f"\nOpportunity Details:")
    print(f"  City: {opportunity.city}")
    print(f"  Country: {opportunity.country}")
    print(f"  Sector: {opportunity.sector}")
    print(f"  Brief: {opportunity.research_brief[:200]}...")

    print(f"\nDocuments to analyze:")
    print(f"  Council: {council_doc.name}")
    print(f"  Investor: {investor_doc.name}")
    print(f"  Provider: {provider_doc.name}")

    print("\n⚠️  NOTE: This test requires publicly accessible PDF URLs")
    print("   Please upload the PDFs from Example_pdfs/ to a public location")
    print("   and update the URLs in this script.")

    # Uncomment below to run actual matching (requires valid public URLs)
    """
    try:
        print("\nStarting three-way match analysis...")
        result = await matcher.match_opportunity(
            opportunity_id=opportunity_id,
            council_doc=council_doc,
            investor_doc=investor_doc,
            provider_doc=provider_doc
        )

        print("\n" + "="*80)
        print("MATCH RESULTS")
        print("="*80)
        print(f"\nOVERALL SCORE: {result.overall_score}/100")
        print("\n" + "-"*80)
        print(result.compatibility_analysis)
        print("\n" + "-"*80)
        print("\nRECOMMENDATIONS:")
        for rec in result.recommendations:
            print(f"  {rec}")
        print("="*80)

    except Exception as e:
        logger.error(f"Error during matching: {str(e)}", exc_info=True)
    """


async def demonstrate_with_sample_analysis():
    """
    Demonstrate the matching logic without requiring actual URLs.
    Shows what the output would look like.
    """
    print("\n" + "="*80)
    print("DEMONSTRATION: THREE-WAY MATCH OUTPUT")
    print("="*80)

    print("""
THREE-WAY MATCH ANALYSIS: Manchester, United Kingdom - renewable_energy

COUNCIL/MUNICIPALITY ALIGNMENT:
Score: 85/100
- Requirements: 10-50MW renewable energy projects, focus on PPAs
- Procurement: Power Purchase Agreement framework, competitive tender
- Key Factors: Alignment with net-zero goals, local job creation, community benefit
- Barriers: Planning permission timeline, grid connection capacity

INVESTOR/FUNDER ALIGNMENT:
Score: 78/100
- Investment Range: £2M - £15M per project
- Sectors: Solar, Wind, Energy Storage
- Strengths: Strong ESG focus, proven UK track record, flexible terms
- Concerns: ROI expectations vs. PPA rates, construction timeline risk

SERVICE PROVIDER ALIGNMENT:
Score: 82/100
- Services: Design, Build, Commission, O&M
- Expertise: Solar PV, Battery Storage, Grid Integration
- Capabilities: 50+ UK projects, ISO certifications, in-house team
- Limitations: Limited wind expertise, potential capacity constraints

OVERALL MATCH SCORE: 81.7/100

RECOMMENDATIONS:
  ✅ STRONG MATCH: Proceed with detailed due diligence and proposal development
  - Conduct site visit to assess grid connection feasibility
  - Negotiate PPA terms that meet investor ROI requirements
  - Confirm service provider capacity for project timeline
  - Engage with planning authority early to expedite approval
""")

    print("\n" + "="*80)
    print("This demonstrates the type of analysis the matcher produces.")
    print("To run with real PDFs, upload them to a public URL and update test_threeway_match.py")
    print("="*80)


async def main():
    """Main test function."""

    print("\n" + "="*80)
    print("THREE-WAY MATCHER TEST SUITE")
    print("="*80)

    # Test 1: Check database connectivity and fetch opportunity
    try:
        await test_threeway_match()
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")

    # Test 2: Show sample output
    await demonstrate_with_sample_analysis()

    print("\n" + "="*80)
    print("NEXT STEPS:")
    print("="*80)
    print("""
1. Upload PDFs to Public Location:
   - Upload files from Example_pdfs/ to AWS S3, GitHub raw, or similar
   - Ensure URLs are publicly accessible (no authentication required)

2. Update URLs:
   - Edit test_threeway_match.py
   - Replace placeholder URLs with your public URLs

3. Run Real Match:
   - python test_threeway_match.py
   - Agent will analyze actual PDF documents

4. Integrate with API:
   - Add endpoint to app/routes/matches.py
   - Allow users to trigger three-way matches via API
""")


if __name__ == "__main__":
    asyncio.run(main())
