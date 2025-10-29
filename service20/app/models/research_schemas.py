"""Pydantic models for research endpoint request/response validation."""

from typing import Optional
from pydantic import BaseModel, Field, field_validator


class CityResearchRequest(BaseModel):
    """Request model for POST /research/city endpoint - triggers AI research agent."""

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
    sector: Optional[str] = Field(
        default="renewable_energy",
        description="Primary sector to research",
        examples=["renewable_energy", "solar_energy", "wind_energy", "energy_storage"]
    )
    investment_range: Optional[str] = Field(
        default="500000-5000000",
        description="Investment range in USD (format: min-max)",
        examples=["500000-5000000", "1000000-10000000"]
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

    @field_validator('sector')
    @classmethod
    def validate_sector(cls, v: Optional[str]) -> str:
        """Validate sector is in allowed list."""
        if v is None:
            return "renewable_energy"

        allowed_sectors = [
            "renewable_energy",
            "solar_energy",
            "wind_energy",
            "energy_storage",
            "green_buildings",
            "sustainable_transport",
            "waste_management",
            "water_management"
        ]

        if v not in allowed_sectors:
            raise ValueError(
                f"Sector must be one of: {', '.join(allowed_sectors)}"
            )
        return v

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "city": "Paris",
                "country_code": "FRA",
                "sector": "renewable_energy",
                "investment_range": "500000-5000000"
            }
        }


class ResearchJobResponse(BaseModel):
    """Response model for POST /research/city endpoint."""

    success: bool = Field(..., description="Whether the research job was accepted")
    message: str = Field(..., description="Human-readable message")
    job_id: str = Field(..., description="Unique job identifier for tracking")
    status: str = Field(..., description="Job status (queued, running, completed, failed)")
    estimated_duration_seconds: int = Field(
        default=120,
        description="Estimated time to complete research in seconds"
    )
    query_endpoint: str = Field(
        ...,
        description="Endpoint to query results once complete"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Research job queued successfully for Paris, FRA",
                "job_id": "paris-fra-20251029-142030",
                "status": "queued",
                "estimated_duration_seconds": 120,
                "query_endpoint": "/chat/query"
            }
        }
