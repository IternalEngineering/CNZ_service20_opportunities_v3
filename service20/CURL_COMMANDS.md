# Service20 API - Curl Command Reference

Complete reference for all Service20 API endpoints with example curl commands.

## Base Configuration

```bash
# Set base URL (adjust port if needed)
export BASE_URL="http://localhost:8000"

# Or for production
export BASE_URL="https://your-production-domain.com"
```

---

## 1. Health & Info Endpoints

### Health Check
```bash
curl -X GET "$BASE_URL/health"
```

**Expected Response:**
```json
{
  "status": "healthy",
  "database": true,
  "timestamp": "2025-01-27T10:30:00Z",
  "version": "1.0.0"
}
```

### API Information
```bash
curl -X GET "$BASE_URL/"
```

**Expected Response:**
```json
{
  "name": "Service20 Investment Opportunities API",
  "version": "1.0.0",
  "status": "running",
  "docs": "/docs",
  "health": "/health",
  "endpoints": {
    "chat_query": "/chat/query",
    "funding_query": "/funding/query",
    "matches_list": "/matches/list",
    "alerts_list": "/alerts/list",
    "bundles_list": "/bundles/list"
  }
}
```

---

## 2. Trigger AI Research (NEW)

### Trigger City Investment Opportunity Research

**Runs the AI research agent** to generate a new comprehensive investment opportunity report for a city.

This endpoint triggers the deep research agent in the background. The process takes 60-180 seconds and stores results in the database.

**Basic Request:**
```bash
curl -X POST "$BASE_URL/research/city" \
  -H "Content-Type: application/json" \
  -d '{
    "city": "Paris",
    "country_code": "FRA"
  }'
```

**With Optional Parameters:**
```bash
curl -X POST "$BASE_URL/research/city" \
  -H "Content-Type: application/json" \
  -d '{
    "city": "Paris",
    "country_code": "FRA",
    "sector": "solar_energy",
    "investment_range": "1000000-10000000"
  }'
```

**More Examples:**
```bash
# London renewable energy research
curl -X POST "$BASE_URL/research/city" \
  -H "Content-Type: application/json" \
  -d '{"city": "London", "country_code": "GBR"}'

# Tokyo solar energy research with custom range
curl -X POST "$BASE_URL/research/city" \
  -H "Content-Type: application/json" \
  -d '{
    "city": "Tokyo",
    "country_code": "JPN",
    "sector": "solar_energy",
    "investment_range": "500000-5000000"
  }'

# New York wind energy research
curl -X POST "$BASE_URL/research/city" \
  -H "Content-Type: application/json" \
  -d '{
    "city": "New York",
    "country_code": "USA",
    "sector": "wind_energy"
  }'
```

**Success Response (202 Accepted):**
```json
{
  "success": true,
  "message": "Research job queued successfully for Paris, France (FRA)",
  "job_id": "paris-fra-20251029-142030",
  "status": "queued",
  "estimated_duration_seconds": 120,
  "query_endpoint": "/chat/query"
}
```

**Available Sectors:**
- `renewable_energy` (default)
- `solar_energy`
- `wind_energy`
- `energy_storage`
- `green_buildings`
- `sustainable_transport`
- `waste_management`
- `water_management`

**Process Flow:**
```bash
# 1. Trigger research (returns immediately)
curl -X POST "$BASE_URL/research/city" \
  -H "Content-Type: application/json" \
  -d '{"city": "Paris", "country_code": "FRA"}'

# Response:
# {
#   "success": true,
#   "job_id": "paris-fra-20251029-142030",
#   "status": "queued",
#   "estimated_duration_seconds": 120
# }

# 2. Wait 2-3 minutes for AI agent to complete research

# 3. Query results (see next section)
curl -X POST "$BASE_URL/chat/query" \
  -H "Content-Type: application/json" \
  -d '{"city": "Paris", "country_code": "FRA"}'
```

