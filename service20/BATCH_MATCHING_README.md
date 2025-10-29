# Batch Three-Way Matching System

## Overview

The batch matching system processes all investment opportunities through the three-way matcher, analyzing each against council requirements, investor criteria, and service provider capabilities. Results are automatically saved to the `service20_matches` table.

## Recent Changes

### Database Migration

The `service20_bundles` table has been renamed to `service20_matches` with the following enhancements:

- **Table Rename**: `service20_bundles` → `service20_matches`
- **Column Rename**: `bundle_id` → `match_id`, `bundle_metrics` → `match_metrics`
- **New Columns Added**:
  - `council_doc_url`, `investor_doc_url`, `provider_doc_url` - URLs to analyzed documents
  - `council_match_score`, `investor_match_score`, `provider_match_score` - Individual scores (0-100)
  - `overall_match_score` - Weighted average of the three scores
  - `match_analysis` - Detailed compatibility analysis text
  - `recommendations` - Array of actionable recommendations
  - `match_failed` - Boolean flag for failed matches
  - `failure_reason` - Text explanation when match_failed=TRUE

### Three-Way Matcher Enhancements

The `threeway_matcher.py` has been updated with:

1. **Database Persistence**: `save_match_result()` method saves all match results to `service20_matches`
2. **Failure Handling**:
   - Matches with overall score < 40 are marked as failed
   - Error handling saves failed matches with error details
   - Failure reasons are stored in the database
3. **Automatic Saving**: `match_opportunity()` now saves results to database by default

### Batch Processing Script

The `batch_match_opportunities.py` script provides:

- **Batch Processing**: Processes all opportunities in `service20_investment_opportunities`
- **Progress Tracking**: Real-time progress display with success/failure counts
- **Error Handling**: Continues processing even if individual matches fail
- **Summary Report**: Complete statistics at the end of the run

## Files

### Core Files

- **threeway_matcher.py** - Main matching agent with Google URL Context integration
- **batch_match_opportunities.py** - Batch processing script for all opportunities
- **migrate_bundles_to_matches.sql** - Database migration script (already applied)
- **run_migration.py** - Python script to execute migration (already executed)

### Documentation

- **THREEWAY_MATCHER_README.md** - Detailed matcher documentation
- **BATCH_MATCHING_README.md** - This file

### Testing & Utilities

- **test_threeway_match.py** - Test script for single opportunity
- **check_tables.py** - Utility to list all service20 tables
- **check_matches_columns.py** - Utility to show service20_matches schema

## How to Use

### Prerequisites

1. **Upload PDFs to Public Location**

   The Google URL Context API requires publicly accessible URLs. Upload your PDFs:

   ```bash
   # Option 1: AWS S3
   aws s3 cp Example_pdfs/ s3://your-bucket/pdfs/ --recursive --acl public-read

   # Option 2: GitHub
   # Create a public repo and upload PDFs, then use raw URLs

   # Option 3: Any web server
   # Upload and ensure public HTTP/HTTPS access
   ```

2. **Update PDF URLs**

   Edit `batch_match_opportunities.py` and update the URLs:

   ```python
   COUNCIL_DOCS = [
       PDFDocument(
           name="Manchester PPA Purchase",
           url="https://your-bucket.s3.amazonaws.com/Manchester_PPA_Purchase.pdf",
           type="council",
           description="Manchester council PPA procurement requirements"
       ),
   ]

   INVESTOR_DOCS = [...]
   PROVIDER_DOCS = [...]
   ```

### Running Batch Matching

```bash
# Activate virtual environment
source .venv/bin/activate  # or venv\Scripts\activate on Windows

# Run batch processing
python batch_match_opportunities.py
```

### Expected Output

```
================================================================================
BATCH THREE-WAY MATCHING - PROCESSING ALL INVESTMENT OPPORTUNITIES
================================================================================

Found 147 investment opportunities to process

Processing opportunities:
--------------------------------------------------------------------------------
✓ [1/147] ID   1 - Paris                | SCORE: 82.3
✓ [2/147] ID   2 - Berlin               | SCORE: 75.1
✗ [3/147] ID   3 - Rome                 | FAILED
✓ [4/147] ID   4 - Madrid               | SCORE: 68.5
...

================================================================================
BATCH PROCESSING COMPLETE
================================================================================

Total Opportunities: 147
Successfully Processed: 145
  - Successful Matches: 98
  - Failed Matches: 47
Errors: 2

Opportunities with errors:
  - ID 23: Failed to analyze documents: Network timeout
  - ID 89: Failed to analyze documents: Invalid PDF format

================================================================================
All results saved to service20_matches table
================================================================================
```

## Match Scoring System

### Individual Scores (0-100)

- **Council Match** - Alignment with municipality requirements
- **Investor Match** - Fit with investor criteria
- **Provider Match** - Service provider capability match

### Overall Score

Weighted average: `(Council + Investor + Provider) / 3`

