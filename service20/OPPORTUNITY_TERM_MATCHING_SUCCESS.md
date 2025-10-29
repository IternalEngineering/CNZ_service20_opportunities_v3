# Opportunity Term Matching - Implementation Success

## Overview

Successfully implemented a new opportunity-term matcher that extracts deal terms from local PDFs and matches them against natural language investment opportunity descriptions.

**Date**: October 29, 2025
**Status**: ✅ Working Successfully

## Problem Statement

The original three-way matcher (`threeway_matcher.py`) was designed for structured investment opportunities (city, sector, amount, ROI fields), but the `service20_investment_opportunities` table actually contains **unstructured AI research reports** (text queries and generated reports).

### User Requirements (from final pivot)

> "the matching agent should extract only the terms necessary for reaching a deal from the pdfs then look at the natural languge description of an investment opportunity from service20_investment_opportunities and return two outputs:
> 1) the location the opportunity will take place as granular as possible e.g., city for a transport opportunity but area within city or specific buildings for something like solar panel installations and
> 2) reasoning why the opportunity matches the terms from pdfs"

## Solution: opportunity_term_matcher_local.py

### Technical Approach

**Why Local Approach**:
- Google URL Context API cannot access `localhost` URLs
- Solution: Read PDFs locally using PyPDF2 and send content directly to OpenAI GPT-4o

### Architecture

```python
class OpportunityTermMatcher:
    def __init__(self):
        self.client = OpenAI()  # Uses GPT-4o

    # 1. Extract PDF text locally
    def extract_pdf_text(pdf_path) -> str

    # 2. Extract terms using AI
    def extract_council_terms(pdf) -> Dict
    def extract_investor_terms(pdf) -> Dict
    def extract_provider_terms(pdf) -> Dict

    # 3. Match opportunity against terms
    def match_opportunity(...) -> OpportunityMatch
```

### Key Features

1. **Local PDF Reading**: Uses PyPDF2 to extract text from PDFs (up to 50 pages)
2. **Smart Truncation**: Limits context to 50,000 chars (~15k tokens) to fit GPT-4o limits
3. **Structured Extraction**: Extracts only actionable deal terms, not marketing language
4. **Location Granularity**: Returns location with granularity level (city/area/building/region/corridor)
5. **Match Reasoning**: Explains how opportunity aligns with each PDF's terms
6. **Confidence Scoring**: 0-100 score based on match quality

### Extraction Queries

#### Council Terms
- Procurement Requirements (contract type, process, eligibility)
- Project Specifications (technical requirements, scale, timeline)
- Financial Terms (budget, payment structure, funding model)
- Location Requirements (geographic scope, specific areas)
- Compliance & Standards (regulations, certifications)
- Key Deadlines (submission dates, milestones)

#### Investor Terms
- Investment Criteria (size, sectors, geographies)
- Financial Terms (returns, equity/debt structure, term length)
- Due Diligence Requirements (documentation needed)
- Risk Tolerance (acceptable levels, security)
- Deal Structure (vehicles, governance rights)
- Exit Requirements (timeline, mechanisms)

#### Provider Terms
- Service Offerings (specific services, capabilities)
- Track Record (project types, scale delivered)
- Geographic Coverage (regions served, expansion)
- Delivery Model (how services are structured)
- Pricing Structure (cost models, pricing)
- Partnership Terms (client/partner relationships)

## Test Results

### Test Case: Bristol Net Zero Opportunity

**Input**:
```
Research net zero investment opportunities in Bristol, focusing on renewable energy,
carbon reduction initiatives, sustainable transport, and green building projects.
```

**PDFs Analyzed**:
- Manchester_PPA_Purchase.pdf (21,415 chars, 9 pages) - Council terms
- ILPA-Model-LPA-Term-Sheet-WOF-Version.pdf (37,010 chars, 15 pages) - Investor terms
- EnergyREV_Bunhill_Case_Study.pdf (5,891 chars, 3 pages) - Provider terms

### Results

**Location**: Bristol
**Granularity**: city
**Confidence**: 75%

**Match Reasoning**:

**Council/Municipality Requirements**:
- ✅ Aligns well with council's focus on renewable energy
- ✅ Involves large-scale renewable energy supply projects
- ✅ Can meet procurement requirements (PPA, PCR 2015 compliance)
- ✅ Geographic scope is UK-based (matches UK domiciled requirement)

**Investor Criteria**:
- ✅ Consistent with focus on long-term returns from diversified portfolios
- ✅ Renewable energy offers stable returns over time
- ✅ Term length (10 years + extensions) aligns with supply agreement (5-15 years)
- ⚠️ Gap: Specific financial terms (preferred return, currency) not mentioned

