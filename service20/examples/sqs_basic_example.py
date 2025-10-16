"""Basic example of sending messages to SQS queues.

This script demonstrates how to send investment and funding opportunities
to the SQS message queues for processing.
"""

import asyncio
import sys
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from open_deep_research.sqs_config import get_sqs_manager


def send_investment_opportunity_example():
    """Send an example investment opportunity to the queue."""
    sqs = get_sqs_manager()

    # Example 1: Solar Farm Project
    solar_opportunity = {
        "opportunity_id": "INV-2025-001",
        "title": "50MW Solar Farm Development in Bristol",
        "description": """
        Large-scale solar farm development project in Bristol, UK. The project aims to
        generate 50MW of clean renewable energy, contributing to the region's net zero
        targets. The development includes:
        - 150 acres of solar panels
        - Battery storage system (20MWh capacity)
        - Grid connection infrastructure
        - 25-year power purchase agreement
        - Expected annual generation: 55 GWh
        """.strip(),
        "location": "Bristol, UK",
        "sector": "Renewable Energy - Solar",
        "investment_amount": 25000000,  # £25M
        "roi": 12.5,  # 12.5% annual return
        "risk_level": "medium",
        "timeline": "24 months to completion",
        "net_zero_impact": {
            "co2_reduction_tons_per_year": 24750,
            "equivalent_homes_powered": 15000
        }
    }

    message_id = sqs.send_investment_opportunity(solar_opportunity)
    print(f"✓ Sent solar farm opportunity: {message_id}")

    # Example 2: Wind Turbine Project
    wind_opportunity = {
        "opportunity_id": "INV-2025-002",
        "title": "Offshore Wind Farm Expansion",
        "description": """
        Expansion of existing offshore wind farm off the coast of Scotland.
        Adding 10 new 15MW turbines to increase capacity by 150MW.
        Project includes marine surveys, environmental impact assessments,
        and grid upgrade works.
        """.strip(),
        "location": "Scottish Coast",
        "sector": "Renewable Energy - Wind",
        "investment_amount": 180000000,  # £180M
        "roi": 15.2,
        "risk_level": "medium-high",
        "timeline": "36 months to completion",
        "net_zero_impact": {
            "co2_reduction_tons_per_year": 135000,
            "equivalent_homes_powered": 95000
        }
    }

    message_id = sqs.send_investment_opportunity(wind_opportunity)
    print(f"✓ Sent wind farm opportunity: {message_id}")

    # Example 3: Energy Efficiency Retrofit
    retrofit_opportunity = {
        "opportunity_id": "INV-2025-003",
        "title": "Commercial Building Energy Retrofit Program",
        "description": """
        Large-scale retrofit program for 50 commercial buildings in London.
        Includes heat pump installations, insulation upgrades, smart building
        management systems, and solar panel installations. Expected to reduce
        building energy consumption by 60%.
        """.strip(),
        "location": "London, UK",
        "sector": "Energy Efficiency",
        "investment_amount": 8500000,  # £8.5M
        "roi": 18.5,
        "risk_level": "low-medium",
        "timeline": "18 months",
        "net_zero_impact": {
            "co2_reduction_tons_per_year": 4200,
            "energy_savings_mwh_per_year": 12000
        }
    }

    message_id = sqs.send_investment_opportunity(retrofit_opportunity)
    print(f"✓ Sent retrofit opportunity: {message_id}")


