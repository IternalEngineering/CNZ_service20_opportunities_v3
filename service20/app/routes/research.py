"""Research endpoint for triggering AI research agents."""

import asyncio
import logging
from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from fastapi.responses import JSONResponse

from ..models.research_schemas import CityResearchRequest, ResearchJobResponse
from ..models import ErrorResponse
from ..services.research import ResearchService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/research", tags=["research"])


async def run_research_background(
    city: str,
    country_code: str,
    sector: str,
    investment_range: str,
    job_id: str
):
    """
    Background task to run research agent.

    Args:
        city: City name
        country_code: ISO country code
        sector: Primary sector
        investment_range: Investment range
        job_id: Job identifier for logging
    """
    try:
        logger.info(f"[JOB {job_id}] Starting background research task")

        result = await ResearchService.run_city_research(
            city=city,
            country_code=country_code,
            sector=sector,
            investment_range=investment_range
        )

        logger.info(
            f"[JOB {job_id}] Research completed successfully. "
            f"Research ID: {result.get('research_id')}"
        )

    except Exception as e:
        logger.error(
            f"[JOB {job_id}] Research failed: {str(e)}",
            exc_info=True
        )


@router.post(
    "/city",
    response_model=ResearchJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        202: {
            "description": "Research job accepted and queued",
            "model": ResearchJobResponse
        },
        400: {
            "description": "Invalid request parameters",
            "model": ErrorResponse
        },
        422: {
            "description": "Validation error",
            "model": ErrorResponse
        },
        500: {
            "description": "Internal server error",
            "model": ErrorResponse
        }
    },
    summary="Trigger AI research for a city investment opportunity",
    description="""
    **Triggers the AI research agent** to generate a comprehensive investment opportunity
    report for a specified city.

    This endpoint runs the deep research agent in the background and stores results
    in the database. The process typically takes 60-180 seconds to complete.

    **What the Agent Does:**
    - Performs web searches for city-specific investment opportunities
    - Analyzes municipal programs, incentives, and partnerships
    - Generates 3-5 specific project proposals with financial projections
    - Calculates carbon reduction impact (tons CO2/year)
    - Assesses technical feasibility and implementation timelines
    - Provides funding and partnership recommendations

    **Process Flow:**
    1. Request accepted immediately (returns 202 status)
    2. Research runs in background (60-180 seconds)
    3. Results stored in `service20_investment_opportunities` table
    4. Query results using `POST /chat/query` with same city/country

    **Parameters:**
    - `city`: City name (e.g., "Paris", "London", "New York")
    - `country_code`: ISO 3166-1 alpha-3 code (e.g., "FRA", "GBR", "USA")
    - `sector` (optional): Primary sector (default: "renewable_energy")
    - `investment_range` (optional): Investment range in USD (default: "500000-5000000")

    **Returns:**
    - Job ID for tracking
    - Estimated completion time
    - Endpoint to query results once complete

    **Example Usage:**
    ```bash
    # 1. Trigger research
    curl -X POST "http://localhost:8000/research/city" \\
      -H "Content-Type: application/json" \\
      -d '{"city": "Paris", "country_code": "FRA"}'

    # 2. Wait 2-3 minutes for research to complete

    # 3. Query results
    curl -X POST "http://localhost:8000/chat/query" \\
      -H "Content-Type: application/json" \\
      -d '{"city": "Paris", "country_code": "FRA"}'
    ```

    **Supported Sectors:**
    - renewable_energy (default)
    - solar_energy
    - wind_energy
    - energy_storage
    - green_buildings
    - sustainable_transport
    - waste_management
    - water_management

    **Supported Countries:**
    USA, GBR, FRA, DEU, ESP, ITA, NLD, BEL, SWE, NOR, DNK, FIN, POL, CZE,
    AUT, CHE, CAN, AUS, NZL, JPN, KOR, SGP, IND, CHN, BRA, MEX, ARG, CHL,
    ZAF, ARE, SAU
    """
)
async def trigger_city_research(
    request: CityResearchRequest,
    background_tasks: BackgroundTasks
) -> ResearchJobResponse:
    """
    Trigger AI research agent for city investment opportunities.

    This endpoint accepts the request immediately and runs research in the background.
    Results are stored in the database and can be retrieved via /chat/query.

    Args:
        request: Research parameters (city, country, sector, range)
        background_tasks: FastAPI background tasks manager

    Returns:
        ResearchJobResponse with job ID and status

    Raises:
        HTTPException: If validation fails or country code is invalid
    """
    try:
        # Validate country code
        country = ResearchService.validate_country_code(request.country_code)
        if not country:
            error_response = ErrorResponse(
                error="InvalidCountryCode",
                message=f"Invalid country code '{request.country_code}'",
                details={
                    "country_code": request.country_code,
                    "supported_codes": list(ResearchService.COUNTRY_CODES.keys())
                }
            )
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=error_response.model_dump()
            )

        # Generate job ID
        job_id = ResearchService.generate_job_id(request.city, request.country_code)

        logger.info(
            f"[JOB {job_id}] Research job accepted: "
            f"city={request.city}, country={country} ({request.country_code}), "
            f"sector={request.sector}, range={request.investment_range}"
        )

        # Queue background task
        background_tasks.add_task(
            run_research_background,
            city=request.city,
            country_code=request.country_code,
            sector=request.sector,
            investment_range=request.investment_range,
            job_id=job_id
        )

        # Build response
        response = ResearchJobResponse(
            success=True,
            message=f"Research job queued successfully for {request.city}, {country} ({request.country_code})",
            job_id=job_id,
            status="queued",
            estimated_duration_seconds=120,
            query_endpoint="/chat/query"
        )

        logger.info(
            f"[JOB {job_id}] Research queued successfully. "
            f"Estimated duration: 120 seconds"
        )

        return response

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        logger.error(
            f"Error processing research request: {str(e)}",
            exc_info=True
        )
        error_response = ErrorResponse(
            error="InternalServerError",
            message="An error occurred while processing your research request",
            details={"error_type": type(e).__name__}
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump()
        )
