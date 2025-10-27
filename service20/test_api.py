"""Test script for Service20 FastAPI endpoints."""

import asyncio
import httpx
from datetime import datetime

# API base URL
BASE_URL = "http://localhost:8000"


async def test_health_endpoint():
    """Test the /health endpoint."""
    print("\n" + "=" * 80)
    print("Testing /health endpoint")
    print("=" * 80)

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/health")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")

            if response.status_code == 200:
                print("✓ Health check PASSED")
                return True
            else:
                print("✗ Health check FAILED")
                return False

        except Exception as e:
            print(f"✗ Error: {str(e)}")
            return False


async def test_root_endpoint():
    """Test the / root endpoint."""
    print("\n" + "=" * 80)
    print("Testing / root endpoint")
    print("=" * 80)

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")

            if response.status_code == 200:
                print("✓ Root endpoint PASSED")
                return True
            else:
                print("✗ Root endpoint FAILED")
                return False

        except Exception as e:
            print(f"✗ Error: {str(e)}")
            return False


async def test_chat_query_existing_city():
    """Test /chat/query with an existing city."""
    print("\n" + "=" * 80)
    print("Testing /chat/query with existing city (Paris, FRA)")
    print("=" * 80)

    async with httpx.AsyncClient() as client:
        try:
            payload = {
                "city": "Paris",
                "country_code": "FRA"
            }

            response = await client.post(
                f"{BASE_URL}/chat/query",
                json=payload,
                timeout=10.0
            )

            print(f"Status Code: {response.status_code}")
            result = response.json()

            if response.status_code == 200:
                print(f"✓ Query SUCCESSFUL")
                print(f"  - Success: {result.get('success')}")
                print(f"  - Message: {result.get('message')}")
                print(f"  - Query Time: {result.get('query_time_ms')}ms")

                if result.get('data'):
                    data = result['data']
                    print(f"  - Opportunity ID: {data.get('id')}")
                    print(f"  - City: {data.get('city')}")
                    print(f"  - Country: {data.get('country')}")
                    print(f"  - Sector: {data.get('sector')}")
                    print(f"  - Created: {data.get('created_at')}")

                return True

            elif response.status_code == 404:
                print(f"✓ Query returned 404 (expected if no data for Paris)")
                print(f"  - Error: {result.get('error')}")
                print(f"  - Message: {result.get('message')}")
                return True

            else:
                print(f"✗ Query FAILED with status {response.status_code}")
                print(f"  - Response: {result}")
                return False

        except Exception as e:
            print(f"✗ Error: {str(e)}")
            return False


async def test_chat_query_non_existent_city():
    """Test /chat/query with a non-existent city."""
    print("\n" + "=" * 80)
    print("Testing /chat/query with non-existent city")
    print("=" * 80)

    async with httpx.AsyncClient() as client:
        try:
            payload = {
                "city": "NonExistentCity",
                "country_code": "XXX"
            }

            response = await client.post(
                f"{BASE_URL}/chat/query",
                json=payload,
                timeout=10.0
            )

            print(f"Status Code: {response.status_code}")
            result = response.json()

            if response.status_code == 404:
                print(f"✓ Query correctly returned 404")
                print(f"  - Error: {result.get('error')}")
                print(f"  - Message: {result.get('message')}")
                return True
            else:
                print(f"✗ Expected 404, got {response.status_code}")
                return False

        except Exception as e:
            print(f"✗ Error: {str(e)}")
            return False


async def test_chat_query_validation_error():
    """Test /chat/query with invalid parameters."""
    print("\n" + "=" * 80)
    print("Testing /chat/query with invalid parameters")
    print("=" * 80)

    async with httpx.AsyncClient() as client:
        try:
            payload = {
                "city": "A",  # Too short
                "country_code": "TOOLONG"  # Too long
            }

            response = await client.post(
                f"{BASE_URL}/chat/query",
                json=payload,
                timeout=10.0
            )

            print(f"Status Code: {response.status_code}")

            if response.status_code == 422:
                print(f"✓ Validation error correctly returned 422")
                print(f"  - Response: {response.json()}")
                return True
            else:
                print(f"✗ Expected 422, got {response.status_code}")
                return False

        except Exception as e:
            print(f"✗ Error: {str(e)}")
            return False


async def main():
    """Run all tests."""
    print("\n")
    print("=" * 80)
    print("Service20 API Test Suite")
    print("=" * 80)
    print(f"Time: {datetime.now().isoformat()}")
    print(f"Base URL: {BASE_URL}")
    print("=" * 80)

    # Run tests
    results = []
    results.append(await test_health_endpoint())
    results.append(await test_root_endpoint())
    results.append(await test_chat_query_existing_city())
    results.append(await test_chat_query_non_existent_city())
    results.append(await test_chat_query_validation_error())

    # Summary
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    passed = sum(results)
    total = len(results)
    print(f"Tests Passed: {passed}/{total}")

    if passed == total:
        print("✓ All tests PASSED")
    else:
        print(f"✗ {total - passed} test(s) FAILED")

    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
