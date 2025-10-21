# Service20 Alert System Documentation

## Overview

Service20 automatically creates alerts when research is completed. The system uses a **dual-alert approach**, creating alerts in both:

1. **PostgreSQL Database** - Direct database insertion for internal tracking
2. **CNZ API v2** - API-based alerts for integration with the main CNZ platform

## Alert Creation Flow

```
Service20 Research Completes
       ↓
SQS Results Queue receives completion message
       ↓
ResearchResultHandler.handle_research_complete() processes message
       ↓
┌──────────────────────────────────────────────────────┐
│  1. Save research to database                        │
│     → service20_investment_opportunities table       │
│                                                       │
│  2. Create Database Alert                            │
│     → alerts table (user_id: api-system-user)        │
│                                                       │
│  3. Create API Alert                                 │
│     → POST https://stage-cnz.icmserver007.com/api/v2/alerts │
│     → Headers: X-API-Key                             │
│     → Includes geonameId and cityCountryCode         │
└──────────────────────────────────────────────────────┘
```

## Database Alert Structure

### Table: `alerts`

```sql
CREATE TABLE alerts (
    id UUID PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    description TEXT,
    criteria JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    last_triggered TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    city_id UUID,
    geoname_id VARCHAR,
    city_country_code VARCHAR
);
```

### Service20 Alert Criteria Format

```json
{
  "type": "service20_research",
  "research_id": "research-001",
  "opportunity_type": "investment",
  "findings_count": 5,
  "report_length": 15000,
  "opportunity_data": {
    "title": "Bristol Green Energy Initiative",
    "location": "Bristol, UK",
    "investment_amount": 500000,
    "roi": 18.5
  }
}
```

## API Alert Structure

### Endpoint

```
POST https://stage-cnz.icmserver007.com/api/v2/alerts
```

### Headers

```http
Content-Type: application/json
X-API-Key: cnz_xEZR7v2ETYz2DnVzrmqDYXprpPKOrNDA97GaD3yjdfA
```

### Request Body

```json
{
  "name": "Service20 Research: Bristol Green Energy Initiative",
  "criteria": {
    "type": "service20_research",
    "conditions": {
      "research_id": "research-001",
      "opportunity_type": "investment",
      "location": "Bristol, UK",
      "findings_count": 5,
      "completed_at": "2025-10-20T13:45:00.000Z"
    }
  },
  "geonameId": "Q21693433",
  "cityCountryCode": "bristol-GB"
}
```

## Implementation Files

### Core Alert Creation

1. **database_storage.py** (`src/open_deep_research/database_storage.py`)
   - `create_service20_alert()` - Creates alerts in PostgreSQL database
   - Uses asyncpg for async database operations
   - Stores detailed research metadata in criteria JSON

2. **create_alert_api.py** (root directory)
   - `create_service20_research_alert()` - Creates alerts via CNZ API
   - Uses requests library for HTTP POST
   - Includes geoname and city-country code support

3. **message_handlers.py** (`src/open_deep_research/message_handlers.py`)
   - `ResearchResultHandler.handle_research_complete()` - Orchestrates both alert methods
   - Called when SQS Results Queue receives completion message
   - Handles errors gracefully for both alert types

### Utility Scripts

1. **view_alerts.py** - View and manage database alerts
   - View all alerts
   - View Service20 alerts only
   - Alert statistics
   - Delete/toggle alert status

2. **query_results.py** - Query research results and SQS queues
   - View research results from database
   - Monitor SQS queue status
   - Search by keyword

## Environment Variables

Required in `.env` file:

```bash
# Database connection
DATABASE_URL=postgresql://user:password@host:5432/database?sslmode=require

# CNZ API (optional - has defaults)
CNZ_API_URL=https://stage-cnz.icmserver007.com/api/v2/alerts
CNZ_API_KEY=cnz_xEZR7v2ETYz2DnVzrmqDYXprpPKOrNDA97GaD3yjdfA
```

## Usage Examples

### Automatic Alert Creation

