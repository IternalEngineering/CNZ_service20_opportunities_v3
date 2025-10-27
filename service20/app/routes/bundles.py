"""Bundles API routes."""

import time
from fastapi import APIRouter, HTTPException
from app.database import get_connection
from app.models.bundle_schemas import (
    BundleQueryRequest,
    BundleListResponse,
    Bundle,
)
from app.services.bundles import bundle_service

router = APIRouter(prefix="/bundles", tags=["Bundles"])


@router.get("/list", response_model=BundleListResponse)
async def list_bundles(
    bundle_type: str = None,
    min_investment: int = None,
    limit: int = 10,
):
    """
    List bundles with optional filters.

    Query Parameters:
    - bundle_type: Type of bundle (regional/sectoral/mixed)
    - min_investment: Minimum total investment amount
    - limit: Maximum number of results (1-100, default 10)

    Returns list of bundles sorted by creation date (newest first).
    """
    start_time = time.time()

    # Validate request
    request = BundleQueryRequest(
        bundle_type=bundle_type,
        min_investment=min_investment,
        limit=limit,
    )

    try:
        async with get_connection() as conn:
            bundles_data = await bundle_service.query_bundles(
                connection=conn,
                bundle_type=request.bundle_type,
                min_investment=request.min_investment,
                limit=request.limit,
            )

            query_time_ms = (time.time() - start_time) * 1000

            bundles = [Bundle(**bundle) for bundle in bundles_data]

            return BundleListResponse(
                success=True,
                data=bundles,
                count=len(bundles),
                message=f"Found {len(bundles)} bundles",
                query_time_ms=query_time_ms,
            )

    except Exception as e:
        query_time_ms = (time.time() - start_time) * 1000
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "InternalServerError",
                "message": f"Failed to query bundles: {str(e)}",
                "query_time_ms": query_time_ms,
            },
        )
