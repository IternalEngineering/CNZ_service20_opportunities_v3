"""
Opportunity-Term Matcher

Extracts deal terms from PDFs and matches them against natural language
investment opportunity descriptions to find location and match reasoning.
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from terms.CNZ_service76_google_url_context.google_url_context import URLContextClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PDFDocument:
    """Represents a PDF document to analyze."""
    name: str
    url: str
    type: str  # 'council', 'investor', 'provider'
    description: str


@dataclass
class OpportunityMatch:
    """Result of matching an opportunity against PDF terms."""
    opportunity_id: int
    location: str
    location_granularity: str  # 'city', 'area', 'building', 'region'
    match_reasoning: str
    council_terms: Dict[str, Any]
    investor_terms: Dict[str, Any]
    provider_terms: Dict[str, Any]
    overall_confidence: float
    extracted_details: Dict[str, Any]


class OpportunityTermMatcher:
    """Matches investment opportunities against deal terms from PDFs."""

    def __init__(self):
        """Initialize the matcher with Google URL Context client."""
        self.url_client = URLContextClient()
        logger.info("OpportunityTermMatcher initialized")

    def extract_council_terms(self, council_doc: PDFDocument) -> Dict[str, Any]:
        """Extract key deal terms from council/municipality PDF."""

        query = f"""
        Analyze this council/municipality document and extract ONLY the key terms
        necessary for reaching a deal:

        Extract:
        1. **Procurement Requirements**: Contract type, procurement process, eligibility criteria
        2. **Project Specifications**: Technical requirements, scale, timeline
        3. **Financial Terms**: Budget range, payment structure, funding model
        4. **Location Requirements**: Geographic scope, specific areas, site requirements
        5. **Compliance & Standards**: Regulations, certifications, standards required
        6. **Key Deadlines**: Submission dates, project milestones

        Return ONLY concrete deal terms that would need to be met. Skip generic statements.
        Format as a structured list of actionable requirements.
        """

        try:
            response = self.url_client.query_url_context(query, [council_doc.url])

            return {
                'raw_terms': response,
                'document_name': council_doc.name,
                'document_url': council_doc.url
            }
        except Exception as e:
            logger.error(f"Error extracting council terms: {str(e)}")
            return {'error': str(e)}

    def extract_investor_terms(self, investor_doc: PDFDocument) -> Dict[str, Any]:
        """Extract key deal terms from investor/funder PDF."""

        query = f"""
        Analyze this investor/funder document and extract ONLY the key terms
        necessary for reaching a deal:

        Extract:
        1. **Investment Criteria**: Minimum/maximum investment size, sectors, geographies
        2. **Financial Terms**: Expected returns, equity/debt structure, term length
        3. **Due Diligence Requirements**: What evidence/documentation is needed
        4. **Risk Tolerance**: Acceptable risk levels, security requirements
        5. **Deal Structure**: Preferred investment vehicles, governance rights
        6. **Exit Requirements**: Exit timeline, exit mechanisms

        Return ONLY concrete deal terms that would need to be met. Skip generic statements.
        Format as a structured list of actionable requirements.
        """

        try:
            response = self.url_client.query_url_context(query, [investor_doc.url])

            return {
                'raw_terms': response,
                'document_name': investor_doc.name,
                'document_url': investor_doc.url
            }
        except Exception as e:
            logger.error(f"Error extracting investor terms: {str(e)}")
            return {'error': str(e)}

    def extract_provider_terms(self, provider_doc: PDFDocument) -> Dict[str, Any]:
        """Extract key capabilities from service provider PDF."""

        query = f"""
        Analyze this service provider document and extract ONLY the key capabilities
        and terms for delivering services:

        Extract:
        1. **Service Offerings**: Specific services, technical capabilities
        2. **Track Record**: Project types delivered, scale of projects
        3. **Geographic Coverage**: Regions/cities served, expansion capability
        4. **Delivery Model**: How services are structured and delivered
        5. **Pricing Structure**: Cost models, pricing approaches
        6. **Partnership Terms**: How they work with clients/partners

        Return ONLY concrete capabilities and terms. Skip marketing language.
        Format as a structured list of what they can deliver.
        """

        try:
            response = self.url_client.query_url_context(query, [provider_doc.url])

            return {
                'raw_terms': response,
                'document_name': provider_doc.name,
                'document_url': provider_doc.url
            }
        except Exception as e:
            logger.error(f"Error extracting provider terms: {str(e)}")
            return {'error': str(e)}

    def match_opportunity(
        self,
        opportunity_id: int,
        opportunity_description: str,
        council_doc: PDFDocument,
        investor_doc: PDFDocument,
        provider_doc: PDFDocument
    ) -> OpportunityMatch:
        """
        Match an opportunity description against extracted PDF terms.

        Returns location and match reasoning.
        """

        logger.info(f"Matching opportunity {opportunity_id}")

        # Extract terms from all PDFs
        logger.info("Extracting council terms...")
        council_terms = self.extract_council_terms(council_doc)

        logger.info("Extracting investor terms...")
        investor_terms = self.extract_investor_terms(investor_doc)

        logger.info("Extracting provider terms...")
        provider_terms = self.extract_provider_terms(provider_doc)

        # Now match the opportunity against all terms
        logger.info("Analyzing opportunity match...")
        match_query = f"""
        You have an investment opportunity description and deal terms from three documents:

        INVESTMENT OPPORTUNITY:
        {opportunity_description[:5000]}  # Truncate if too long

        COUNCIL/MUNICIPALITY TERMS:
        {council_terms.get('raw_terms', 'Not available')}

        INVESTOR/FUNDER TERMS:
        {investor_terms.get('raw_terms', 'Not available')}

        SERVICE PROVIDER CAPABILITIES:
        {provider_terms.get('raw_terms', 'Not available')}

        Analyze this opportunity and provide:

        1. **LOCATION** - Extract the most granular location where this opportunity will take place:
           - For city-wide projects: City name
           - For transport/infrastructure: Specific routes, stations, or corridors
           - For buildings/solar: Specific buildings, addresses, or facilities
           - For area developments: Neighborhood or district names

        2. **MATCH REASONING** - Explain WHY this opportunity matches (or doesn't match) the deal terms:
           - How it meets council/municipality requirements
           - How it aligns with investor criteria
           - How the provider's capabilities fit the need
           - What specific terms from the PDFs are satisfied
           - What gaps or mismatches exist

        3. **EXTRACTED DETAILS** - Pull out key opportunity details:
           - Investment size/scale
           - Timeline
           - Project type
           - Target returns (if mentioned)
           - Key stakeholders

        4. **CONFIDENCE SCORE** (0-100) - How confident are you in this match?

        Format your response as:

        LOCATION: [specific location]
        GRANULARITY: [city|area|building|region|corridor]

        MATCH REASONING:
        [Detailed reasoning with specific references to PDF terms]

        EXTRACTED DETAILS:
        [Key opportunity details as bullet points]

        CONFIDENCE: [0-100]
        """

        # Query using the URL context (we'll just use one doc URL as context)
        try:
            response = self.url_client.query_url_context(
                match_query,
                [council_doc.url]  # Use council doc as context
            )

            # Parse the response
            location, granularity, reasoning, details, confidence = self._parse_match_response(response)

            return OpportunityMatch(
                opportunity_id=opportunity_id,
                location=location,
                location_granularity=granularity,
                match_reasoning=reasoning,
                council_terms=council_terms,
                investor_terms=investor_terms,
                provider_terms=provider_terms,
                overall_confidence=confidence,
                extracted_details=details
            )

        except Exception as e:
            logger.error(f"Error matching opportunity: {str(e)}")
            return OpportunityMatch(
                opportunity_id=opportunity_id,
                location="Unknown - Error occurred",
                location_granularity="unknown",
                match_reasoning=f"Error during matching: {str(e)}",
                council_terms=council_terms,
                investor_terms=investor_terms,
                provider_terms=provider_terms,
                overall_confidence=0.0,
                extracted_details={'error': str(e)}
            )

    def _parse_match_response(self, response: str) -> tuple:
        """Parse the AI response into structured components."""

        try:
            # Extract location
            location = "Unknown"
            if "LOCATION:" in response:
                location = response.split("LOCATION:")[1].split("\n")[0].strip()

            # Extract granularity
            granularity = "city"  # default
            if "GRANULARITY:" in response:
                gran_text = response.split("GRANULARITY:")[1].split("\n")[0].strip().lower()
                if gran_text in ['city', 'area', 'building', 'region', 'corridor']:
                    granularity = gran_text

            # Extract reasoning
            reasoning = "No reasoning provided"
            if "MATCH REASONING:" in response:
                reasoning_section = response.split("MATCH REASONING:")[1]
                if "EXTRACTED DETAILS:" in reasoning_section:
                    reasoning = reasoning_section.split("EXTRACTED DETAILS:")[0].strip()
                elif "CONFIDENCE:" in reasoning_section:
                    reasoning = reasoning_section.split("CONFIDENCE:")[0].strip()
                else:
                    reasoning = reasoning_section.strip()

            # Extract details
            details = {}
            if "EXTRACTED DETAILS:" in response:
                details_section = response.split("EXTRACTED DETAILS:")[1]
                if "CONFIDENCE:" in details_section:
                    details_text = details_section.split("CONFIDENCE:")[0].strip()
                else:
                    details_text = details_section.strip()
                details = {'text': details_text}

            # Extract confidence
            confidence = 50.0  # default
            if "CONFIDENCE:" in response:
                try:
                    conf_text = response.split("CONFIDENCE:")[1].split("\n")[0].strip()
                    # Extract just the number
                    import re
                    conf_match = re.search(r'(\d+(?:\.\d+)?)', conf_text)
                    if conf_match:
                        confidence = float(conf_match.group(1))
                except:
                    confidence = 50.0

            return location, granularity, reasoning, details, confidence

        except Exception as e:
            logger.error(f"Error parsing response: {str(e)}")
            return "Unknown", "city", response, {}, 50.0


if __name__ == "__main__":
    # Test with a sample
    matcher = OpportunityTermMatcher()

    # Example documents
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

    # Sample opportunity
    opportunity = """
    Research net zero investment opportunities in Bristol, focusing on renewable energy,
    carbon reduction initiatives, sustainable transport, and green building projects.
    """

    result = matcher.match_opportunity(
        opportunity_id=1,
        opportunity_description=opportunity,
        council_doc=council_doc,
        investor_doc=investor_doc,
        provider_doc=provider_doc
    )

    print("\n" + "="*80)
    print("OPPORTUNITY MATCH RESULT")
    print("="*80)
    print(f"\nLocation: {result.location}")
    print(f"Granularity: {result.location_granularity}")
    print(f"\nMatch Reasoning:\n{result.match_reasoning}")
    print(f"\nConfidence: {result.overall_confidence}%")
    print("="*80)
