"""Pydantic models for funding opportunities."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class FundingQueryRequest(BaseModel):
    """Request model for /funding/query endpoint."""

    funder_type: Optional[str] = Field(
        None,
        description="Funder type (e.g., 'impact_investor', 'foundation', 'venture_capital')",
        examples=["impact_investor", "foundation", "venture_capital"]
    )
    scope: Optional[str] = Field(
        None,
        description="Scope (e.g., 'city', 'national', 'regional', 'global')",
        examples=["national", "global"]
    )
    country: Optional[str] = Field(
        None,
        description="Country name or code",
        examples=["United States", "USA"]
    )
    sector: Optional[str] = Field(
        None,
        description="Sector filter",
        examples=["renewable_energy", "solar_energy"]
    )
    limit: int = Field(
        10,
        ge=1,
        le=100,
        description="Maximum number of results"
    )


class FundingOpportunity(BaseModel):
    """Funding opportunity research data."""

    id: int = Field(..., description="Unique identifier")
    funder_type: Optional[str] = Field(None, description="Type of funder")
    scope: Optional[str] = Field(None, description="Geographic scope")
    countries: Optional[List[str]] = Field(default_factory=list, description="Countries covered")
    sectors: Optional[List[str]] = Field(default_factory=list, description="Sectors of interest")
    min_investment: Optional[int] = Field(None, description="Minimum investment amount")
    max_investment: Optional[int] = Field(None, description="Maximum investment amount")
    query: str = Field(..., description="Original research query")
    research_brief: Optional[str] = Field(None, description="Executive summary")
    final_report: Optional[str] = Field(None, description="Complete research report")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    langfuse_trace_id: Optional[str] = Field(None, description="Langfuse trace identifier")

    class Config:
        from_attributes = True


class FundingQueryResponse(BaseModel):
    """Response model for /funding/query endpoint."""

    success: bool = Field(..., description="Whether the request was successful")
    data: List[FundingOpportunity] = Field(default_factory=list, description="Funding opportunities")
    count: int = Field(..., description="Number of results returned")
    message: str = Field(..., description="Human-readable message")
    query_time_ms: float = Field(..., description="Query execution time in milliseconds")
