# Funder Research System - Architecture & Plan

## Overview

Design and implementation plan for `research_funder_opportunity.py` - a deep research agent that discovers and analyzes funding sources (investors, grants, development banks) for Net Zero projects.

---

## Core Requirements

### 1. Use Deep Research Agent
- Leverage existing `deep_researcher` from LangGraph
- Same proven workflow as `research_city_opportunity.py`
- Multi-iteration research with tool calling
- Comprehensive report generation

### 2. Search for Multiple Funder Types
- **Grants**: Government programs, foundations, climate funds
- **Development Banks**: World Bank, EIB, regional development banks
- **Impact Investors**: ESG funds, climate-focused VCs, family offices
- **Private Equity**: Green infrastructure funds, renewable energy funds
- **Corporate Funds**: Corporate sustainability initiatives
- **Green Bonds**: Bond issuers seeking green projects

### 3. Store Matching-Relevant Information

#### Geographic Scope (Critical for Matching)
- **Scope Level**: global, continental, multi_national, national, regional, city
- **Continents**: Europe, North America, Asia, Africa, etc.
- **Countries**: Specific countries or "all"
- **Regions**: Western Europe, Southeast Asia, etc.
- **Cities**: Specific cities if city-level funding

#### Financial Information
- **Total Fund Size**: AUM or total available
- **Min/Max Investment**: Ticket size range
- **Typical Investment**: Average deal size
- **Investment Types**: equity, debt, grant, blended_finance

#### Sector Focus
- **Primary Sectors**: renewable_energy, sustainable_transport, etc.
- **Subsectors**: solar, wind, EV charging, etc.
- **Excluded Sectors**: What they WON'T fund

#### Project Criteria
- **Project Stages**: early_stage, development, construction, operational
- **Technology Maturity**: pilot, proven, mature
- **ROI Requirements**: Min/target/max ROI
- **Carbon Metrics**: Required CO2 reduction

---

## Research Prompt Structure

### Input Parameters

```python
--funder-type:
    - impact_investor
    - development_bank
    - government_grant
    - private_equity
    - green_bond
    - corporate_fund
    - foundation

--scope:
    - global
    - continental (requires --continents)
    - national (requires --countries)
    - regional (requires --regions)
    - city (requires --cities)

--sectors: (comma-separated)
    - renewable_energy
    - solar_energy
    - wind_energy
    - energy_storage
    - sustainable_transport
    - green_buildings
    - waste_management
    - water_management

--min-investment: (optional, in USD)
--max-investment: (optional, in USD)

--project-stage: (optional)
    - all (default)
    - early_stage
    - development
    - construction
    - operational
```

### Example Commands

```bash
# European impact investors for solar
python research_funder_opportunity.py \
  --funder-type impact_investor \
  --scope continental \
  --continents Europe \
  --sectors solar_energy,energy_storage \
  --min-investment 1000000 \
  --max-investment 20000000

# Development banks for sustainable transport globally
python research_funder_opportunity.py \
  --funder-type development_bank \
  --scope global \
  --sectors sustainable_transport \
  --min-investment 10000000

# French government grants for renewable energy
python research_funder_opportunity.py \
  --funder-type government_grant \
  --scope national \
  --countries France \
  --sectors renewable_energy,green_buildings

# City-level funding for Paris
python research_funder_opportunity.py \
  --funder-type government_grant \
  --scope city \
  --cities Paris \
  --countries France \
  --sectors renewable_energy
```

---

## Research Prompt Template

