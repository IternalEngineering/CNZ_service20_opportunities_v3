"""Chat endpoint for querying investment opportunities."""

import logging
import time
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from ..models import ChatQueryRequest, ChatQueryResponse, InvestmentOpportunity, ErrorResponse
from ..database import get_connection
from ..services import InvestmentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])
investment_service = InvestmentService()


@router.post(
    "/query",
    response_model=ChatQueryResponse,
    responses={
        200: {
            "description": "Investment opportunity found",
            "model": ChatQueryResponse
        },
        404: {
            "description": "No investment opportunity found",
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
    summary="Query investment opportunities by city and country",
    description="""
    Retrieve the most recent investment opportunity research for a given city and country.

    This endpoint returns the latest research data including:
    - Executive summary and full report
    - Sector information
    - Financial projections
    - Carbon impact metrics
    - Research metadata and tracing information

    **Parameters:**
    - `city`: City name (e.g., "Paris", "London", "New York")
    - `country_code`: ISO 3166-1 alpha-3 code (e.g., "FRA", "GBR", "USA")

    **Returns:**
    - Latest investment opportunity data with complete research report
    - Query execution time in milliseconds
    """
)
async def query_investment_opportunity(request: ChatQueryRequest) -> ChatQueryResponse:
    """
    Query the latest investment opportunity for a city and country.

    Args:
        request: Request containing city and country_code

    Returns:
        ChatQueryResponse with opportunity data or error message

    Raises:
        HTTPException: If no opportunity found or database error occurs
    """
    start_time = time.time()

    try:
        async with get_connection() as conn:
            # Query investment opportunity
            opportunity_data = await investment_service.get_latest_opportunity(
                connection=conn,
                city=request.city,
                country_code=request.country_code
            )

            query_time_ms = (time.time() - start_time) * 1000

            if opportunity_data is None:
                # No opportunity found
                error_response = ErrorResponse(
                    error="NotFound",
                    message=f"No investment opportunity found for city '{request.city}' and country code '{request.country_code}'",
                    details={
                        "city": request.city,
                        "country_code": request.country_code
                    }
                )
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content=error_response.model_dump()
                )

            # Convert to Pydantic model
            opportunity = InvestmentOpportunity(**opportunity_data)

            # Build success response
            response = ChatQueryResponse(
                success=True,
                data=opportunity,
                message=f"Investment opportunity found for {request.city}, {request.country_code}",
                query_time_ms=round(query_time_ms, 2)
            )

            logger.info(
                f"Successfully retrieved opportunity id={opportunity.id} for "
                f"city='{request.city}', country_code='{request.country_code}' "
                f"(query_time={query_time_ms:.2f}ms)"
            )

            return response

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        logger.error(f"Error processing chat query: {str(e)}", exc_info=True)
        error_response = ErrorResponse(
            error="InternalServerError",
            message="An error occurred while processing your request",
            details={"error_type": type(e).__name__}
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump()
        )
