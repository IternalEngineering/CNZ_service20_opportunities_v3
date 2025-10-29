"""
Three-Way Matching Agent using Google URL Context API.

This agent analyzes investment opportunities against:
1. Council/Municipality requirements (from PDFs)
2. Investor/Funder criteria (from PDFs)
3. Service Provider capabilities (from PDFs)

Uses Google's URL Context Grounding to analyze PDF documents.
"""

import sys
import os
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json
from uuid import uuid4
from datetime import datetime

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parents[1] / "terms" / "CNZ_service76_google_url_context"))

from google_url_context import URLContextClient
import asyncpg
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()


@dataclass
class InvestmentOpportunity:
    """Investment opportunity data."""
    id: int
    city: str
    country: str
    country_code: str
    sector: str
    research_brief: str
    estimated_investment: Optional[float] = None
    carbon_reduction: Optional[float] = None
    project_type: Optional[str] = None


@dataclass
class PDFDocument:
    """PDF document metadata."""
    name: str
    url: str
    type: str  # 'council', 'investor', or 'provider'
    description: str


@dataclass
class ThreeWayMatch:
    """Result of three-way matching."""
    opportunity: InvestmentOpportunity
    council_match: Dict[str, Any]
    investor_match: Dict[str, Any]
    provider_match: Dict[str, Any]
    overall_score: float
    compatibility_analysis: str
    recommendations: List[str]


