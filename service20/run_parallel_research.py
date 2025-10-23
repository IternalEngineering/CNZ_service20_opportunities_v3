#!/usr/bin/env python3
"""
Run parallel research for all test cities: opportunities + funding + matching

This script:
1. Fetches all cities with test@urbanzero.ai from the database
2. Runs research_city_opportunity.py for each city in parallel
3. Runs research_funder_opportunity.py for relevant funders
4. Finally runs the matching agent to match opportunities with funders
"""

import asyncio
import asyncpg
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv
import os

load_dotenv()

# Add src directory to path for tracing
sys.path.insert(0, str(Path(__file__).parent / "src"))
from open_deep_research.tracing import initialize_tracing

# Color output
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class Fore:
        GREEN = RED = YELLOW = CYAN = MAGENTA = BLUE = WHITE = ""
    class Style:
        BRIGHT = RESET_ALL = ""


# Country code mapping for funder research
COUNTRY_MAPPING = {
    'US': 'United States',
    'CA': 'Canada',
    'GB': 'United Kingdom',
    'SE': 'Sweden',
    'DK': 'Denmark',
    'AU': 'Australia',
    'IN': 'India',
    'NZ': 'New Zealand',
    'AE': 'United Arab Emirates',
    'CO': 'Colombia',
    'BR': 'Brazil',
    'ZA': 'South Africa',
    'JP': 'Japan',
    'SG': 'Singapore',
}

# 2-letter to 3-letter ISO country code conversion (CRITICAL for research_city_opportunity.py)
ALPHA2_TO_ALPHA3 = {
    'US': 'USA', 'CA': 'CAN', 'GB': 'GBR', 'SE': 'SWE',
    'DK': 'DNK', 'AU': 'AUS', 'IN': 'IND', 'NZ': 'NZL',
    'AE': 'ARE', 'CO': 'COL', 'BR': 'BRA', 'ZA': 'ZAF',
    'JP': 'JPN', 'SG': 'SGP', 'FR': 'FRA', 'DE': 'DEU',
    'ES': 'ESP', 'IT': 'ITA', 'NL': 'NLD', 'BE': 'BEL',
    'NO': 'NOR', 'FI': 'FIN', 'PL': 'POL', 'CZ': 'CZE',
    'AT': 'AUT', 'CH': 'CHE', 'KR': 'KOR', 'CN': 'CHN',
    'MX': 'MEX', 'AR': 'ARG', 'CL': 'CHL', 'SA': 'SAU'
}

# Continent mapping for broader funder research
CONTINENT_MAPPING = {
    'US': 'North America',
    'CA': 'North America',
    'GB': 'Europe',
    'SE': 'Europe',
    'DK': 'Europe',
    'AU': 'Oceania',
    'IN': 'Asia',
    'NZ': 'Oceania',
    'AE': 'Asia',
    'CO': 'South America',
    'BR': 'South America',
    'ZA': 'Africa',
    'JP': 'Asia',
    'SG': 'Asia',
}


async def get_test_cities() -> List[Dict]:
    """Fetch all cities with test@urbanzero.ai email from database."""
    print(f"{Fore.CYAN}[*] Fetching cities from database...{Style.RESET_ALL}")

    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    try:
        cities = await conn.fetch('''
            SELECT
                city,
                text_responses->>'country_code' as country_code,
                text_responses->>'success_criteria' as success_criteria,
                job_role,
                organization,
                created_at
            FROM service6_onboarding_voice
            WHERE email = 'test@urbanzero.ai'
            ORDER BY created_at DESC
        ''')

        city_list = []
        for city in cities:
            city_list.append({
                'city': city['city'],
                'country_code': city['country_code'],
                'country_name': COUNTRY_MAPPING.get(city['country_code'], city['country_code']),
                'continent': CONTINENT_MAPPING.get(city['country_code'], 'Unknown'),
                'success_criteria': city['success_criteria'],
                'job_role': city['job_role'],
                'organization': city['organization']
            })

        print(f"{Fore.GREEN}[+] Found {len(city_list)} cities{Style.RESET_ALL}")
        return city_list

    finally:
        await conn.close()


