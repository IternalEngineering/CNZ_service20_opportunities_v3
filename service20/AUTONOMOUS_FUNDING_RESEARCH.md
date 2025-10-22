# Autonomous Funding Research - Systematic Query Generation

**Date**: October 22, 2025
**Purpose**: Define systematic approaches for the funding researcher agent to run autonomously

---

## Problem Statement

The investment opportunities agent and matching agent can run autonomously because they have clear triggers:
- **Investment Agent**: New cities entering the database → Research opportunities
- **Matching Agent**: New opportunities or funders in database → Match them

**Challenge**: The funding researcher needs a systematic way to generate research queries autonomously rather than waiting for manual inputs.

---

## Autonomous Trigger Strategies

### Strategy 1: Database-Driven Research (RECOMMENDED)

**Trigger**: Analyze existing investment opportunities to identify funding gaps

#### How It Works:

1. **Query unmatched opportunities** from `service20_investment_opportunities`:
   ```sql
   SELECT
     city, country, primary_sector, sectors,
     investment_amount_usd, roi_percent,
     project_stage
   FROM service20_investment_opportunities
   WHERE id NOT IN (
     SELECT opportunity_id
     FROM service20_matches
     WHERE match_score > 0.7
   )
   OR id IN (
     SELECT opportunity_id
     FROM service20_matches
     GROUP BY opportunity_id
     HAVING COUNT(*) < 3  -- Less than 3 potential funders
   )
   ORDER BY created_at DESC
   LIMIT 20;
   ```

2. **Aggregate common patterns**:
   - Most common geographic regions with unmatched opportunities
   - Most common sectors with funding gaps
   - Investment ranges with few funders
   - Project stages with limited funding options

3. **Generate targeted research queries**:
   ```python
   # Example: If 15 solar projects in France lack funders
   research_query = {
       "funder_type": "impact_investor",
       "scope": "national",
       "countries": ["France"],
       "sectors": ["solar_energy"],
       "min_investment": 1000000,
       "max_investment": 10000000
   }
   ```

#### Implementation:

```python
# autonomous_funding_trigger.py

async def analyze_funding_gaps():
    """Analyze database to identify funding gaps and generate research queries."""

    # 1. Find opportunities with no/few matches
    unmatched_opportunities = await get_unmatched_opportunities()

    # 2. Aggregate by geography, sector, investment range
    funding_gaps = aggregate_funding_gaps(unmatched_opportunities)

    # 3. Prioritize gaps by:
    #    - Number of opportunities affected (more = higher priority)
    #    - Total investment volume (larger = higher priority)
    #    - Recency (newer opportunities = higher priority)
    prioritized_gaps = prioritize_gaps(funding_gaps)

    # 4. Generate research queries for top N gaps
    research_queries = []
    for gap in prioritized_gaps[:10]:  # Top 10 gaps
        query = generate_research_query(gap)
        research_queries.append(query)

    return research_queries
```

**Advantages**:
- ✅ Directly addresses actual needs in the database
- ✅ Prioritizes high-impact research
- ✅ Completely autonomous - no manual input needed
- ✅ Adaptive to changing portfolio composition

**Example Scenarios**:

1. **Scenario**: 12 wind energy projects in Germany lack funders
   - **Trigger**: Generate query for German renewable energy funders
   - **Result**: Find 5-8 new German/European wind energy funders

2. **Scenario**: 8 sustainable transport projects in Southeast Asia have low match scores
   - **Trigger**: Research Asian development banks and impact investors for transport
   - **Result**: Improve match quality for existing opportunities

---

### Strategy 2: Geographic Expansion Research

**Trigger**: When a new country/region appears in the opportunities database

#### How It Works:

1. **Monitor new geographies** entering the database:
   ```sql
   SELECT DISTINCT country, COUNT(*) as opportunity_count
   FROM service20_investment_opportunities
   WHERE created_at > NOW() - INTERVAL '7 days'
   GROUP BY country
   HAVING COUNT(*) >= 3;  -- At least 3 opportunities
   ```

2. **Check funder coverage** for that geography:
   ```sql
   SELECT COUNT(*)
   FROM service20_funding_opportunities
   WHERE
     'Germany' = ANY(countries)
     OR geographic_scope = 'global'
     OR geographic_scope = 'continental' AND 'Europe' = ANY(continent);
   ```