### Score Interpretation

- **75-100**: Strong match - Proceed with due diligence
- **60-74**: Moderate match - Address gaps before proceeding
- **40-59**: Weak match - Consider alternative partners
- **0-39**: Failed match - Automatically marked as `match_failed=TRUE`

## Database Schema

### service20_matches Table

Key columns for three-way matching:

| Column | Type | Description |
|--------|------|-------------|
| match_id | VARCHAR | Unique identifier (UUID) |
| opportunity_ids | ARRAY | Investment opportunity IDs |
| council_doc_url | TEXT | URL to council requirements PDF |
| investor_doc_url | TEXT | URL to investor criteria PDF |
| provider_doc_url | TEXT | URL to provider capabilities PDF |
| council_match_score | DECIMAL(5,2) | Council alignment score (0-100) |
| investor_match_score | DECIMAL(5,2) | Investor fit score (0-100) |
| provider_match_score | DECIMAL(5,2) | Provider capability score (0-100) |
| overall_match_score | DECIMAL(5,2) | Overall three-way score (0-100) |
| match_analysis | TEXT | Detailed compatibility analysis |
| recommendations | TEXT[] | Actionable recommendations array |
| match_failed | BOOLEAN | TRUE if score < 40 or error occurred |
| failure_reason | TEXT | Explanation when match_failed=TRUE |
| match_metrics | JSONB | Full analysis data from all three parties |
| created_at | TIMESTAMP | When match was created |

## Querying Results

### Successful Matches

```sql
SELECT
    match_id,
    opportunity_ids,
    overall_match_score,
    council_match_score,
    investor_match_score,
    provider_match_score,
    recommendations
FROM service20_matches
WHERE match_failed = FALSE
ORDER BY overall_match_score DESC
LIMIT 10;
```

### Failed Matches

```sql
SELECT
    match_id,
    opportunity_ids,
    overall_match_score,
    failure_reason
FROM service20_matches
WHERE match_failed = TRUE
ORDER BY created_at DESC;
```

### Matches by Score Range

```sql
-- Strong matches
SELECT COUNT(*) FROM service20_matches WHERE overall_match_score >= 75;

-- Moderate matches
SELECT COUNT(*) FROM service20_matches WHERE overall_match_score BETWEEN 60 AND 74;

-- Weak matches
SELECT COUNT(*) FROM service20_matches WHERE overall_match_score BETWEEN 40 AND 59;

-- Failed matches
SELECT COUNT(*) FROM service20_matches WHERE match_failed = TRUE;
```

## Troubleshooting

### Issue: "Placeholder URLs detected"

**Solution**: Update the PDF URLs in `batch_match_opportunities.py` with actual public URLs.

### Issue: "Could not initialize matcher"

**Cause**: Missing environment variables.

**Solution**: Ensure `.env` file contains:
```env
GOOGLE_API_KEY=your_google_api_key
DATABASE_URL=postgresql://user:password@host:port/database
```

### Issue: "Failed to analyze documents: 403 Forbidden"

**Cause**: PDFs are not publicly accessible.

**Solution**:
- Verify URLs are accessible via browser without authentication
- Ensure S3 bucket has public read permissions
- Check firewall rules on web server

### Issue: "Network timeout"

**Cause**: Google API rate limiting or network issues.

**Solution**:
- Increase delay between requests in `batch_match_opportunities.py`
- Retry failed opportunities manually
- Check Google API quotas

## Performance Considerations

### Processing Time

- **Per Opportunity**: ~5-10 seconds (Google API latency)
- **100 Opportunities**: ~10-15 minutes
- **1000 Opportunities**: ~2-3 hours

### Rate Limiting

The batch script includes a 1-second delay between requests to avoid rate limiting. Adjust if needed:

```python
# In batch_match_opportunities.py
await asyncio.sleep(1)  # Increase to 2 or 3 if rate limited
```

### Cost Estimation

Google URL Context API pricing varies. For 147 opportunities:
- 147 requests × 3 documents each = 441 document analyses
- Estimated cost: ~$5-10 depending on document size and API tier

## Future Enhancements

1. **Parallel Processing**: Process multiple opportunities concurrently
2. **Document Library**: Store common council/investor/provider docs in database
3. **Smart Matching**: Use ML to select best document combinations
4. **Incremental Updates**: Only process new or updated opportunities
5. **Web Interface**: API endpoint to trigger batch processing via UI
6. **Notifications**: Email/Slack alerts when batch completes
7. **Resume Capability**: Save progress and resume from last processed opportunity

## Support

For issues or questions:
1. Check logs: Detailed error messages are logged to console
2. Verify environment variables are set correctly
3. Ensure PDFs are publicly accessible
4. Review `service20_matches` table for saved results

---

**Created**: 2025-10-28
**Service**: Service20 Investment Opportunities
**Technology**: Google Gemini 2.5-pro with URL Context Grounding
**Database**: PostgreSQL (service20_matches table)
