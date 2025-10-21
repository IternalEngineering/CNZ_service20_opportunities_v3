# Service20 Matching System

## Overview

The Service20 Matching System intelligently discovers synergies between investment opportunities and funding opportunities, creating bundled portfolios that match funder scale requirements. The system follows Service20's dual-agent SQS architecture for event-driven, scalable matching.

## Architecture

### Components

1. **Matching Agent** (`matching_agent.py`) - Background service that:
   - Listens for match requests on SQS
   - Analyzes alerts from `service20_alerts` table
   - Creates bundles in `service20_bundles` table
   - Sends notifications for high-confidence matches

2. **Trigger Script** (`trigger_matching.py`) - Sends match requests to SQS

3. **Database Tables**:
   - **service20_alerts** - Input: Active investment and funding alerts
   - **service20_bundles** - Output: Match proposals and bundled opportunities

4. **SQS Queues**:
   - **service20-match-requests** - Input: Match job triggers
   - **service20-match-results** - Output: High-confidence match notifications
   - **service20-research-results** - Output: Job completion stats

## How It Works

### Matching Process

```mermaid
graph LR
    A[Trigger Matching] --> B[SQS: match_request]
    B --> C[Matching Agent]
    C --> D[Fetch Alerts]
    D --> E[service20_alerts]
    E --> F[Score Opportunities]
    F --> G[Create Bundles]
    G --> H[service20_bundles]
    H --> I{High Confidence?}
    I -->|Yes| J[SQS: match_found]
    I -->|No| K[Store Only]
```

### Scoring Algorithm

The CompatibilityScorer calculates match quality using 5 weighted factors:

1. **Sector Alignment (30% weight)**
   - Perfect match: Same sector (1.0)
   - Related match: Compatible sectors (0.7)
   - Partial match: Some overlap (0.6)
   - No match: Different sectors (0.2)

2. **Financial Fit (25% weight)**
   - Checks if total investment meets funder's minimum
   - Validates within funding capacity
   - Penalties for mismatches

3. **Timeline Compatibility (20% weight)**
   - Projects starting in same year: 1.0
   - Multi-year spread: 0.6
   - No timeline data: 0.7

4. **ROI Expectations (15% weight)**
   - Blended ROI >= Funder minimum: 0.9-1.0
   - Nearly acceptable (>= 80%): 0.6
   - Below expectations: 0.3

5. **Technical Compatibility (10% weight)**
   - Same technology across projects: 1.0
   - Mixed technologies: 0.7

**Total Score** = Weighted average of all 5 factors (0.00 to 1.00)

### Bundling Strategy

When a single opportunity is too small for a funder's minimum investment requirement, the system creates bundles:

1. **Group by Sector** - Opportunities are grouped by primary sector
2. **Try Combinations** - Tests 2-5 opportunity combinations
3. **Filter by Size** - Only bundles meeting >= 80% of minimum investment
4. **Score Each Bundle** - Calculates compatibility for each combination
5. **Keep Best Matches** - Stores top-scoring bundles per funder

**Example Bundle**:
- Paris solar ($2M) + Lyon wind ($3M) + Nice storage ($2M) = $7M bundle
- Matches funder looking for $5-10M renewable energy portfolio

### Confidence Levels

- **High (>= 0.80)**: Auto-notify both parties, appears in dashboard
- **Medium (0.60-0.80)**: Store in database, requires manual review
- **Low (< 0.60)**: Rejected, not created

## Usage

### Quick Start

```bash
# 1. Start the matching agent (background service)
python matching_agent.py

# 2. Trigger a matching job (separate terminal)
python trigger_matching.py
```

### Trigger Matching

```bash
# Match last 30 days (default)
python trigger_matching.py

# Match last 7 days only
python trigger_matching.py --lookback 7

# Match last 60 days
python trigger_matching.py --lookback 60
```

### Run as Background Service

#### Using PM2 (Recommended)
```bash
pm2 start matching_agent.py --name "service20-matching" --interpreter python
pm2 save
pm2 startup
```

#### Using Screen
```bash
screen -S matching-agent
python matching_agent.py
# Detach: Ctrl+A, D
# Reattach: screen -r matching-agent
```

#### Using Nohup
```bash
nohup python matching_agent.py > matching_agent.log 2>&1 &
```

### Query Results

#### View All Bundles

```sql
SELECT
    bundle_id,
    bundle_name,
    opportunity_count,
    cities,
    countries,
    total_investment,
    blended_roi,
    total_carbon_reduction,
    compatibility_score,
    confidence_level,
    status,
    created_at
FROM service20_bundles
ORDER BY created_at DESC
LIMIT 20;
```