**What the AI Agent Does:**
- Performs web searches for city-specific Net Zero opportunities
- Analyzes municipal programs and incentives
- Generates 3-5 specific project proposals with financial projections
- Calculates carbon reduction impact (tons CO2/year)
- Assesses technical feasibility and timelines
- Provides funding and partnership recommendations

**Error Response (400 - Invalid Country):**
```json
{
  "success": false,
  "error": "InvalidCountryCode",
  "message": "Invalid country code 'XXX'",
  "details": {
    "country_code": "XXX",
    "supported_codes": ["USA", "GBR", "FRA", "DEU", ...]
  }
}
```

---

## 3. Investment Opportunities (Chat Query)

### Query Latest Investment Opportunity by City

Get the most recent **cached** investment research for a specific city and country.

**Basic Query:**
```bash
curl -X POST "$BASE_URL/chat/query" \
  -H "Content-Type: application/json" \
  -d '{
    "city": "Paris",
    "country_code": "FRA"
  }'
```

**More Examples:**
```bash
# Tokyo, Japan
curl -X POST "$BASE_URL/chat/query" \
  -H "Content-Type: application/json" \
  -d '{"city": "Tokyo", "country_code": "JPN"}'

# New York, USA
curl -X POST "$BASE_URL/chat/query" \
  -H "Content-Type: application/json" \
  -d '{"city": "New York", "country_code": "USA"}'

# London, UK
curl -X POST "$BASE_URL/chat/query" \
  -H "Content-Type: application/json" \
  -d '{"city": "London", "country_code": "GBR"}'
```

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "city": "Paris",
    "country": "France",
    "country_code": "FRA",
    "sector": "renewable_energy",
    "research_brief": "Executive summary...",
    "final_report": "# Full report...",
    "created_at": "2025-01-27T10:30:00Z",
    "langfuse_trace_id": "trace-123"
  },
  "message": "Investment opportunity found for Paris, FRA",
  "query_time_ms": 42.15
}
```

**Not Found Response (404):**
```json
{
  "success": false,
  "error": "NotFound",
  "message": "No investment opportunity found for city 'Berlin' and country code 'DEU'"
}
```

---

## 4. Funding Opportunities

### Query Funding Opportunities with Filters

Search funding opportunities by type, scope, country, and sector.

**All Filters:**
```bash
curl -X POST "$BASE_URL/funding/query" \
  -H "Content-Type: application/json" \
  -d '{
    "funder_type": "impact_investor",
    "scope": "national",
    "country": "United States",
    "sector": "renewable_energy",
    "limit": 20
  }'
```

**Filter by Funder Type:**
```bash
# Impact Investors
curl -X POST "$BASE_URL/funding/query" \
  -H "Content-Type: application/json" \
  -d '{"funder_type": "impact_investor", "limit": 10}'

# Foundations
curl -X POST "$BASE_URL/funding/query" \
  -H "Content-Type: application/json" \
  -d '{"funder_type": "foundation", "limit": 10}'

# Venture Capital
curl -X POST "$BASE_URL/funding/query" \
  -H "Content-Type: application/json" \
  -d '{"funder_type": "venture_capital", "limit": 10}'
```

**Filter by Scope:**
```bash
# City-level
curl -X POST "$BASE_URL/funding/query" \
  -H "Content-Type: application/json" \
  -d '{"scope": "city", "limit": 10}'

# National
curl -X POST "$BASE_URL/funding/query" \
  -H "Content-Type: application/json" \
  -d '{"scope": "national", "limit": 10}'

# Global
curl -X POST "$BASE_URL/funding/query" \
  -H "Content-Type: application/json" \
  -d '{"scope": "global", "limit": 10}'
```

**Filter by Country:**
```bash
curl -X POST "$BASE_URL/funding/query" \
  -H "Content-Type: application/json" \
  -d '{"country": "United States", "limit": 15}'