async def check_existing_research(city: str, country_code: str) -> bool:
    """Check if research already exists for a city."""
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    try:
        result = await conn.fetchval('''
            SELECT COUNT(*)
            FROM service20_investment_opportunities
            WHERE city = $1 AND country = $2
        ''', city, country_code)
        return result > 0
    finally:
        await conn.close()


def run_city_research(city_data: Dict) -> Dict:
    """Run opportunity research for a specific city in a subprocess."""
    city = city_data['city']
    country_code_alpha2 = city_data['country_code']

    # CRITICAL: Convert 2-letter code to 3-letter (research_city_opportunity.py requires 3-letter)
    country_code_alpha3 = ALPHA2_TO_ALPHA3.get(country_code_alpha2, country_code_alpha2)

    log_file = Path(__file__).parent / f"logs/opportunity_{city.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    log_file.parent.mkdir(exist_ok=True)

    print(f"{Fore.CYAN}[*] Starting opportunity research: {city}, {country_code_alpha2} ({country_code_alpha3}){Style.RESET_ALL}")
    print(f"    Log: {log_file}")

    cmd = [
        sys.executable,
        "research_city_opportunity.py",
        "--city", city,
        "--country", country_code_alpha3,  # Use 3-letter code
        "--sector", "renewable_energy",
        "--range", "1000000-50000000"
    ]

    try:
        # CRITICAL: Keep file handle open - don't use context manager
        log_handle = open(log_file, 'w', encoding='utf-8')
        process = subprocess.Popen(
            cmd,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            cwd=Path(__file__).parent,
            text=True
        )

        return {
            'type': 'opportunity',
            'city': city,
            'country_code': country_code_alpha2,
            'process': process,
            'log_file': log_file,
            'log_handle': log_handle,  # Keep handle for cleanup
            'start_time': time.time()
        }
    except Exception as e:
        print(f"{Fore.RED}[!] Failed to start research for {city}: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        return None


def run_funder_research(country_data: Dict, funder_type: str) -> Dict:
    """Run funder research for a specific country/region."""
    country_name = country_data['country_name']
    country_code = country_data['country_code']
    continent = country_data['continent']

    log_file = Path(__file__).parent / f"logs/funder_{funder_type}_{country_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    log_file.parent.mkdir(exist_ok=True)

    print(f"{Fore.CYAN}[*] Starting funder research: {funder_type} - {country_name}{Style.RESET_ALL}")
    print(f"    Log: {log_file}")

    # Determine scope (continental for broader reach)
    scope = "continental" if country_code in ['US', 'CA', 'GB'] else "national"

    cmd = [
        sys.executable,
        "research_funder_opportunity.py",
        funder_type,
        "--scope", scope,
        "--countries", country_name,
        "--sectors", "renewable_energy,solar_energy,wind_energy,energy_storage",
        "--min", "500000",
        "--max", "50000000"
    ]

    # Add continent for continental scope
    if scope == "continental":
        cmd.extend(["--continents", continent])

    try:
        # CRITICAL: Keep file handle open - don't use context manager
        log_handle = open(log_file, 'w', encoding='utf-8')
        process = subprocess.Popen(
            cmd,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            cwd=Path(__file__).parent,
            text=True
        )

        return {
            'type': 'funder',
            'funder_type': funder_type,
            'country': country_name,
            'country_code': country_code,
            'process': process,
            'log_file': log_file,
            'log_handle': log_handle,  # Keep handle for cleanup
            'start_time': time.time()
        }
    except Exception as e:
        print(f"{Fore.RED}[!] Failed to start funder research for {country_name}: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        return None


def run_matching_agent() -> Dict:
    """Run the matching agent to match opportunities with funders."""
    log_file = Path(__file__).parent / f"logs/matching_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    log_file.parent.mkdir(exist_ok=True)

    print(f"{Fore.MAGENTA}[*] Starting matching agent...{Style.RESET_ALL}")
    print(f"    Log: {log_file}")

    cmd = [sys.executable, "trigger_matching.py"]

    try:
        # CRITICAL: Keep file handle open - don't use context manager
        log_handle = open(log_file, 'w', encoding='utf-8')
        process = subprocess.Popen(
            cmd,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            cwd=Path(__file__).parent,
            text=True
        )

        return {
            'type': 'matching',
            'process': process,
            'log_file': log_file,
            'log_handle': log_handle,  # Keep handle for cleanup
            'start_time': time.time()
        }
    except Exception as e:
        print(f"{Fore.RED}[!] Failed to start matching agent: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Main execution function."""
    # Initialize tracing
    initialize_tracing("service20-parallel-research")

    print("=" * 80)
    print(f"{Fore.WHITE}{Style.BRIGHT}PARALLEL RESEARCH EXECUTION{Style.RESET_ALL}")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Fetch cities
    cities = await get_test_cities()

    if not cities:
        print(f"{Fore.RED}[!] No cities found{Style.RESET_ALL}")
        return 1

    print()
    print("=" * 80)
    print(f"{Fore.YELLOW}PHASE 1: OPPORTUNITY RESEARCH ({len(cities)} cities){Style.RESET_ALL}")
    print("=" * 80)
    print()

    # Check which cities need research
    cities_to_research = []
    for city_data in cities:
        exists = await check_existing_research(city_data['city'], city_data['country_code'])
        if exists:
            print(f"{Fore.GREEN}[✓] {city_data['city']}, {city_data['country_code']} - Already researched{Style.RESET_ALL}")
        else:
            cities_to_research.append(city_data)

    print()
    print(f"{Fore.CYAN}Cities requiring research: {len(cities_to_research)}/{len(cities)}{Style.RESET_ALL}")
    print()

    # Start opportunity research for all cities
    running_tasks = []
    for city_data in cities_to_research:
        task_info = run_city_research(city_data)
        if task_info:
            running_tasks.append(task_info)
        time.sleep(3)  # Stagger starts to avoid overwhelming the system

    print()
    print(f"{Fore.GREEN}[+] Started {len(running_tasks)} opportunity research tasks{Style.RESET_ALL}")
    print()

    # Monitor opportunity research
    completed = []
    failed = []

    print(f"{Fore.CYAN}[~] Monitoring opportunity research progress...{Style.RESET_ALL}")
    print("    (This may take 5-15 minutes per city)")
    print()

    while running_tasks:
        for task_info in running_tasks[:]:
            process = task_info['process']

            if process.poll() is not None:
                running_tasks.remove(task_info)
                elapsed = time.time() - task_info['start_time']
                elapsed_min = elapsed / 60

                city = task_info.get('city', task_info.get('country', 'Unknown'))

                if process.returncode == 0:
                    print(f"{Fore.GREEN}[✓] {city}: COMPLETED in {elapsed_min:.1f} min{Style.RESET_ALL}")
                    completed.append(task_info)
                else:
                    print(f"{Fore.RED}[✗] {city}: FAILED (code {process.returncode}) after {elapsed_min:.1f} min{Style.RESET_ALL}")
                    failed.append(task_info)

                # Close log file handle
                if 'log_handle' in task_info:
                    task_info['log_handle'].close()

        if running_tasks:
            time.sleep(5)  # Check every 5 seconds for better responsiveness

    print()
    print("=" * 80)
    print(f"{Fore.YELLOW}PHASE 1 COMPLETE{Style.RESET_ALL}")
    print("=" * 80)
    print(f"Completed: {len(completed)}, Failed: {len(failed)}")
    print()

    # Phase 2: Funder Research
    print("=" * 80)
    print(f"{Fore.YELLOW}PHASE 2: FUNDER RESEARCH{Style.RESET_ALL}")
    print("=" * 80)
    print()

    # Get unique countries for funder research
    unique_countries = {}
    for city_data in cities:
        country_code = city_data['country_code']
        if country_code not in unique_countries:
            unique_countries[country_code] = city_data

    print(f"Researching funders for {len(unique_countries)} countries")
    print()

    # Start funder research for each country/region
    funder_types = ['impact_investor', 'development_bank', 'government_grant']
    running_tasks = []

    for country_code, country_data in unique_countries.items():
        for funder_type in funder_types:
            task_info = run_funder_research(country_data, funder_type)
            if task_info:
                running_tasks.append(task_info)
            time.sleep(3)  # Stagger starts

    print(f"{Fore.GREEN}[+] Started {len(running_tasks)} funder research tasks{Style.RESET_ALL}")
    print()

    # Monitor funder research
    funder_completed = []
    funder_failed = []

    print(f"{Fore.CYAN}[~] Monitoring funder research progress...{Style.RESET_ALL}")
    print()

    while running_tasks:
        for task_info in running_tasks[:]:
            process = task_info['process']

            if process.poll() is not None:
                running_tasks.remove(task_info)
                elapsed = time.time() - task_info['start_time']
                elapsed_min = elapsed / 60

                label = f"{task_info.get('funder_type', '')} - {task_info.get('country', '')}"

                if process.returncode == 0:
                    print(f"{Fore.GREEN}[✓] {label}: COMPLETED in {elapsed_min:.1f} min{Style.RESET_ALL}")
                    funder_completed.append(task_info)
                else:
                    print(f"{Fore.RED}[✗] {label}: FAILED (code {process.returncode}) after {elapsed_min:.1f} min{Style.RESET_ALL}")
                    funder_failed.append(task_info)

                # Close log file handle
                if 'log_handle' in task_info:
                    task_info['log_handle'].close()

        if running_tasks:
            time.sleep(5)  # Check every 5 seconds for better responsiveness

    print()
    print("=" * 80)
    print(f"{Fore.YELLOW}PHASE 2 COMPLETE{Style.RESET_ALL}")
    print("=" * 80)
    print(f"Completed: {len(funder_completed)}, Failed: {len(funder_failed)}")
    print()

    # Phase 3: Matching
    print("=" * 80)
    print(f"{Fore.YELLOW}PHASE 3: MATCHING OPPORTUNITIES WITH FUNDERS{Style.RESET_ALL}")
    print("=" * 80)
    print()

    matching_task = run_matching_agent()
    if matching_task:
        print(f"{Fore.CYAN}[~] Waiting for matching to complete...{Style.RESET_ALL}")
        print()

        # Wait for matching to complete
        matching_task['process'].wait()
        elapsed = time.time() - matching_task['start_time']
        elapsed_min = elapsed / 60

        if matching_task['process'].returncode == 0:
            print(f"{Fore.GREEN}[✓] Matching COMPLETED in {elapsed_min:.1f} min{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}[✗] Matching FAILED (code {matching_task['process'].returncode}) after {elapsed_min:.1f} min{Style.RESET_ALL}")

        # Close log file handle
        if 'log_handle' in matching_task:
            matching_task['log_handle'].close()

    print()
    print("=" * 80)
    print(f"{Fore.WHITE}{Style.BRIGHT}FINAL SUMMARY{Style.RESET_ALL}")
    print("=" * 80)
    print()
    print(f"{Fore.CYAN}Opportunity Research:{Style.RESET_ALL}")
    print(f"  Completed: {len(completed)}")
    print(f"  Failed: {len(failed)}")
    print()
    print(f"{Fore.CYAN}Funder Research:{Style.RESET_ALL}")
    print(f"  Completed: {len(funder_completed)}")
    print(f"  Failed: {len(funder_failed)}")
    print()

    if failed:
        print(f"{Fore.RED}Failed opportunity research:{Style.RESET_ALL}")
        for task in failed:
            print(f"  - {task['city']}, {task['country_code']}: {task['log_file']}")
        print()

    if funder_failed:
        print(f"{Fore.RED}Failed funder research:{Style.RESET_ALL}")
        for task in funder_failed:
            print(f"  - {task['funder_type']} ({task['country']}): {task['log_file']}")
        print()

    print("=" * 80)
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    return 0 if not (failed or funder_failed) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
