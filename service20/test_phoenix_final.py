"""Test Arize Phoenix tracing using direct OpenTelemetry configuration.

This script uses OpenTelemetry directly to send traces to Phoenix,
avoiding the full Phoenix package dependencies that cause conflicts.

Space ID: U3BhY2U6MjUzOlA5amY=
Account Created: 2025-10-22
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
load_dotenv()

# Import OpenTelemetry
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

# Import OpenInference instrumentation for LangChain
from openinference.instrumentation.langchain import LangChainInstrumentor

# Import LangChain components
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

# Color output
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class Fore:
        GREEN = RED = YELLOW = CYAN = MAGENTA = ""
    class Style:
        BRIGHT = RESET_ALL = ""


def setup_phoenix_tracing():
    """Setup OpenTelemetry with Phoenix OTLP endpoint."""

    print(f"{Fore.CYAN}{'=' * 80}")
    print(f"Setting up Arize Phoenix Tracing (Direct OTLP)")
    print(f"{'=' * 80}{Style.RESET_ALL}\n")

    # Phoenix configuration
    PHOENIX_API_KEY = os.getenv("PHOENIX_API_KEY")
    PHOENIX_COLLECTOR_ENDPOINT = os.getenv("PHOENIX_COLLECTOR_ENDPOINT", "https://app.phoenix.arize.com")
    PHOENIX_SPACE_ID = os.getenv("PHOENIX_SPACE_ID", "U3BhY2U6MjUzOlA5amY=")

    if not PHOENIX_API_KEY:
        print(f"{Fore.RED}ERROR: PHOENIX_API_KEY not found in environment variables{Style.RESET_ALL}")
        return False

    print(f"{Fore.YELLOW}Phoenix Configuration:{Style.RESET_ALL}")
    print(f"  Space ID: {PHOENIX_SPACE_ID}")
    print(f"  Collector Endpoint: {PHOENIX_COLLECTOR_ENDPOINT}")
    print(f"  API Key: {'*' * 20}{PHOENIX_API_KEY[-8:]}...")
    print()

    try:
        # Create resource with service info
        resource = Resource.create({
            "service.name": "service20-research-test",
            "service.version": "1.0.0",
        })

        # Create tracer provider
        tracer_provider = TracerProvider(resource=resource)

        # Create OTLP exporter for Phoenix
        # Phoenix uses /v1/traces endpoint
        # Try Bearer token format for the API key
        otlp_exporter = OTLPSpanExporter(
            endpoint=f"{PHOENIX_COLLECTOR_ENDPOINT}/v1/traces",
            headers={
                "authorization": f"Bearer {PHOENIX_API_KEY}",
            }
        )

        # Add span processor
        span_processor = BatchSpanProcessor(otlp_exporter)
        tracer_provider.add_span_processor(span_processor)

        # Set as global tracer provider
        trace.set_tracer_provider(tracer_provider)

        print(f"{Fore.GREEN}[OK] OpenTelemetry tracer configured for Phoenix{Style.RESET_ALL}")
        print(f"{Fore.GREEN}[OK] Endpoint: {PHOENIX_COLLECTOR_ENDPOINT}/v1/traces{Style.RESET_ALL}")

        # Instrument LangChain
        LangChainInstrumentor().instrument(tracer_provider=tracer_provider)

        print(f"{Fore.GREEN}[OK] LangChain instrumented{Style.RESET_ALL}")
        print()

        return True

    except Exception as e:
        print(f"{Fore.RED}ERROR: Failed to setup Phoenix tracing: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        return False


async def run_simple_llm_test():
    """Run a simple LLM call to test tracing."""

    print(f"{Fore.CYAN}{'=' * 80}")
    print(f"Running Simple LLM Test")
    print(f"{'=' * 80}{Style.RESET_ALL}\n")

    # Simple test query
    test_query = """What are the top 3 renewable energy opportunities in Copenhagen, Denmark?
    Provide a brief 3-sentence answer."""

    print(f"{Fore.YELLOW}Test Query:{Style.RESET_ALL}")
    print(f"{test_query}\n")

    print(f"{Fore.YELLOW}Calling OpenAI GPT-4o-mini...{Style.RESET_ALL}\n")

    try:
        # Initialize LLM (will be traced by LangChainInstrumentor)
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

        # Call LLM
        response = llm.invoke([HumanMessage(content=test_query)])

        # Extract response
        answer = response.content

        print(f"\n{Fore.GREEN}{'=' * 80}")
        print(f"LLM Response Received!")
        print(f"{'=' * 80}{Style.RESET_ALL}\n")

        print(f"{Fore.CYAN}Response:{Style.RESET_ALL}")
        print(f"{answer}\n")

        print(f"{Fore.GREEN}[OK] LLM call completed successfully{Style.RESET_ALL}")
        print(f"{Fore.GREEN}[OK] Trace sent to Phoenix{Style.RESET_ALL}")
        print()

        # Force flush spans to ensure they're sent
        trace.get_tracer_provider().force_flush()
        print(f"{Fore.GREEN}[OK] Traces flushed to Phoenix{Style.RESET_ALL}\n")

        return True

    except Exception as e:
        print(f"\n{Fore.RED}{'=' * 80}")
        print(f"Error during LLM call: {e}")
        print(f"{'=' * 80}{Style.RESET_ALL}\n")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function."""

    print(f"\n{Fore.MAGENTA}{'=' * 80}")
    print(f"Arize Phoenix Tracing Test (Direct OTLP)")
    print(f"Service20 - LangChain Instrumentation")
    print(f"{'=' * 80}{Style.RESET_ALL}\n")

    # Step 1: Setup Phoenix tracing
    if not setup_phoenix_tracing():
        print(f"{Fore.RED}Failed to setup Phoenix tracing{Style.RESET_ALL}")
        sys.exit(1)

    # Step 2: Run LLM test
    success = await run_simple_llm_test()

    # Step 3: Report results
    print(f"\n{Fore.CYAN}{'=' * 80}")
    print(f"Test Results")
    print(f"{'=' * 80}{Style.RESET_ALL}\n")

    if success:
        print(f"{Fore.GREEN}[OK] All tests passed{Style.RESET_ALL}\n")
        print(f"{Fore.YELLOW}Next Steps:{Style.RESET_ALL}")
        phoenix_endpoint = os.getenv("PHOENIX_COLLECTOR_ENDPOINT", "https://app.phoenix.arize.com")
        space_id = os.getenv("PHOENIX_SPACE_ID", "U3BhY2U6MjUzOlA5amY=")
        print(f"  1. Go to Phoenix dashboard: {phoenix_endpoint}")
        print(f"  2. Navigate to your space (Space ID: {space_id})")
        print(f"  3. Look for project: service20-research-test")
        print(f"  4. Verify traces are appearing (may take 10-30 seconds)")
        print(f"  5. You should see:")
        print(f"     - LLM calls to OpenAI GPT-4o-mini")
        print(f"     - Input prompts and output responses")
        print(f"     - Token usage and latency metrics")
        print(f"     - Span names from LangChain instrumentation")
        print()
    else:
        print(f"{Fore.RED}[FAIL] Tests failed{Style.RESET_ALL}\n")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
