"""Test Deep Researcher with database access and Langfuse tracing."""

import sys
import os
import json
import argparse
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from langfuse import Langfuse
import asyncpg

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

# Load environment variables
load_dotenv()

async def save_to_database(query: str, result: dict, langfuse_trace_id: str = None):
    """Save research results to the service20_investment_opportunities table."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("[WARNING] DATABASE_URL not set, skipping database save")
        return None

    conn = await asyncpg.connect(database_url)

    try:
        # Extract data from result
        final_message = result["messages"][-1] if result.get("messages") else None
        final_report = final_message.content if final_message and hasattr(final_message, 'content') else str(final_message)
        research_brief = result.get("research_brief", "")

        # Track tool usage
        db_tools_used = []
        web_tools_used = []
        tool_calls_count = 0

        for msg in result.get("messages", []):
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    tool_calls_count += 1
                    tool_name = tool_call.get("name", "unknown")
                    if tool_name in ['search_opportunities', 'get_database_schema',
                                    'query_esg_metrics', 'execute_readonly_query', 'get_opportunity_details']:
                        if tool_name not in db_tools_used:
                            db_tools_used.append(tool_name)
                    else:
                        if tool_name not in web_tools_used:
                            web_tools_used.append(tool_name)

        # Insert into database
        insert_query = """
        INSERT INTO service20_investment_opportunities
            (query, research_brief, final_report, tool_calls_count,
             database_tools_used, web_tools_used, langfuse_trace_id, metadata)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        RETURNING id;
        """

        metadata = {
            "total_messages": len(result.get("messages", [])),
            "has_research_brief": bool(research_brief),
            "db_tool_count": len(db_tools_used),
            "web_tool_count": len(web_tools_used)
        }

        record_id = await conn.fetchval(
            insert_query,
            query,
            research_brief,
            final_report,
            tool_calls_count,
            db_tools_used,
            web_tools_used,
            langfuse_trace_id,
            json.dumps(metadata)
        )

        print(f"[OK] Research saved to database with ID: {record_id}")
        return record_id

    except Exception as e:
        print(f"[ERROR] Failed to save to database: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        await conn.close()

async def test_researcher(query: str):
    """Run deep researcher with Langfuse tracing."""

    print("=" * 80)
    print("Deep Researcher + Database Test with Langfuse Tracing")
    print("=" * 80)
    print()

    # Initialize Langfuse
    print("1. Initializing Langfuse...")
    public_key = os.getenv('LANGFUSE_PUBLIC_KEY')
    secret_key = os.getenv('LANGFUSE_SECRET_KEY')
    host = os.getenv('LANGFUSE_BASE_URL', 'https://cloud.langfuse.com')

    if not public_key or not secret_key:
        print("[ERROR] Langfuse credentials not found in .env")
        return False

    langfuse = Langfuse(
        public_key=public_key,
        secret_key=secret_key,
        host=host
    )
    print(f"[OK] Langfuse initialized: {host}")
    print()

    # Test query
    print(f"[QUERY] {query}")
    print()

    # Create a trace with context manager
    print("2. Creating Langfuse trace...")
    with langfuse.start_as_current_span(
        name="deep_researcher_database_query",
        input={"query": query},
        metadata={
            "test_type": "database_integration",
            "tools_available": [
                "search_opportunities",
                "get_database_schema",
                "query_esg_metrics",
                "execute_readonly_query",
                "tavily_search"
            ]
        }
    ) as main_span:

        print("[OK] Trace created")
        print()

        try:
            print("3. Loading Deep Researcher...")
            from src.open_deep_research.deep_researcher import deep_researcher

            print("[OK] Deep Researcher loaded")
            print("[INFO] Starting research with database tools...")
            print()

            # Run the researcher with allow_clarification=False to skip clarification
            result = await deep_researcher.ainvoke(
                {"messages": [{"role": "user", "content": query}]},
                config={"configurable": {"allow_clarification": False}}
            )

            print("=" * 80)
            print("[RESULT] Research Result")
            print("=" * 80)
            print()

            # Extract the final message
            if result and "messages" in result:
                final_message = result["messages"][-1]
                response_content = final_message.content if hasattr(final_message, 'content') else str(final_message)

                print(response_content)
                print()

                # Update span with output
                langfuse.update_current_span(
                    output={"response": response_content}
                )
            else:
                print("No response generated")
                langfuse.update_current_span(
                    output={"error": "No response"}
                )

            print("=" * 80)

            # Check if database tools were used
            if result and "messages" in result:
                tool_calls = []
                for msg in result["messages"]:
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        for tool_call in msg.tool_calls:
                            tool_calls.append({
                                "tool": tool_call.get("name", "unknown"),
                                "args": tool_call.get("args", {})
                            })

                if tool_calls:
                    print("[INFO] Tools Used:")
                    db_tools_used = []
                    web_tools_used = []

                    for i, tc in enumerate(tool_calls, 1):
                        tool_name = tc['tool']
                        if tool_name in ['search_opportunities', 'get_database_schema',
                                        'query_esg_metrics', 'execute_readonly_query']:
                            db_tools_used.append(tool_name)
                            print(f"  {i}. [DATABASE] {tool_name}")
                        else:
                            web_tools_used.append(tool_name)
                            print(f"  {i}. [WEB] {tool_name}")

                        if tc['args']:
                            print(f"     Args: {json.dumps(tc['args'], indent=11)[:200]}...")

                    print()
                    print(f"[SUMMARY] Tool Usage:")
                    print(f"   Database tools: {len(db_tools_used)}")
                    print(f"   Web tools: {len(web_tools_used)}")
                    print(f"   Total tools: {len(tool_calls)}")

                    # Update span metadata
                    langfuse.update_current_span(
                        metadata={
                            "tools_used": [tc["tool"] for tc in tool_calls],
                            "tool_count": len(tool_calls),
                            "database_tool_count": len(db_tools_used),
                            "web_tool_count": len(web_tools_used)
                        }
                    )
                else:
                    print("[WARNING] No tools were called")

            print()

            # Save to database
            print("=" * 80)
            print("4. Saving to database...")
            await save_to_database(query, result, langfuse_trace_id=None)
            print()

        except Exception as e:
            print(f"[ERROR] Error: {e}")
            langfuse.update_current_span(
                output={"error": str(e)}
            )
            import traceback
            traceback.print_exc()
            return False

    print("=" * 80)
    print("5. Flushing traces to Langfuse...")

    # Flush traces to Langfuse
    try:
        langfuse.flush()
        print("[OK] Traces sent successfully!")
        print(f"[INFO] View trace at: {host}")
        print("   Look for trace 'deep_researcher_database_query'")
        print("=" * 80)
        return True
    except Exception as e:
        print(f"[ERROR] Flush failed: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Test Deep Researcher with database access and Langfuse tracing"
    )
    parser.add_argument(
        "query",
        nargs="?",
        default="List all the tables in the database and tell me how many opportunities we have",
        help="Research query to test (default: list tables and count opportunities)"
    )

    args = parser.parse_args()

    success = asyncio.run(test_researcher(args.query))
    sys.exit(0 if success else 1)
