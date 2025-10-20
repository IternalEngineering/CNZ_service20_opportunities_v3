"""Create Service20 alerts via the CNZ API.

This script creates alerts using the CNZ API v2 endpoint that matches the staging
infrastructure format with API key authentication.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
import requests

load_dotenv()


def create_alert_via_api(
    name: str,
    criteria: Dict[str, Any],
    geoname_id: Optional[str] = None,
    city_country_code: Optional[str] = None,
    api_url: str = None,
    api_key: str = None
) -> Optional[Dict]:
    """Create an alert via the CNZ API v2 endpoint.

    Args:
        name: Alert name
        criteria: Alert criteria (type and conditions)
        geoname_id: Geoname ID for the city
        city_country_code: City-country code (e.g., "bristol-GB")
        api_url: API endpoint URL (defaults to staging)
        api_key: API key for authentication

    Returns:
        Response data if successful, None otherwise
    """
    # Default to staging if not provided
    if not api_url:
        api_url = os.getenv("CNZ_API_URL", "https://stage-cnz.icmserver007.com/api/v2/alerts")

    if not api_key:
        api_key = os.getenv("CNZ_API_KEY", "cnz_xEZR7v2ETYz2DnVzrmqDYXprpPKOrNDA97GaD3yjdfA")

    # Prepare request payload
    payload = {
        "name": name,
        "criteria": criteria
    }

    if geoname_id:
        payload["geonameId"] = geoname_id

    if city_country_code:
        payload["cityCountryCode"] = city_country_code

    # Make API request
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }

    try:
        print(f"Creating alert via API: {api_url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")

        response = requests.post(api_url, json=payload, headers=headers)

        print(f"Status Code: {response.status_code}")

        if response.status_code in [200, 201]:
            result = response.json()
            print(f"[OK] Alert created successfully")
            print(f"Response: {json.dumps(result, indent=2)}")
            return result
        else:
            print(f"[ERROR] Failed to create alert")
            print(f"Error: {response.text}")
            return None

    except Exception as e:
        print(f"[ERROR] Error creating alert: {e}")
        return None


def create_service20_research_alert(
    research_id: str,
    opportunity_type: str,
    title: str,
    location: str,
    findings_count: int,
    geoname_id: Optional[str] = None,
    city_country_code: Optional[str] = None
) -> Optional[Dict]:
    """Create a Service20 research completion alert.

    Args:
        research_id: Research ID
        opportunity_type: Type of opportunity (investment/funding)
        title: Opportunity title
        location: Location description
        findings_count: Number of findings
        geoname_id: Geoname ID for the city
        city_country_code: City-country code

    Returns:
        API response if successful, None otherwise
    """
    alert_name = f"Service20 Research: {title[:50]}"

    criteria = {
        "type": "service20_research",
        "conditions": {
            "research_id": research_id,
            "opportunity_type": opportunity_type,
            "location": location,
            "findings_count": findings_count,
            "completed_at": datetime.utcnow().isoformat()
        }
    }

    return create_alert_via_api(
        name=alert_name,
        criteria=criteria,
        geoname_id=geoname_id,
        city_country_code=city_country_code
    )


def main():
    """Test alert creation."""
    print("=" * 80)
    print("Service20 Alert API Test")
    print("=" * 80)
    print()

    # Example 1: Bristol Transport Decarbonization (matching your example)
    print("Example 1: Bristol Transport Decarbonization")
    print("-" * 80)
    result = create_alert_via_api(
        name="Bristol Transport Decarbonization",
        criteria={
            "type": "opportunity",
            "conditions": {
                "category": "transport",
                "investment_min": 250000
            }
        },
        geoname_id="Q21693433",
        city_country_code="bristol-GB"
    )
    print()

    # Example 2: Service20 Research Alert
    print("Example 2: Service20 Investment Research Alert")
    print("-" * 80)
    result = create_service20_research_alert(
        research_id="service20-bristol-001",
        opportunity_type="investment",
        title="Bristol Green Energy Initiative",
        location="Bristol, UK",
        findings_count=5,
        geoname_id="Q21693433",
        city_country_code="bristol-GB"
    )
    print()


if __name__ == "__main__":
    main()
