# Service20 Agent Input/Output Formats

## Overview
Both the **NetZeroInvestmentOpportunityHandler** and **NetZeroFundingOpportunityHandler** are fully configured to handle standardized input/output formats through AWS SQS message queues.

---

## 1. NetZeroInvestmentOpportunityHandler

### Input Format (Investment Opportunities)

The agent accepts investment opportunities via SQS messages with the following structure:

```python
{
    "opportunity_id": str,           # Unique identifier (e.g., "INV-2025-001")
    "title": str,                    # Project title
    "description": str,              # Detailed project description
    "location": str,                 # Geographic location
    "sector": str,                   # Industry sector (e.g., "Renewable Energy - Solar")
    "investment_amount": float,      # Required investment amount
    "roi": float,                    # Expected return on investment (%)
    "risk_level": str,              # Risk assessment (e.g., "medium", "low-medium")
    "timeline": str,                # Project completion timeline (optional)
    "net_zero_impact": {            # Environmental impact metrics (optional)
        "co2_reduction_tons_per_year": float,
        "equivalent_homes_powered": int,
        "energy_savings_mwh_per_year": float
    }
}
```

**Example Input:**
```python
{
    "opportunity_id": "INV-2025-001",
    "title": "50MW Solar Farm Development in Bristol",
    "description": "Large-scale solar farm development project...",
    "location": "Bristol, UK",
    "sector": "Renewable Energy - Solar",
    "investment_amount": 25000000,  # £25M
    "roi": 12.5,
    "risk_level": "medium",
    "timeline": "24 months to completion",
    "net_zero_impact": {
        "co2_reduction_tons_per_year": 24750,
        "equivalent_homes_powered": 15000
    }
}
```

### Deep Research Prompt Generated
The agent automatically constructs a comprehensive research prompt including:
1. Market analysis for sector & location
2. Competitive landscape and similar projects
3. Regulatory environment and compliance requirements
4. Risk factors and mitigation strategies
5. **Potential funding sources that might match this opportunity**
6. Expected ROI and financial projections
7. Environmental impact and Net Zero contribution
8. Key stakeholders and partnerships

### Output Format (Research Results)

After deep research, the agent produces:

```python
{
    "research_id": str,              # Same as opportunity_id from input
    "opportunity_type": "investment",
    "research_brief": str,           # Summary of research scope
    "final_report": str,             # Full PROJECT PROPOSAL in markdown format
    "findings": list,                # List of detailed research notes
    "opportunity_data": dict         # Original opportunity data
}
```

**Final Report Structure (Markdown):**
```markdown
# [Project Title]

## Executive Summary
Brief overview of the proposed project and key value proposition

## Market Opportunity
Analysis of the market need, size, and growth potential based on research

## Project Description
Detailed description of the proposed net zero initiative/investment

## Sustainability Impact
Quantified environmental benefits (CO2 reduction, energy savings, etc.)

## Financial Analysis
- Estimated investment required
- Revenue model and ROI projections
- Break-even timeline
- Risk factors

## Implementation Plan
Key milestones, timeline, and resource requirements

## Competitive Advantage
What makes this opportunity unique or superior to alternatives

## Conclusion
Summary of why this is a compelling investment opportunity

### Sources
[1] Source Title: URL
[2] Source Title: URL
...
```

---

## 2. NetZeroFundingOpportunityHandler

### Input Format (Funding Opportunities)

The agent accepts funding opportunities via SQS messages:

```python
{
    "funding_id": str,               # Unique identifier (e.g., "FUND-2025-001")
    "title": str,                    # Funding program title
    "description": str,              # Program description
    "funder": str,                   # Funding organization name
    "amount_available": float,       # Total fund size
    "deadline": str,                 # Application deadline (ISO date or "Rolling")
    "eligible_sectors": list[str],   # List of eligible sectors
    "requirements": list[str],       # List of eligibility requirements
    "funding_range": {              # Min/max funding amounts (optional)
        "min": float,
        "max": float
    },
    "funding_types": list[str],     # Types of funding (optional: "Debt", "Equity", etc.)
    "success_rate": float           # Historical approval rate (optional: 0.0-1.0)
}
```