Alerts are created automatically when:
1. Service20 research completes
2. Results are sent to SQS Results Queue
3. Message handler processes the completion message

### Manual Alert Creation (Testing)

#### Database Alert

```python
import asyncio
from open_deep_research.database_storage import create_service20_alert

research_results = {
    "research_id": "test-001",
    "opportunity_type": "investment",
    "research_brief": "Research brief text...",
    "final_report": "Full report text...",
    "findings": ["Finding 1", "Finding 2"]
}

opportunity_data = {
    "title": "Bristol Green Energy",
    "location": "Bristol, UK",
    "investment_amount": 500000,
    "roi": 18.5
}

alert_id = await create_service20_alert(research_results, opportunity_data)
print(f"Created alert: {alert_id}")
```

#### API Alert

```python
from create_alert_api import create_service20_research_alert

result = create_service20_research_alert(
    research_id="test-001",
    opportunity_type="investment",
    title="Bristol Green Energy",
    location="Bristol, UK",
    findings_count=5,
    geoname_id="Q21693433",
    city_country_code="bristol-GB"
)
```

#### Using curl

```bash
curl -X POST https://stage-cnz.icmserver007.com/api/v2/alerts \
  -H "Content-Type: application/json" \
  -H "X-API-Key: cnz_xEZR7v2ETYz2DnVzrmqDYXprpPKOrNDA97GaD3yjdfA" \
  -d '{
    "name": "Service20 Research: Bristol Project",
    "criteria": {
      "type": "service20_research",
      "conditions": {
        "research_id": "test-001",
        "opportunity_type": "investment"
      }
    },
    "geonameId": "Q21693433",
    "cityCountryCode": "bristol-GB"
  }'
```

### View Alerts

#### Command-line Script

```bash
# Interactive menu
python view_alerts.py

# View stats directly
python -c "import asyncio; from view_alerts import get_alert_stats; asyncio.run(get_alert_stats())"

# View Service20 alerts only
python -c "import asyncio; from view_alerts import view_service20_alerts; asyncio.run(view_service20_alerts())"
```

#### Via MindsDB (SSH Tunnel Required)

```bash
# First, set up SSH tunnel
cd ../service21
powershell -ExecutionPolicy Bypass -File setup_tunnel.ps1

# Query alerts
curl -X POST http://localhost:47334/api/sql/query \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT * FROM urbanzero_postgres.alerts WHERE criteria->>\"type\" = \"service20_research\";"}'
```

## Where Alerts Appear

### 1. PostgreSQL Database
- **Table**: `alerts`
- **Access**:
  - Direct SQL queries
  - MindsDB at http://localhost:47334 (via SSH tunnel)
  - `view_alerts.py` script
- **User**: `api-system-user` (system-generated alerts)

### 2. CNZ API v2 Platform
- **Endpoint**: https://stage-cnz.icmserver007.com/api/v2/alerts
- **Access**: Via API key authentication
- **Integration**: Connected to main CNZ platform
- **Visibility**: Available to CNZ platform users

### 3. UrbanZero Web Application (Potential)
- **URL**: `/alerts` page
- **Note**: Database alerts could appear here if user is `api-system-user`
- **Integration**: Uses same `alerts` table via backend API

## Alert Statistics

Current alert counts (example):

```
Total Alerts: 44
Active Alerts: 43
Service20 Alerts: 0 (will increase as research completes)
Triggered Alerts: 1
```

## Troubleshooting

### Database Alerts Not Created

1. Check DATABASE_URL is set in `.env`
2. Verify database connection:
   ```bash
   python -c "import os, asyncpg, asyncio; asyncio.run(asyncpg.connect(os.getenv('DATABASE_URL')))"
   ```
3. Check message handler logs for errors

### API Alerts Not Created

1. Check CNZ_API_URL and CNZ_API_KEY in `.env`
2. Test API connectivity:
   ```bash
   python create_alert_api.py
   ```
3. Verify API endpoint is accessible
4. Check API key is valid