```python
research_prompt = f"""
Research {FUNDER_TYPE_DESCRIPTIONS[funder_type]} for Net Zero projects.

GEOGRAPHIC SCOPE: {scope}
{f"Continents: {', '.join(continents)}" if scope == 'continental' else ''}
{f"Countries: {', '.join(countries)}" if countries else ''}
{f"Regions: {', '.join(regions)}" if regions else ''}
{f"Cities: {', '.join(cities)}" if cities else ''}

SECTOR FOCUS: {', '.join(sectors)}

INVESTMENT CRITERIA:
- Minimum Investment: ${min_investment:,}
- Maximum Investment: ${max_investment:,}
- Project Stages: {', '.join(project_stages)}

REQUIRED INFORMATION FOR EACH FUNDER:

1. IDENTIFICATION
   - Official name
   - Funder type and subtype
   - Organization type (public/private/non-profit)
   - Website and contact information

2. GEOGRAPHIC COVERAGE
   - Geographic scope (global/continental/national/regional/city)
   - Specific continents, countries, regions, or cities covered
   - Any geographic restrictions or preferences

3. SECTOR FOCUS
   - Primary sectors funded
   - Specific subsectors or technologies
   - Sectors explicitly excluded

4. FINANCIAL CRITERIA
   - Total fund size or assets under management
   - Minimum and maximum investment amounts
   - Typical ticket size
   - Investment types (equity/debt/grant/blended)
   - Financial instruments used

5. RETURN EXPECTATIONS
   - Minimum ROI required (if applicable)
   - Target ROI range
   - Willing to accept below-market returns?
   - Concessional finance available?

6. PROJECT REQUIREMENTS
   - Preferred project stages
   - Technology maturity requirements
   - Carbon reduction metrics required?
   - Impact measurement requirements
   - Co-financing requirements

7. APPLICATION PROCESS
   - How to apply (process description)
   - Application URL or portal
   - Contact email and phone
   - Typical decision timeline
   - Next call for proposals date (if applicable)
   - Current deadline (if applicable)

8. TRACK RECORD
   - Number of active projects
   - Total projects funded historically
   - Average deal size
   - 2-3 recent deal examples with details

9. CURRENT STATUS
   - Currently accepting applications? (yes/no)
   - Fund status (active/closed/fundraising/deploying)
   - Next fundraising round date

DELIVERABLES:

Provide a comprehensive analysis with:

1. Executive Summary (200-300 words)
   - Overview of {funder_type} landscape in specified geography
   - Total funding available
   - Key trends and opportunities

2. Detailed Funder Profiles (5-10 funders minimum)
   For each funder, provide:
   - All information listed above in structured format
   - Recent deal examples with project details and terms
   - Application strategy and tips
   - Likelihood of success rating (high/medium/low)

3. Comparison Matrix
   - Side-by-side comparison of key criteria
   - Best matches for different project types
   - Geographic coverage comparison

4. Application Strategy
   - Recommended approach for each funder
   - Timeline for applications
   - Required documentation checklist
   - Common success factors

5. Red Flags and Exclusions
   - Common reasons for rejection
   - Projects they explicitly won't fund
   - Geographic or sector restrictions

IMPORTANT:
- Only include ACTIVE funders currently accepting applications or with upcoming calls
- Verify all information is current (2023-2025)
- Include specific contact information and application URLs
- Cite sources for all claims
- Flag any uncertain information

Reference official websites, recent annual reports, and reputable financial databases.
"""
```

---

## Data Extraction & Storage

### Structured Data to Extract

```python
funding_data = {
    # Research outputs
    "query": research_prompt,
    "research_brief": brief_summary,
    "final_report": full_report,
    "notes": top_findings,

    # Funder identification
    "funder_name": "European Investment Bank",
    "funder_type": "development_bank",
    "funder_subtype": "multilateral_development_bank",
    "organization_type": "multilateral",

    # Geographic scope
    "geographic_scope": "continental",
    "continent": ["Europe"],
    "countries": ["EU Member States", "EU Candidate Countries"],
    "regions": [],
    "cities": [],

    # Sector focus
    "primary_sector": "renewable_energy",
    "sectors": ["solar_energy", "wind_energy", "energy_storage", "sustainable_transport"],
    "subsectors": ["offshore_wind", "grid_scale_battery", "EV_charging"],
    "excluded_sectors": ["fossil_fuels", "nuclear"],

    # Financial criteria
    "total_fund_size": 500000000000,  # $500B
    "currency": "EUR",
    "min_investment": 25000000,
    "max_investment": 500000000,
    "typical_investment": 100000000,

    # Investment structure
    "investment_types": ["senior_debt", "subordinated_debt", "guarantee"],
    "financial_instruments": ["project_finance_loan", "guarantee", "blended_finance"],

    # Return expectations
    "min_roi_requirement": 0.0,  # Can be 0 for development banks
    "target_roi": 5.0,
    "max_acceptable_roi": 12.0,
    "accepts_below_market_returns": True,
    "concessional_finance": True,

    # Timeline
    "investment_horizon_min": 10,
    "investment_horizon_max": 30,
    "typical_timeline": "15-25 years",

    # Project criteria
    "project_stages": ["development", "construction", "operational"],
    "technology_maturity": ["proven", "mature"],

    # ESG requirements
    "requires_carbon_metrics": True,
    "min_carbon_reduction": 10000,  # tons/year
    "sdg_alignment": ["SDG 7", "SDG 13"],
    "impact_measurement_required": True,

    # Application
    "application_process": "Submit concept note through EIB portal...",
    "application_url": "https://www.eib.org/en/projects/",
    "contact_email": "info@eib.org",
    "decision_timeline": "6-12 months",

    # Requirements
    "requires_co_financing": True,
    "min_co_financing_percent": 25.0,
    "local_participation_required": False,

    # Track record
    "active_portfolio_count": 450,
    "total_projects_funded": 2000,
    "average_deal_size": 75000000,
    "recent_deals": [
        {
            "project": "Offshore Wind Farm - North Sea",
            "location": "Netherlands",
            "amount": 150000000,
            "type": "senior_debt",
            "year": 2024
        }
    ],

    # Availability
    "currently_accepting": True,
    "next_call_date": "2025-03-01",
    "deadline_date": None,  # Rolling basis
    "fund_status": "active",

    # Sources
    "sources": [
        {"url": "https://www.eib.org", "type": "official_website"},
        {"url": "https://www.eib.org/annual-report-2024", "type": "annual_report"}
    ],
    "last_verified_date": "2025-01-21",
    "data_quality_score": 0.95
}
```

