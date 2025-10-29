# Three-Way Matching Agent with Google URL Context

## Overview

The Three-Way Matcher analyzes investment opportunities against three parties:
1. **Councils/Municipalities** - Requirements and procurement processes
2. **Investors/Funders** - Investment criteria and term sheets
3. **Service Providers** - Capabilities and track record

Uses **Google's URL Context Grounding API** (Gemini 2.5-pro) to analyze PDF documents without traditional RAG processing.

## Files Created

- `threeway_matcher.py` - Main matching agent with URL Context integration
- `test_threeway_match.py` - Test script and demonstration

## How It Works

### Input
- **Investment Opportunity** (from database) - City, country, sector, investment needs
- **Council PDF** - Requirements, procurement processes, renewable energy goals
- **Investor PDF** - Term sheets, investment criteria, return expectations
- **Provider PDF** - Capabilities, track record, service offerings

### Process

```
┌─────────────────────────────────────────────────────────────────┐
│                    INVESTMENT OPPORTUNITY                        │
│          (e.g., Manchester 10MW Solar PV Project)               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────────┐
        │      Google URL Context API Analysis         │
        │         (Gemini 2.5-pro Model)               │
        └─────────────────────────────────────────────┘
                 │                │                │
                 ▼                ▼                ▼
        ┌────────────┐   ┌────────────┐   ┌────────────┐
        │  Council   │   │  Investor  │   │  Provider  │
        │   Match    │   │   Match    │   │   Match    │
        │  Score:85  │   │  Score:78  │   │  Score:82  │
        └────────────┘   └────────────┘   └────────────┘
                 │                │                │
                 └────────────────┴────────────────┘
                              ▼
                    ┌──────────────────────┐
                    │  Overall Score: 81.7  │
                    │  + Recommendations    │
                    └──────────────────────┘
```

### Output

**ThreeWayMatch** object containing:
- Individual match scores (0-100) for each party
- Overall compatibility score (0-100)
- Detailed analysis of requirements alignment
- Key strengths, concerns, and barriers
- Actionable recommendations

## Key Features

### 1. Database Integration
- Fetches opportunities from `service20_investment_opportunities` table
- Retrieves city, country, sector, and research brief

### 2. URL Context Analysis
- Uses Google's Gemini API to read and understand PDF documents
- Analyzes council requirements, investor criteria, and provider capabilities
- No need for traditional RAG pipeline (embedding, chunking, vector store)

### 3. Structured Matching Logic

**Council Analysis:**
- Renewable energy goals
- Project requirements (size, type, timeline)
- Procurement processes
- Budget constraints
- Technology preferences

**Investor Analysis:**
- Investment range (min/max ticket size)
- Sector and geographic coverage
- Return expectations (ROI, IRR)
- Project stages (early/construction/operational)
- ESG requirements

**Provider Analysis:**
- Services offered (design, build, O&M)
- Technology expertise
- Geographic coverage
- Track record and certifications
- Typical project timelines

### 4. Scoring System
- Individual scores (0-100) for each party
- Weighted average for overall score:
  - Council: 33%
  - Investor: 33%
  - Provider: 33%
- **75-100**: Strong match - proceed
- **60-74**: Moderate match - address gaps
- **0-59**: Weak match - reconsider

### 5. Recommendations
- Automated recommendations based on scores
- Identifies specific barriers and concerns
- Suggests mitigation strategies

## Example Usage

### Basic Test

```python
from threeway_matcher import ThreeWayMatcher, PDFDocument
import asyncio

# Initialize matcher
matcher = ThreeWayMatcher()

# Define documents (must be publicly accessible URLs)
council_doc = PDFDocument(
    name="Manchester PPA Purchase",
    url="https://example.com/manchester_ppa.pdf",
    type="council",
    description="Manchester PPA procurement"
)

investor_doc = PDFDocument(
    name="Clean Energy Fund Terms",
    url="https://example.com/cef_terms.pdf",
    type="investor",
    description="Investment fund term sheet"
)

provider_doc = PDFDocument(
    name="EnergyREV Capabilities",
    url="https://example.com/energyrev.pdf",
    type="provider",
    description="Service provider capabilities"
)

# Run match
async def run_match():
    result = await matcher.match_opportunity(
        opportunity_id=1,
        council_doc=council_doc,
        investor_doc=investor_doc,
        provider_doc=provider_doc
    )

    print(f"Overall Score: {result.overall_score}/100")
    print(result.compatibility_analysis)
    print("\nRecommendations:")
    for rec in result.recommendations:
        print(f"  - {rec}")

asyncio.run(run_match())
```

## Example PDF Categories

### Council Documents (in Example_pdfs/)
- `Manchester_PPA_Purchase.pdf` - PPA procurement framework
- `Oldham_Green_New_Deal_Prospectus.pdf` - Green investment prospectus
- `Islington_Bunhill_OM_Strategy.pdf` - District heating strategy
- `TfGM_PPA_Tender.pdf` - Transport authority PPA tender

### Investor Documents
- `ILPA-Model-LPA-Term-Sheet-WOF-Version.pdf` - Standard term sheet
- `cef-rrf-termsheet.pdf` - Clean Energy Finance terms
- `Pro-Forma-Investment-Term-Sheet.pdf` - Investment template
- `Simpact_TEMPLATE_TS-1.pdf` - Impact investment template

