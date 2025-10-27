"""Pydantic models for bundles."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class BundleQueryRequest(BaseModel):
    """Request model for /bundles/list endpoint."""

    bundle_type: Optional[str] = Field(
        None,
        description="Bundle type filter",
        examples=["regional", "sectoral", "mixed"]
    )
    min_investment: Optional[int] = Field(
        None,
        description="Minimum total investment amount",
        examples=[1000000, 5000000]
    )
    limit: int = Field(
        10,
        ge=1,
        le=100,
        description="Maximum number of results"
    )


class Bundle(BaseModel):
    """Bundle data."""

    bundle_id: str = Field(..., description="Unique bundle identifier")
    bundle_type: str = Field(..., description="Type of bundle")
    opportunity_ids: List[int] = Field(default_factory=list, description="IDs of bundled opportunities")
    total_investment: Optional[int] = Field(None, description="Total investment amount")
    total_carbon_impact: Optional[float] = Field(None, description="Total CO2 reduction (tons/year)")
    geographic_coverage: Optional[List[str]] = Field(default_factory=list, description="Geographic regions")
    financial_analysis: Optional[Dict[str, Any]] = Field(None, description="Financial analysis (JSONB)")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        from_attributes = True


class BundleListResponse(BaseModel):
    """Response model for /bundles/list endpoint."""

    success: bool = Field(..., description="Whether the request was successful")
    data: List[Bundle] = Field(default_factory=list, description="Bundles")
    count: int = Field(..., description="Number of results returned")
    message: str = Field(..., description="Human-readable message")
    query_time_ms: float = Field(..., description="Query execution time in milliseconds")