```

**Filter by Sector:**
```bash
# Renewable Energy
curl -X POST "$BASE_URL/funding/query" \
  -H "Content-Type: application/json" \
  -d '{"sector": "renewable_energy", "limit": 10}'

# Solar Energy
curl -X POST "$BASE_URL/funding/query" \
  -H "Content-Type: application/json" \
  -d '{"sector": "solar_energy", "limit": 10}'
```

**No Filters (Latest 10):**
```bash
curl -X POST "$BASE_URL/funding/query" \
  -H "Content-Type: application/json" \
  -d '{"limit": 10}'
```

**Success Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "funder_type": "impact_investor",
      "scope": "national",
      "countries": ["United States"],
      "sectors": ["renewable_energy", "solar_energy"],
      "min_investment": 1000000,
      "max_investment": 10000000,
      "query": "impact investors renewable energy USA",
      "research_brief": "Executive summary...",
      "final_report": "# Full research report...",
      "metadata": {},
      "created_at": "2025-01-27T10:30:00Z",
      "langfuse_trace_id": "trace-456"
    }
  ],
  "count": 1,
  "message": "Found 1 funding opportunities",
  "query_time_ms": 35.20
}
```

---

## 5. Opportunity Matches

### List Opportunity Matches with Filters

Retrieve opportunity-funder matches with various filters.

**All Filters:**
```bash
curl -X GET "$BASE_URL/matches/list?match_type=single&confidence_level=high&status=proposed&limit=20"
```

**Filter by Match Type:**
```bash
# Single matches
curl -X GET "$BASE_URL/matches/list?match_type=single&limit=10"

# Bundled matches
curl -X GET "$BASE_URL/matches/list?match_type=bundled&limit=10"
```

**Filter by Confidence Level:**
```bash
# High confidence
curl -X GET "$BASE_URL/matches/list?confidence_level=high&limit=10"

# Medium confidence
curl -X GET "$BASE_URL/matches/list?confidence_level=medium&limit=10"

# Low confidence
curl -X GET "$BASE_URL/matches/list?confidence_level=low&limit=10"
```

**Filter by Status:**
```bash
# Proposed matches
curl -X GET "$BASE_URL/matches/list?status=proposed&limit=10"

# Reviewed matches
curl -X GET "$BASE_URL/matches/list?status=reviewed&limit=10"

# Accepted matches
curl -X GET "$BASE_URL/matches/list?status=accepted&limit=10"

# Rejected matches
curl -X GET "$BASE_URL/matches/list?status=rejected&limit=10"
```

**No Filters (Latest 10):**
```bash
curl -X GET "$BASE_URL/matches/list?limit=10"
```

**Combined Filters:**
```bash
# High confidence accepted single matches
curl -X GET "$BASE_URL/matches/list?match_type=single&confidence_level=high&status=accepted&limit=15"

# Proposed bundled matches
curl -X GET "$BASE_URL/matches/list?match_type=bundled&status=proposed&limit=10"
```

**Success Response:**
```json
{
  "success": true,
  "data": [
    {
      "match_id": "match-123",
      "match_type": "single",
      "compatibility_score": 85.5,
      "confidence_level": "high",
      "status": "proposed",
      "opportunities_data": [
        {
          "city": "Paris",
          "sector": "renewable_energy",
          "investment_needed": 5000000
        }
      ],
      "funders_data": [
        {
          "name": "Green Impact Fund",
          "type": "impact_investor",
          "max_investment": 10000000
        }
      ],
      "bundle_metrics": null,
      "created_at": "2025-01-27T10:30:00Z",
      "updated_at": "2025-01-27T11:00:00Z"
    }
  ],
  "count": 1,
  "message": "Found 1 opportunity matches",
  "query_time_ms": 28.50
}
```

---

## 6. User Alerts

### List User Alerts with Filters

Retrieve user alerts with optional filtering.