### Provider Documents
- `EnergyREV_Bunhill_Case_Study.pdf` - Project case study
- `Cornwall_Insight_Financing_Options.pdf` - Financing options guide

## Requirements

### Python Packages
```bash
pip install google-genai asyncpg python-dotenv
```

### Environment Variables
```bash
GOOGLE_API_KEY=your_google_api_key
DATABASE_URL=postgresql://user:password@host:port/database
```

### Important Limitations

**Google URL Context API requires:**
1. **Publicly accessible URLs** - Cannot use `file://` or `localhost`
2. **Max 20 URLs** per request
3. **Max 34MB** per URL
4. **Supported formats**: PDF, HTML, JSON, XML, CSV, images
5. **Not supported**: Paywalled content, YouTube, Google Workspace files, video/audio

## Next Steps

### To Use with Example PDFs:

1. **Upload PDFs to Public Location**
   ```bash
   # Option 1: AWS S3
   aws s3 cp Example_pdfs/ s3://your-bucket/pdfs/ --recursive --acl public-read

   # Option 2: GitHub (create public repo)
   # Upload to GitHub and use raw URLs

   # Option 3: Any web server
   # Upload and ensure public access
   ```

2. **Update URLs in test_threeway_match.py**
   ```python
   council_doc = PDFDocument(
       name="Manchester PPA",
       url="https://your-bucket.s3.amazonaws.com/Manchester_PPA_Purchase.pdf",
       type="council",
       description="Manchester PPA procurement"
   )
   ```

3. **Run Test**
   ```bash
   python test_threeway_match.py
   ```

### To Integrate with Service20 API:

Add to `app/routes/matches.py`:

```python
@router.post("/three-way-match", response_model=ThreeWayMatchResponse)
async def create_three_way_match(request: ThreeWayMatchRequest):
    """
    Perform three-way match analysis using URL Context API.

    Requires:
    - opportunity_id: Database ID
    - council_url: Public URL to council requirements PDF
    - investor_url: Public URL to investor term sheet PDF
    - provider_url: Public URL to provider capabilities PDF
    """
    matcher = ThreeWayMatcher()

    result = await matcher.match_opportunity(
        opportunity_id=request.opportunity_id,
        council_doc=PDFDocument(name="Council", url=request.council_url, type="council"),
        investor_doc=PDFDocument(name="Investor", url=request.investor_url, type="investor"),
        provider_doc=PDFDocument(name="Provider", url=request.provider_url, type="provider")
    )

    return ThreeWayMatchResponse(
        success=True,
        overall_score=result.overall_score,
        compatibility_analysis=result.compatibility_analysis,
        recommendations=result.recommendations
    )
```

## Benefits

1. **No RAG Infrastructure Needed** - Google handles document access directly
2. **Fresh Data** - Always reads latest version of documents
3. **Structured Analysis** - Consistent JSON output format
4. **Automated Recommendations** - Actionable next steps
5. **Database Integration** - Works seamlessly with Service20 data
6. **Scalable** - Can analyze up to 20 documents simultaneously

## Comparison: URL Context vs Traditional RAG

| Feature | URL Context | Traditional RAG |
|---------|------------|-----------------|
| **Setup** | API call | Embedding pipeline, vector store |
| **Updates** | Always current | Requires re-embedding |
| **Infrastructure** | None | Vector DB, embedding model |
| **Cost** | Per-API-call | Storage + compute |
| **Latency** | ~5-10 sec | ~1-2 sec (after indexing) |
| **Best for** | Fresh docs, one-time analysis | Frequent queries, large corpus |

## Example Output

```
THREE-WAY MATCH ANALYSIS: Manchester, United Kingdom - renewable_energy

COUNCIL/MUNICIPALITY ALIGNMENT:
Score: 85/100
- Requirements: 10-50MW renewable energy projects, focus on PPAs
- Procurement: Power Purchase Agreement framework, competitive tender
- Key Factors: Alignment with net-zero goals, local job creation
- Barriers: Planning permission timeline, grid connection capacity

INVESTOR/FUNDER ALIGNMENT:
Score: 78/100
- Investment Range: £2M - £15M per project
- Sectors: Solar, Wind, Energy Storage
- Strengths: Strong ESG focus, proven UK track record
- Concerns: ROI expectations vs. PPA rates

SERVICE PROVIDER ALIGNMENT:
Score: 82/100
- Services: Design, Build, Commission, O&M
- Expertise: Solar PV, Battery Storage, Grid Integration
- Capabilities: 50+ UK projects, ISO certifications
- Limitations: Limited wind expertise

OVERALL MATCH SCORE: 81.7/100

RECOMMENDATIONS:
  - STRONG MATCH: Proceed with detailed due diligence
  - Conduct site visit to assess grid connection feasibility
  - Negotiate PPA terms that meet investor ROI requirements
  - Engage with planning authority early to expedite approval
```

## Future Enhancements

1. **Batch Processing** - Analyze multiple opportunities simultaneously
2. **Document Library** - Store URLs to common council/investor/provider docs
3. **Score Weighting** - Allow custom importance weights for each party
4. **Historical Tracking** - Track match scores over time
5. **API Integration** - Full REST API endpoints for web access
6. **Notification System** - Alert when strong matches are found

---

**Created**: 2025-10-28
**Service**: Service20 Investment Opportunities
**Technology**: Google Gemini 2.5-pro with URL Context Grounding
