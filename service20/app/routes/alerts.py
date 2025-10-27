"""Alerts API routes."""

import time
from fastapi import APIRouter, HTTPException
from app.database import get_connection
from app.models.alert_schemas import (
    AlertQueryRequest,
    AlertListResponse,
    Alert,
)
from app.services.alerts import alert_service

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("/list", response_model=AlertListResponse)
async def list_alerts(
    user_id: int = None,
    alert_type: str = None,
    status: str = None,
    limit: int = 10,
):
    """
    List alerts with optional filters.

    Query Parameters:
    - user_id: Filter by user ID
    - alert_type: Type of alert (city_opportunity/funder_opportunity)
    - status: Alert status (active/paused/expired)
    - limit: Maximum number of results (1-100, default 10)

    Returns list of alerts sorted by creation date (newest first).
    """
    start_time = time.time()

    # Validate request
    request = AlertQueryRequest(
        user_id=user_id,
        alert_type=alert_type,
        status=status,
        limit=limit,
    )

    try:
        async with get_connection() as conn:
            alerts_data = await alert_service.query_alerts(
                connection=conn,
                user_id=request.user_id,
                alert_type=request.alert_type,
                status=request.status,
                limit=request.limit,
            )

            query_time_ms = (time.time() - start_time) * 1000

            alerts = [Alert(**alert) for alert in alerts_data]

            return AlertListResponse(
                success=True,
                data=alerts,
                count=len(alerts),
                message=f"Found {len(alerts)} alerts",
                query_time_ms=query_time_ms,
            )

    except Exception as e:
        query_time_ms = (time.time() - start_time) * 1000
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "InternalServerError",
                "message": f"Failed to query alerts: {str(e)}",
                "query_time_ms": query_time_ms,
            },
        )