**All Filters:**
```bash
curl -X GET "$BASE_URL/alerts/list?user_id=42&alert_type=city_opportunity&status=active&limit=20"
```

**Filter by User:**
```bash
# User ID 1
curl -X GET "$BASE_URL/alerts/list?user_id=1&limit=10"

# User ID 42
curl -X GET "$BASE_URL/alerts/list?user_id=42&limit=10"
```

**Filter by Alert Type:**
```bash
# City opportunity alerts
curl -X GET "$BASE_URL/alerts/list?alert_type=city_opportunity&limit=10"

# Funder opportunity alerts
curl -X GET "$BASE_URL/alerts/list?alert_type=funder_opportunity&limit=10"
```

**Filter by Status:**
```bash
# Active alerts
curl -X GET "$BASE_URL/alerts/list?status=active&limit=10"

# Paused alerts
curl -X GET "$BASE_URL/alerts/list?status=paused&limit=10"

# Expired alerts
curl -X GET "$BASE_URL/alerts/list?status=expired&limit=10"
```

**No Filters (Latest 10):**
```bash
curl -X GET "$BASE_URL/alerts/list?limit=10"
```

**Combined Filters:**
```bash
# Active city opportunity alerts for user 42
curl -X GET "$BASE_URL/alerts/list?user_id=42&alert_type=city_opportunity&status=active&limit=15"

# All active alerts
curl -X GET "$BASE_URL/alerts/list?status=active&limit=50"
```

**Success Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "user_id": 42,
      "alert_type": "city_opportunity",
      "research_id": "research-789",
      "title": "Paris Renewable Energy Alert",
      "description": "New opportunities in Paris renewable sector",
      "criteria": {
        "city": "Paris",
        "sector": "renewable_energy",
        "min_investment": 1000000
      },
      "status": "active",
      "created_at": "2025-01-27T10:30:00Z",
      "updated_at": "2025-01-27T11:00:00Z"
    }
  ],
  "count": 1,
  "message": "Found 1 alerts",
  "query_time_ms": 22.80
}
```

---

## 7. Opportunity Bundles

### List Opportunity Bundles with Filters

Retrieve bundled opportunities with filtering options.

**All Filters:**
```bash
curl -X GET "$BASE_URL/bundles/list?bundle_type=regional&min_investment=5000000&limit=20"
```

**Filter by Bundle Type:**
```bash
# Regional bundles
curl -X GET "$BASE_URL/bundles/list?bundle_type=regional&limit=10"

# Sectoral bundles
curl -X GET "$BASE_URL/bundles/list?bundle_type=sectoral&limit=10"

# Mixed bundles
curl -X GET "$BASE_URL/bundles/list?bundle_type=mixed&limit=10"
```

**Filter by Minimum Investment:**
```bash
# Bundles >= $1M
curl -X GET "$BASE_URL/bundles/list?min_investment=1000000&limit=10"

# Bundles >= $5M
curl -X GET "$BASE_URL/bundles/list?min_investment=5000000&limit=10"

# Bundles >= $10M
curl -X GET "$BASE_URL/bundles/list?min_investment=10000000&limit=10"
```

**No Filters (Latest 10):**
```bash
curl -X GET "$BASE_URL/bundles/list?limit=10"
```

**Combined Filters:**
```bash
# Regional bundles over $5M
curl -X GET "$BASE_URL/bundles/list?bundle_type=regional&min_investment=5000000&limit=15"

