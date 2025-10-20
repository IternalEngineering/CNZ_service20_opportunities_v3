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

## Related Documentation

- [Service20 Main README](README.md)
- [SQS Integration](docs/sqs-integration.md)
- [Database Schema](docs/database-schema.md)
- [MindsDB Setup](../service21/MINDSDB_SETUP.md)
