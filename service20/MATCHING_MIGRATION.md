# Matching System Migration

## Overview

The matching system has been migrated from a direct Python class-based system to a Service20-compliant dual-agent SQS architecture.

## What Changed

### Old System (`src/open_deep_research/matching_engine.py`)
- Direct function calls to matching engine
- Stored results in `opportunity_matches` table
- Synchronous processing
- No event-driven architecture

### New System (`matching_agent.py`)
- **SQS-based messaging** - Matches triggered via SQS match_request messages
- **service20_bundles table** - All results stored in comprehensive bundles table
- **Asynchronous agent** - Runs as background service listening for messages
- **Event-driven** - Integrates with Service20's dual-agent architecture
- **Notifications** - High-confidence matches trigger automatic SQS notifications

## Architecture Changes

### Old Flow
```
User → matching_engine.py → Database (opportunity_matches)
```

### New Flow
```
User → trigger_matching.py → SQS (match_request) → matching_agent.py → Database (service20_bundles) → SQS (match_results)
```

## Database Changes

### Removed Table
- `opportunity_matches` - No longer used

### Active Table
- `service20_bundles` - Stores all bundled and simple matches
  - 38 columns with comprehensive metrics
  - Supports simple (1:1) and bundled (N:1) matches
  - JSONB fields for flexible criteria storage
  - Geographic distribution tracking
  - Financial and carbon impact metrics

## Migration Steps

### 1. Drop Old Table (Optional)
```sql
-- Only if you're certain all old data is migrated or no longer needed
DROP TABLE IF EXISTS opportunity_matches;
```

### 2. Remove Old Matching Engine
```bash
# Archived for reference
mv src/open_deep_research/matching_engine.py src/open_deep_research/matching_engine.py.old
```

### 3. Start New Matching Agent
```bash
# Terminal 1: Start the matching agent
python matching_agent.py

# Terminal 2: Trigger a match job
python trigger_matching.py --lookback 30
```

## Usage Examples

### Trigger Matching Job
```bash
# Match last 30 days of alerts
python trigger_matching.py

# Match last 7 days
python trigger_matching.py --lookback 7

# Match last 60 days
python trigger_matching.py --lookback 60
```

### Run Matching Agent as Service
```bash
# Using screen (Linux)
screen -S matching-agent python matching_agent.py

# Using nohup
nohup python matching_agent.py > matching_agent.log 2>&1 &

# Using PM2 (Node.js process manager)
pm2 start matching_agent.py --name "service20-matching" --interpreter python
```

### Query Results
```sql
-- View all bundles
SELECT
    bundle_id, bundle_name, opportunity_count,
    cities, countries, total_investment,
    blended_roi, compatibility_score, confidence_level,
    status, created_at
FROM service20_bundles
ORDER BY created_at DESC;

-- View high-confidence bundles
SELECT
    bundle_id, bundle_name, opportunity_count,
    total_investment, blended_roi, compatibility_score
FROM service20_bundles
WHERE confidence_level = 'high'
AND status = 'proposed'
ORDER BY compatibility_score DESC;

-- View bundles by sector
SELECT
    primary_sector, COUNT(*) as bundle_count,
    SUM(total_investment) as total_funding_needed,
    AVG(compatibility_score) as avg_score
FROM service20_bundles
GROUP BY primary_sector
ORDER BY bundle_count DESC;
```

## Key Differences in Behavior

### Scoring Algorithm
- **Same weights**: Sector (30%), Financial (25%), Timeline (20%), ROI (15%), Technical (10%)
- **Enhanced sector matching**: Now supports related sectors (e.g., solar_energy matches renewable_energy)
- **Geographic regions**: Automatically calculates regions from countries

### Bundle Creation
- **Simple matches** (score >= 0.60): Creates single-opportunity bundles
- **Bundled matches** (2-5 opportunities): Tries combinations to meet funder minimums
- **Deduplication**: Keeps only best-scoring bundle for each combination

### Confidence Levels
- **High (>= 0.80)**: Auto-notify both parties via SQS
- **Medium (0.60-0.80)**: Store in database, no auto-notification
- **Low (< 0.60)**: Rejected, not stored

### Notifications
- **Old system**: No automatic notifications
- **New system**: High-confidence matches automatically sent to `service20-match-results` SQS queue

## SQS Queues Used

### Input Queue
- **service20-match-requests** - Receives match_request messages to trigger matching jobs

### Output Queues
- **service20-match-results** - High-confidence matches sent here for notification
- **service20-research-results** - Match job completion stats

## Compatibility

### What Works the Same
- Scoring algorithm (same weights and logic)
- Compatibility thresholds (>= 0.60 for matches)
- Bundle size limits (2-5 opportunities)

### What's Different
- Trigger mechanism (SQS instead of direct call)
- Storage location (service20_bundles instead of opportunity_matches)
- Notification system (SQS-based)

## Troubleshooting

### Matching Agent Not Processing Messages
1. Check SQS queue configuration:
   ```bash
   echo $SQS_MATCH_REQUESTS_QUEUE_URL
   ```

2. Verify AWS credentials:
   ```bash
   echo $AWS_ACCESS_KEY_ID
   echo $AWS_SECRET_ACCESS_KEY
   ```

3. Check agent logs for errors

### No Matches Created
1. Verify alerts exist:
   ```sql
   SELECT COUNT(*), alert_type FROM service20_alerts
   WHERE status = 'active'
   GROUP BY alert_type;
   ```

2. Check lookback period (try increasing `--lookback` days)

3. Review scoring thresholds in CompatibilityScorer

### Database Connection Errors
1. Verify DATABASE_URL is set:
   ```bash
   echo $DATABASE_URL
   ```

2. Test connection:
   ```bash
   python -c "import asyncpg; import asyncio; import os; asyncio.run(asyncpg.connect(os.getenv('DATABASE_URL')))"
   ```

## Rollback Plan

If you need to temporarily revert to the old system:

1. Restore old matching_engine.py:
   ```bash
   mv src/open_deep_research/matching_engine.py.old src/open_deep_research/matching_engine.py
   ```

2. Recreate opportunity_matches table:
   ```bash
   python setup_database.py  # If you have the old schema
   ```

3. Update code to use old matching engine instead of SQS triggers

## Future Enhancements

- **Syndicated matching** (1 large opportunity : N funders) - Schema supports it, agent needs implementation
- **Machine learning scoring** - Replace weighted scoring with ML model
- **Real-time matching** - Process each alert immediately instead of batch jobs
- **Auto-approval** - Very high confidence (>= 0.95) matches auto-approved

## Questions?

- Check SQS queue status: `aws sqs get-queue-attributes --queue-url <URL> --attribute-names All`
- Monitor agent: `tail -f matching_agent.log`
- Query bundles: See SQL examples above
