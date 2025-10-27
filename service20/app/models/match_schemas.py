"""Pydantic models for opportunity matches."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class MatchQueryRequest(BaseModel):
    """Request model for /matches/list endpoint."""

    match_type: Optional[str] = Field(
        None,
        description="Match type filter ('single' or 'bundled')",
        examples=["single", "bundled"]
    )
    confidence_level: Optional[str] = Field(
        None,
        description="Confidence level filter ('high', 'medium', 'low')",
        examples=["high", "medium"]
    )
    status: Optional[str] = Field(
        None,
        description="Status filter ('proposed', 'reviewed', 'accepted', 'rejected')",
        examples=["proposed", "accepted"]
    )
    limit: int = Field(
        10,
        ge=1,
        le=100,
        description="Maximum number of results"
    )


class OpportunityMatch(BaseModel):
    """Opportunity match data."""

    match_id: str = Field(..., description="Unique match identifier")
    match_type: str = Field(..., description="Type of match (single/bundled)")
    compatibility_score: float = Field(..., description="Compatibility score (0-100)")
    confidence_level: str = Field(..., description="Confidence level (high/medium/low)")
    status: str = Field(..., description="Match status")
    opportunities_data: List[Dict[str, Any]] = Field(default_factory=list, description="Opportunity details")
    funders_data: List[Dict[str, Any]] = Field(default_factory=list, description="Funder details")
    bundle_metrics: Optional[Dict[str, Any]] = Field(None, description="Bundle metrics if bundled")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        from_attributes = True


class MatchListResponse(BaseModel):
    """Response model for /matches/list endpoint."""

    success: bool = Field(..., description="Whether the request was successful")
    data: List[OpportunityMatch] = Field(default_factory=list, description="Matches")
    count: int = Field(..., description="Number of results returned")
    message: str = Field(..., description="Human-readable message")
    query_time_ms: float = Field(..., description="Query execution time in milliseconds")