def send_funding_opportunity_example():
    """Send an example funding opportunity to the queue."""
    sqs = get_sqs_manager()

    # Example 1: Government Net Zero Innovation Fund
    gov_funding = {
        "funding_id": "FUND-2025-001",
        "title": "UK Net Zero Innovation Fund 2025",
        "description": """
        The UK Government's flagship funding program for innovative net zero
        technologies and projects. This round focuses on breakthrough technologies
        in renewable energy, carbon capture, and green transport. Funding supports
        projects from feasibility studies through to full commercialization.
        """.strip(),
        "funder": "UK Department for Energy Security and Net Zero",
        "amount_available": 50000000,  # £50M total fund
        "deadline": "2025-12-31",
        "eligible_sectors": [
            "Renewable Energy",
            "Carbon Capture and Storage",
            "Green Transport",
            "Energy Storage",
            "Hydrogen Technologies"
        ],
        "requirements": [
            "UK-based organization",
            "Demonstrable net zero contribution",
            "Innovation focus",
            "Match funding of at least 25%",
            "Delivery within 3 years"
        ],
        "funding_range": {
            "min": 500000,
            "max": 5000000
        },
        "success_rate": 0.15  # 15% approval rate
    }

    message_id = sqs.send_funding_opportunity(gov_funding)
    print(f"✓ Sent government funding opportunity: {message_id}")

    # Example 2: Green Investment Bank
    gib_funding = {
        "funding_id": "FUND-2025-002",
        "title": "Green Investment Bank Infrastructure Fund",
        "description": """
        Debt and equity financing for large-scale renewable energy and
        infrastructure projects. Focus on projects that will deliver significant
        carbon reductions and support the UK's net zero targets. Flexible
        financing structures available.
        """.strip(),
        "funder": "UK Green Investment Bank",
        "amount_available": 200000000,  # £200M
        "deadline": "Rolling applications",
        "eligible_sectors": [
            "Offshore Wind",
            "Solar Energy",
            "Energy Storage",
            "Grid Infrastructure",
            "Waste to Energy"
        ],
        "requirements": [
            "Project value minimum £10M",
            "Viable business case",
            "Planning permission secured or near secured",
            "Strong management team",
            "Proven technology"
        ],
        "funding_range": {
            "min": 10000000,
            "max": 50000000
        },
        "funding_types": ["Debt", "Equity", "Mezzanine"],
        "success_rate": 0.25
    }

    message_id = sqs.send_funding_opportunity(gib_funding)
    print(f"✓ Sent bank funding opportunity: {message_id}")

    # Example 3: EU Innovation Fund
    eu_funding = {
        "funding_id": "FUND-2025-003",
        "title": "EU Innovation Fund - Net Zero Technologies",
        "description": """
        European Union funding for innovative low-carbon technologies.
        Supports demonstration and deployment of breakthrough technologies
        that can contribute to significant emissions reductions. Priority
        given to projects with cross-border collaboration.
        """.strip(),
        "funder": "European Commission",
        "amount_available": 100000000,  # €100M
        "deadline": "2025-09-30",
        "eligible_sectors": [
            "Renewable Energy",
            "Energy Intensive Industries",
            "Carbon Capture",
            "Energy Storage",
            "Novel technologies"
        ],
        "requirements": [
            "EU member state participation",
            "Technology readiness level 7-9",
            "Significant innovation component",
            "Cross-border collaboration preferred",
            "Minimum 40% emissions reduction"
        ],
        "funding_range": {
            "min": 7500000,
            "max": 60000000
        },
        "success_rate": 0.20
    }

    message_id = sqs.send_funding_opportunity(eu_funding)
    print(f"✓ Sent EU funding opportunity: {message_id}")


def main():
    """Run the example scripts."""
    print("=" * 60)
    print("SQS Message Queue - Basic Example")
    print("=" * 60)
    print()

    print("Sending Investment Opportunities...")
    print("-" * 60)
    send_investment_opportunity_example()
    print()

    print("Sending Funding Opportunities...")
    print("-" * 60)
    send_funding_opportunity_example()
    print()

    print("=" * 60)
    print("✓ All messages sent successfully!")
    print()
    print("Next steps:")
    print("  1. Run the consumer example to process these messages")
    print("  2. Check AWS SQS console to see messages in queues")
    print("  3. View processed research results")
    print("=" * 60)


if __name__ == "__main__":
    main()