3. **If coverage is low** (< 5 funders), trigger comprehensive geographic research:
   ```python
   # For new country with opportunities
   research_queries = [
       # Development banks
       {
           "funder_type": "development_bank",
           "scope": "national",
           "countries": [country],
           "sectors": ["renewable_energy", "sustainable_transport"]
       },
       # Impact investors
       {
           "funder_type": "impact_investor",
           "scope": "continental",
           "continents": [continent_of_country],
           "countries": [country],
           "sectors": ["renewable_energy"]
       },
       # Government grants
       {
           "funder_type": "government_grant",
           "scope": "national",
           "countries": [country],
           "sectors": ["renewable_energy", "energy_efficiency"]
       }
   ]
   ```

**Advantages**:
- ✅ Proactively builds funder database for new regions
- ✅ Ensures comprehensive geographic coverage
- ✅ Triggered automatically by opportunity creation

---

### Strategy 3: Sector-Specific Research Cycles

**Trigger**: Scheduled research for different sectors on a rotating basis

#### How It Works:

1. **Define sector research matrix**:
   ```python
   SECTOR_RESEARCH_SCHEDULE = {
       "renewable_energy": {
           "frequency_days": 14,  # Every 2 weeks
           "priority": "high",
           "subsectors": ["solar", "wind", "hydro", "geothermal"]
       },
       "sustainable_transport": {
           "frequency_days": 21,  # Every 3 weeks
           "priority": "high",
           "subsectors": ["EV_charging", "public_transit", "cycling"]
       },
       "green_buildings": {
           "frequency_days": 30,  # Monthly
           "priority": "medium",
           "subsectors": ["retrofit", "HVAC", "insulation"]
       },
       "waste_management": {
           "frequency_days": 45,  # Every 1.5 months
           "priority": "medium",
           "subsectors": ["recycling", "composting", "waste_to_energy"]
       }
   }
   ```

2. **Track last research date** per sector:
   ```sql
   CREATE TABLE funding_research_schedule (
       sector VARCHAR(100) PRIMARY KEY,
       last_research_date DATE,
       next_research_date DATE,
       research_count INTEGER DEFAULT 0
   );
   ```

3. **Trigger research** when `next_research_date` is reached:
   ```python
   async def check_sector_research_schedule():
       """Check if any sectors need research updates."""

       sectors_needing_research = await db.fetch("""
           SELECT sector, last_research_date
           FROM funding_research_schedule
           WHERE next_research_date <= CURRENT_DATE
           ORDER BY next_research_date ASC
           LIMIT 5;
       """)

       for sector_record in sectors_needing_research:
           sector = sector_record['sector']

           # Generate queries for all funder types in this sector
           for funder_type in ["development_bank", "impact_investor", "private_equity"]:
               query = {
                   "funder_type": funder_type,
                   "scope": "global",
                   "sectors": [sector],
                   "min_investment": 500000,
                   "max_investment": 50000000
               }
               await schedule_research(query)
   ```

**Advantages**:
- ✅ Keeps funder database fresh and up-to-date
- ✅ Systematic coverage of all sectors
- ✅ Configurable priorities and frequencies

---

### Strategy 4: Market Intelligence Research

**Trigger**: Monitor external news/trends to identify emerging funding opportunities

#### How It Works:

1. **Monitor news sources** for funding announcements:
   - New climate funds launched
   - Government grant programs announced
   - Development bank initiatives
   - Corporate sustainability funds

2. **Use news API** or web scraping:
   ```python
   from tavily import TavilyClient

   async def monitor_funding_news():
       """Monitor news for new funding opportunities."""

       client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

       search_queries = [
           "new climate fund launched 2025",
           "renewable energy investment program announced",
           "development bank climate initiative",
           "green bond fund 2025",
           "impact investor climate fund"
       ]

       new_funders = []
       for query in search_queries:
           results = await client.search(
               query=query,
               search_depth="advanced",
               max_results=10,
               days=7  # Last 7 days
           )

           # Parse results for funding announcements
           for result in results:
               if is_funding_announcement(result):
                   funder_info = extract_funder_info(result)
                   new_funders.append(funder_info)

       return new_funders
   ```

3. **Trigger deep research** for identified funders:
   ```python
   # Once a new funder is identified, trigger detailed research
   for funder in new_funders:
       research_query = {
           "funder_name": funder['name'],
           "funder_type": funder['type'],
           "focus": "comprehensive_profile"
       }
       await schedule_detailed_research(research_query)
   ```

**Advantages**:
- ✅ Stays current with market developments
- ✅ Captures new funding opportunities early
- ✅ Proactive rather than reactive

**Challenges**:
- ⚠️ Requires news API access (Tavily, NewsAPI, etc.)
- ⚠️ May generate false positives
- ⚠️ Needs validation logic

---

