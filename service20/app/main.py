"""Service20 FastAPI Application - Investment Opportunities API."""

import sys
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

# Add src directory to path for tracing import
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from open_deep_research.tracing import initialize_tracing, get_tracer

from .config import settings
from .database import create_pool, close_pool, test_connection
from .routes import chat_router
from .routes.funding import router as funding_router
from .routes.matches import router as matches_router
from .routes.alerts import router as alerts_router
from .routes.bundles import router as bundles_router
from .routes.research import router as research_router
from .models import HealthResponse, ErrorResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management for the FastAPI application."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")

    # Initialize tracing
    logger.info("Initializing Arize/Langfuse tracing...")
    tracing_initialized = initialize_tracing("service20-api")
    if tracing_initialized:
        logger.info("✓ Tracing initialized successfully")
    else:
        logger.warning("! Tracing not initialized (no credentials found)")

    # Initialize database pool
    logger.info("Creating database connection pool...")
    try:
        await create_pool()
        logger.info("✓ Database pool created")

        # Test connection
        if await test_connection():
            logger.info("✓ Database connection test passed")
        else:
            logger.warning("! Database connection test failed")
    except Exception as e:
        logger.error(f"✗ Failed to initialize database: {str(e)}")
        raise

    logger.info(f"✓ {settings.app_name} is ready!")
    logger.info(f"  - Docs: http://localhost:{settings.api_port}/docs")
    logger.info(f"  - Health: http://localhost:{settings.api_port}/health")
    logger.info(f"  - Endpoints:")
    logger.info(f"    • POST /research/city - Trigger AI research for a city (NEW)")
    logger.info(f"    • POST /chat/query - Investment opportunities by city")
    logger.info(f"    • POST /funding/query - Funding opportunities")
    logger.info(f"    • GET  /matches/list - Opportunity matches")
    logger.info(f"    • GET  /alerts/list - User alerts")
    logger.info(f"    • GET  /bundles/list - Opportunity bundles")

    yield

    # Shutdown
    logger.info("Shutting down...")
    await close_pool()
    logger.info("✓ Database pool closed")
    logger.info(f"✓ {settings.app_name} stopped")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    ## Service20 Investment Opportunities API

    Real-time asynchronous API for querying Net Zero investment opportunities research.

    ### Features
    - **Fast Queries**: Async database queries with connection pooling
    - **Tracing**: Integrated Arize Phoenix & Langfuse observability
    - **Type Safety**: Pydantic models for request/response validation
    - **Auto Documentation**: Interactive API docs at `/docs`

    ### Main Endpoint
    - `POST /chat/query`: Retrieve latest investment research for a city/country

    ### Quick Start
    ```bash
    curl -X POST http://localhost:8000/chat/query \\
      -H "Content-Type: application/json" \\
      -d '{"city": "Paris", "country_code": "FRA"}'
    ```
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add request processing time to response headers."""
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"
    return response


# Exception handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors."""
    return JSONResponse(
        status_code=404,
        content=ErrorResponse(
            error="NotFound",
            message=f"Endpoint {request.url.path} not found"
        ).model_dump()
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="InternalServerError",
            message="An internal server error occurred"
        ).model_dump()
    )


# Health check endpoint
@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["health"],
    summary="Health check endpoint",
    description="Check the health status of the API and database connection"
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns:
        HealthResponse with service and database status
    """
    db_healthy = await test_connection()

    return HealthResponse(
        status="healthy" if db_healthy else "degraded",
        database=db_healthy,
        timestamp=datetime.utcnow(),
        version=settings.app_version
    )


# Root endpoint
@app.get(
    "/",
    tags=["info"],
    summary="API information",
    description="Get basic information about the API"
)
async def root():
    """
    Root endpoint with API information.

    Returns:
        Basic API information
    """
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "research_city": "/research/city",
            "chat_query": "/chat/query",
            "funding_query": "/funding/query",
            "matches_list": "/matches/list",
            "alerts_list": "/alerts/list",
            "bundles_list": "/bundles/list"
        }
    }


# Include routers
app.include_router(research_router)  # NEW: Trigger AI research
app.include_router(chat_router)
app.include_router(funding_router)
app.include_router(matches_router)
app.include_router(alerts_router)
app.include_router(bundles_router)

# Get tracer for manual spans (available to other modules)
tracer = get_tracer(__name__)