class ThreeWayMatcher:
    """
    Matches investment opportunities with councils, investors, and providers
    using Google URL Context API to analyze their requirement documents.
    """

    def __init__(self, google_api_key: Optional[str] = None, database_url: Optional[str] = None):
        """
        Initialize the three-way matcher.

        Args:
            google_api_key: Google API key for URL Context API
            database_url: PostgreSQL connection string
        """
        self.google_api_key = google_api_key or os.getenv('GOOGLE_API_KEY')
        self.database_url = database_url or os.getenv('DATABASE_URL')

        if not self.google_api_key:
            raise ValueError("GOOGLE_API_KEY not found")

        if not self.database_url:
            raise ValueError("DATABASE_URL not found")

        self.url_client = URLContextClient(api_key=self.google_api_key)
        logger.info("ThreeWayMatcher initialized")

    async def get_opportunity_from_db(self, opportunity_id: int) -> InvestmentOpportunity:
        """
        Retrieve investment opportunity from database.

        Args:
            opportunity_id: ID of the opportunity

        Returns:
            InvestmentOpportunity object
        """
        conn = await asyncpg.connect(self.database_url)
        try:
            row = await conn.fetchrow(
                """
                SELECT id, city, country, country_code, sector, research_brief
                FROM service20_investment_opportunities
                WHERE id = $1
                """,
                opportunity_id
            )

            if not row:
                raise ValueError(f"Opportunity {opportunity_id} not found")

            return InvestmentOpportunity(
                id=row['id'],
                city=row['city'],
                country=row['country'],
                country_code=row['country_code'],
                sector=row['sector'],
                research_brief=row['research_brief'] or ""
            )
        finally:
            await conn.close()

    def analyze_council_requirements(
        self,
        opportunity: InvestmentOpportunity,
        council_doc: PDFDocument
    ) -> Dict[str, Any]:
        """
        Analyze if opportunity meets council/municipality requirements.

        Args:
            opportunity: Investment opportunity
            council_doc: Council requirements PDF

        Returns:
            Dict with analysis results
        """
        query = f"""
        Analyze this council/municipality document for renewable energy project requirements.

        PROJECT CONTEXT:
        - City: {opportunity.city}
        - Country: {opportunity.country}
        - Sector: {opportunity.sector}
        - Brief: {opportunity.research_brief[:500]}

        ANALYSIS REQUIRED:
        1. Does this council have renewable energy/net-zero goals?
        2. What are their project requirements (size, type, timeline)?
        3. What procurement processes do they use (PPAs, tenders, etc.)?
        4. What are their budget constraints and funding sources?
        5. Do they have any specific technology preferences or restrictions?
        6. Match score (0-100): How well does this opportunity align with their needs?

        Provide a structured JSON response with:
        {{
            "has_renewable_goals": true/false,
            "project_requirements": "summary",
            "procurement_process": "description",
            "budget_range": "estimated range",
            "technology_preferences": ["list"],
            "match_score": 0-100,
            "key_alignment_factors": ["list"],
            "potential_barriers": ["list"]
        }}
        """

        logger.info(f"Analyzing council document: {council_doc.name}")
        response = self.url_client.query_url_context(query, [council_doc.url])

        try:
            # Try to parse as JSON
            return json.loads(response)
        except json.JSONDecodeError:
            # If not JSON, return raw text
            return {
                "raw_analysis": response,
                "match_score": 50  # Default neutral score
            }

    def analyze_investor_criteria(
        self,
        opportunity: InvestmentOpportunity,
        investor_doc: PDFDocument
    ) -> Dict[str, Any]:
        """
        Analyze if opportunity meets investor/funder criteria.

        Args:
            opportunity: Investment opportunity
            investor_doc: Investor criteria PDF

        Returns:
            Dict with analysis results
        """
        query = f"""
        Analyze this investor/funder term sheet or criteria document.

        PROJECT CONTEXT:
        - City: {opportunity.city}, {opportunity.country}
        - Sector: {opportunity.sector}
        - Brief: {opportunity.research_brief[:500]}

        ANALYSIS REQUIRED:
        1. What is the investment range (min/max ticket size)?
        2. What sectors or technologies do they fund?
        3. What geographic regions do they cover?
        4. What are their return expectations (ROI, IRR)?
        5. What project stages do they invest in (early, construction, operational)?
        6. What are their ESG or impact requirements?
        7. Match score (0-100): How well does this opportunity fit their criteria?

        Provide a structured JSON response with:
        {{
            "investment_range": {{"min": number, "max": number}},
            "sectors": ["list"],
            "geographic_coverage": ["list"],
            "return_expectations": "description",
            "project_stages": ["list"],
            "esg_requirements": "summary",
            "match_score": 0-100,
            "key_strengths": ["list"],
            "potential_concerns": ["list"]
        }}
        """

        logger.info(f"Analyzing investor document: {investor_doc.name}")
        response = self.url_client.query_url_context(query, [investor_doc.url])

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "raw_analysis": response,
                "match_score": 50
            }

    def analyze_provider_capabilities(
        self,
        opportunity: InvestmentOpportunity,
        provider_doc: PDFDocument
    ) -> Dict[str, Any]:
        """
        Analyze if service provider can deliver the project.

        Args:
            opportunity: Investment opportunity
            provider_doc: Service provider capabilities PDF

        Returns:
            Dict with analysis results
        """
        query = f"""
        Analyze this service provider's capabilities for renewable energy projects.

        PROJECT CONTEXT:
        - City: {opportunity.city}, {opportunity.country}
        - Sector: {opportunity.sector}
        - Brief: {opportunity.research_brief[:500]}

        ANALYSIS REQUIRED:
        1. What services does this provider offer (design, build, O&M)?
        2. What technologies or sectors do they specialize in?
        3. What is their geographic coverage?
        4. What is their project track record (size, complexity)?
        5. Do they have relevant certifications or accreditations?
        6. What is their typical project timeline?
        7. Match score (0-100): Can they deliver this project?

        Provide a structured JSON response with:
        {{
            "services_offered": ["list"],
            "technology_expertise": ["list"],
            "geographic_coverage": ["list"],
            "track_record": "summary",
            "certifications": ["list"],
            "typical_timeline": "duration",
            "match_score": 0-100,
            "key_capabilities": ["list"],
            "potential_limitations": ["list"]
        }}
        """

        logger.info(f"Analyzing provider document: {provider_doc.name}")
        response = self.url_client.query_url_context(query, [provider_doc.url])

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "raw_analysis": response,
                "match_score": 50
            }

    def calculate_overall_score(
        self,
        council_match: Dict[str, Any],
        investor_match: Dict[str, Any],
        provider_match: Dict[str, Any]
    ) -> float:
        """
        Calculate overall three-way match score.

        Args:
            council_match: Council analysis results
            investor_match: Investor analysis results
            provider_match: Provider analysis results

        Returns:
            Overall score (0-100)
        """
        council_score = council_match.get('match_score', 50)
        investor_score = investor_match.get('match_score', 50)
        provider_score = provider_match.get('match_score', 50)

        # Weighted average: all three parties are equally important
        overall = (council_score + investor_score + provider_score) / 3

        logger.info(f"Scores - Council: {council_score}, Investor: {investor_score}, Provider: {provider_score}, Overall: {overall:.1f}")

        return round(overall, 1)

    def generate_compatibility_analysis(
        self,
        opportunity: InvestmentOpportunity,
        council_match: Dict[str, Any],
        investor_match: Dict[str, Any],
        provider_match: Dict[str, Any]
    ) -> str:
        """
        Generate human-readable compatibility analysis.

        Args:
            opportunity: Investment opportunity
            council_match: Council analysis
            investor_match: Investor analysis
            provider_match: Provider analysis

        Returns:
            Compatibility analysis text
        """
        analysis = f"""
THREE-WAY MATCH ANALYSIS: {opportunity.city}, {opportunity.country} - {opportunity.sector}

COUNCIL/MUNICIPALITY ALIGNMENT:
Score: {council_match.get('match_score', 'N/A')}/100
- Requirements: {council_match.get('project_requirements', 'Not specified')}
- Procurement: {council_match.get('procurement_process', 'Not specified')}
- Key Factors: {', '.join(council_match.get('key_alignment_factors', ['Not specified']))}
- Barriers: {', '.join(council_match.get('potential_barriers', ['None identified']))}

INVESTOR/FUNDER ALIGNMENT:
Score: {investor_match.get('match_score', 'N/A')}/100
- Investment Range: {investor_match.get('investment_range', 'Not specified')}
- Sectors: {', '.join(investor_match.get('sectors', ['Not specified']))}
- Strengths: {', '.join(investor_match.get('key_strengths', ['Not specified']))}
- Concerns: {', '.join(investor_match.get('potential_concerns', ['None identified']))}

SERVICE PROVIDER ALIGNMENT:
Score: {provider_match.get('match_score', 'N/A')}/100
- Services: {', '.join(provider_match.get('services_offered', ['Not specified']))}
- Expertise: {', '.join(provider_match.get('technology_expertise', ['Not specified']))}
- Capabilities: {', '.join(provider_match.get('key_capabilities', ['Not specified']))}
- Limitations: {', '.join(provider_match.get('potential_limitations', ['None identified']))}
"""
        return analysis.strip()

    def generate_recommendations(
        self,
        overall_score: float,
        council_match: Dict[str, Any],
        investor_match: Dict[str, Any],
        provider_match: Dict[str, Any]
    ) -> List[str]:
        """
        Generate actionable recommendations.

        Args:
            overall_score: Overall match score
            council_match: Council analysis
            investor_match: Investor analysis
            provider_match: Provider analysis

        Returns:
            List of recommendations
        """
        recommendations = []

        if overall_score >= 75:
            recommendations.append("✅ STRONG MATCH: Proceed with detailed due diligence and proposal development")
        elif overall_score >= 60:
            recommendations.append("⚠️ MODERATE MATCH: Address identified gaps before proceeding")
        else:
            recommendations.append("❌ WEAK MATCH: Consider alternative partners or restructure opportunity")

        # Council-specific recommendations
        if council_match.get('match_score', 50) < 60:
            barriers = council_match.get('potential_barriers', [])
            if barriers:
                recommendations.append(f"Council: Address barriers - {', '.join(barriers[:2])}")

        # Investor-specific recommendations
        if investor_match.get('match_score', 50) < 60:
            concerns = investor_match.get('potential_concerns', [])
            if concerns:
                recommendations.append(f"Investor: Mitigate concerns - {', '.join(concerns[:2])}")

        # Provider-specific recommendations
        if provider_match.get('match_score', 50) < 60:
            limitations = provider_match.get('potential_limitations', [])
            if limitations:
                recommendations.append(f"Provider: Strengthen capabilities - {', '.join(limitations[:2])}")

        return recommendations

    async def save_match_result(
        self,
        match: ThreeWayMatch,
        council_doc: PDFDocument,
        investor_doc: PDFDocument,
        provider_doc: PDFDocument,
        failed: bool = False,
        failure_reason: Optional[str] = None
    ) -> str:
        """
        Save match result to service20_matches table.

        Args:
            match: ThreeWayMatch result object
            council_doc: Council requirements document
            investor_doc: Investor criteria document
            provider_doc: Service provider document
            failed: Whether the match failed
            failure_reason: Reason for failure if failed=True

        Returns:
            Match ID (UUID string)
        """
        conn = await asyncpg.connect(self.database_url)
        try:
            match_id = str(uuid4())

            # Extract scores
            council_score = match.council_match.get('match_score', 0) if match else 0
            investor_score = match.investor_match.get('match_score', 0) if match else 0
            provider_score = match.provider_match.get('match_score', 0) if match else 0
            overall_score = match.overall_score if match and not failed else 0

            # Prepare data
            opportunity = match.opportunity if match else None
            analysis = match.compatibility_analysis if match and not failed else failure_reason or "Match failed"
            recommendations = match.recommendations if match and not failed else []

            # Insert into database
            await conn.execute("""
                INSERT INTO service20_matches (
                    id, match_id, bundle_name, bundle_description,
                    opportunity_ids, opportunity_count,
                    cities, countries, regions,
                    primary_sector, sectors, subsectors,
                    total_investment, currency, match_metrics,
                    compatibility_score, confidence_level, criteria,
                    created_at, updated_at,
                    council_doc_url, investor_doc_url, provider_doc_url,
                    council_match_score, investor_match_score, provider_match_score,
                    overall_match_score, match_analysis, recommendations,
                    match_failed, failure_reason
                ) VALUES (
                    gen_random_uuid(), $1, $2, $3,
                    $4, $5,
                    $6, $7, $8,
                    $9, $10, $11,
                    $12, $13, $14,
                    $15, $16, $17,
                    $18, $19,
                    $20, $21, $22,
                    $23, $24, $25,
                    $26, $27, $28,
                    $29, $30
                )
            """,
                match_id,  # $1
                f"Three-Way Match: {opportunity.city if opportunity else 'Unknown'}, {opportunity.country if opportunity else 'Unknown'}",  # $2
                f"Council-Investor-Provider match for {opportunity.sector if opportunity and opportunity.sector else 'unknown'} opportunity",  # $3 - Handle NULL sector
                [str(opportunity.id)] if opportunity else [],  # $4 - Convert ID to string for array
                1 if opportunity else 0,  # $5
                [opportunity.city] if opportunity else [],  # $6
                [opportunity.country] if opportunity else [],  # $7
                [],  # regions - $8
                opportunity.sector if opportunity and opportunity.sector else "unknown",  # $9 - Handle NULL sector
                [opportunity.sector] if opportunity and opportunity.sector else ["unknown"],  # $10 - Handle NULL sector
                [],  # subsectors - $11
                0,  # total_investment - $12
                "USD",  # currency - $13
                json.dumps({
                    "council_analysis": match.council_match if match else {},
                    "investor_analysis": match.investor_match if match else {},
                    "provider_analysis": match.provider_match if match else {}
                }),  # match_metrics - $14
                overall_score,  # compatibility_score - $15
                "high" if overall_score >= 75 else ("medium" if overall_score >= 60 else "low"),  # confidence_level - $16
                json.dumps({
                    "council_doc": council_doc.name,
                    "investor_doc": investor_doc.name,
                    "provider_doc": provider_doc.name
                }),  # criteria - $17
                datetime.utcnow(),  # created_at - $18
                datetime.utcnow(),  # updated_at - $19
                council_doc.url,  # council_doc_url - $20
                investor_doc.url,  # investor_doc_url - $21
                provider_doc.url,  # provider_doc_url - $22
                council_score,  # council_match_score - $23
                investor_score,  # investor_match_score - $24
                provider_score,  # provider_match_score - $25
                overall_score,  # overall_match_score - $26
                analysis,  # match_analysis - $27
                recommendations,  # recommendations - $28
                failed,  # match_failed - $29
                failure_reason  # failure_reason - $30
            )

            logger.info(f"Saved match result to database: {match_id} (failed={failed})")
            return match_id

        except Exception as e:
            logger.error(f"Error saving match result: {str(e)}", exc_info=True)
            raise
        finally:
            await conn.close()

    async def match_opportunity(
        self,
        opportunity_id: int,
        council_doc: PDFDocument,
        investor_doc: PDFDocument,
        provider_doc: PDFDocument,
        save_to_db: bool = True
    ) -> ThreeWayMatch:
        """
        Perform three-way match analysis with error handling and database persistence.

        Args:
            opportunity_id: Database ID of opportunity
            council_doc: Council requirements document
            investor_doc: Investor criteria document
            provider_doc: Service provider document
            save_to_db: Whether to save result to database (default: True)

        Returns:
            ThreeWayMatch object with complete analysis

        Raises:
            ValueError: If opportunity not found or analysis fails
        """
        logger.info(f"Starting three-way match for opportunity {opportunity_id}")

        try:
            # Get opportunity from database
            opportunity = await self.get_opportunity_from_db(opportunity_id)
            logger.info(f"Analyzing: {opportunity.city}, {opportunity.country} - {opportunity.sector}")

            # Analyze each party's requirements/capabilities
            try:
                council_match = self.analyze_council_requirements(opportunity, council_doc)
                investor_match = self.analyze_investor_criteria(opportunity, investor_doc)
                provider_match = self.analyze_provider_capabilities(opportunity, provider_doc)
            except Exception as e:
                logger.error(f"Error during document analysis: {str(e)}")
                raise ValueError(f"Failed to analyze documents: {str(e)}")

            # Calculate overall score
            overall_score = self.calculate_overall_score(council_match, investor_match, provider_match)

            # Check if match is viable (threshold = 40)
            if overall_score < 40:
                failure_reason = f"Failed to find terms that fit. Overall match score ({overall_score:.1f}) below minimum threshold (40). "
                failure_reason += f"Council: {council_match.get('match_score', 0)}, "
                failure_reason += f"Investor: {investor_match.get('match_score', 0)}, "
                failure_reason += f"Provider: {provider_match.get('match_score', 0)}"

                logger.warning(f"Match failed for opportunity {opportunity_id}: {failure_reason}")

                # Create a minimal match object for failed match
                result = ThreeWayMatch(
                    opportunity=opportunity,
                    council_match=council_match,
                    investor_match=investor_match,
                    provider_match=provider_match,
                    overall_score=overall_score,
                    compatibility_analysis=failure_reason,
                    recommendations=["Match score too low - consider different partners or restructure opportunity"]
                )

                # Save failed match to database
                if save_to_db:
                    await self.save_match_result(
                        result, council_doc, investor_doc, provider_doc,
                        failed=True, failure_reason=failure_reason
                    )

                return result

            # Generate analysis and recommendations for successful match
            compatibility_analysis = self.generate_compatibility_analysis(
                opportunity, council_match, investor_match, provider_match
            )
            recommendations = self.generate_recommendations(
                overall_score, council_match, investor_match, provider_match
            )

            result = ThreeWayMatch(
                opportunity=opportunity,
                council_match=council_match,
                investor_match=investor_match,
                provider_match=provider_match,
                overall_score=overall_score,
                compatibility_analysis=compatibility_analysis,
                recommendations=recommendations
            )

            # Save successful match to database
            if save_to_db:
                await self.save_match_result(
                    result, council_doc, investor_doc, provider_doc,
                    failed=False
                )

            logger.info(f"Successfully completed match for opportunity {opportunity_id} with score {overall_score:.1f}")
            return result

        except Exception as e:
            logger.error(f"Error matching opportunity {opportunity_id}: {str(e)}", exc_info=True)

            # Try to save failed match if we have the opportunity
            try:
                if save_to_db and 'opportunity' in locals():
                    # Create minimal failed match
                    failed_match = ThreeWayMatch(
                        opportunity=opportunity,
                        council_match={},
                        investor_match={},
                        provider_match={},
                        overall_score=0,
                        compatibility_analysis=f"Match failed due to error: {str(e)}",
                        recommendations=["Technical error - retry with valid documents"]
                    )
                    await self.save_match_result(
                        failed_match, council_doc, investor_doc, provider_doc,
                        failed=True, failure_reason=f"Error during matching: {str(e)}"
                    )
            except Exception as save_error:
                logger.error(f"Could not save failed match: {str(save_error)}")

            raise