### Strategy 5: Funder Update Cycles

**Trigger**: Periodic updates for existing funders to refresh data

#### How It Works:

1. **Track funder data age**:
   ```sql
   SELECT
     id, funder_name, funder_type,
     last_verified_date,
     CURRENT_DATE - last_verified_date as days_since_update
   FROM service20_funding_opportunities
   WHERE last_verified_date < CURRENT_DATE - INTERVAL '90 days'
   ORDER BY last_verified_date ASC
   LIMIT 20;
   ```

2. **Trigger refresh research** for stale funders:
   ```python
   async def refresh_stale_funders():
       """Update information for funders not verified recently."""

       stale_funders = await get_stale_funders(max_age_days=90)

       for funder in stale_funders:
           # Generate focused update query
           update_query = f"""
           Update information for {funder['funder_name']}.

           Focus on:
           - Current fund status (active/closed/fundraising)
           - Application deadlines and next calls
           - Recent deals and portfolio updates
           - Changes to investment criteria
           - New contact information

           Verify all information is current as of {datetime.now().year}.
           """

           await schedule_research(update_query)
   ```

**Advantages**:
- ✅ Keeps existing data fresh
- ✅ Prevents outdated information in matches
- ✅ Identifies closed funds or changed criteria

---

## Recommended Implementation Architecture

### Phase 1: Core Autonomous Engine

```python
# autonomous_research_scheduler.py

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict

class AutonomousResearchScheduler:
    """Manages autonomous funding research triggers and execution."""

    def __init__(self):
        self.strategies = {
            "funding_gaps": FundingGapStrategy(),
            "geographic_expansion": GeographicExpansionStrategy(),
            "sector_cycles": SectorCycleStrategy(),
            "funder_updates": FunderUpdateStrategy()
        }

    async def run_continuous(self):
        """Continuously monitor and trigger research."""

        while True:
            # Check all strategies
            for name, strategy in self.strategies.items():
                try:
                    # Check if strategy should trigger
                    should_trigger, queries = await strategy.check()

                    if should_trigger:
                        print(f"[{name}] Triggered with {len(queries)} queries")

                        # Execute research for each query
                        for query in queries:
                            await self.execute_research(query)

                            # Throttle to avoid overwhelming the system
                            await asyncio.sleep(60)  # 1 minute between researches

                except Exception as e:
                    print(f"[{name}] Error: {e}")
                    continue

            # Sleep before next check cycle
            await asyncio.sleep(3600)  # Check every hour

    async def execute_research(self, query: Dict):
        """Execute a research query."""

        # Call research_funder_opportunity.py with query parameters
        result = await research_funder_opportunity(
            funder_type=query['funder_type'],
            scope=query['scope'],
            countries=query.get('countries'),
            sectors=query['sectors'],
            min_investment=query.get('min_investment'),
            max_investment=query.get('max_investment')
        )

        return result
```

### Phase 2: Strategy Implementations

```python
# strategies/funding_gap_strategy.py

class FundingGapStrategy:
    """Identifies funding gaps by analyzing unmatched opportunities."""

    async def check(self) -> tuple[bool, List[Dict]]:
        """Check if there are funding gaps to address."""

        # 1. Get unmatched opportunities
        unmatched = await self.get_unmatched_opportunities()

        if len(unmatched) < 5:
            return False, []  # Not enough to trigger

        # 2. Aggregate by patterns
        gaps = self.aggregate_gaps(unmatched)

        # 3. Generate research queries
        queries = []
        for gap in gaps[:5]:  # Top 5 gaps
            query = {
                "funder_type": self.select_funder_type(gap),
                "scope": gap['scope'],
                "countries": gap['countries'],
                "sectors": gap['sectors'],
                "min_investment": gap['min_investment'],
                "max_investment": gap['max_investment']
            }
            queries.append(query)

        return True, queries

    async def get_unmatched_opportunities(self):
        """Query opportunities with no/few high-quality matches."""

        return await db.fetch("""
            SELECT
              o.id, o.city, o.country, o.primary_sector,
              o.sectors, o.investment_amount_usd, o.project_stage,
              COALESCE(m.match_count, 0) as match_count
            FROM service20_investment_opportunities o
            LEFT JOIN (
              SELECT opportunity_id, COUNT(*) as match_count
              FROM service20_matches
              WHERE match_score > 0.7
              GROUP BY opportunity_id
            ) m ON o.id = m.opportunity_id
            WHERE COALESCE(m.match_count, 0) < 3
            ORDER BY o.created_at DESC;
        """)

    def aggregate_gaps(self, opportunities: List[Dict]) -> List[Dict]:
        """Aggregate opportunities into funding gaps."""

        from collections import defaultdict

        gaps = defaultdict(lambda: {
            'opportunities': [],
            'count': 0,
            'total_investment': 0
        })

        for opp in opportunities:
            # Create gap key: country + primary sector
            key = (opp['country'], opp['primary_sector'])

            gaps[key]['opportunities'].append(opp)
            gaps[key]['count'] += 1
            gaps[key]['total_investment'] += opp['investment_amount_usd']
            gaps[key]['country'] = opp['country']
            gaps[key]['sector'] = opp['primary_sector']

        # Convert to list and sort by priority
        gap_list = list(gaps.values())
        gap_list.sort(
            key=lambda g: (g['count'], g['total_investment']),
            reverse=True
        )

        return gap_list
```

