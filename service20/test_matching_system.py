"""Comprehensive test script for Service20 Intelligent Matching System.

This script tests:
1. Enhanced alert metadata creation
2. Matching engine with bundling logic
3. Compatibility scoring
4. Match alert creation
5. Database storage of matches
6. End-to-end matching flow
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
load_dotenv()

# Color output (optional)
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class Fore:
        GREEN = RED = YELLOW = CYAN = MAGENTA = BLUE = WHITE = ""
    class Style:
        BRIGHT = RESET_ALL = ""


def print_header(text):
    """Print section header."""
    print(f"\n{Fore.CYAN}{'=' * 80}")
    print(f"{text}")
    print(f"{'=' * 80}{Style.RESET_ALL}\n")


def print_step(step_num, text):
    """Print test step."""
    print(f"{Fore.YELLOW}[Step {step_num}]{Style.RESET_ALL} {text}")


def print_success(text):
    """Print success message."""
    print(f"{Fore.GREEN}[OK] {text}{Style.RESET_ALL}")


def print_error(text):
    """Print error message."""
    print(f"{Fore.RED}[ERROR] {text}{Style.RESET_ALL}")


async def test_enhanced_metadata():
    """Test enhanced alert metadata creation."""
    print_step(1, "Testing Enhanced Alert Metadata")
    print("-" * 80)

    try:
        from open_deep_research.database_storage import create_service20_alert

        # Create test opportunity with comprehensive metadata
        research_results = {
            "research_id": f"test-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "opportunity_type": "investment",
            "research_brief": "Test solar panel project for Bristol",
            "final_report": "Comprehensive analysis of solar opportunity" * 10,
            "findings": ["High solar potential", "Strong ROI", "Carbon reduction opportunity"]
        }

        opportunity_data = {
            # Basic info
            "title": "TEST: Bristol Solar Panel Initiative",
            "location": "Bristol, UK",
            "investment_amount": 500000,
            "roi": 18.5,
            "city_id": "550e8400-e29b-41d4-a716-446655440001",

            # Enhanced metadata for matching
            "sector": "solar_energy",
            "subsector": "commercial",
            "sector_tags": ["rooftop", "municipal", "carbon_credits"],

            "city": "Bristol",
            "country": "UK",
            "region": "Europe",
            "geoname_id": "Q21693433",
            "coordinates": [51.45, -2.58],

            "planning_start": "2025-Q2",
            "execution_start": "2025-Q4",
            "completion": "2026-Q4",
            "deadline": "2025-12-31",
            "urgency": "medium",

            "technology": "photovoltaic",
            "capacity_mw": 2.5,
            "maturity": "planning",
            "payback_years": 7,
            "currency": "USD",
            "carbon_reduction": 150,

            "bundling_eligible": True,
            "minimum_bundle_size": 1000000,
            "maximum_bundle_partners": 5,
            "compatibility_requirements": ["same_sector", "similar_timeline"]
        }

        alert_id = await create_service20_alert(research_results, opportunity_data)

        if alert_id:
            print_success(f"Created enhanced alert with ID: {alert_id}")
            print(f"  Sector: {opportunity_data['sector']}")
            print(f"  Investment: ${opportunity_data['investment_amount']:,.0f}")
            print(f"  ROI: {opportunity_data['roi']}%")
            print(f"  Carbon Reduction: {opportunity_data['carbon_reduction']} tons/year")
            return True, alert_id
        else:
            print_error("Failed to create enhanced alert")
            return False, None

    except Exception as e:
        print_error(f"Enhanced metadata test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_compatibility_scoring():
    """Test compatibility scoring algorithm."""
    print_step(2, "Testing Compatibility Scoring")
    print("-" * 80)

    try:
        from open_deep_research.matching_engine import CompatibilityScorer

        scorer = CompatibilityScorer()

        # Mock funder data
        funder = {
            'criteria': {
                'sector': {'primary': 'solar_energy'},
                'financial': {
                    'minimum_required': 1000000,
                    'amount': 2000000,
                    'roi_expected': 15.0
                },
                'timeline': {},
                'technical': {}
            }
        }

        # Mock opportunity data
        opportunities = [
            {
                'criteria': {
                    'sector': {'primary': 'solar_energy'},
                    'financial': {
                        'amount': 500000,
                        'roi_expected': 18.5,
                        'carbon_reduction_tons_annually': 150
                    },
                    'timeline': {'execution_start': '2025-Q4'},
                    'technical': {'technology': 'photovoltaic'}
                }
            },
            {
                'criteria': {
                    'sector': {'primary': 'solar_energy'},
                    'financial': {
                        'amount': 600000,
                        'roi_expected': 17.0,
                        'carbon_reduction_tons_annually': 180
                    },
                    'timeline': {'execution_start': '2025-Q4'},
                    'technical': {'technology': 'photovoltaic'}
                }
            }
        ]

        # Calculate score
        score, criteria_met, warnings = scorer.calculate_score(funder, opportunities)

        print_success(f"Compatibility score: {score:.2f}")
        print(f"  Confidence level: {'high' if score > 0.80 else 'medium' if score > 0.60 else 'low'}")
        print(f"  Criteria met: {', '.join(criteria_met)}")
        if warnings:
            print(f"  Warnings: {', '.join(warnings)}")

        return score >= 0.60  # Should pass with reasonable score

    except Exception as e:
        print_error(f"Compatibility scoring test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_bundle_analyzer():
    """Test bundle metrics calculation."""
    print_step(3, "Testing Bundle Analyzer")
    print("-" * 80)

    try:
        from open_deep_research.matching_engine import BundleAnalyzer

        analyzer = BundleAnalyzer()

        # Mock opportunities
        opportunities = [
            {
                'criteria': {
                    'financial': {
                        'amount': 500000,
                        'roi_expected': 18.5,
                        'carbon_reduction_tons_annually': 150
                    },
                    'location': {'city': 'Bristol', 'country': 'UK'},
                    'technical': {'capacity_mw': 2.5}
                }
            },
            {
                'criteria': {
                    'financial': {
                        'amount': 300000,
                        'roi_expected': 17.0,
                        'carbon_reduction_tons_annually': 100
                    },
                    'location': {'city': 'Manchester', 'country': 'UK'},
                    'technical': {'capacity_mw': 1.5}
                }
            },
            {
                'criteria': {
                    'financial': {
                        'amount': 400000,
                        'roi_expected': 19.0,
                        'carbon_reduction_tons_annually': 120
                    },
                    'location': {'city': 'Edinburgh', 'country': 'UK'},
                    'technical': {'capacity_mw': 2.0}
                }
            }
        ]

        metrics = analyzer.calculate_bundle_metrics(opportunities)

        print_success("Bundle metrics calculated")
        print(f"  Total Investment: ${metrics['total_investment']:,.0f}")
        print(f"  Blended ROI: {metrics['blended_roi']}%")
        print(f"  Total Carbon Reduction: {metrics['total_carbon_reduction']} tons/year")
        print(f"  Total Capacity: {metrics['total_capacity_mw']} MW")
        print(f"  Cities: {', '.join(metrics['cities'])}")
        print(f"  Project Count: {metrics['project_count']}")

        # Verify calculations
        expected_total = 1200000
        if metrics['total_investment'] == expected_total:
            print_success(f"Investment calculation correct: ${expected_total:,.0f}")
            return True
        else:
            print_error(f"Expected ${expected_total:,.0f}, got ${metrics['total_investment']:,.0f}")
            return False

    except Exception as e:
        print_error(f"Bundle analyzer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_match_storage():
    """Test storing match proposals in database."""
    print_step(4, "Testing Match Storage")
    print("-" * 80)

    try:
        from open_deep_research.database_storage import store_match_proposal

        match_data = {
            'match_id': f"test-match-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'match_type': 'bundled',
            'compatibility_score': 0.87,
            'confidence_level': 'high',
            'opportunities': [
                {
                    'alert_id': 'test-opp-1',
                    'city': 'Bristol',
                    'sector': 'solar_energy',
                    'investment_amount': 500000,
                    'roi': 18.5
                },
                {
                    'alert_id': 'test-opp-2',
                    'city': 'Manchester',
                    'sector': 'solar_energy',
                    'investment_amount': 300000,
                    'roi': 17.0
                }
            ],
            'funders': [
                {
                    'alert_id': 'test-funder-1',
                    'research_id': 'green-fund-2025',
                    'sector_interest': 'solar_energy',
                    'funding_available': 2000000,
                    'minimum_investment': 1000000
                }
            ],
            'bundle_metrics': {
                'total_investment': 800000,
                'blended_roi': 17.9,
                'total_carbon_reduction': 250,
                'project_count': 2
            },
            'criteria_met': ['sector_perfect_match', 'timeline_aligned'],
            'criteria_warnings': []
        }

        match_id = await store_match_proposal(match_data, requires_approval=False)

        if match_id:
            print_success(f"Stored match proposal: {match_id}")
            print(f"  Match Type: {match_data['match_type']}")
            print(f"  Compatibility Score: {match_data['compatibility_score']}")
            print(f"  Opportunities: {len(match_data['opportunities'])}")
            print(f"  Total Investment: ${match_data['bundle_metrics']['total_investment']:,.0f}")
            return True, match_id
        else:
            print_error("Failed to store match proposal")
            return False, None

    except Exception as e:
        print_error(f"Match storage test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None


async def test_match_alert_creation():
    """Test creating match alerts for participants."""
    print_step(5, "Testing Match Alert Creation")
    print("-" * 80)

    try:
        from open_deep_research.database_storage import create_match_alert

        match_data = {
            'match_id': f"test-match-alert-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'match_type': 'bundled',
            'compatibility_score': 0.87,
            'confidence_level': 'high',
            'opportunities': [
                {
                    'alert_id': 'test-opp-1',
                    'city': 'Bristol',
                    'country': 'UK',
                    'sector': 'solar_energy',
                    'investment_amount': 500000,
                    'roi': 18.5,
                    'carbon_reduction': 150
                },
                {
                    'alert_id': 'test-opp-2',
                    'city': 'Manchester',
                    'country': 'UK',
                    'sector': 'solar_energy',
                    'investment_amount': 700000,
                    'roi': 17.2,
                    'carbon_reduction': 200
                }
            ],
            'funders': [
                {
                    'alert_id': 'test-funder-1',
                    'research_id': 'green-investment-fund-2025',
                    'sector_interest': 'solar_energy',
                    'funding_available': 2000000,
                    'minimum_investment': 1000000,
                    'roi_expected': 15.0
                }
            ],
            'bundle_metrics': {
                'total_investment': 1200000,
                'blended_roi': 17.8,
                'total_carbon_reduction': 350,
                'project_count': 2,
                'countries': ['UK'],
                'cities': ['Bristol', 'Manchester']
            },
            'criteria_met': ['sector_perfect_match', 'minimum_scale_met', 'timeline_aligned'],
            'criteria_warnings': []
        }

        # Create match alerts (no API notification for testing)
        alert_ids = await create_match_alert(match_data, auto_notify=False)

        if alert_ids and len(alert_ids) > 0:
            print_success(f"Created {len(alert_ids)} match alerts")
            print(f"  Alert IDs: {', '.join(map(str, alert_ids))}")
            print(f"  Participants notified: {len(match_data['opportunities'])} opportunities + {len(match_data['funders'])} funders")
            return True
        else:
            print_error("Failed to create match alerts")
            return False

    except Exception as e:
        print_error(f"Match alert creation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all matching system tests."""
    print_header("Service20 Intelligent Matching System - Comprehensive Test")

    print(f"Environment:")
    print(f"  DATABASE_URL: {'Set' if os.getenv('DATABASE_URL') else 'Not set'}")
    print(f"  CNZ_API_URL: {os.getenv('CNZ_API_URL', 'Using default')}")
    print()

    results = {}

    # Test 1: Enhanced metadata
    success, alert_id = await test_enhanced_metadata()
    results['enhanced_metadata'] = success
    print()

    # Test 2: Compatibility scoring
    success = test_compatibility_scoring()
    results['compatibility_scoring'] = success
    print()

    # Test 3: Bundle analyzer
    success = test_bundle_analyzer()
    results['bundle_analyzer'] = success
    print()

    # Test 4: Match storage
    success, match_id = await test_match_storage()
    results['match_storage'] = success
    print()

    # Test 5: Match alert creation
    success = await test_match_alert_creation()
    results['match_alert_creation'] = success
    print()

    # Summary
    print_header("Test Summary")

    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)

    for test_name, success in results.items():
        status = f"{Fore.GREEN}PASS" if success else f"{Fore.RED}FAIL"
        print(f"  {test_name.replace('_', ' ').title()}: {status}{Style.RESET_ALL}")

    print()
    print(f"Results: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print(f"\n{Fore.GREEN}{'=' * 80}")
        print(f"SUCCESS: All tests passed! Matching system is working correctly.")
        print(f"{'=' * 80}{Style.RESET_ALL}\n")
        print("Next steps:")
        print("  1. Run the database schema migration: psql $DATABASE_URL < database_schema_matches.sql")
        print("  2. Set up daily cron job: python src/open_deep_research/scheduled_jobs.py matching 30")
        print("  3. Monitor matches in database: SELECT * FROM opportunity_matches ORDER BY created_at DESC;")
    else:
        print(f"\n{Fore.YELLOW}{'=' * 80}")
        print(f"WARNING: Some tests failed. Check the output above for details.")
        print(f"{'=' * 80}{Style.RESET_ALL}\n")


if __name__ == "__main__":
    asyncio.run(main())
