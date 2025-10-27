"""Pydantic models for alerts."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class AlertQueryRequest(BaseModel):
    """Request model for /alerts/list endpoint."""

    user_id: Optional[int] = Field(
        None,
        description="Filter by user ID",
        examples=[1, 42]
    )
    alert_type: Optional[str] = Field(
        None,
        description="Alert type filter",
        examples=["city_opportunity", "funder_opportunity"]
    )
    status: Optional[str] = Field(
        None,
        description="Status filter ('active', 'paused', 'expired')",
        examples=["active", "paused"]
    )
    limit: int = Field(
        10,
        ge=1,
        le=100,
        description="Maximum number of results"
    )


class Alert(BaseModel):
    """Alert data."""

    id: int = Field(..., description="Alert ID")
    user_id: int = Field(..., description="User ID")
    alert_type: str = Field(..., description="Type of alert")
    research_id: Optional[str] = Field(None, description="Related research ID")
    title: Optional[str] = Field(None, description="Alert title")
    description: Optional[str] = Field(None, description="Alert description")
    criteria: Dict[str, Any] = Field(default_factory=dict, description="Matching criteria (JSONB)")
    status: str = Field(..., description="Alert status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        from_attributes = True


class AlertListResponse(BaseModel):
    """Response model for /alerts/list endpoint."""

    success: bool = Field(..., description="Whether the request was successful")
    data: List[Alert] = Field(default_factory=list, description="Alerts")
    count: int = Field(..., description="Number of results returned")
    message: str = Field(..., description="Human-readable message")
    query_time_ms: float = Field(..., description="Query execution time in milliseconds")
