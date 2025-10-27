"""Opportunity matches API routes."""

import time
from fastapi import APIRouter, HTTPException
from app.database import get_connection
from app.models.match_schemas import (
    MatchQueryRequest,
    MatchListResponse,
    OpportunityMatch,
)
from app.services.matches import match_service

router = APIRouter(prefix="/matches", tags=["Matches"])


@router.get("/list", response_model=MatchListResponse)
async def list_matches(
    match_type: str = None,
    confidence_level: str = None,
    status: str = None,
    limit: int = 10,
):
    """
    List opportunity matches with optional filters.

    Query Parameters:
    - match_type: Type of match (single/bundled)
    - confidence_level: Confidence level (high/medium/low)
    - status: Match status (proposed/reviewed/accepted/rejected)
    - limit: Maximum number of results (1-100, default 10)

    Returns list of matches sorted by creation date (newest first).
    """
    start_time = time.time()

    # Validate request
    request = MatchQueryRequest(
        match_type=match_type,
        confidence_level=confidence_level,
        status=status,
        limit=limit,
    )

    try:
        async with get_connection() as conn:
            matches_data = await match_service.query_matches(
                connection=conn,
                match_type=request.match_type,
                confidence_level=request.confidence_level,
                status=request.status,
                limit=request.limit,
            )

            query_time_ms = (time.time() - start_time) * 1000

            matches = [OpportunityMatch(**match) for match in matches_data]

            return MatchListResponse(
                success=True,
                data=matches,
                count=len(matches),
                message=f"Found {len(matches)} opportunity matches",
                query_time_ms=query_time_ms,
            )

    except Exception as e:
        query_time_ms = (time.time() - start_time) * 1000
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "InternalServerError",
                "message": f"Failed to query matches: {str(e)}",
                "query_time_ms": query_time_ms,
            },
        )
