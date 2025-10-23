"""Test Arize Phoenix tracing with auto-instrumentation.

This script tests the NEW Arize Phoenix account integration using the modern
register() function with auto_instrument=True for automatic LangChain tracing.

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

# Import Phoenix for auto-instrumentation
from phoenix.otel import register

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
    """Initialize Arize Phoenix tracing with auto-instrumentation."""

    print(f"{Fore.CYAN}{'=' * 80}")
    print(f"Setting up Arize Phoenix Tracing (Auto-Instrumentation)")
    print(f"{'=' * 80}{Style.RESET_ALL}\n")

    # Phoenix configuration from environment
    PHOENIX_API_KEY = os.getenv("PHOENIX_API_KEY")
    PHOENIX_COLLECTOR_ENDPOINT = os.getenv("PHOENIX_COLLECTOR_ENDPOINT", "https://app.phoenix.arize.com")
    PHOENIX_SPACE_ID = os.getenv("PHOENIX_SPACE_ID", "U3BhY2U6MjUzOlA5amY=")

    if not PHOENIX_API_KEY:
        print(f"{Fore.RED}ERROR: PHOENIX_API_KEY not found in environment variables{Style.RESET_ALL}")
        print(f"Please add PHOENIX_API_KEY to your .env file")
        return None

    print(f"{Fore.YELLOW}Phoenix Configuration:{Style.RESET_ALL}")
    print(f"  Space ID: {PHOENIX_SPACE_ID}")
    print(f"  Collector Endpoint: {PHOENIX_COLLECTOR_ENDPOINT}")
    print(f"  API Key: {'*' * 20}{PHOENIX_API_KEY[-8:]}...")
    print()

    try:
        # Register Phoenix with auto-instrumentation
        # This will automatically trace all LangChain operations
        tracer_provider = register(
            project_name="service20-research-test",
            auto_instrument=True,  # Automatically instrument LangChain
        )

        print(f"{Fore.GREEN}[OK] Phoenix tracer registered with auto-instrumentation{Style.RESET_ALL}")
        print(f"{Fore.GREEN}[OK] All LangChain operations will be automatically traced{Style.RESET_ALL}")
        print()

        return tracer_provider

    except Exception as e:
        print(f"{Fore.RED}ERROR: Failed to setup Phoenix tracing: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        return None


async def run_simple_llm_test():
    """Run a simple LLM call to test Phoenix tracing."""

    print(f"{Fore.CYAN}{'=' * 80}")
    print(f"Running Simple LLM Test with Phoenix Tracing")
    print(f"{'=' * 80}{Style.RESET_ALL}\n")

    # Simple test query
    test_query = """What are the top 3 renewable energy opportunities in Copenhagen, Denmark?
    Provide a brief 3-sentence answer."""

    print(f"{Fore.YELLOW}Test Query:{Style.RESET_ALL}")
    print(f"{test_query}\n")

    print(f"{Fore.YELLOW}Calling OpenAI GPT-4o-mini...{Style.RESET_ALL}\n")

    try:
        # Initialize LLM (will be automatically traced by Phoenix)
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

        # Call LLM - Phoenix will automatically capture this
        response = llm.invoke([HumanMessage(content=test_query)])

        # Extract response
        answer = response.content

        print(f"\n{Fore.GREEN}{'=' * 80}")
        print(f"LLM Response Received!")
        print(f"{'=' * 80}{Style.RESET_ALL}\n")

        print(f"{Fore.CYAN}Response:{Style.RESET_ALL}")
        print(f"{answer}\n")

        print(f"{Fore.GREEN}[OK] LLM call completed successfully{Style.RESET_ALL}")
        print(f"{Fore.GREEN}[OK] Trace automatically sent to Phoenix{Style.RESET_ALL}")
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
    print(f"Arize Phoenix Tracing Test")
    print(f"Service20 - Auto-Instrumentation Test")
    print(f"{'=' * 80}{Style.RESET_ALL}\n")

    # Step 1: Setup Phoenix tracing
    tracer_provider = setup_phoenix_tracing()
    if not tracer_provider:
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
        print(f"  1. Go to Phoenix dashboard: https://app.phoenix.arize.com")
        print(f"  2. Navigate to your space: U3BhY2U6MjUzOlA5amY=")
        print(f"  3. Look for project: service20-research-test")
        print(f"  4. Verify traces are appearing (may take 10-30 seconds)")
        print(f"  5. You should see:")
        print(f"     - LLM calls to OpenAI GPT-4o-mini")
        print(f"     - Input prompts and output responses")
        print(f"     - Token usage and latency metrics")
        print()
    else:
        print(f"{Fore.RED}[FAIL] Tests failed{Style.RESET_ALL}\n")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