#### View High-Confidence Bundles

```sql
SELECT
    bundle_id,
    bundle_name,
    opportunity_count,
    total_investment,
    blended_roi,
    compatibility_score,
    bundling_rationale
FROM service20_bundles
WHERE confidence_level = 'high'
AND status = 'proposed'
ORDER BY compatibility_score DESC;
```

#### View Bundles by Sector

```sql
SELECT
    primary_sector,
    COUNT(*) as bundle_count,
    SUM(total_investment) as total_funding_needed,
    AVG(blended_roi) as avg_roi,
    AVG(compatibility_score) as avg_compatibility
FROM service20_bundles
GROUP BY primary_sector
ORDER BY bundle_count DESC;
```

#### View Bundle Details

```sql
SELECT
    bundle_id,
    bundle_name,
    opportunity_ids,
    cities,
    countries,
    regions,
    sectors,
    total_investment,
    blended_roi,
    total_carbon_reduction,
    bundle_metrics,
    criteria,
    bundling_rationale
FROM service20_bundles
WHERE bundle_id = 'bundle-20250121120000-3opp';
```

## Database Schema

### service20_bundles Table

Key columns (38 total):

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| bundle_id | VARCHAR(255) | Unique bundle identifier |
| bundle_name | VARCHAR(500) | Human-readable name |
| opportunity_ids | TEXT[] | Array of research IDs |
| opportunity_count | INTEGER | Number of opportunities |
| cities | TEXT[] | Array of city names |
| countries | TEXT[] | Array of country names |
| regions | TEXT[] | Array of regions |
| primary_sector | VARCHAR(100) | Main sector |
| sectors | TEXT[] | All sectors involved |
| total_investment | DECIMAL(20,2) | Total funding needed |
| blended_roi | DECIMAL(5,2) | Weighted average ROI |
| roi_range_min | DECIMAL(5,2) | Minimum ROI |
| roi_range_max | DECIMAL(5,2) | Maximum ROI |
| total_carbon_reduction | DECIMAL(15,2) | Total CO2 reduction (tons/year) |
| compatibility_score | DECIMAL(3,2) | Overall match score (0.00-1.00) |
| confidence_level | VARCHAR(20) | low / medium / high |
| bundling_rationale | TEXT | Why these projects bundle well |
| status | VARCHAR(50) | proposed / matched / approved / rejected |
| matched_funder_id | VARCHAR(255) | Funder research ID |
| bundle_metrics | JSONB | Detailed metrics |
| criteria | JSONB | Criteria met and warnings |

## Integration with Service20 Workflow

### Complete Flow

```
1. Research City Opportunities
   ↓ (research_city_opportunity.py)
2. Store in service20_investment_opportunities
   ↓
3. Create Alert in service20_alerts
   ↓
4. Trigger Matching (trigger_matching.py)
   ↓
5. Matching Agent Processes Alerts
   ↓
6. Create Bundles in service20_bundles
   ↓
7. High-Confidence Matches → SQS Notification
   ↓
8. Dashboard Shows Bundles
   ↓
9. Admin Reviews/Approves
   ↓
10. Notify Participants
```

### Event Flow

```
Research Complete Event
  ↓
Create Alert (service20_alerts)
  ↓
Trigger Match Request (manual or scheduled)
  ↓
Match Request → SQS (service20-match-requests)
  ↓
Matching Agent Receives Message
  ↓
Fetch Active Alerts (service20_alerts)
  ↓
Score & Bundle Opportunities
  ↓
Store Bundles (service20_bundles)
  ↓
High-Confidence Matches → SQS (service20-match-results)
  ↓
Job Complete → SQS (service20-research-results)
```

## Configuration

### Environment Variables

Required in `.env`:

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:port/db?sslmode=require

# AWS Credentials
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=eu-west-2

# SQS Queue URLs (created automatically if not provided)
SQS_MATCH_REQUESTS_QUEUE_URL=https://sqs.eu-west-2.amazonaws.com/.../service20-match-requests
SQS_MATCH_RESULTS_QUEUE_URL=https://sqs.eu-west-2.amazonaws.com/.../service20-match-results
SQS_RESULTS_QUEUE_URL=https://sqs.eu-west-2.amazonaws.com/.../service20-research-results
```

### Matching Agent Settings

Configurable in `matching_agent.py`:

- `max_bundle_size` - Maximum opportunities per bundle (default: 5)
- `lookback_days` - How far back to search for alerts (default: 30)
- `poll_interval` - SQS polling interval (default: 20 seconds for long polling)

## Monitoring

### Check Agent Status

```bash
# If using PM2
pm2 status service20-matching
pm2 logs service20-matching