### Alerts Not Appearing in Web UI

1. Verify user_id matches logged-in user
2. Check alerts table for records
3. Ensure backend API is running
4. Check browser console for errors

## Future Enhancements

Potential improvements:

1. **User-specific Alerts** - Allow users to subscribe to research topics
2. **Email Notifications** - Send emails when alerts are triggered
3. **Webhook Integration** - POST to external services on alert creation
4. **Alert Filtering** - Advanced filtering by opportunity type, location, ROI, etc.
5. **Alert Aggregation** - Batch multiple alerts into digests
6. **Custom Alert Rules** - User-defined criteria for alert triggers

---

# Intelligent Matching System (NEW)

## Overview

The Service20 Intelligent Matching System automatically discovers synergies between investment opportunities and funding sources. The system can **bundle multiple city projects** together to meet investor scale requirements.

### Key Capability: Project Bundling

**Example Scenario:**
- 🏙️ Bristol wants solar panels ($500k investment)
- 🏙️ Manchester wants solar panels ($300k investment)
- 🏙️ Edinburgh wants solar panels ($400k investment)
- 💰 Investor seeks solar projects but needs $1M minimum

**Solution:** Service20 automatically bundles all three cities into one $1.2M project, notifies all parties of the match opportunity.

## Matching Architecture

```
Daily Matching Job (runs at 2 AM UTC)
       ↓
┌──────────────────────────────────────────────────┐
│  1. Fetch Active Alerts (last 30 days)          │
│     → Opportunities & Funding sources            │
│                                                  │
│  2. Matching Engine                              │
│     → Group opportunities by sector              │
│     → Find simple matches (1:1)                  │
│     → Find bundled matches (1:many)              │
│     → Calculate compatibility scores             │
│                                                  │
│  3. Confidence Classification                    │
│     → High confidence (>80%): auto-notify        │
│     → Medium confidence (60-80%): queue approval │
│     → Low confidence (<60%): skip                │
│                                                  │
│  4. Create Match Alerts                          │
│     → Store match in opportunity_matches table   │
│     → Create alerts for all participants         │
│     → Send to database + CNZ API                 │
└──────────────────────────────────────────────────┘
```

## Enhanced Alert Metadata

All opportunity and funding alerts now include comprehensive metadata for intelligent matching:

### Sector Information
```json
"sector": {
  "primary": "solar_energy",
  "secondary": "commercial",
  "tags": ["rooftop", "municipal", "carbon_credits"]
}
```

### Financial Details
```json
"financial": {
  "amount": 500000,
  "minimum_required": 1000000,  // For funders
  "roi_expected": 18.5,
  "payback_years": 7,
  "currency": "USD",
  "carbon_reduction_tons_annually": 150
}
```

### Location Data
```json
"location": {
  "city": "Bristol",
  "country": "UK",
  "region": "Europe",
  "geoname_id": "Q21693433",
  "coordinates": [51.45, -2.58]
}
```

### Timeline
```json
"timeline": {
  "planning_start": "2025-Q2",
  "execution_start": "2025-Q4",
  "completion": "2026-Q4",
  "deadline": "2025-12-31",
  "urgency": "medium"
}
```

### Technical Specifications
```json
"technical": {
  "technology": "photovoltaic",
  "capacity_mw": 2.5,
  "maturity": "planning"  // planning | ready | in_progress
}
```

### Bundling Eligibility
```json
"bundling": {
  "eligible": true,
  "minimum_bundle_size": 1000000,
  "maximum_bundle_partners": 5,
  "compatibility_requirements": ["same_sector", "similar_timeline"]
}
```

## Compatibility Scoring

The matching engine calculates compatibility scores based on multiple dimensions:

| Dimension | Weight | Criteria |
|-----------|--------|----------|
| **Sector Alignment** | 30% | Primary sector match, technology compatibility |
| **Financial Fit** | 25% | Scale requirements met, within funding capacity |
| **Timeline Compatibility** | 20% | Execution timelines aligned (within 6 months) |
| **ROI Expectations** | 15% | Blended ROI meets or exceeds funder expectations |
| **Technical Compatibility** | 10% | Technology consistency, maturity level |