**Example Input:**
```python
{
    "funding_id": "FUND-2025-001",
    "title": "UK Net Zero Innovation Fund 2025",
    "description": "The UK Government's flagship funding program...",
    "funder": "UK Department for Energy Security and Net Zero",
    "amount_available": 50000000,  # £50M
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

### Deep Research Prompt Generated
The agent automatically constructs a research prompt including:
1. Funder background, history, and previous funding patterns
2. Application requirements and success factors
3. Eligible project types and criteria
4. Competition analysis (application rates, success rates)
5. **Potential investment opportunities that match this funding**
6. Strategic approach for applications
7. Similar past funding awards and their outcomes
8. Key contacts and networking opportunities

### Output Format (Research Results)

Identical structure to investment agent output:

```python
{
    "research_id": str,              # Same as funding_id from input
    "opportunity_type": "funding",
    "research_brief": str,
    "final_report": str,             # Full analysis in markdown format
    "findings": list,
    "opportunity_data": dict         # Original funding data
}
```

---

## 3. SQS Queue Configuration

### Queue Names
- **Investment Queue:** `service20-investment-opportunities`
- **Funding Queue:** `service20-funding-opportunities`
- **Results Queue:** `service20-research-results`

### Queue Settings
```python
visibility_timeout = 300      # 5 minutes
message_retention = 345600    # 4 days
receive_wait_time = 20        # Long polling
max_messages = 10             # Batch size
```

### Environment Variables Required
```bash
# AWS Credentials
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=eu-west-2

# Queue URLs (optional - auto-created if not provided)
SQS_INVESTMENT_QUEUE_URL=https://sqs.eu-west-2.amazonaws.com/...
SQS_FUNDING_QUEUE_URL=https://sqs.eu-west-2.amazonaws.com/...
SQS_RESULTS_QUEUE_URL=https://sqs.eu-west-2.amazonaws.com/...

# AI Model APIs
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key  # Optional
TAVILY_API_KEY=your_key     # For web search
```

---

## 4. Message Flow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     External Systems                         │
│            (Investment/Funding Identification)               │
└──────────────────────────┬──────────────────────────────────┘
                           │
                ┌──────────┴──────────┐
                │   AWS SQS Queues    │
                │                     │
    ┌───────────┤  Investment Queue   │
    │           │  Funding Queue      │
    │           │  Results Queue      │
    │           └──────────┬──────────┘
    │                      │
    │           ┌──────────┴──────────┐
    │           │  Enhanced Handlers  │
    │           │  (with Deep Research│
    │           │   Integration)      │
    │           └──────────┬──────────┘
    │                      │
    │           ┌──────────┴──────────────────────────┐
    │           │  ResearchOrchestrator               │
    │           │  - Builds research prompt           │
    │           │  - Invokes deep_researcher workflow │
    │           └──────────┬──────────────────────────┘
    │                      │
    │           ┌──────────┴──────────────┐
    │           │  Deep Researcher        │
    │           │  (LangGraph Workflow)   │
    │           │                         │
    │           │  1. Clarify with user   │
    │           │  2. Write research brief│
    │           │  3. Research supervisor │
    │           │  4. Final report gen    │
    │           └──────────┬──────────────┘
    │                      │
    │           ┌──────────┴──────────────┐
    │           │  Research Results       │
    │           │  - research_id          │
    │           │  - research_brief       │
    │           │  - final_report         │
    │           │  - findings             │
    │           └──────────┬──────────────┘
    │                      │
    └──────────────────────┤
                           │
                ┌──────────┴──────────┐
                │  Results Queue      │
                │  (for downstream    │
                │   processing)       │
                └─────────────────────┘
```

---

## 5. Configuration Options

### LangGraph Configuration
Both agents can be configured with:

```python
config = RunnableConfig(
    configurable={
        "research_model": "gpt-4o",              # Main research model
        "compression_model": "gpt-4o-mini",      # Compression/summarization
        "final_report_model": "gpt-4o",          # Report generation
        "max_concurrent_research_units": 3,      # Parallel research agents
        "max_researcher_iterations": 10,         # Max research depth
        "allow_clarification": False,            # Skip user clarification
    }
)
```

### Handler Execution Modes

**1. Manual Single Research:**
```python
orchestrator = ResearchOrchestrator(config)
result = await orchestrator.conduct_research_for_opportunity(
    opportunity_data,
    opportunity_type="investment"  # or "funding"
)
```

**2. Automatic Queue Processing (Single Agent):**
```python
await run_enhanced_investment_handler(config, max_iterations=None)
# or
await run_enhanced_funding_handler(config, max_iterations=None)
```

