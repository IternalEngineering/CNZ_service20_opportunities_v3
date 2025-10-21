# Changelog - January 21, 2025

## Major Changes: Matching System Migration to SQS-Based Agent Architecture

### Summary

Replaced the old class-based matching system with a new **SQS-driven Matching Agent** that follows Service20's dual-agent architecture. The new system provides event-driven, scalable matching with comprehensive bundle tracking in the `service20_bundles` table.

---

## New Files Created

### Core Matching System

1. **matching_agent.py** (970 lines)
   - Main matching agent running as background service
   - Listens for `match_request` messages on SQS
   - Uses CompatibilityScorer with 5-factor weighted scoring
   - Creates bundles (2-5 opportunities) to meet funder scale requirements
   - Stores all results in `service20_bundles` table
   - Automatically sends SQS notifications for high-confidence matches (>= 0.80)

2. **trigger_matching.py** (102 lines)
   - Command-line tool to trigger matching jobs
   - Sends `match_request` message to SQS
   - Configurable lookback period (default: 30 days)
   - Usage: `python trigger_matching.py --lookback 30`

3. **drop_old_matches_table.py** (95 lines)
   - Safe cleanup script for old `opportunity_matches` table
   - Checks for existing data before deletion
   - Requires manual confirmation if data exists

### Documentation

4. **MATCHING_README.md** (650 lines)
   - Comprehensive guide to new matching system
   - Architecture diagrams and flow charts
   - Usage examples (trigger, run as service, query results)
   - SQL queries for viewing bundles
   - Monitoring and troubleshooting guide
   - Integration with Service20 workflow

5. **MATCHING_MIGRATION.md** (280 lines)
   - Migration guide from old to new system
   - Before/after architecture comparison
   - Database changes (opportunity_matches → service20_bundles)
   - SQS queue documentation
   - Rollback plan if needed

6. **CITY_RESEARCH_README.md** (285 lines)
   - Documentation for city-specific research feature
   - Usage examples with country codes
   - Database schema details
   - Integration with research workflow

7. **CHANGELOG_2025-01-21.md** (this file)
   - Summary of all changes made today

### City-Specific Research

8. **research_city_opportunity.py** (285 lines)
   - City-specific investment opportunity research script
   - Requires `--city` and `--country` (ISO 3166-1 alpha-3 codes)
   - Optional `--sector` and `--range` parameters
   - Validates country codes (30+ supported countries)
   - Stores results with city/country metadata
   - Usage: `python research_city_opportunity.py --city Paris --country FRA`

### Dashboard & Monitoring

9. **api_server.py** (created/enhanced)
   - REST API server for dashboard
   - New endpoints: `/api/history/investment`, `/api/history/funding`
   - Serves real data from database tables

10. **runs_dashboard.html** (enhanced)
    - Added "Research History" tab
    - Displays all historical research runs
    - Filterable table with statistics
    - Real-time data fetching from API

### Database Setup

11. **setup_database.py** (created)
    - Creates service20_alerts, service20_bundles tables
    - Runs SQL schema files automatically

12. **database_schema_bundles.sql** (created)
    - Comprehensive schema for service20_bundles table
    - 38 columns including opportunity_ids[], cities[], countries[]
    - Financial metrics, carbon impact, timeline tracking
    - 14 indexes for optimal query performance

13. **database_schema_alerts.sql** (created)
    - Schema for service20_alerts table
    - Stores active investment and funding alerts
    - JSONB criteria field for flexible matching

14. **database_schema_matches.sql** (reference only, deprecated)
    - Old opportunity_matches table schema
    - No longer used, replaced by service20_bundles

---

## Modified Files

### Database Storage

1. **src/open_deep_research/database_storage.py**
   - Added `store_investment_research()` function
   - Accepts city, country_code, country, sector parameters
   - Stores city-specific metadata with research results
   - Enhanced for service20_investment_opportunities table

### SQS Configuration

