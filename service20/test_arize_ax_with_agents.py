"""Test Arize AX tracing with agent metadata and graph visualization.

This script demonstrates how to add agent metadata using graph.node.id
and graph.node.parent_id attributes for proper agent workflow visualization
in Arize AX dashboard.

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

# Import OpenTelemetry for manual span creation
from opentelemetry import trace
from opentelemetry.trace import get_tracer

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
    """Setup Arize AX tracing with agent metadata support."""

    print(f"{Fore.CYAN}{'=' * 80}")
    print(f"Setting up Arize AX Tracing with Agent Metadata (EU Region)")
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
            project_name="service20-agent-workflow",
            endpoint=Endpoint.ARIZE_EUROPE,  # Built-in EU endpoint
            transport=Transport.HTTP,  # Explicitly use HTTP transport
        )

        print(f"{Fore.GREEN}[OK] Arize AX tracer registered{Style.RESET_ALL}")
        print(f"{Fore.GREEN}[OK] Project: service20-agent-workflow{Style.RESET_ALL}")

        # Instrument LangChain
        LangChainInstrumentor().instrument(tracer_provider=tracer_provider)

        print(f"{Fore.GREEN}[OK] LangChain instrumented{Style.RESET_ALL}")
        print(f"{Fore.GREEN}[OK] Agent metadata enabled{Style.RESET_ALL}")
        print()

        return tracer_provider

    except Exception as e:
        print(f"{Fore.RED}ERROR: Failed to setup Arize AX tracing: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        return None


async def run_agent_workflow_test():
    """Run a simulated agent workflow with graph metadata."""

    print(f"{Fore.CYAN}{'=' * 80}")
    print(f"Running Agent Workflow Test with Graph Metadata")
    print(f"{'=' * 80}{Style.RESET_ALL}\n")

    # Get tracer
    tracer = get_tracer(__name__)

    # Test query
    test_query = """What are the top 3 renewable energy opportunities in Copenhagen, Denmark?
    Provide a brief 3-sentence answer."""

    print(f"{Fore.YELLOW}Test Query:{Style.RESET_ALL}")
    print(f"{test_query}\n")

    print(f"{Fore.YELLOW}Starting Agent Workflow...{Style.RESET_ALL}\n")

    try:
        # Main workflow span (top-level coordinator)
        with tracer.start_as_current_span(
            name="Research Workflow",
            attributes={
                "graph.node.id": "research_workflow",
                "workflow.type": "research",
                "workflow.version": "1.0.0",
            }
        ) as workflow_span:

            print(f"{Fore.CYAN}[Workflow] Research Workflow started{Style.RESET_ALL}")

            # Query planning agent
            with tracer.start_as_current_span(
                name="Query Planner Agent",
                attributes={
                    "graph.node.id": "query_planner",
                    "graph.node.parent_id": "research_workflow",
                    "agent.role": "planner",
                    "agent.task": "analyze_query",
                }
            ) as planner_span:
                print(f"{Fore.YELLOW}  [Query Planner] Analyzing query...{Style.RESET_ALL}")
                planner_span.set_attribute("query.input", test_query)
                planner_span.set_attribute("query.complexity", "medium")
                planner_span.set_attribute("query.topics", "renewable_energy,copenhagen,opportunities")
                print(f"{Fore.GREEN}  [Query Planner] Query analyzed successfully{Style.RESET_ALL}")

            # Research agent
            with tracer.start_as_current_span(
                name="Research Agent",
                attributes={
                    "graph.node.id": "research_agent",
                    "graph.node.parent_id": "research_workflow",
                    "agent.role": "researcher",
                    "agent.task": "gather_information",
                }
            ) as research_span:
                print(f"{Fore.YELLOW}  [Research Agent] Calling LLM for research...{Style.RESET_ALL}")

                # Initialize LLM (will be traced by LangChainInstrumentor)
                llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

                # Call LLM
                response = llm.invoke([HumanMessage(content=test_query)])
                answer = response.content

                research_span.set_attribute("research.model", "gpt-4o-mini")
                research_span.set_attribute("research.response_length", len(answer))
                research_span.set_attribute("research.success", True)
                print(f"{Fore.GREEN}  [Research Agent] Research completed{Style.RESET_ALL}")

            # Synthesis agent
            with tracer.start_as_current_span(
                name="Synthesis Agent",
                attributes={
                    "graph.node.id": "synthesis_agent",
                    "graph.node.parent_id": "research_workflow",
                    "agent.role": "synthesizer",
                    "agent.task": "format_response",
                }
            ) as synthesis_span:
                print(f"{Fore.YELLOW}  [Synthesis Agent] Formatting response...{Style.RESET_ALL}")
                synthesis_span.set_attribute("synthesis.format", "structured")
                synthesis_span.set_attribute("synthesis.output_length", len(answer))
                print(f"{Fore.GREEN}  [Synthesis Agent] Response formatted{Style.RESET_ALL}")

            # Set workflow completion attributes
            workflow_span.set_attribute("workflow.status", "completed")
            workflow_span.set_attribute("workflow.agents_used", 3)
            workflow_span.set_attribute("workflow.success", True)

        print(f"\n{Fore.GREEN}{'=' * 80}")
        print(f"Agent Workflow Completed!")
        print(f"{'=' * 80}{Style.RESET_ALL}\n")

        print(f"{Fore.CYAN}LLM Response:{Style.RESET_ALL}")
        print(f"{answer}\n")

        print(f"{Fore.GREEN}[OK] Agent workflow executed successfully{Style.RESET_ALL}")
        print(f"{Fore.GREEN}[OK] Graph metadata sent to Arize AX{Style.RESET_ALL}")
        print()

        return True

    except Exception as e:
        print(f"\n{Fore.RED}{'=' * 80}")
        print(f"Error during agent workflow: {e}")
        print(f"{'=' * 80}{Style.RESET_ALL}\n")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function."""

    print(f"\n{Fore.MAGENTA}{'=' * 80}")
    print(f"Arize AX Agent Metadata Test (EU Region)")
    print(f"Service20 - Agent Workflow with Graph Visualization")
    print(f"{'=' * 80}{Style.RESET_ALL}\n")

    # Step 1: Setup Arize AX tracing
    tracer_provider = setup_arize_ax_tracing()
    if not tracer_provider:
        print(f"{Fore.RED}Failed to setup Arize AX tracing{Style.RESET_ALL}")
        sys.exit(1)

    # Step 2: Run agent workflow test
    success = await run_agent_workflow_test()

    # Step 3: Report results
    print(f"\n{Fore.CYAN}{'=' * 80}")
    print(f"Test Results")
    print(f"{'=' * 80}{Style.RESET_ALL}\n")

    if success:
        print(f"{Fore.GREEN}[OK] All tests passed{Style.RESET_ALL}\n")
        print(f"{Fore.YELLOW}Next Steps:{Style.RESET_ALL}")
        print(f"  1. Go to Arize AX dashboard:")
        print(f"     https://app.eu-west-1a.arize.com/organizations/QWNjb3VudE9yZ2FuaXphdGlvbjoxNzQ6UmVJZw==/spaces/U3BhY2U6MjUzOlA5amY=")
        print(f"  2. Look for project: service20-agent-workflow")
        print(f"  3. Navigate to Agents tab to see workflow visualization")
        print(f"  4. You should see a graph showing:")
        print(f"     - Research Workflow (top-level)")
        print(f"       - Query Planner Agent")
        print(f"       - Research Agent (with LLM call)")
        print(f"       - Synthesis Agent")
        print(f"  5. Each node will show:")
        print(f"     - Agent role and task")
        print(f"     - Input/output information")
        print(f"     - Performance metrics")
        print()
    else:
        print(f"{Fore.RED}[FAIL] Tests failed{Style.RESET_ALL}\n")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
