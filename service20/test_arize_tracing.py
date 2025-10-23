"""Test Arize Phoenix tracing with a simple LLM call.

This script tests Arize Phoenix (Arize observability) integration by running
a simple research query and verifying that traces appear in Arize.

Space ID: U3BhY2U6MjUwOk15bW0=
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

# Import Phoenix and OpenTelemetry
from phoenix.otel import register
from openinference.instrumentation.langchain import LangChainInstrumentor

# Import LangChain components
from langchain_core.messages import HumanMessage
from open_deep_research.deep_researcher import deep_researcher

# Color output
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class Fore:
        GREEN = RED = YELLOW = CYAN = MAGENTA = ""
    class Style:
        BRIGHT = RESET_ALL = ""


def setup_arize_tracing():
    """Initialize Arize Phoenix tracing with Space ID."""

    print(f"{Fore.CYAN}{'=' * 80}")
    print(f"Setting up Arize Phoenix Tracing")
    print(f"{'=' * 80}{Style.RESET_ALL}\n")

    # Arize configuration
    ARIZE_SPACE_ID = "U3BhY2U6MjUwOk15bW0="
    ARIZE_API_KEY = os.getenv("ARIZE_API_KEY")

    if not ARIZE_API_KEY:
        print(f"{Fore.RED}ERROR: ARIZE_API_KEY not found in environment variables{Style.RESET_ALL}")
        print(f"Please add ARIZE_API_KEY to your .env file")
        sys.exit(1)

    print(f"{Fore.YELLOW}Arize Configuration:{Style.RESET_ALL}")
    print(f"  Space ID: {ARIZE_SPACE_ID}")
    print(f"  API Key: {'*' * len(ARIZE_API_KEY[:4]) + ARIZE_API_KEY[:4]}...")
    print()

    # Register Phoenix with Arize
    try:
        tracer_provider = register(
            project_name="service20-research",
            endpoint="https://app.arize.com/v1/traces",
            headers={
                "space-id": ARIZE_SPACE_ID,
                "api-key": ARIZE_API_KEY
            }
        )

        print(f"{Fore.GREEN}✓ Phoenix tracer registered with Arize{Style.RESET_ALL}")

        # Instrument LangChain
        LangChainInstrumentor().instrument(tracer_provider=tracer_provider)

        print(f"{Fore.GREEN}✓ LangChain instrumented{Style.RESET_ALL}")
        print()

        return True

    except Exception as e:
        print(f"{Fore.RED}ERROR: Failed to setup Arize tracing: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        return False


async def run_simple_research_test():
    """Run a simple research query to test tracing."""

    print(f"{Fore.CYAN}{'=' * 80}")
    print(f"Running Simple Research Test")
    print(f"{'=' * 80}{Style.RESET_ALL}\n")

    # Simple test query
    test_query = """
    Research renewable energy opportunities in Copenhagen, Denmark.

    Focus on:
    1. Solar energy potential
    2. Wind energy potential
    3. Investment opportunities (€1M-€5M range)

    Provide a brief 2-paragraph summary with:
    - Key opportunities
    - Investment amounts
    - Expected ROI
    """

    print(f"{Fore.YELLOW}Test Query:{Style.RESET_ALL}")
    print(test_query)
    print()

    print(f"{Fore.YELLOW}Starting research...{Style.RESET_ALL}\n")

    try:
        # Run research with tracing
        thread_id = f"arize-test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        result = await deep_researcher.ainvoke(
            {"messages": [HumanMessage(content=test_query)]},
            config={"configurable": {"thread_id": thread_id}}
        )

        # Extract results
        final_report = result.get("final_report", "")
        research_brief = result.get("research_brief", "")

        print(f"\n{Fore.GREEN}{'=' * 80}")
        print(f"Research Completed!")
        print(f"{'=' * 80}{Style.RESET_ALL}\n")

        print(f"{Fore.CYAN}Research Brief:{Style.RESET_ALL}")
        print(f"{research_brief}\n")

        print(f"{Fore.CYAN}Report Preview (first 500 chars):{Style.RESET_ALL}")
        print(f"{final_report[:500]}...\n")

        print(f"{Fore.GREEN}✓ Research completed successfully{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✓ Traces should now be visible in Arize{Style.RESET_ALL}")
        print()

        return True

    except Exception as e:
        print(f"\n{Fore.RED}{'=' * 80}")
        print(f"Error during research: {e}")
        print(f"{'=' * 80}{Style.RESET_ALL}\n")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function."""

    print(f"\n{Fore.MAGENTA}{'=' * 80}")
    print(f"Arize Phoenix Tracing Test")
    print(f"Service20 - Open Deep Research")
    print(f"{'=' * 80}{Style.RESET_ALL}\n")

    # Step 1: Setup Arize tracing
    if not setup_arize_tracing():
        print(f"{Fore.RED}Failed to setup Arize tracing{Style.RESET_ALL}")
        sys.exit(1)

    # Step 2: Run research test
    success = await run_simple_research_test()

    # Step 3: Report results
    print(f"\n{Fore.CYAN}{'=' * 80}")
    print(f"Test Results")
    print(f"{'=' * 80}{Style.RESET_ALL}\n")

    if success:
        print(f"{Fore.GREEN}✓ All tests passed{Style.RESET_ALL}\n")
        print(f"{Fore.YELLOW}Next Steps:{Style.RESET_ALL}")
        print(f"  1. Go to Arize dashboard: https://app.arize.com")
        print(f"  2. Navigate to Space: U3BhY2U6MjUwOk15bW0=")
        print(f"  3. Look for project: service20-research")
        print(f"  4. Verify traces are appearing")
        print()
    else:
        print(f"{Fore.RED}✗ Tests failed{Style.RESET_ALL}\n")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
