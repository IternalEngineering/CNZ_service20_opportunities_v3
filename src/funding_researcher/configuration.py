"""Configuration for the funding research agent."""

from __future__ import annotations

import os
from enum import Enum
from typing import Any, Literal, Optional

from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field


class SearchAPI(Enum):
    """Enumeration of available search API providers."""

    TAVILY = "tavily"
    EXA = "exa"
    DUCKDUCKGO = "duckduckgo"


class Configuration(BaseModel):
    """Main configuration for the funding research agent."""

    # API Keys (loaded from environment)
    openai_api_key: str = Field(
        default="",
        metadata={
            "x_oap_ui_config": {
                "type": "text",
                "description": "OpenAI API key"
            }
        }
    )
    anthropic_api_key: str = Field(
        default="",
        metadata={
            "x_oap_ui_config": {
                "type": "text",
                "description": "Anthropic API key"
            }
        }
    )
    tavily_api_key: str = Field(
        default="",
        metadata={
            "x_oap_ui_config": {
                "type": "text",
                "description": "Tavily API key for web search"
            }
        }
    )
    exa_api_key: str = Field(
        default="",
        metadata={
            "x_oap_ui_config": {
                "type": "text",
                "description": "Exa API key for web search"
            }
        }
    )

    # Model Configuration
    model_provider: Literal["openai", "anthropic", "google", "groq"] = Field(
        default="openai",
        metadata={
            "x_oap_ui_config": {
                "type": "select",
                "default": "openai",
                "description": "LLM provider to use",
                "options": [
                    {"label": "OpenAI", "value": "openai"},
                    {"label": "Anthropic", "value": "anthropic"},
                    {"label": "Google", "value": "google"},
                    {"label": "Groq", "value": "groq"},
                ]
            }
        }
    )
    model_name: str = Field(
        default="gpt-4o-mini",
        metadata={
            "x_oap_ui_config": {
                "type": "text",
                "default": "gpt-4o-mini",
                "description": "Model name to use for all LLM calls"
            }
        }
    )
    temperature: float = Field(
        default=0.0,
        metadata={
            "x_oap_ui_config": {
                "type": "slider",
                "default": 0.0,
                "min": 0.0,
                "max": 2.0,
                "step": 0.1,
                "description": "Temperature for model responses"
            }
        }
    )
    max_tokens: int = Field(
        default=4000,
        metadata={
            "x_oap_ui_config": {
                "type": "number",
                "default": 4000,
                "description": "Maximum tokens in model response"
            }
        }
    )

    # Search Configuration
    search_api: SearchAPI = Field(
        default=SearchAPI.TAVILY,
        metadata={
            "x_oap_ui_config": {
                "type": "select",
                "default": "tavily",
                "description": "Search API to use for research",
                "options": [
                    {"label": "Tavily", "value": SearchAPI.TAVILY.value},
                    {"label": "Exa", "value": SearchAPI.EXA.value},
                    {"label": "DuckDuckGo", "value": SearchAPI.DUCKDUCKGO.value},
                ]
            }
        }
    )
    max_results_per_query: int = Field(
        default=10,
        metadata={
            "x_oap_ui_config": {
                "type": "slider",
                "default": 10,
                "min": 5,
                "max": 20,
                "step": 1,
                "description": "Maximum search results to retrieve per query"
            }
        }
    )
    max_concurrent_searches: int = Field(
        default=3,
        metadata={
            "x_oap_ui_config": {
                "type": "slider",
                "default": 3,
                "min": 1,
                "max": 10,
                "step": 1,
                "description": "Maximum number of concurrent search operations"
            }
        }
    )

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "Configuration":
        """Create a Configuration instance from a RunnableConfig."""
        configurable = config.get("configurable", {}) if config else {}
        field_names = list(cls.model_fields.keys())
        values: dict[str, Any] = {
            field_name: os.environ.get(field_name.upper(), configurable.get(field_name))
            for field_name in field_names
        }
        return cls(**{k: v for k, v in values.items() if v is not None})

    def get_model(self):
        """Get configured language model instance."""
        if self.model_provider == "openai":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=self.model_name,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                api_key=self.openai_api_key or os.environ.get("OPENAI_API_KEY", ""),
            )
        elif self.model_provider == "anthropic":
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(
                model=self.model_name,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                api_key=self.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY", ""),
            )
        elif self.model_provider == "google":
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model=self.model_name,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                google_api_key=os.environ.get("GOOGLE_API_KEY", ""),
            )
        elif self.model_provider == "groq":
            from langchain_groq import ChatGroq
            return ChatGroq(
                model=self.model_name,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                api_key=os.environ.get("GROQ_API_KEY", ""),
            )
        else:
            raise ValueError(f"Unsupported model provider: {self.model_provider}")

    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True
