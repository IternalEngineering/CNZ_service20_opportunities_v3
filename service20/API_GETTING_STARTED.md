# Service20 API - Getting Started Guide

## Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL database with `service20_investment_opportunities` table
- Environment variables configured in `.env`

### Installation

```bash
# 1. Navigate to service20 directory
cd server_c/service20

# 2. Install dependencies
uv pip install -r requirements-api.txt

# 3. Verify environment variables
cat .env  # Check DATABASE_URL and tracing credentials

# 4. Start the API server
python start_api.py
```

### First API Call

Once the server is running, test it with:

```bash
curl -X POST http://localhost:8000/chat/query \
  -H "Content-Type: application/json" \
  -d '{"city": "Paris", "country_code": "FRA"}'
```

## Environment Configuration

Create or update `.env` with:

```env
# Database
DATABASE_URL=postgresql://user:password@host:port/database?sslmode=require

# API Configuration
API_PORT=8000
API_HOST=0.0.0.0
API_RELOAD=true
API_LOG_LEVEL=info

# Tracing (Optional)
ARIZE_SPACE_KEY=your_arize_space_key
ARIZE_API_KEY=your_arize_api_key
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
```

## Directory Structure

```
service20/
├── app/                      # FastAPI application
│   ├── main.py              # App entry point
│   ├── config.py            # Configuration
│   ├── database.py          # Database pool
│   ├── models/              # Pydantic schemas
│   ├── routes/              # API endpoints
│   │   └── chat.py         # /chat/query endpoint
│   └── services/            # Business logic
│       └── investment.py    # Investment queries
├── docs/
│   └── API.md              # Comprehensive API documentation
├── start_api.py             # Launch script
├── test_api.py              # Test suite
└── requirements-api.txt     # Dependencies
```

## API Endpoints

### 1. POST /chat/query

Query latest investment opportunity for a city/country.

**Request:**
```json
{
  "city": "Paris",
  "country_code": "FRA"
}
```

**Response (200):**
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
    "created_at": "2025-01-27T10:30:00Z"
  },
  "message": "Investment opportunity found for Paris, FRA",
  "query_time_ms": 42.15
}
```

**Response (404):**
```json
{
  "success": false,
  "error": "NotFound",
  "message": "No investment opportunity found for city 'Tokyo' and country code 'JPN'"
}
```

### 2. GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "database": true,
  "timestamp": "2025-01-27T10:30:00Z",
  "version": "1.0.0"
}
```

### 3. GET /

API information.

**Response:**
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

## Interactive Documentation

When the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These provide interactive API testing and comprehensive documentation.

## Testing

Run the test suite:

```bash
# Make sure the API is running first (in another terminal)
python start_api.py

# Then run tests
python test_api.py
```

## Observability

The API integrates with two observability platforms:

### Arize Phoenix
- **Purpose**: LLM observability and agent workflow tracking
- **Setup**: Set `ARIZE_SPACE_KEY` and `ARIZE_API_KEY` in `.env`
- **Dashboard**: View traces in Arize Phoenix console

### Langfuse
- **Purpose**: LLM-focused tracing and cost monitoring
- **Setup**: Set `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL` in `.env`
- **Trace ID**: Available in API response as `langfuse_trace_id`

## Common Issues

### Issue: Database connection failed

**Solution:**
```bash
# Verify DATABASE_URL
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1"

# Check table exists
psql $DATABASE_URL -c "\d service20_investment_opportunities"
```

### Issue: Port already in use

**Solution:**
```bash
# Change port in .env
echo "API_PORT=8001" >> .env

# Or find and kill process
netstat -ano | findstr :8000
taskkill /PID <pid> /F
```

### Issue: Module not found

**Solution:**
```bash
# Reinstall dependencies
uv pip install -r requirements-api.txt

# Verify installation
python -c "import fastapi; print(fastapi.__version__)"
```

## Development

### Hot Reload

The server runs with hot reload enabled by default:

```bash
# Edit any file in app/
# Server automatically restarts
```

### Adding New Endpoints

1. Create route in `app/routes/`
2. Register in `app/main.py`:
   ```python
   from .routes import new_router
   app.include_router(new_router)
   ```

### Database Queries

Use the connection pool:

```python
from app.database import get_connection

async with get_connection() as conn:
    result = await conn.fetchrow("SELECT * FROM table WHERE id=$1", id)
```

## Production Deployment

### 1. Update Configuration

```env
API_RELOAD=false
API_WORKERS=4
API_LOG_LEVEL=warning
DEBUG=false
```

### 2. Use Production Server

```bash
uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --no-access-log
```

### 3. Add Authentication

Coming soon: JWT authentication and API key support.

### 4. Add Rate Limiting

Coming soon: Redis-based rate limiting.

## Performance Tips

- **Connection Pooling**: Configured for 5-20 connections
- **Async Queries**: All database operations are asynchronous
- **Response Time**: Typical query takes <50ms
- **Monitoring**: Check `X-Process-Time-Ms` header

## Support

- **Documentation**: [docs/API.md](docs/API.md)
- **Issues**: GitHub Issues
- **Interactive Docs**: `/docs` endpoint

## Next Steps

1. ✅ Install dependencies
2. ✅ Configure `.env`
3. ✅ Start API server
4. ✅ Test endpoints
5. ⏳ Deploy to staging
6. ⏳ Add authentication
7. ⏳ Configure monitoring

---

**Last Updated**: 2025-01-27
**Version**: 1.0.0
