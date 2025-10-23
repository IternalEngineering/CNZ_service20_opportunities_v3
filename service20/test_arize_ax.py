"""Test Arize AX tracing with LangChain instrumentation.

This script uses Arize AX (not Phoenix) with the EU region endpoint.

Organization: QWNjb3VudE9yZ2FuaXphdGlvbjoxNzQ6UmVJZw==
Space: U3BhY2U6MjUzOlA5amY=
Region: eu-west-1a
Dashboard: https://app.eu-west-1a.arize.com/organizations/QWNjb3VudE9yZ2FuaXphdGlvbjoxNzQ6UmVJZw==/spaces/U3BhY2U6MjUzOlA5amY=
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

# Import Arize OTEL registration
from arize.otel import register
from arize.otel.otel import Transport, Endpoint

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


def setup_arize_ax_tracing():
    """Setup Arize AX tracing using arize.otel.register()."""

    print(f"{Fore.CYAN}{'=' * 80}")
    print(f"Setting up Arize AX Tracing (EU Region)")
    print(f"{'=' * 80}{Style.RESET_ALL}\n")

    # Arize AX configuration
    ARIZE_SPACE_KEY = os.getenv("ARIZE_SPACE_KEY", "U3BhY2U6MjUzOlA5amY=")
    ARIZE_API_KEY = os.getenv("ARIZE_API_KEY")

    if not ARIZE_API_KEY:
        print(f"{Fore.RED}ERROR: ARIZE_API_KEY not found in environment variables{Style.RESET_ALL}")
        return None

    print(f"{Fore.YELLOW}Arize AX Configuration:{Style.RESET_ALL}")
    print(f"  Space Key: {ARIZE_SPACE_KEY}")
    print(f"  Endpoint: {Endpoint.ARIZE_EUROPE.value}")
    print(f"  API Key: {'*' * 20}{ARIZE_API_KEY[-8:]}...")
    print()

    try:
        # Register with Arize AX using the official method
        # Use built-in ARIZE_EUROPE endpoint and HTTP transport
        tracer_provider = register(
            space_id=ARIZE_SPACE_KEY,
            api_key=ARIZE_API_KEY,
            project_name="service20-research-test",
            endpoint=Endpoint.ARIZE_EUROPE,  # Built-in EU endpoint
            transport=Transport.HTTP,  # Explicitly use HTTP transport
        )

        print(f"{Fore.GREEN}[OK] Arize AX tracer registered{Style.RESET_ALL}")
        print(f"{Fore.GREEN}[OK] Project: service20-research-test{Style.RESET_ALL}")

        # Instrument LangChain
        LangChainInstrumentor().instrument(tracer_provider=tracer_provider)

        print(f"{Fore.GREEN}[OK] LangChain instrumented{Style.RESET_ALL}")
        print()

        return tracer_provider

    except Exception as e:
        print(f"{Fore.RED}ERROR: Failed to setup Arize AX tracing: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        return None


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
        print(f"{Fore.GREEN}[OK] Trace sent to Arize AX{Style.RESET_ALL}")
        print()

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
    print(f"Arize AX Tracing Test (EU Region)")
    print(f"Service20 - LangChain Instrumentation")
    print(f"{'=' * 80}{Style.RESET_ALL}\n")

    # Step 1: Setup Arize AX tracing
    tracer_provider = setup_arize_ax_tracing()
    if not tracer_provider:
        print(f"{Fore.RED}Failed to setup Arize AX tracing{Style.RESET_ALL}")
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
        print(f"  1. Go to Arize AX dashboard:")
        print(f"     https://app.eu-west-1a.arize.com/organizations/QWNjb3VudE9yZ2FuaXphdGlvbjoxNzQ6UmVJZw==/spaces/U3BhY2U6MjUzOlA5amY=")
        print(f"  2. Look for project: service20-research-test")
        print(f"  3. Navigate to Traces section")
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