### Confidence Levels

- **High (>0.80)**: Auto-notify all parties immediately
- **Medium (0.60-0.80)**: Queue for human approval before notification
- **Low (<0.60)**: Log only, no alerts created

## Match Alert Types

### Service20 Match Alert for Opportunities (Cities)

```json
{
  "type": "service20_match",
  "match_id": "match-bundled-20251020-001",
  "match_type": "bundled",
  "role": "opportunity_provider",

  "your_project": {
    "city": "Bristol",
    "sector": "solar_energy",
    "investment_amount": 500000,
    "roi": 18.5,
    "carbon_reduction": 150
  },

  "match_details": {
    "compatibility_score": 0.87,
    "confidence": "high",
    "partner_cities": ["Manchester", "Edinburgh"],
    "funder": "green-investment-fund-2025",
    "criteria_met": [
      "sector_perfect_match",
      "minimum_scale_met",
      "timeline_aligned",
      "roi_acceptable"
    ]
  },

  "bundle_metrics": {
    "total_investment": 1200000,
    "blended_roi": 17.8,
    "total_carbon_reduction": 450,
    "project_count": 3
  },

  "next_steps": [
    "Review the match details and compatibility score",
    "Contact partner cities if bundled",
    "Prepare project documentation and financial projections",
    "Schedule introduction call with funder"
  ]
}
```

### Service20 Match Alert for Funders (Investors)

```json
{
  "type": "service20_match",
  "match_id": "match-bundled-20251020-001",
  "match_type": "bundled",
  "role": "funder",

  "matched_opportunities": [
    {
      "city": "Bristol",
      "country": "UK",
      "sector": "solar_energy",
      "investment_amount": 500000,
      "roi": 18.5,
      "carbon_reduction": 150
    },
    // ... more opportunities
  ],

  "match_details": {
    "compatibility_score": 0.87,
    "confidence": "high",
    "criteria_met": ["sector_alignment", "scale_achieved", "roi_acceptable"],
    "warnings": []
  },

  "bundle_metrics": {
    "total_investment": 1200000,
    "blended_roi": 17.8,
    "total_carbon_reduction": 450,
    "geographic_spread": 1,
    "countries": ["UK"],
    "cities": ["Bristol", "Manchester", "Edinburgh"]
  },

  "next_steps": [
    "Review project details and financial projections",
    "Assess combined risk profile",
    "Contact project lead(s) for more information",
    "Schedule due diligence review"
  ]
}
```

## Database Schema for Matches

### Table: `opportunity_matches`

```sql
CREATE TABLE opportunity_matches (
    id UUID PRIMARY KEY,
    match_id VARCHAR UNIQUE NOT NULL,
    match_type VARCHAR NOT NULL,  -- 'simple', 'bundled', 'syndicated'

    -- Participants (JSON arrays)
    opportunity_alert_ids JSONB NOT NULL,
    funder_alert_ids JSONB NOT NULL,
    opportunities_data JSONB NOT NULL,
    funders_data JSONB NOT NULL,

    -- Match quality
    compatibility_score DECIMAL(5,2) NOT NULL,
    confidence_level VARCHAR NOT NULL,  -- 'high', 'medium', 'low'

    -- Bundle calculations
    bundle_metrics JSONB,

    -- Matching criteria
    criteria_met TEXT[],
    criteria_warnings TEXT[],

    -- Workflow
    requires_approval BOOLEAN DEFAULT FALSE,
    approved_by VARCHAR,
    approved_at TIMESTAMP,

    notifications_sent BOOLEAN DEFAULT FALSE,
    notified_at TIMESTAMP,

    status VARCHAR DEFAULT 'proposed',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## Running the Matching System

### Daily Scheduled Job

**Setup cron job (Linux):**
```bash
# Run daily at 2 AM UTC
0 2 * * * cd /path/to/service20 && python src/open_deep_research/scheduled_jobs.py matching 30
```

**Setup AWS EventBridge:**
```json
{
  "rule": "Service20-Daily-Matching",
  "schedule": "cron(0 2 * * ? *)",
  "target": "Lambda function or ECS task",
  "input": {
    "job": "matching",
    "lookback_days": 30
  }
}
```

### Manual Execution (Testing)

```bash
# Run matching job
python src/open_deep_research/scheduled_jobs.py matching 30