# Sectoral bundles over $1M
curl -X GET "$BASE_URL/bundles/list?bundle_type=sectoral&min_investment=1000000&limit=10"
```

**Success Response:**
```json
{
  "success": true,
  "data": [
    {
      "bundle_id": "bundle-abc",
      "bundle_type": "regional",
      "opportunity_ids": [1, 2, 3],
      "total_investment": 15000000,
      "total_carbon_impact": 50000.5,
      "geographic_coverage": ["France", "Germany", "Spain"],
      "financial_analysis": {
        "total_roi": 12.5,
        "payback_period": 8,
        "risk_score": 3.2
      },
      "metadata": {},
      "created_at": "2025-01-27T10:30:00Z",
      "updated_at": "2025-01-27T11:00:00Z"
    }
  ],
  "count": 1,
  "message": "Found 1 bundles",
  "query_time_ms": 31.25
}
```

---

## Testing Workflow

### Complete Test Sequence

Test all endpoints in order:

```bash
# 1. Check API health
curl -X GET "$BASE_URL/health"

# 2. Get API info
curl -X GET "$BASE_URL/"

# 3. Query investment opportunity
curl -X POST "$BASE_URL/chat/query" \
  -H "Content-Type: application/json" \
  -d '{"city": "Paris", "country_code": "FRA"}'

# 4. Query funding opportunities
curl -X POST "$BASE_URL/funding/query" \
  -H "Content-Type: application/json" \
  -d '{"funder_type": "impact_investor", "limit": 5}'

# 5. List opportunity matches
curl -X GET "$BASE_URL/matches/list?confidence_level=high&limit=5"

# 6. List user alerts
curl -X GET "$BASE_URL/alerts/list?status=active&limit=5"

# 7. List bundles
curl -X GET "$BASE_URL/bundles/list?bundle_type=regional&limit=5"
```

---

## Error Handling Examples

### 404 Not Found
```bash
curl -X POST "$BASE_URL/chat/query" \
  -H "Content-Type: application/json" \
  -d '{"city": "NonExistentCity", "country_code": "XXX"}'
```

Response:
```json
{
  "success": false,
  "error": "NotFound",
  "message": "No investment opportunity found for city 'NonExistentCity' and country code 'XXX'"
}
```

### 422 Validation Error
```bash
curl -X POST "$BASE_URL/chat/query" \
  -H "Content-Type: application/json" \
  -d '{"city": "X", "country_code": "TOOLONG"}'
```

Response:
```json
{
  "detail": [
    {
      "loc": ["body", "city"],
      "msg": "String should have at least 2 characters",
      "type": "string_too_short"
    },
    {
      "loc": ["body", "country_code"],
      "msg": "String should have at most 3 characters",
      "type": "string_too_long"
    }
  ]
}
```

---

## Performance Monitoring

All responses include `X-Process-Time-Ms` header:

```bash
curl -X GET "$BASE_URL/health" -i | grep "X-Process-Time-Ms"
```

Output:
```
X-Process-Time-Ms: 12.34
```

---

## Batch Testing Script

Save as `test_all_endpoints.sh`:

```bash
#!/bin/bash

BASE_URL="http://localhost:8000"

echo "=== Testing Service20 API ==="

echo -e "\n1. Health Check"
curl -s -X GET "$BASE_URL/health" | jq

echo -e "\n2. Investment Opportunity Query"
curl -s -X POST "$BASE_URL/chat/query" \
  -H "Content-Type: application/json" \
  -d '{"city": "Paris", "country_code": "FRA"}' | jq

echo -e "\n3. Funding Query"
curl -s -X POST "$BASE_URL/funding/query" \
  -H "Content-Type: application/json" \
  -d '{"funder_type": "impact_investor", "limit": 3}' | jq

echo -e "\n4. Matches List"
curl -s -X GET "$BASE_URL/matches/list?limit=3" | jq

echo -e "\n5. Alerts List"
curl -s -X GET "$BASE_URL/alerts/list?limit=3" | jq

echo -e "\n6. Bundles List"
curl -s -X GET "$BASE_URL/bundles/list?limit=3" | jq

echo -e "\n=== All tests complete ==="
```

Run with:
```bash
chmod +x test_all_endpoints.sh
./test_all_endpoints.sh
```

---

## Interactive API Documentation

For interactive testing, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

**Last Updated**: 2025-01-27
**API Version**: 1.0.0
