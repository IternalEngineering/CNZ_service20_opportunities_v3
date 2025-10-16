# Agent Input Formats - Quick Reference

## NetZeroInvestmentOpportunityHandler

### Input: Investment Opportunity JSON

```json
{
  "opportunity_id": "INV-2025-001",
  "title": "50MW Solar Farm Development in Bristol",
  "description": "Large-scale solar farm development project in Bristol, UK. The project aims to generate 50MW of clean renewable energy, contributing to the region's net zero targets. The development includes: 150 acres of solar panels, Battery storage system (20MWh capacity), Grid connection infrastructure, 25-year power purchase agreement, Expected annual generation: 55 GWh",
  "location": "Bristol, UK",
  "sector": "Renewable Energy - Solar",
  "investment_amount": 25000000,
  "roi": 12.5,
  "risk_level": "medium",
  "timeline": "24 months to completion",
  "net_zero_impact": {
    "co2_reduction_tons_per_year": 24750,
    "equivalent_homes_powered": 15000
  }
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `opportunity_id` | string | Yes | Unique identifier (e.g., "INV-2025-001") |
| `title` | string | Yes | Project title |
| `description` | string | Yes | Detailed project description |
| `location` | string | Yes | Geographic location |
| `sector` | string | Yes | Industry sector (e.g., "Renewable Energy - Solar") |
| `investment_amount` | number | Yes | Required investment amount in currency |
| `roi` | number | Yes | Expected return on investment (%) |
| `risk_level` | string | No | Risk assessment (e.g., "low", "medium", "high") |
| `timeline` | string | No | Project completion timeline |
| `net_zero_impact` | object | No | Environmental impact metrics |
| `net_zero_impact.co2_reduction_tons_per_year` | number | No | Annual CO2 reduction in tons |
| `net_zero_impact.equivalent_homes_powered` | number | No | Number of homes equivalent |
| `net_zero_impact.energy_savings_mwh_per_year` | number | No | Annual energy savings in MWh |

### Additional Examples

**Example 1: Wind Energy**
```json
{
  "opportunity_id": "INV-2025-002",
  "title": "Offshore Wind Farm Expansion",
  "description": "Expansion of existing offshore wind farm off the coast of Scotland. Adding 10 new 15MW turbines to increase capacity by 150MW.",
  "location": "Scottish Coast",
  "sector": "Renewable Energy - Wind",
  "investment_amount": 180000000,
  "roi": 15.2,
  "risk_level": "medium-high",
  "timeline": "36 months to completion",
  "net_zero_impact": {
    "co2_reduction_tons_per_year": 135000,
    "equivalent_homes_powered": 95000
  }
}
```

**Example 2: Energy Efficiency**
```json
{
  "opportunity_id": "INV-2025-003",
  "title": "Commercial Building Energy Retrofit Program",
  "description": "Large-scale retrofit program for 50 commercial buildings in London. Includes heat pump installations, insulation upgrades, smart building management systems, and solar panels.",
  "location": "London, UK",
  "sector": "Energy Efficiency",
  "investment_amount": 8500000,
  "roi": 18.5,
  "risk_level": "low-medium",
  "timeline": "18 months",
  "net_zero_impact": {
    "co2_reduction_tons_per_year": 4200,
    "energy_savings_mwh_per_year": 12000
  }
}
```

**Example 3: Energy Storage**
```json
{
  "opportunity_id": "INV-2025-004",
  "title": "Smart Grid Battery Storage System",
  "description": "Development of a 100MWh grid-scale battery storage system to support renewable energy integration. The system will store excess solar and wind energy during peak generation.",
  "location": "Scotland, UK",
  "sector": "Energy Storage",
  "investment_amount": 45000000,
  "roi": 16.8,
  "risk_level": "medium"
}
```

---

## NetZeroFundingOpportunityHandler

### Input: Funding Opportunity JSON

```json
{
  "funding_id": "FUND-2025-001",
  "title": "UK Net Zero Innovation Fund 2025",
  "description": "The UK Government's flagship funding program for innovative net zero technologies and projects. This round focuses on breakthrough technologies in renewable energy, carbon capture, and green transport.",
  "funder": "UK Department for Energy Security and Net Zero",
  "amount_available": 50000000,
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
  "success_rate": 0.15
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `funding_id` | string | Yes | Unique identifier (e.g., "FUND-2025-001") |
| `title` | string | Yes | Funding program title |
| `description` | string | Yes | Program description |
| `funder` | string | Yes | Funding organization name |
| `amount_available` | number | Yes | Total fund size in currency |
| `deadline` | string | Yes | Application deadline (ISO date or "Rolling") |
| `eligible_sectors` | array[string] | Yes | List of eligible sectors |
| `requirements` | array[string] | No | List of eligibility requirements |
| `funding_range` | object | No | Min/max funding amounts |
| `funding_range.min` | number | No | Minimum funding amount |
| `funding_range.max` | number | No | Maximum funding amount |
| `funding_types` | array[string] | No | Types of funding (e.g., "Debt", "Equity") |
| `success_rate` | number | No | Historical approval rate (0.0-1.0) |

### Additional Examples

**Example 1: Investment Bank**
```json
{
  "funding_id": "FUND-2025-002",
  "title": "Green Investment Bank Infrastructure Fund",
  "description": "Debt and equity financing for large-scale renewable energy and infrastructure projects. Focus on projects that will deliver significant carbon reductions.",
  "funder": "UK Green Investment Bank",
  "amount_available": 200000000,
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
```

**Example 2: EU Fund**
```json
{
  "funding_id": "FUND-2025-003",
  "title": "EU Innovation Fund - Net Zero Technologies",
  "description": "European Union funding for innovative low-carbon technologies. Supports demonstration and deployment of breakthrough technologies that can contribute to significant emissions reductions.",
  "funder": "European Commission",
  "amount_available": 100000000,
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
```

---

## How to Send Inputs

### Method 1: Using SQS Manager (Python)

```python
from open_deep_research.sqs_config import get_sqs_manager

sqs = get_sqs_manager()

# Send investment opportunity
investment = {
    "opportunity_id": "INV-2025-001",
    "title": "Solar Farm Project",
    "description": "...",
    "location": "Bristol, UK",
    "sector": "Solar Energy",
    "investment_amount": 25000000,
    "roi": 12.5
}

message_id = sqs.send_investment_opportunity(investment)
print(f"Sent investment: {message_id}")

# Send funding opportunity
funding = {
    "funding_id": "FUND-2025-001",
    "title": "Government Fund",
    "description": "...",
    "funder": "UK Government",
    "amount_available": 50000000,
    "deadline": "2025-12-31",
    "eligible_sectors": ["Renewable Energy"]
}

message_id = sqs.send_funding_opportunity(funding)
print(f"Sent funding: {message_id}")
```

### Method 2: Using AWS SQS Directly

```python
import boto3
import json

sqs = boto3.client('sqs', region_name='eu-west-2')

# Investment queue
queue_url = "https://sqs.eu-west-2.amazonaws.com/.../service20-investment-opportunities"

message = {
    "type": "investment_opportunity",
    "payload": {
        "opportunity_id": "INV-2025-001",
        # ... rest of fields
    }
}

response = sqs.send_message(
    QueueUrl=queue_url,
    MessageBody=json.dumps(message)
)
```

### Method 3: Using AWS CLI

```bash
# Send investment opportunity
aws sqs send-message \
  --queue-url https://sqs.eu-west-2.amazonaws.com/.../service20-investment-opportunities \
  --message-body '{
    "type": "investment_opportunity",
    "payload": {
      "opportunity_id": "INV-2025-001",
      "title": "Solar Farm Project",
      "description": "...",
      "location": "Bristol, UK",
      "sector": "Solar Energy",
      "investment_amount": 25000000,
      "roi": 12.5
    }
  }'

# Send funding opportunity
aws sqs send-message \
  --queue-url https://sqs.eu-west-2.amazonaws.com/.../service20-funding-opportunities \
  --message-body '{
    "type": "funding_opportunity",
    "payload": {
      "funding_id": "FUND-2025-001",
      "title": "Government Fund",
      "description": "...",
      "funder": "UK Government",
      "amount_available": 50000000,
      "deadline": "2025-12-31",
      "eligible_sectors": ["Renewable Energy"]
    }
  }'
```

---

## Input Validation

The agents expect:

### Investment Opportunities
- ✅ Must have `opportunity_id` or `id` field
- ✅ Must have `title` and `description`
- ✅ Must have `location` and `sector`
- ✅ Must have `investment_amount`
- ⚠️ Optional: `roi`, `risk_level`, `timeline`, `net_zero_impact`

### Funding Opportunities
- ✅ Must have `funding_id` or `id` field
- ✅ Must have `title` and `description`
- ✅ Must have `funder` name
- ✅ Must have `amount_available` and `deadline`
- ✅ Must have `eligible_sectors` (array)
- ⚠️ Optional: `requirements`, `funding_range`, `funding_types`, `success_rate`

---

## Common Input Sectors

Both agents recognize these sector categories:

**Energy Generation:**
- Renewable Energy - Solar
- Renewable Energy - Wind
- Renewable Energy - Hydro
- Renewable Energy - Geothermal
- Renewable Energy - Biomass
- Hydrogen Technologies
- Nuclear Energy

**Energy Infrastructure:**
- Energy Storage
- Grid Infrastructure
- Smart Grid Technologies
- Energy Distribution

**Energy Use:**
- Energy Efficiency
- Building Retrofits
- Industrial Decarbonization
- Heat Pumps

**Transport:**
- Electric Vehicles
- Green Transport
- Aviation Decarbonization
- Maritime Decarbonization

**Carbon Management:**
- Carbon Capture and Storage
- Carbon Capture Utilization
- Nature-Based Solutions
- Afforestation

**Other:**
- Waste to Energy
- Circular Economy
- Water Management
- Sustainable Agriculture

---

## Input Size Limits

- **Description field:** No hard limit, but keep under 5000 characters for optimal processing
- **Array fields:** No hard limit on number of items
- **Number fields:** Standard float/integer ranges
- **Total message size:** SQS limit is 256 KB per message

---

## Testing Your Inputs

Run the basic example to test:

```bash
cd examples
python sqs_basic_example.py
```

This will send 3 investment opportunities and 3 funding opportunities to the queues.