2. **src/open_deep_research/sqs_config.py**
   - Added 3 new message types:
     - `MATCH_FOUND` - Successful match proposals
     - `MATCH_APPROVAL_NEEDED` - Low/medium confidence matches
     - `MATCH_STATUS_CHANGE` - Match status updates
   - Added 3 new SQS queues:
     - `match_requests_queue_url` - Trigger matching jobs
     - `match_results_queue_url` - Match notifications
     - `match_approvals_queue_url` - Matches needing approval
   - Added convenience methods for match-related messages

### Documentation

3. **ALERTS_DOCUMENTATION.md**
   - Updated with matching system integration
   - Added match request workflow examples

---

## Archived Files

1. **src/open_deep_research/matching_engine.py** → **matching_engine.py.old**
   - Old class-based matching system
   - Archived for reference
   - Use new `matching_agent.py` instead

---

## Database Schema Changes

### New Table: service20_bundles (38 columns)

Created comprehensive table for storing bundled opportunities:

- **Bundle identification**: bundle_id, bundle_name, bundle_description
- **Composition**: opportunity_ids[], opportunity_count
- **Geography**: cities[], countries[], regions[]
- **Sectors**: primary_sector, sectors[], subsectors[]
- **Financial**: total_investment, blended_roi, roi_range_min/max
- **Carbon impact**: total_carbon_reduction, average_carbon_per_project
- **Timeline**: earliest_start_date, latest_completion_date, timeline_alignment_score
- **Technical**: technologies[], total_capacity_mw
- **Scoring**: compatibility_score, confidence_level, bundling_rationale
- **Matching**: status, matched_funder_id, match_date
- **Metadata**: bundle_metrics (JSONB), criteria (JSONB)

### Updated Table: service20_investment_opportunities

Added 4 new columns for city-specific research:

- `city` (VARCHAR 255) - City name
- `country_code` (VARCHAR 3) - ISO 3166-1 alpha-3 code
- `country` (VARCHAR 255) - Full country name
- `sector` (VARCHAR 100) - Primary sector

Created indexes on city, country_code, and sector for optimal query performance.

### Deprecated Table: opportunity_matches

No longer used. Can be dropped with `python drop_old_matches_table.py`.

---

## Architecture Changes

### Old System
```
User → matching_engine.py → opportunity_matches table
```

### New System
```
User → trigger_matching.py
  ↓
SQS (match_request)
  ↓
matching_agent.py (background service)
  ↓
service20_bundles table
  ↓
SQS (match_results) for high-confidence matches
```

---

## Key Features

### Matching Agent

1. **5-Factor Scoring Algorithm**
   - Sector Alignment: 30% weight
   - Financial Fit: 25% weight
   - Timeline Compatibility: 20% weight
   - ROI Expectations: 15% weight
   - Technical Compatibility: 10% weight

2. **Intelligent Bundling**
   - Combines 2-5 opportunities to meet funder minimums
   - Groups by sector and region
   - Calculates blended ROI, total carbon reduction
   - Geographic diversification tracking

3. **Confidence Levels**
   - High (>= 0.80): Auto-notify both parties
   - Medium (0.60-0.80): Store, requires manual review
   - Low (< 0.60): Rejected, not stored

4. **Event-Driven Architecture**
   - SQS-based triggering
   - Background service (runs continuously)
   - Scalable and fault-tolerant
   - Follows Service20 dual-agent pattern

### City-Specific Research

1. **Country Code Validation**
   - 30+ supported countries (ISO 3166-1 alpha-3)
   - Helpful error messages with full country list
   - Automatic country name resolution

2. **Flexible Parameters**
   - Required: `--city` and `--country`
   - Optional: `--sector` (8 options) and `--range` (investment amount)
   - Defaults: renewable_energy, $500K-$5M

3. **Enhanced Storage**
   - City and country metadata stored with every research
   - Enables location-based matching and filtering
   - Supports geographic bundling strategies

---

## Usage Examples

### Trigger Matching Job

