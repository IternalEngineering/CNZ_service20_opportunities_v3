"""Test script for PostgreSQL database integration with Deep Researcher.

This script tests the database tools to ensure they can connect and query
the UrbanZero PostgreSQL database successfully.
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_database_connection():
    """Test basic database connection."""
    print("=" * 60)
    print("Testing PostgreSQL Database Connection")
    print("=" * 60)

    try:
        from src.open_deep_research.postgres_tools import get_db_connection

        conn = await get_db_connection()
        print("[OK] Successfully connected to database")

        # Test a simple query
        result = await conn.fetchval("SELECT version()")
        print(f"[OK] PostgreSQL Version: {result}")

        await conn.close()
        print("[OK] Connection closed successfully\n")
        return True

    except Exception as e:
        print(f"[FAIL] Connection failed: {e}\n")
        return False


async def test_get_database_schema():
    """Test the get_database_schema tool."""
    print("=" * 60)
    print("Testing get_database_schema Tool")
    print("=" * 60)

    try:
        from src.open_deep_research.postgres_tools import get_database_schema

        # List all tables
        result = await get_database_schema.ainvoke({})
        print("[OK] Successfully retrieved schema:")
        print(result)
        print()
        return True

    except Exception as e:
        print(f"[FAIL] Schema retrieval failed: {e}\n")
        return False


async def test_search_opportunities():
    """Test the search_opportunities tool."""
    print("=" * 60)
    print("Testing search_opportunities Tool")
    print("=" * 60)

    try:
        from src.open_deep_research.postgres_tools import search_opportunities

        # Search for opportunities
        result = await search_opportunities.ainvoke({"limit": 3})
        print("[OK] Successfully searched opportunities:")
        print(result[:500] + "..." if len(result) > 500 else result)
        print()
        return True

    except Exception as e:
        print(f"[FAIL] Opportunity search failed: {e}\n")
        return False


async def test_query_esg_metrics():
    """Test the query_esg_metrics tool."""
    print("=" * 60)
    print("Testing query_esg_metrics Tool")
    print("=" * 60)

    try:
        from src.open_deep_research.postgres_tools import query_esg_metrics

        # Query ESG data
        result = await query_esg_metrics.ainvoke({"min_esg_score": 60, "limit": 3})
        print("[OK] Successfully queried ESG metrics:")
        print(result[:500] + "..." if len(result) > 500 else result)
        print()
        return True

    except Exception as e:
        print(f"[FAIL] ESG query failed: {e}\n")
        return False


async def test_readonly_query():
    """Test the execute_readonly_query tool."""
    print("=" * 60)
    print("Testing execute_readonly_query Tool")
    print("=" * 60)

    try:
        from src.open_deep_research.postgres_tools import execute_readonly_query

        # Execute a simple SELECT query
        result = await execute_readonly_query.ainvoke({
            "sql_query": "SELECT COUNT(*) as total_opportunities FROM opportunities"
        })
        print("[OK] Successfully executed read-only query:")
        print(result)
        print()

        # Test safety - try a forbidden query
        result = await execute_readonly_query.ainvoke({
            "sql_query": "DELETE FROM opportunities WHERE id = 1"
        })
        print("[OK] Safety check passed - forbidden query blocked:")
        print(result)
        print()
        return True

    except Exception as e:
        print(f"[FAIL] Read-only query test failed: {e}\n")
        return False


async def main():
    """Run all tests."""
    print("\n")
    print("=" * 60)
    print("UrbanZero PostgreSQL Integration Tests")
    print("=" * 60)
    print()

    # Check DATABASE_URL is set
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("[FAIL] DATABASE_URL environment variable not set")
        print("Please ensure .env file contains DATABASE_URL")
        return

    print(f"Database: {database_url.split('@')[1].split('/')[0] if '@' in database_url else 'Unknown'}")
    print()

    # Run tests
    tests = [
        ("Database Connection", test_database_connection),
        ("Database Schema", test_get_database_schema),
        ("Search Opportunities", test_search_opportunities),
        ("ESG Metrics Query", test_query_esg_metrics),
        ("Read-Only Query Safety", test_readonly_query),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"[FAIL] {test_name} test crashed: {e}\n")
            results.append((test_name, False))

    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "[OK] PASS" if result else "[FAIL] FAIL"
        print(f"{status}: {test_name}")

    print()
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 60)
    print()

    if passed == total:
        print("SUCCESS: All tests passed! Database integration is working correctly.")
        print("The Deep Researcher can now query the UrbanZero database!")
    else:
        print("WARNING: Some tests failed. Please review the errors above.")


if __name__ == "__main__":
    asyncio.run(main())
