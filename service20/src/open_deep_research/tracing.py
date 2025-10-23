"""
Multi-platform tracing initialization for Service20.

This module provides centralized tracing setup for the Service20 investment
opportunities research service. It supports multiple observability platforms:
- Arize Phoenix for LLM observability and agent workflow tracking
- Langfuse for LLM-focused tracing and cost monitoring

Usage:
    from open_deep_research.tracing import initialize_tracing, get_tracer

    # Initialize once at startup (auto-detects platform from env vars)
    initialize_tracing("service20-city-research")

    # Or explicitly choose platform
    initialize_arize_tracing("service20-city-research")
    initialize_langfuse_tracing("service20-city-research")

    # Get tracer for manual spans
    tracer = get_tracer(__name__)
    with tracer.start_as_current_span("operation_name"):
        # Your code here
        pass
"""

import os
import logging
from typing import Optional, Literal
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

# Global state
_tracer_provider: Optional[TracerProvider] = None
_is_initialized = False
_active_platform: Optional[Literal["arize", "langfuse"]] = None
_logger = logging.getLogger(__name__)


def initialize_arize_tracing(project_name: str = "service20-production") -> bool:
    """
    Initialize Arize AX tracing once at startup.

    This function sets up OpenTelemetry tracing with Arize Phoenix backend,
    including automatic instrumentation for LangChain operations.

    Args:
        project_name: Name of the project in Arize (default: "service20-production")

    Returns:
        True if initialization succeeded, False otherwise

    Note:
        - Safe to call multiple times (idempotent)
        - Requires ARIZE_SPACE_KEY and ARIZE_API_KEY environment variables
        - Falls back gracefully if credentials not found
        - Automatically instruments LangChain calls
    """
    global _tracer_provider, _is_initialized, _active_platform

    if _is_initialized:
        _logger.info(f"Tracing already initialized with {_active_platform}")
        return True

    # Check for required credentials
    ARIZE_SPACE_KEY = os.getenv("ARIZE_SPACE_KEY")
    ARIZE_API_KEY = os.getenv("ARIZE_API_KEY")

    if not ARIZE_API_KEY or not ARIZE_SPACE_KEY:
        _logger.warning(
            "Arize credentials not found in environment. "
            "Set ARIZE_SPACE_KEY and ARIZE_API_KEY to enable tracing. "
            "Running without observability."
        )
        return False

    try:
        # Import here to avoid dependency issues if arize not installed
        from arize.otel import register
        from arize.otel.otel import Transport, Endpoint
        from openinference.instrumentation.langchain import LangChainInstrumentor

        # Register with Arize (EU endpoint)
        _tracer_provider = register(
            space_id=ARIZE_SPACE_KEY,
            api_key=ARIZE_API_KEY,
            project_name=project_name,
            endpoint=Endpoint.ARIZE_EUROPE,
            transport=Transport.HTTP,
        )

        # Auto-instrument LangChain
        LangChainInstrumentor().instrument(tracer_provider=_tracer_provider)

        _is_initialized = True
        _active_platform = "arize"
        _logger.info(f"✓ Arize tracing initialized successfully")
        _logger.info(f"  Project: {project_name}")
        _logger.info(f"  Endpoint: EU (eu-west-1a)")
        _logger.info(f"  Transport: HTTP")

        return True

    except ImportError as e:
        _logger.error(
            f"Failed to import Arize dependencies: {e}. "
            "Install with: pip install arize-otel openinference-instrumentation-langchain"
        )
        return False

    except Exception as e:
        _logger.error(f"Failed to initialize Arize tracing: {e}", exc_info=True)
        return False


def initialize_langfuse_tracing(session_id: Optional[str] = None) -> bool:
    """
    Initialize Langfuse tracing once at startup.

    This function sets up Langfuse for LLM observability, cost tracking,
    and prompt management.

    Args:
        session_id: Optional session ID for grouping traces

    Returns:
        True if initialization succeeded, False otherwise

    Note:
        - Safe to call multiple times (idempotent)
        - Requires LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_BASE_URL
        - Falls back gracefully if credentials not found
        - Provides cost tracking and prompt versioning
    """
    global _tracer_provider, _is_initialized, _active_platform

    if _is_initialized:
        _logger.info(f"Tracing already initialized with {_active_platform}")
        return True

    # Check for required credentials
    LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
    LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
    LANGFUSE_BASE_URL = os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")

    if not LANGFUSE_PUBLIC_KEY or not LANGFUSE_SECRET_KEY:
        _logger.warning(
            "Langfuse credentials not found in environment. "
            "Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY to enable tracing. "
            "Running without observability."
        )
        return False

    try:
        # Import here to avoid dependency issues if langfuse not installed
        from langfuse import Langfuse
        from langfuse.callback import CallbackHandler

        # Initialize Langfuse client
        langfuse = Langfuse(
            public_key=LANGFUSE_PUBLIC_KEY,
            secret_key=LANGFUSE_SECRET_KEY,
            host=LANGFUSE_BASE_URL,
        )

        # Test connection
        langfuse.auth_check()

        _is_initialized = True
        _active_platform = "langfuse"
        _logger.info(f"✓ Langfuse tracing initialized successfully")
        _logger.info(f"  Base URL: {LANGFUSE_BASE_URL}")
        if session_id:
            _logger.info(f"  Session ID: {session_id}")

        return True

    except ImportError as e:
        _logger.error(
            f"Failed to import Langfuse dependencies: {e}. "
            "Install with: pip install langfuse"
        )
        return False

    except Exception as e:
        _logger.error(f"Failed to initialize Langfuse tracing: {e}", exc_info=True)
        return False


def initialize_tracing(project_name: str = "service20-production") -> bool:
    """
    Initialize tracing with auto-detection of available platform.

    Tries platforms in order of preference:
    1. Arize (if credentials available)
    2. Langfuse (if credentials available)
    3. No tracing (fallback)

    Args:
        project_name: Name of the project (used for Arize)

    Returns:
        True if any platform initialized successfully, False otherwise
    """
    # Try Arize first
    if os.getenv("ARIZE_API_KEY") and os.getenv("ARIZE_SPACE_KEY"):
        return initialize_arize_tracing(project_name)

    # Fallback to Langfuse
    if os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"):
        return initialize_langfuse_tracing()

    _logger.warning(
        "No observability platform credentials found. "
        "Running without tracing. "
        "Set credentials for Arize or Langfuse to enable observability."
    )
    return False


def get_tracer(name: str) -> trace.Tracer:
    """
    Get an OpenTelemetry tracer for creating manual spans.

    Args:
        name: Name of the tracer (typically __name__ of calling module)

    Returns:
        OpenTelemetry Tracer instance

    Example:
        tracer = get_tracer(__name__)
        with tracer.start_as_current_span(
            name="City Research",
            attributes={
                "city": "Paris",
                "country": "FRA",
                "sector": "renewable_energy"
            }
        ):
            # Your research logic here
            result = await deep_researcher.ainvoke(...)
    """
    return trace.get_tracer(name)


def is_tracing_enabled() -> bool:
    """
    Check if tracing has been initialized.

    Returns:
        True if tracing is active, False otherwise
    """
    return _is_initialized


def get_active_platform() -> Optional[Literal["arize", "langfuse"]]:
    """
    Get the currently active observability platform.

    Returns:
        "arize", "langfuse", or None if tracing not initialized
    """
    return _active_platform


def get_tracer_provider() -> Optional[TracerProvider]:
    """
    Get the global TracerProvider instance.

    Returns:
        TracerProvider if initialized, None otherwise
    """
    return _tracer_provider
