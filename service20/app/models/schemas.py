"""Pydantic models for request/response validation."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator


class ChatQueryRequest(BaseModel):
    """Request model for /chat/query endpoint."""

    city: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="City name (e.g., 'Paris', 'London', 'New York')",
        examples=["Paris", "London", "Tokyo"]
    )
    country_code: str = Field(
        ...,
        min_length=2,
        max_length=3,
        description="ISO 3166-1 alpha-3 country code (e.g., 'FRA', 'GBR', 'USA')",
        examples=["FRA", "GBR", "USA"]
    )

    @field_validator('country_code')
    @classmethod
    def uppercase_country_code(cls, v: str) -> str:
        """Convert country code to uppercase."""
        return v.upper()

    @field_validator('city')
    @classmethod
    def strip_city(cls, v: str) -> str:
        """Strip whitespace from city name."""
        return v.strip()


class InvestmentOpportunity(BaseModel):
    """Investment opportunity research data."""

    id: int = Field(..., description="Unique identifier")
    city: Optional[str] = Field(None, description="City name")
    country: Optional[str] = Field(None, description="Country name")
    country_code: Optional[str] = Field(None, description="ISO 3166-1 alpha-3 country code")
    sector: Optional[str] = Field(None, description="Primary sector")
    query: str = Field(..., description="Original research query")
    research_brief: Optional[str] = Field(None, description="Executive summary of research")
    final_report: Optional[str] = Field(None, description="Complete research report")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    notes: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Research notes")
    research_iterations: Optional[int] = Field(0, description="Number of research iterations")
    tool_calls_count: Optional[int] = Field(0, description="Number of tool calls made")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    langfuse_trace_id: Optional[str] = Field(None, description="Langfuse trace identifier")

    class Config:
        """Pydantic configuration."""
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "city": "Paris",
                "country": "France",
                "country_code": "FRA",
                "sector": "renewable_energy",
                "query": "Research Net Zero investment opportunities in Paris, France",
                "research_brief": "Paris offers significant renewable energy investment opportunities...",
                "final_report": "# Investment Opportunities in Paris\n\n## Executive Summary\n...",
                "metadata": {"region": "Western Europe"},
                "notes": [{"finding": "Strong municipal support"}],
                "research_iterations": 3,
                "tool_calls_count": 15,
                "created_at": "2025-01-27T10:30:00Z",
                "langfuse_trace_id": "trace_abc123"
            }
        }


class ChatQueryResponse(BaseModel):
    """Response model for /chat/query endpoint."""

    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[InvestmentOpportunity] = Field(None, description="Investment opportunity data")
    message: str = Field(..., description="Human-readable message")
    query_time_ms: float = Field(..., description="Query execution time in milliseconds")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "id": 1,
                    "city": "Paris",
                    "country": "France",
                    "country_code": "FRA",
                    "sector": "renewable_energy",
                    "query": "Research Net Zero investment opportunities in Paris, France",
                    "research_brief": "Paris offers significant renewable energy investment opportunities...",
                    "created_at": "2025-01-27T10:30:00Z"
                },
                "message": "Investment opportunity found for Paris, FRA",
                "query_time_ms": 45.32
            }
        }


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Service status")
    database: bool = Field(..., description="Database connection status")
    timestamp: datetime = Field(..., description="Current timestamp")
    version: str = Field(..., description="API version")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "database": True,
                "timestamp": "2025-01-27T10:30:00Z",
                "version": "1.0.0"
            }
        }


class ErrorResponse(BaseModel):
    """Error response model."""

    success: bool = Field(False, description="Always False for errors")
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "NotFound",
                "message": "No investment opportunity found for city 'Tokyo' and country code 'JPN'",
                "details": {"city": "Tokyo", "country_code": "JPN"}
            }
        }
