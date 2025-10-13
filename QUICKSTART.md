# Quick Start Guide - Funding Research Agent

Get started with the Funding Research Agent in 5 minutes.

## Prerequisites

- Python 3.11+
- OpenAI API key (or Anthropic/Google/Groq)
- Tavily API key (optional - can use DuckDuckGo for free)

## Installation

```bash
# 1. Navigate to project
cd funding-research-agent

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -e .

# 4. Configure environment
cp .env.example .env
# Edit .env and add your API keys
```

## Minimal .env Setup

```bash
# Required: At least one LLM provider
OPENAI_API_KEY=sk-your-key-here

# Optional: Better search results
TAVILY_API_KEY=tvly-your-key-here

# Will use DuckDuckGo (free) if no search API key provided
```

## Usage Options

### Option 1: LangGraph Studio (Recommended)

```bash
uvx langgraph dev
```

Then:
1. Open browser at http://localhost:8123
2. Fill in project details in the UI
3. Click "Run" and watch the research happen
4. Export results

### Option 2: Python Script

Create `my_research.py`:

```python
import asyncio
from funding_researcher.graph import graph

async def find_funding():
    initial_state = {
        "messages": [],
        "project_description": "Your project description here",
        "project_location": "Your location",
        "project_sectors": ["Energy", "Sustainability"],
        "funding_types": ["grant", "loan", "equity"],
        "current_level": "regional",
        "regional_funders": [],
        "national_funders": [],
        "global_funders": [],
        "search_queries": [],
        "search_results": [],
        "final_report": "",
        "total_funders_found": 0,
    }

    result = await graph.ainvoke(initial_state)
    print(f"Found {result['total_funders_found']} funders!")
    print(result['final_report'])

asyncio.run(find_funding())
```

Run it:
```bash
python my_research.py
```

### Option 3: Use Examples

```bash
# Interactive example
python src/funding_researcher/examples/example_usage.py

# Test scripts
python tests/test_funding_research.py
```

## Example: Solar Farm Project

```python
import asyncio
from funding_researcher.graph import graph

async def main():
    state = {
        "messages": [],
        "project_description": (
            "50MW solar farm with battery storage providing power to 5,000 homes. "
            "Includes community benefit fund and biodiversity measures. Cost: £40M."
        ),
        "project_location": "Scotland, UK",
        "project_sectors": ["Energy", "Sustainability", "Infrastructure"],
        "funding_types": ["grant", "loan", "equity"],
        "current_level": "regional",
        "regional_funders": [],
        "national_funders": [],
        "global_funders": [],
        "search_queries": [],
        "search_results": [],
        "final_report": "",
        "total_funders_found": 0,
    }

    print("🔍 Researching funding opportunities...")
    result = await graph.ainvoke(state)

    print(f"\n✅ Found {result['total_funders_found']} funders")
    print(f"   • Regional: {len(result['regional_funders'])}")
    print(f"   • National: {len(result['national_funders'])}")
    print(f"   • Global: {len(result['global_funders'])}")

    # Save report
    with open("funding_report.md", "w") as f:
        f.write(result["final_report"])
    print("\n💾 Report saved to funding_report.md")

asyncio.run(main())
```

## What Gets Returned

For each funder found:

```python
FunderMetadata(
    name="Green Growth Fund",
    organization="Scottish Enterprise",
    level="regional",
    location="Scotland",
    opportunity_type="Grant",
    award_range="£25k - £2m",
    sectors=["Energy", "Sustainability"],
    registration_details="Applications open year-round",
    eligibility="Scottish SMEs and startups",
    website="https://...",
    contact_info="greenfunds@scotent.co.uk",
    additional_notes="Focus on Net Zero projects",
    source_url="https://..."
)
```

## Configuration

You can configure the agent via:

**1. Config object:**
```python
config = {
    "configurable": {
        "model_provider": "openai",
        "model_name": "gpt-4o-mini",
        "search_api": "tavily",
        "max_results_per_query": 10,
    }
}

result = await graph.ainvoke(state, config)
```

**2. Environment variables:**
```bash
MODEL_PROVIDER=openai
MODEL_NAME=gpt-4o-mini
SEARCH_API=tavily
```

**3. LangGraph Studio UI** (most user-friendly)

## Common Use Cases

### Research for Specific Location

```python
"project_location": "Manchester, UK"  # City-level
"project_location": "Scotland"         # Region-level
"project_location": "United Kingdom"   # Country-level
```

### Target Specific Funding Types

```python
"funding_types": ["grant"]                      # Only grants
"funding_types": ["grant", "loan"]              # Grants and loans
"funding_types": ["grant", "loan", "equity"]    # All types
```

### Focus on Sectors

```python
"project_sectors": ["Energy"]                   # Single sector
"project_sectors": [
    "Energy",
    "Sustainability",
    "Infrastructure"
]  # Multiple sectors
```

## Troubleshooting

**No results found:**
- Check your project description is detailed enough
- Try broader location (e.g., "UK" instead of "Small Town, UK")
- Switch search API: `"search_api": "duckduckgo"`

**API errors:**
- Verify API keys in `.env`
- Check API rate limits
- Try reducing `max_concurrent_searches` to 1

**Import errors:**
- Ensure you ran `pip install -e .`
- Activate virtual environment
- Check Python version is 3.11+

**Slow performance:**
- This is normal - research takes 2-5 minutes per level
- Use LangGraph Studio to see progress in real-time
- Consider using faster models (gpt-4o-mini vs gpt-4o)

## Next Steps

1. **Customize prompts** in `src/funding_researcher/prompts.py`
2. **Add more sectors** to match your project
3. **Tune search queries** for your specific domain
4. **Export results** to CSV or database
5. **Integrate** into your application workflow

## Full Documentation

See [README.md](README.md) for complete documentation.

## Support

- Check [CLAUDE.md](CLAUDE.md) for development guidelines
- Review [examples](src/funding_researcher/examples/) for more use cases
- See [tests](tests/) for additional patterns

Happy funding research! 🚀
