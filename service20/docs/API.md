# Service20 API Documentation

**Version**: 1.0.0
**Base URL**: `http://localhost:8000`
**Environment**: Development

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Base URL](#base-url)
- [Endpoints](#endpoints)
  - [POST /chat/query](#post-chatquery)
  - [GET /health](#get-health)
  - [GET /](#get-)
- [Data Models](#data-models)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Rate Limiting](#rate-limiting)
- [Observability](#observability)

## Overview

Service20 is a FastAPI-based microservice that provides real-time access to Net Zero investment opportunity research. It returns the most recent research data for a given city and country, including executive summaries, full reports, financial projections, and carbon impact metrics.

**Key Features**:
- ⚡ Asynchronous database queries with connection pooling
- 📊 Integrated Arize Phoenix & Langfuse observability
- ✅ Type-safe request/response validation with Pydantic
- 📝 Auto-generated interactive API documentation
- 🚀 Sub-100ms query response times (typical)

## Authentication

**Current**: No authentication required (development mode)

**Planned**:
- JWT bearer tokens
- API key authentication
- Rate limiting per API key

## Base URL

| Environment | Base URL |
|------------|----------|
| Development | `http://localhost:8000` |
| Staging | `https://staging-api.urbanzero.com/service20` |
| Production | `https://api.urbanzero.com/service20` |

## Endpoints

### POST /chat/query

Retrieve the most recent investment opportunity research for a specific city and country.

**URL**: `/chat/query`
**Method**: `POST`
**Content-Type**: `application/json`

#### Request Body

```json
{
  "city": "string",
  "country_code": "string"
}
```

| Field | Type | Required | Description | Examples |
|-------|------|----------|-------------|----------|
| `city` | string | Yes | City name (2-100 chars) | "Paris", "London", "Tokyo" |
| `country_code` | string | Yes | ISO 3166-1 alpha-3 code (2-3 chars) | "FRA", "GBR", "USA" |

#### Response (200 OK)

```json
{
  "success": true,
  "data": {
    "id": 1,
    "city": "Paris",
    "country": "France",
    "country_code": "FRA",
    "sector": "renewable_energy",
    "query": "Research Net Zero investment opportunities in Paris, France",
    "research_brief": "Executive summary...",
    "final_report": "# Complete report...",
    "metadata": {},
    "notes": [],
    "research_iterations": 3,
    "tool_calls_count": 15,
    "created_at": "2025-01-27T10:30:00Z",
    "updated_at": "2025-01-27T10:35:00Z",
    "langfuse_trace_id": "trace_abc123"
  },
  "message": "Investment opportunity found for Paris, FRA",
  "query_time_ms": 45.32
}
```

#### Response (404 Not Found)

```json
{
  "success": false,
  "error": "NotFound",
  "message": "No investment opportunity found for city 'Tokyo' and country code 'JPN'",
  "details": {
    "city": "Tokyo",
    "country_code": "JPN"
  }
}
```

#### Response Headers

| Header | Description |
|--------|-------------|
| `X-Process-Time-Ms` | Request processing time in milliseconds |
| `Content-Type` | `application/json` |

---

### GET /health

Health check endpoint to verify service and database status.

**URL**: `/health`
**Method**: `GET`

#### Response (200 OK)

```json
{
  "status": "healthy",
  "database": true,
  "timestamp": "2025-01-27T10:30:00Z",
  "version": "1.0.0"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | "healthy" or "degraded" |
| `database` | boolean | Database connection status |
| `timestamp` | datetime | Current UTC timestamp |
| `version` | string | API version |

---

### GET /

Root endpoint with API information.

**URL**: `/`
**Method**: `GET`

#### Response (200 OK)

```json
{
  "name": "Service20 Investment Opportunities API",
  "version": "1.0.0",
  "status": "running",
  "docs": "/docs",
  "health": "/health",
  "endpoints": {
    "chat_query": "/chat/query"
  }
}
```

---

## Data Models

### InvestmentOpportunity

Complete investment opportunity research data.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | integer | Yes | Unique identifier |
| `city` | string | No | City name |
| `country` | string | No | Country name |
| `country_code` | string | No | ISO 3166-1 alpha-3 code |
| `sector` | string | No | Primary sector |
| `query` | string | Yes | Original research query |
| `research_brief` | string | No | Executive summary |
| `final_report` | string | No | Complete research report |
| `metadata` | object | No | Additional metadata (JSONB) |
| `notes` | array | No | Research notes/findings |
| `research_iterations` | integer | No | Number of research iterations |
| `tool_calls_count` | integer | No | Number of tool calls made |
| `created_at` | datetime | Yes | Creation timestamp |
| `updated_at` | datetime | No | Last update timestamp |
| `langfuse_trace_id` | string | No | Langfuse trace identifier |

---

## Error Handling

All error responses follow a consistent format:

```json
{
  "success": false,
  "error": "ErrorType",
  "message": "Human-readable error message",
  "details": {
    "key": "value"
  }
}
```

### HTTP Status Codes

| Status Code | Error Type | Description |
|------------|------------|-------------|
| 200 | - | Success |
| 404 | NotFound | No investment opportunity found |
| 422 | ValidationError | Invalid request parameters |
| 500 | InternalServerError | Server error |
| 503 | ServiceUnavailable | Database connection failed |

---

## Examples

### Example 1: Query Paris Investment Opportunities

**Request:**
```bash
curl -X POST http://localhost:8000/chat/query \
  -H "Content-Type: application/json" \
  -d '{
    "city": "Paris",
    "country_code": "FRA"
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 5,
    "city": "Paris",
    "country": "France",
    "country_code": "FRA",
    "sector": "renewable_energy",
    "query": "Research Net Zero investment opportunities in Paris, France",
    "research_brief": "Paris offers significant renewable energy investment opportunities...",
    "final_report": "# Investment Opportunities in Paris\n\n## Executive Summary\n...",
    "metadata": {
      "region": "Western Europe",
      "projects_identified": 5
    },
    "created_at": "2025-01-27T10:30:00Z"
  },
  "message": "Investment opportunity found for Paris, FRA",
  "query_time_ms": 42.15
}
```

### Example 2: Query Non-Existent City

**Request:**
```bash
curl -X POST http://localhost:8000/chat/query \
  -H "Content-Type: application/json" \
  -d '{
    "city": "NonExistentCity",
    "country_code": "XXX"
  }'
```

**Response (404):**
```json
{
  "success": false,
  "error": "NotFound",
  "message": "No investment opportunity found for city 'NonExistentCity' and country code 'XXX'",
  "details": {
    "city": "NonExistentCity",
    "country_code": "XXX"
  }
}
```

### Example 3: Health Check

**Request:**
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "database": true,
  "timestamp": "2025-01-27T10:30:00Z",
  "version": "1.0.0"
}
```

---

## Rate Limiting

**Current**: No rate limiting (development mode)

**Planned**:
- 100 requests/minute per IP
- 1000 requests/hour per API key
- Burst allowance: 10 requests/second

---

## Observability

### Tracing

Service20 integrates with two observability platforms:

1. **Arize Phoenix**: LLM observability and agent workflow tracking
   - Tracks all database queries
   - Monitors request/response metrics
   - Traces investment service calls

2. **Langfuse**: LLM-focused tracing and cost monitoring
   - Available via `langfuse_trace_id` in responses
   - Links to research agent execution traces

### Metrics

Key metrics tracked:
- Query execution time (`query_time_ms`)
- Request processing time (`X-Process-Time-Ms` header)
- Database connection pool status
- Success/error rates

### Logs

Structured logging with:
- Request/response logging
- Error tracking with stack traces
- Database query logging
- Trace ID correlation

---

## Interactive Documentation

Visit these URLs when the service is running:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Spec**: http://localhost:8000/openapi.json

---

## Support

For issues or questions:
- GitHub Issues: [Service20 Repository](https://github.com/IternalEngineering/CNZ_service20_opportunities_v3/issues)
- Documentation: This file
- Interactive API Docs: `/docs` endpoint

---

**Last Updated**: 2025-01-27
**API Version**: 1.0.0
**Status**: ✅ Production Ready