**Service Provider Capabilities**:
- ✅ Expertise in energy centers and heat distribution complements renewable energy
- ✅ Capabilities in renewable energy projects are relevant
- ⚠️ Geographic mismatch: Provider focused on London (Islington), not Bristol

**Extracted Details**:
- Investment size/scale: Large-scale renewable energy supply
- Timeline: Long-term supply agreement (5 to 15 years)
- Project type: Renewable energy, carbon reduction, sustainable transport, green building
- Target returns: Not explicitly mentioned
- Key stakeholders: Bristol City Council, potential investors, renewable energy service providers

## Files Created

1. **opportunity_term_matcher_local.py** (392 lines)
   - Main implementation using OpenAI GPT-4o
   - Reads PDFs locally with PyPDF2
   - Extracts terms and matches opportunities

2. **test_opportunity_term_matching.py** (135 lines)
   - Test script with HTTP server for public URLs (not needed for local version)
   - Connects to database to fetch real opportunity data

3. **opportunity_term_matcher.py** (370 lines)
   - Original Google URL Context implementation (requires public URLs)
   - Cannot access localhost URLs
   - Preserved for reference

## Comparison: Original vs New Approach

### Original Three-Way Matcher (threeway_matcher.py)
- ❌ Designed for structured opportunities (city, sector, amount fields)
- ❌ Got NULL/empty data from research reports
- ❌ Produced generic 50/50/50 scores with "Not specified" reasoning
- ❌ No location extraction capability

### New Opportunity-Term Matcher (opportunity_term_matcher_local.py)
- ✅ Designed for natural language research reports
- ✅ Extracts only actionable deal terms from PDFs
- ✅ Produces detailed, specific match reasoning with PDF references
- ✅ Extracts granular location information
- ✅ Identifies both matches AND gaps/mismatches
- ✅ Realistic confidence scoring (75% with identified gaps)

## Next Steps

### 1. Create Batch Processing Script
Create `run_opportunity_term_matching_batch.py` to process all 41 opportunities:
- Loop through all opportunities in database
- Use full research report (query + brief + final_report) as input
- Save results to database (may need new table or modify service20_matches schema)
- Add rate limiting for OpenAI API

### 2. Update Database Schema (Optional)
Current `service20_matches` table may need updates:
- Add `location_granularity` column (city/area/building/region/corridor)
- Ensure `match_reasoning` column can store detailed text
- Add `extracted_details` JSONB column

### 3. Production Deployment
- Add error handling for PDF reading failures
- Implement retry logic for OpenAI API calls
- Add logging and monitoring
- Consider caching extracted PDF terms (council/investor/provider PDFs don't change often)

## Dependencies

Required Python packages (already installed):
- `openai` - OpenAI Python SDK
- `PyPDF2==3.0.1` - PDF text extraction
- `python-dotenv` - Environment variable management
- `asyncpg` - PostgreSQL async driver (for batch processing)

## Performance Metrics

From test run:
- PDF extraction: ~1-2 seconds per PDF
- Term extraction: ~3-5 seconds per PDF (OpenAI API call)
- Final matching: ~5-7 seconds (OpenAI API call)
- **Total time per opportunity**: ~20-30 seconds
- **Estimated batch time (41 opportunities)**: 14-20 minutes

## Cost Estimate

Using GPT-4o pricing:
- Input: $2.50 per 1M tokens
- Output: $10.00 per 1M tokens

Per opportunity (estimated):
- PDF term extraction: 3 calls × ~12k tokens input + 500 tokens output = ~36k input + 1.5k output
- Final matching: 1 call × ~15k tokens input + 500 tokens output = ~15k input + 500 tokens output
- **Total per opportunity**: ~51k input tokens + 2k output tokens = ~$0.15

**Batch cost (41 opportunities)**: ~$6.15

## Conclusion

✅ **Successfully implemented** a new opportunity-term matcher that meets all user requirements:
1. ✅ Extracts only terms necessary for reaching a deal from PDFs
2. ✅ Analyzes natural language opportunity descriptions
3. ✅ Returns granular location information
4. ✅ Provides detailed reasoning why opportunity matches PDF terms
5. ✅ Identifies both strengths and gaps in matches
6. ✅ Realistic confidence scoring

The implementation is ready for batch processing of all 41 investment opportunities.

---

**Implementation Date**: October 29, 2025
**Status**: ✅ Complete and Tested
**Test Success**: Bristol renewable energy opportunity - 75% confidence match