async def main():
    """Test the three-way matcher with example PDFs."""

    # Define example documents (using file:// URLs for local PDFs)
    terms_dir = Path(__file__).parents[1] / "terms" / "Example_pdfs"

    # Council documents
    council_docs = [
        PDFDocument(
            name="Manchester PPA Purchase",
            url=f"file://{terms_dir / 'Manchester_PPA_Purchase.pdf'}",
            type="council",
            description="Manchester council PPA procurement document"
        ),
        PDFDocument(
            name="Oldham Green New Deal",
            url=f"file://{terms_dir / 'Oldham_Green_New_Deal_Prospectus.pdf'}",
            type="council",
            description="Oldham Green New Deal investment prospectus"
        ),
    ]

    # Investor documents
    investor_docs = [
        PDFDocument(
            name="ILPA Model Term Sheet",
            url=f"file://{terms_dir / 'ILPA-Model-LPA-Term-Sheet-WOF-Version.pdf'}",
            type="investor",
            description="ILPA standard investment term sheet"
        ),
        PDFDocument(
            name="CEF RRF Term Sheet",
            url=f"file://{terms_dir / 'cef-rrf-termsheet.pdf'}",
            type="investor",
            description="Clean Energy Finance term sheet"
        ),
    ]

    # Provider documents
    provider_docs = [
        PDFDocument(
            name="EnergyREV Bunhill Case Study",
            url=f"file://{terms_dir / 'EnergyREV_Bunhill_Case_Study.pdf'}",
            type="provider",
            description="Energy provider case study"
        ),
        PDFDocument(
            name="Cornwall Insight Financing",
            url=f"file://{terms_dir / 'Cornwall_Insight_Financing_Options.pdf'}",
            type="provider",
            description="Financing options for renewable projects"
        ),
    ]

    # Initialize matcher
    matcher = ThreeWayMatcher()

    # Example: Match opportunity ID 1
    opportunity_id = 1

    try:
        result = await matcher.match_opportunity(
            opportunity_id=opportunity_id,
            council_doc=council_docs[0],  # Manchester PPA
            investor_doc=investor_docs[0],  # ILPA Term Sheet
            provider_doc=provider_docs[0]  # EnergyREV Case Study
        )

        print("\n" + "="*80)
        print("THREE-WAY MATCH RESULTS")
        print("="*80)
        print(f"\nOpportunity: {result.opportunity.city}, {result.opportunity.country}")
        print(f"Sector: {result.opportunity.sector}")
        print(f"\nOVERALL MATCH SCORE: {result.overall_score}/100")
        print("\n" + "-"*80)
        print(result.compatibility_analysis)
        print("\n" + "-"*80)
        print("\nRECOMMENDATIONS:")
        for rec in result.recommendations:
            print(f"  {rec}")
        print("="*80)

    except Exception as e:
        logger.error(f"Error during matching: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