**3. Parallel Processing (Both Agents):**
```python
await run_enhanced_handlers_parallel(config, max_iterations=None)
```

---

## 6. Usage Examples

### Send Investment Opportunity
```python
from open_deep_research.sqs_config import get_sqs_manager

sqs = get_sqs_manager()

opportunity = {
    "opportunity_id": "INV-2025-001",
    "title": "Smart Grid Battery Storage",
    "description": "100MWh grid-scale battery storage...",
    "location": "Scotland, UK",
    "sector": "Energy Storage",
    "investment_amount": 45000000,
    "roi": 16.8,
    "risk_level": "medium"
}

message_id = sqs.send_investment_opportunity(opportunity)
print(f"Sent: {message_id}")
```

### Send Funding Opportunity
```python
funding = {
    "funding_id": "FUND-2025-001",
    "title": "UK Net Zero Innovation Fund",
    "description": "Government funding for innovative projects...",
    "funder": "UK Department for Energy Security",
    "amount_available": 50000000,
    "deadline": "2025-12-31",
    "eligible_sectors": ["Renewable Energy", "Energy Storage"],
    "requirements": ["UK-based", "Match funding 25%"]
}

message_id = sqs.send_funding_opportunity(funding)
print(f"Sent: {message_id}")
```

### Process Messages
```python
# Run enhanced handlers with automatic research
config = RunnableConfig(
    configurable={
        "research_model": "gpt-4o",
        "compression_model": "gpt-4o-mini",
        "max_concurrent_research_units": 2,
        "allow_clarification": False
    }
)

# Process both queues in parallel
await run_enhanced_handlers_parallel(config, max_iterations=10)
```

### Retrieve Research Results
```python
sqs = get_sqs_manager()

messages = sqs.receive_research_results()

for msg in messages:
    payload = msg['payload']
    print(f"Research ID: {payload['research_id']}")
    print(f"Type: {payload['opportunity_type']}")
    print(f"Report:\n{payload['final_report']}")

    # Delete message after processing
    sqs.delete_message(
        sqs.config.results_queue_url,
        msg['receipt_handle']
    )
```

---

## 7. Key Features

### ✅ Both Agents Are Fully Configured For:

1. **Standardized Input/Output Formats**
   - Well-defined JSON schemas
   - Comprehensive field validation
   - Flexible optional fields

2. **SQS Message Queue Integration**
   - Automatic queue creation
   - Long polling for efficiency
   - Message persistence (4 days)
   - Error handling and retries

3. **Deep Research Integration**
   - Automatic prompt generation
   - Parallel research execution
   - Comprehensive source citations
   - Markdown-formatted reports

4. **Bidirectional Matching Potential**
   - Investment agent identifies potential funders
   - Funding agent identifies potential investments
   - Framework ready for matching algorithm implementation

5. **Flexible Configuration**
   - Multiple LLM providers supported
   - Adjustable research depth
   - Configurable concurrency
   - Model selection per task

### 🚧 TODO: Matching Logic Implementation

Currently marked as TODO in both agents:
- `_check_funding_matches()` (Investment handler)
- `_check_investment_matches()` (Funding handler)

These methods exist but need implementation to:
- Parse research findings
- Extract matching criteria
- Query opposite queue
- Calculate compatibility scores
- Send match notifications

---

## 8. Integration Checklist

For external systems integrating with these agents:

- [ ] Configure AWS SQS access (credentials, region)
- [ ] Set up API keys (OpenAI, Tavily)
- [ ] Create or reference queue URLs
- [ ] Structure input messages per schema
- [ ] Poll results queue for research outputs
- [ ] Handle message deletion after processing
- [ ] Implement error handling for failed research
- [ ] Configure LangGraph parameters for use case
- [ ] Set up monitoring/logging integration
- [ ] Test end-to-end message flow

---

## Conclusion

Both the **NetZeroInvestmentOpportunityHandler** and **NetZeroFundingOpportunityHandler** are production-ready with:
- ✅ Fully defined input/output formats
- ✅ Complete SQS queue integration
- ✅ Deep research workflow integration
- ✅ Comprehensive configuration options
- ✅ Working example code
- ⚠️ Matching logic framework ready (needs implementation)

The agents can be deployed immediately and will generate high-quality research reports for Net Zero investment and funding opportunities.