# Run cleanup job
python src/open_deep_research/scheduled_jobs.py cleanup 90
```

## Viewing Match Proposals

### Via Python Script

```python
import asyncio
from open_deep_research.database_storage import get_match_proposals

async def view_matches():
    # Get all high-confidence matches
    matches = await get_match_proposals(min_confidence='high', limit=20)

    for match in matches:
        print(f"Match ID: {match['match_id']}")
        print(f"Type: {match['match_type']}")
        print(f"Score: {match['compatibility_score']}")
        print(f"Opportunities: {len(match['opportunities_data'])}")
        print(f"Total Investment: ${match['bundle_metrics']['total_investment']:,.0f}")
        print("---")

asyncio.run(view_matches())
```

### Via SQL Query

```sql
-- View recent high-confidence matches
SELECT
    match_id,
    match_type,
    compatibility_score,
    jsonb_array_length(opportunity_alert_ids) as opportunity_count,
    bundle_metrics->>'total_investment' as total_investment,
    bundle_metrics->>'blended_roi' as blended_roi,
    created_at
FROM opportunity_matches
WHERE confidence_level = 'high'
ORDER BY created_at DESC
LIMIT 10;
```

## Alert Notifications

### Who Gets Notified?

**For a bundled match with 3 cities + 1 funder:**
- ✅ Bristol receives alert: "Your project can be bundled with Manchester & Edinburgh"
- ✅ Manchester receives alert: "Your project can be bundled with Bristol & Edinburgh"
- ✅ Edinburgh receives alert: "Your project can be bundled with Bristol & Manchester"
- ✅ Funder receives alert: "Found bundled opportunity: 3 solar projects totaling $1.2M"

### Notification Channels

1. **Database Alerts**: Stored in `alerts` table
2. **CNZ API Alerts**: Posted to `/api/v2/alerts`
3. **SQS Messages**: Match details sent to match_results_queue

## Match Proposal Workflow

```
1. Service20 finds match
2. Calculates compatibility score
3. If score > 0.80 (high confidence):
   → Auto-create alerts for all parties
   → Send to database + API immediately
   → Cities/funders coordinate directly

4. If score 0.60-0.80 (medium confidence):
   → Store match in database
   → Create alerts (not sent yet)
   → Queue for human approval
   → If approved: send notifications

5. Service20 role ends:
   → Match proposals delivered
   → Parties coordinate independently
   → No tracking of acceptance/rejection
```

## Key Features

✅ **Intelligent Bundling**: Automatically combines small projects to meet large investor requirements

✅ **Global Reach**: No geographic constraints - can bundle cities worldwide

✅ **Confidence-Based Automation**: High-quality matches auto-notify, others get human review

✅ **Rich Metadata**: Comprehensive data enables sophisticated matching

✅ **Daily Batch Processing**: Efficient resource usage with scheduled job

✅ **Proposal Service**: Service20 just proposes matches, parties coordinate directly

## Success Metrics

Track matching effectiveness:
- Number of matches proposed per week
- Average compatibility score
- Percentage of high-confidence matches
- Average bundle size (number of cities)
- Match acceptance rate (if tracking externally)

## Related Documentation

- [Service20 Main README](README.md)
- [SQS Integration](docs/sqs-integration.md)
- [Database Schema](docs/database-schema.md)
- [Matching Engine Code](src/open_deep_research/matching_engine.py)
- [Scheduled Jobs](src/open_deep_research/scheduled_jobs.py)
- [MindsDB Setup](../service21/MINDSDB_SETUP.md)