---

## Matching Agent Integration

### Key Fields for Matching

The matching agent will use these fields for compatibility scoring:

1. **Geographic Match**:
   ```python
   # Check if funder covers opportunity's location
   if opportunity_country in funder_countries:
       geographic_score = 1.0
   elif opportunity_continent in funder_continents:
       geographic_score = 0.8
   ```

2. **Sector Match**:
   ```python
   # Check sector alignment
   if opportunity_sector in funder_sectors:
       sector_score = 1.0
   ```

3. **Financial Match**:
   ```python
   # Check if opportunity amount within funder range
   if funder_min <= opportunity_amount <= funder_max:
       financial_score = 1.0
   ```

4. **Stage Match**:
   ```python
   # Check project stage compatibility
   if opportunity_stage in funder_project_stages:
       stage_score = 1.0
   ```

5. **ROI Match**:
   ```python
   # Check if opportunity ROI meets funder requirements
   if opportunity_roi >= funder_min_roi:
       roi_score = 1.0
   ```

---

## Implementation Steps

### Phase 1: Core Script
1. ✅ Create `database_schema_funding_opportunities.sql`
2. ⏳ Create `research_funder_opportunity.py` with:
   - Argument parsing (funder-type, scope, sectors, etc.)
   - Input validation
   - Research prompt generation
   - Deep research execution
   - Data storage

### Phase 2: Storage Function
3. ⏳ Add `store_funding_research()` to `database_storage.py`
   - Accept structured funding data
   - Map to table columns
   - Handle arrays and JSONB fields
   - Return research ID

### Phase 3: Documentation
4. ⏳ Create `FUNDING_RESEARCH_README.md` with:
   - Usage examples for each funder type
   - Geographic scope options
   - Sector options
   - Output examples

### Phase 4: Testing
5. ⏳ Test with real queries:
   - European impact investors
   - US development banks
   - French government grants
   - Global green bond funds

### Phase 5: Matching Integration
6. ⏳ Update `matching_agent.py` to:
   - Read from `service20_funding_opportunities`
   - Match geographic scopes
   - Consider investment ranges
   - Weight by fund status (active vs closed)

---

## Expected Outputs

### Example Research Result

**Query**: European impact investors for solar energy ($1M-$10M)

**Output**: 8 funder profiles including:
1. **Sunrock Infrastructure Fund** (Private Equity)
   - Geography: Western Europe
   - Sectors: Solar, Energy Storage
   - Investment: €3M-€15M
   - ROI Target: 12-15%
   - Currently Accepting: Yes

2. **European Climate Foundation** (Foundation)
   - Geography: EU Member States
   - Sectors: All renewable energy
   - Investment: €500K-€5M (grants)
   - ROI Target: N/A (grant)
   - Currently Accepting: Next call March 2025

3. **Nordic Climate Fund** (Development Bank)
   - Geography: Nordic countries + Baltics
   - Sectors: Renewable energy, Energy efficiency
   - Investment: €2M-€20M
   - ROI Target: 5-8% (concessional)
   - Currently Accepting: Yes (rolling)

---

## Success Metrics

1. **Accuracy**: 90%+ of funders are active and accepting applications
2. **Completeness**: All required fields populated for matching
3. **Freshness**: Data verified within last 6 months
4. **Relevance**: Funders match specified criteria
5. **Actionability**: Clear application process for each funder

---

## Next Steps

1. Implement `research_funder_opportunity.py` following this plan
2. Add storage function to `database_storage.py`
3. Create comprehensive documentation
4. Test with 5-10 different query types
5. Integrate with matching agent
6. Deploy and monitor results

---

## Questions to Resolve

1. ✅ Should we support multiple funder types in one search? → No, keep focused
2. ✅ How to handle inactive funders? → Only include if next_call_date exists
3. ✅ Should we research multiple geographies at once? → Yes, via arrays
4. ⏳ How to update stale funder data? → Periodic re-research (future feature)
5. ⏳ Integration with external databases? → Future enhancement (Crunchbase, PitchBook)