### Phase 3: Scheduling & Orchestration

```python
# Start autonomous research scheduler
async def main():
    scheduler = AutonomousResearchScheduler()

    print("Starting autonomous funding research scheduler...")
    print("Strategies enabled:")
    print("  - Funding Gap Analysis")
    print("  - Geographic Expansion")
    print("  - Sector Research Cycles")
    print("  - Funder Data Updates")
    print()

    await scheduler.run_continuous()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Priority Ranking System

### Research Priority Score

Calculate priority for each potential research query:

```python
def calculate_research_priority(gap: Dict) -> float:
    """Calculate priority score (0-100) for a research query."""

    score = 0.0

    # 1. Number of opportunities affected (30 points max)
    opportunity_score = min(gap['opportunity_count'] / 10 * 30, 30)
    score += opportunity_score

    # 2. Total investment volume (30 points max)
    investment_score = min(gap['total_investment'] / 50000000 * 30, 30)
    score += investment_score

    # 3. Recency (20 points max)
    days_old = (datetime.now() - gap['oldest_opportunity_date']).days
    recency_score = max(20 - (days_old / 30), 0)  # Decay over 30 days
    score += recency_score

    # 4. Current funder coverage (20 points max)
    # Lower coverage = higher priority
    current_funder_count = gap.get('existing_funder_count', 0)
    coverage_score = max(20 - (current_funder_count * 4), 0)
    score += coverage_score

    return score
```

---

## Throttling & Rate Limiting

To avoid overwhelming the system:

```python
RESEARCH_THROTTLING = {
    "max_concurrent_researches": 2,
    "min_delay_between_researches": 60,  # seconds
    "max_researches_per_hour": 10,
    "max_researches_per_day": 50
}
```

---

## Monitoring & Metrics

Track autonomous research effectiveness:

```python
# Metrics to track
METRICS = {
    "researches_triggered": 0,
    "researches_completed": 0,
    "researches_failed": 0,
    "funders_discovered": 0,
    "new_matches_created": 0,
    "funding_gaps_closed": 0,
    "average_research_duration": 0,
    "strategy_trigger_counts": {}
}
```

---

## Summary & Recommendation

### **Recommended Approach**: Hybrid Strategy

Implement **Strategy 1 (Database-Driven)** as the primary method with **Strategy 3 (Sector Cycles)** as a backup:

1. **Primary (70% of researches)**: Database-Driven Funding Gap Analysis
   - Runs every 6 hours
   - Identifies top 5 funding gaps
   - Generates targeted research queries

2. **Secondary (20% of researches)**: Sector Research Cycles
   - Runs on schedule (different sector every week)
   - Ensures comprehensive sector coverage
   - Updates existing funder data

3. **Tertiary (10% of researches)**: Geographic Expansion
   - Triggers when new countries appear
   - Builds comprehensive regional coverage

### Implementation Timeline

- **Week 1**: Implement Strategy 1 (Database-Driven)
- **Week 2**: Add throttling and monitoring
- **Week 3**: Implement Strategy 3 (Sector Cycles)
- **Week 4**: Add Strategy 2 (Geographic Expansion)
- **Week 5+**: Monitor, optimize, and iterate

### Expected Benefits

- ✅ **100% autonomous operation** - No manual query input needed
- ✅ **Intelligent prioritization** - Focuses on highest-impact research
- ✅ **Adaptive system** - Responds to actual portfolio needs
- ✅ **Comprehensive coverage** - All sectors and geographies eventually covered
- ✅ **Fresh data** - Regular updates keep funder information current
- ✅ **Higher match rates** - More funders = better matching opportunities

---

**Status**: Proposal - Ready for implementation
**Next Steps**: Implement `autonomous_research_scheduler.py` with Strategy 1