# If using screen
screen -r matching-agent

# If using nohup
tail -f matching_agent.log
```

### Check SQS Queues

```bash
# Get queue attributes
aws sqs get-queue-attributes \
  --queue-url https://sqs.eu-west-2.amazonaws.com/.../service20-match-requests \
  --attribute-names All

# Check message count
aws sqs get-queue-attributes \
  --queue-url https://sqs.eu-west-2.amazonaws.com/.../service20-match-requests \
  --attribute-names ApproximateNumberOfMessages
```

### Database Monitoring

```sql
-- Bundle creation rate
SELECT
    DATE(created_at) as date,
    COUNT(*) as bundles_created,
    COUNT(*) FILTER (WHERE confidence_level = 'high') as high_confidence,
    AVG(compatibility_score) as avg_score
FROM service20_bundles
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Success rate by sector
SELECT
    primary_sector,
    COUNT(*) as total_bundles,
    COUNT(*) FILTER (WHERE confidence_level = 'high') as high_conf,
    ROUND(100.0 * COUNT(*) FILTER (WHERE confidence_level = 'high') / COUNT(*), 2) as success_rate
FROM service20_bundles
GROUP BY primary_sector
ORDER BY success_rate DESC;
```

## Troubleshooting

### No Messages Received

**Problem**: Matching agent running but not processing messages

**Solutions**:
1. Check SQS queue URL: `echo $SQS_MATCH_REQUESTS_QUEUE_URL`
2. Verify AWS credentials: `aws sts get-caller-identity`
3. Test trigger: `python trigger_matching.py`
4. Check agent logs for errors

### No Bundles Created

**Problem**: Agent processes messages but creates no bundles

**Solutions**:
1. Verify alerts exist:
   ```sql
   SELECT alert_type, status, COUNT(*)
   FROM service20_alerts
   GROUP BY alert_type, status;
   ```

2. Check if scores are too low (increase lookback period):
   ```bash
   python trigger_matching.py --lookback 60
   ```

3. Review scoring thresholds in `CompatibilityScorer`

### Database Connection Errors

**Problem**: `DATABASE_URL not set` or connection fails

**Solutions**:
1. Check `.env` file exists and contains `DATABASE_URL`
2. Test connection:
   ```bash
   python -c "import asyncpg; import asyncio; import os; asyncio.run(asyncpg.connect(os.getenv('DATABASE_URL')))"
   ```
3. Verify SSL mode: `?sslmode=require` in connection string

### Low Match Quality

**Problem**: Only low-confidence matches created

**Solutions**:
1. Review alert criteria - ensure complete and realistic
2. Check sector alignment - use related sectors
3. Verify financial data - ROI, investment amounts correct
4. Add more opportunities to increase bundling options

## Best Practices

### When to Trigger Matching

- **After Research Batch** - After creating multiple new research reports
- **Daily Schedule** - Run daily matching at off-peak hours
- **On Demand** - When admin creates new funding alert
- **Weekly Cleanup** - Process older alerts (60+ day lookback)

### Bundle Quality

- **Geographic Diversity** - Bundles across multiple cities are stronger
- **Sector Focus** - Same-sector bundles score higher
- **Timeline Alignment** - Projects starting within 6 months of each other
- **ROI Balance** - Mix of stable and high-return projects

### Alert Management

- **Keep Active** - Only keep alerts active while seeking matches
- **Update Criteria** - Refresh criteria as projects evolve
- **Archive Old Alerts** - Move inactive alerts to 'completed' or 'cancelled'

## Future Enhancements

### Planned Features

1. **Syndicated Matching** (1 large opportunity : N funders)
   - Schema supports it
   - Agent implementation pending

2. **Machine Learning Scoring**
   - Replace weighted scoring with ML model
   - Learn from approved/rejected matches

3. **Real-time Matching**
   - Process each alert immediately
   - No batch jobs needed

4. **Auto-Approval**
   - Very high confidence (>= 0.95) auto-approved
   - Instant notifications

5. **Dashboard Integration**
   - View bundles in runs_dashboard.html
   - Approve/reject from UI
   - Track notification status

## Support

For issues or questions:

1. Check this README
2. Review MATCHING_MIGRATION.md for migration details
3. Inspect agent logs
4. Query service20_bundles table for results
5. Check SQS queue status

## Related Files

- `matching_agent.py` - Main matching agent
- `trigger_matching.py` - Trigger matching jobs
- `database_schema_bundles.sql` - Bundle table schema
- `MATCHING_MIGRATION.md` - Migration guide from old system
- `drop_old_matches_table.py` - Remove old opportunity_matches table
