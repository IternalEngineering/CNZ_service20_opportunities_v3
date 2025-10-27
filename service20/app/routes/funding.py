"""Funding opportunities API routes."""

import time
from fastapi import APIRouter, HTTPException
from app.database import get_connection
from app.models.funding_schemas import (
    FundingQueryRequest,
    FundingQueryResponse,
    FundingOpportunity,
)
from app.services.funding import funding_service

router = APIRouter(prefix="/funding", tags=["Funding"])


@router.post("/query", response_model=FundingQueryResponse)
async def query_funding_opportunities(request: FundingQueryRequest):
    """
    Query funding opportunities with optional filters.

    Filters:
    - funder_type: Type of funder (impact_investor, foundation, venture_capital)
    - scope: Geographic scope (city, national, regional, global)
    - country: Country name or code
    - sector: Sector filter (renewable_energy, solar_energy, etc.)
    - limit: Maximum number of results (1-100, default 10)

    Returns list of funding opportunities sorted by creation date (newest first).
    """
    start_time = time.time()

    try:
        async with get_connection() as conn:
            opportunities_data = await funding_service.query_funding_opportunities(
                connection=conn,
                funder_type=request.funder_type,
                scope=request.scope,
                country=request.country,
                sector=request.sector,
                limit=request.limit,
            )

            query_time_ms = (time.time() - start_time) * 1000

            opportunities = [FundingOpportunity(**opp) for opp in opportunities_data]

            return FundingQueryResponse(
                success=True,
                data=opportunities,
                count=len(opportunities),
                message=f"Found {len(opportunities)} funding opportunities",
                query_time_ms=query_time_ms,
            )

    except Exception as e:
        query_time_ms = (time.time() - start_time) * 1000
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "InternalServerError",
                "message": f"Failed to query funding opportunities: {str(e)}",
                "query_time_ms": query_time_ms,
            },
        )
