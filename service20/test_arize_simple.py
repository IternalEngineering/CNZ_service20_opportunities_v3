"""Simple Arize test using OpenTelemetry directly without Phoenix."""

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


def setup_arize_tracing_simple():
    """Setup OpenTelemetry with Arize OTLP endpoint."""

    print(f"{Fore.CYAN}{'=' * 80}")
    print(f"Setting up Arize Tracing (OpenTelemetry)")
    print(f"{'=' * 80}{Style.RESET_ALL}\n")

    # Arize configuration
    ARIZE_SPACE_ID = os.getenv("ARIZE_SPACE_ID", "U3BhY2U6MjUwOk15bW0=")
    ARIZE_API_KEY = os.getenv("ARIZE_API_KEY")

    if not ARIZE_API_KEY:
        print(f"{Fore.RED}ERROR: ARIZE_API_KEY not found in environment variables{Style.RESET_ALL}")
        return False

    print(f"{Fore.YELLOW}Arize Configuration:{Style.RESET_ALL}")
    print(f"  Space ID: {ARIZE_SPACE_ID}")
    print(f"  API Key: {'*' * 20}{ARIZE_API_KEY[-8:]}...")
    print()

    try:
        # Create resource with service info
        resource = Resource.create({
            "service.name": "service20-research",
            "service.version": "1.0.0",
        })

        # Create tracer provider
        tracer_provider = TracerProvider(resource=resource)

        # Create OTLP exporter for Arize
        # Correct endpoint: https://otlp.arize.com/v1/traces (HTTP)
        # Try using Authorization Bearer token format for JWT
        otlp_exporter = OTLPSpanExporter(
            endpoint="https://otlp.arize.com/v1/traces",
            headers={
                "authorization": f"Bearer {ARIZE_API_KEY}",
                "arize-space-id": ARIZE_SPACE_ID,
            }
        )

        # Add span processor
        span_processor = BatchSpanProcessor(otlp_exporter)
        tracer_provider.add_span_processor(span_processor)

        # Set as global tracer provider
        trace.set_tracer_provider(tracer_provider)

        print(f"{Fore.GREEN}[OK] OpenTelemetry tracer configured with Arize{Style.RESET_ALL}")
        print(f"{Fore.GREEN}[OK] Endpoint: https://otlp.arize.com/v1/traces{Style.RESET_ALL}")
        print()

        return True

    except Exception as e:
        print(f"{Fore.RED}ERROR: Failed to setup Arize tracing: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        return False


async def run_simple_llm_test():
    """Run a simple LLM call to test tracing."""

    print(f"{Fore.CYAN}{'=' * 80}")
    print(f"Running Simple LLM Test")
    print(f"{'=' * 80}{Style.RESET_ALL}\n")

    # Get tracer
    tracer = trace.get_tracer("service20.test")

    # Simple test query
    test_query = "What are the top 3 renewable energy opportunities in Copenhagen, Denmark? Provide a brief 3-sentence answer."

    print(f"{Fore.YELLOW}Test Query:{Style.RESET_ALL}")
    print(f"{test_query}\n")

    print(f"{Fore.YELLOW}Calling OpenAI GPT-4o-mini...{Style.RESET_ALL}\n")

    try:
        # Create a manual span for the entire operation
        with tracer.start_as_current_span("llm_research_test") as span:
            span.set_attribute("test.query", test_query)
            span.set_attribute("test.model", "gpt-4o-mini")
            span.set_attribute("test.timestamp", datetime.now().isoformat())

            # Initialize LLM
            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

            # Call LLM
            response = llm.invoke([HumanMessage(content=test_query)])

            # Extract response
            answer = response.content

            # Add response attributes to span
            span.set_attribute("test.response_length", len(answer))
            span.set_attribute("test.success", True)

            print(f"\n{Fore.GREEN}{'=' * 80}")
            print(f"LLM Response Received!")
            print(f"{'=' * 80}{Style.RESET_ALL}\n")

            print(f"{Fore.CYAN}Response:{Style.RESET_ALL}")
            print(f"{answer}\n")

            print(f"{Fore.GREEN}[OK] LLM call completed successfully{Style.RESET_ALL}")
            print(f"{Fore.GREEN}[OK] Trace sent to Arize{Style.RESET_ALL}")
            print()

        # Force flush spans to ensure they're sent
        trace.get_tracer_provider().force_flush()
        print(f"{Fore.GREEN}[OK] Traces flushed to Arize{Style.RESET_ALL}\n")

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
    print(f"Arize Tracing Test (OpenTelemetry Direct)")
    print(f"Service20 - Simple LLM Call")
    print(f"{'=' * 80}{Style.RESET_ALL}\n")

    # Step 1: Setup Arize tracing
    if not setup_arize_tracing_simple():
        print(f"{Fore.RED}Failed to setup Arize tracing{Style.RESET_ALL}")
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
        print(f"  1. Go to Arize dashboard: https://app.arize.com")
        print(f"  2. Navigate to Space ID: U3BhY2U6MjUwOk15bW0=")
        print(f"  3. Look for service: service20-research")
        print(f"  4. Verify traces are appearing (may take 10-30 seconds)")
        print(f"  5. You should see:")
        print(f"     - Span name: llm_research_test")
        print(f"     - Attributes: test.query, test.model, test.response_length")
        print()
    else:
        print(f"{Fore.RED}[FAIL] Tests failed{Style.RESET_ALL}\n")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