```bash
# Match last 30 days (default)
python trigger_matching.py

# Match last 7 days only
python trigger_matching.py --lookback 7
```

### Run Matching Agent

```bash
# Direct execution (foreground)
python matching_agent.py

# Using PM2 (recommended for production)
pm2 start matching_agent.py --name "service20-matching" --interpreter python
pm2 save
pm2 startup
```

### City-Specific Research

```bash
# Research Paris renewable energy
python research_city_opportunity.py --city Paris --country FRA

# Research New York solar with custom range
python research_city_opportunity.py --city "New York" --country USA --sector solar_energy --range 1000000-10000000
```

### Query Bundles

```sql
-- View all bundles
SELECT bundle_id, bundle_name, opportunity_count,
       total_investment, blended_roi, compatibility_score, confidence_level
FROM service20_bundles
ORDER BY created_at DESC;

-- High-confidence bundles only
SELECT * FROM service20_bundles
WHERE confidence_level = 'high' AND status = 'proposed'
ORDER BY compatibility_score DESC;

-- Bundles by sector
SELECT primary_sector, COUNT(*) as bundle_count,
       SUM(total_investment) as total_funding,
       AVG(compatibility_score) as avg_score
FROM service20_bundles
GROUP BY primary_sector;
```

---

## SQS Queues

### New Queues Created

1. **service20-match-requests** - Input queue for match job triggers
2. **service20-match-results** - Output queue for high-confidence matches
3. **service20-match-approvals** - Queue for matches needing admin approval

### Existing Queues Used

- **service20-investment-opportunities** - Investment opportunity alerts
- **service20-funding-opportunities** - Funding opportunity alerts
- **service20-research-results** - Research completion notifications

---

## Integration with Service20 Workflow

### Complete Flow

1. **City Research**: `research_city_opportunity.py` generates investment research
2. **Store Results**: Data saved to `service20_investment_opportunities` table
3. **Create Alert**: Admin creates alert in `service20_alerts` table
4. **Trigger Matching**: `trigger_matching.py` sends SQS match_request
5. **Agent Processes**: Matching agent receives message and processes alerts
6. **Create Bundles**: Results stored in `service20_bundles` table
7. **Notify High-Confidence**: Automatic SQS notifications for score >= 0.80
8. **Dashboard Display**: Bundles appear in `runs_dashboard.html`
9. **Admin Review**: Approve or reject proposals
10. **Execute & Track**: Update status, notify participants

---

## Breaking Changes

### For Users of Old Matching System

- **matching_engine.py** is now archived (`.old`)
- **opportunity_matches** table deprecated, use `service20_bundles` instead
- Direct function calls replaced with SQS messaging
- Different storage structure and schema

### Migration Path

1. Read `MATCHING_MIGRATION.md` for complete migration guide
2. Optionally run `drop_old_matches_table.py` to remove old table
3. Start using `trigger_matching.py` instead of direct engine calls
4. Update any custom code to query `service20_bundles` table

---

## Testing Status

- ✅ Database schema created successfully
- ✅ City-specific research script tested
- ✅ SQS configuration validated
- ⏳ Matching agent needs live testing with real alert data
- ⏳ End-to-end workflow testing pending

---

## Next Steps

1. **Test matching agent** with actual alert data
2. **Set up cron jobs** for daily matching triggers
3. **Integrate with dashboard** to display bundles visually
4. **Implement notification handlers** for match_results SQS messages
5. **Add bundling to dashboard** for admin approval workflow

---

## Files Summary

**Created:** 14 new files (1,970 lines of Python, 1,215 lines of documentation, 112 lines of SQL)

**Modified:** 3 files (database_storage.py, sqs_config.py, ALERTS_DOCUMENTATION.md)

**Archived:** 1 file (matching_engine.py → .old)

**Repository:** https://github.com/IternalEngineering/CNZ_service20_opportunities_v3.git

**Branch:** main

**Commit Date:** January 21, 2025
