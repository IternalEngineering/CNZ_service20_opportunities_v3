"""State definitions for the funding research agent."""

from __future__ import annotations

from typing import Annotated, Literal
from typing_extensions import TypedDict

from langgraph.graph import add_messages
from langchain_core.messages import AnyMessage
from pydantic import BaseModel, Field


class FunderMetadata(BaseModel):
    """Structured metadata for a funding opportunity."""

    name: str = Field(description="Name of the funder or funding program")
    organization: str = Field(description="Organization providing the funding")
    level: Literal["regional", "national", "global"] = Field(
        description="Geographic level of funding"
    )
    location: str = Field(description="Geographic location or coverage area")
    opportunity_type: str = Field(
        description="Type of funding (e.g., Grant, Loan, Equity, Tax Credit)"
    )
    award_range: str = Field(description="Range or amount of funding available")
    sectors: list[str] = Field(
        default_factory=list,
        description="Relevant sectors (e.g., Energy, Sustainability, Manufacturing)"
    )
    registration_details: str = Field(
        description="Application process and timing information"
    )
    eligibility: str = Field(
        default="",
        description="Eligibility criteria for applicants"
    )
    website: str = Field(default="", description="Official website or application URL")
    contact_info: str = Field(default="", description="Contact information if available")
    additional_notes: str = Field(
        default="",
        description="Additional relevant information"
    )
    source_url: str = Field(default="", description="URL where this information was found")


class ResearchState(TypedDict):
    """State for the funding research workflow."""

    messages: Annotated[list[AnyMessage], add_messages]
    project_description: str
    project_location: str
    project_sectors: list[str]
    funding_types: list[str]  # e.g., ["grant", "loan", "equity"]

    # Research progress tracking
    current_level: Literal["regional", "national", "global", "completed"]
    regional_funders: list[FunderMetadata]
    national_funders: list[FunderMetadata]
    global_funders: list[FunderMetadata]

    # Search queries and results
    search_queries: list[str]
    search_results: list[dict]

    # Final output
    final_report: str
    total_funders_found: int
