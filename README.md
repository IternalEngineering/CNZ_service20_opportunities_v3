# Funding Research Agent for Net Zero Projects

An intelligent deep research agent that finds funding opportunities for Net Zero and sustainability projects across regional, national, and global levels. Built on LangGraph and powered by multiple LLM providers and search APIs.

## Features

- 🔍 **Multi-Level Research**: Automatically searches for funders at regional, national, and global levels
- 🤖 **AI-Powered**: Uses LLMs to generate targeted search queries and extract structured funder information
- 🌐 **Multiple Search APIs**: Supports Tavily, Exa, and DuckDuckGo for comprehensive web research
- 📊 **Structured Output**: Returns detailed metadata for each funding opportunity
- 🔧 **Configurable**: Flexible configuration via environment variables or UI
- 📝 **Comprehensive Reports**: Generates detailed markdown reports with all findings

## Funder Metadata Structure

Each funding opportunity includes:

- **Name**: Funding program or opportunity name
- **Organization**: Provider of the funding
- **Level**: Regional, national, or global
- **Location**: Geographic coverage area
- **Opportunity Type**: Grant, Loan, Equity, Tax Credit, etc.
- **Award Range**: Funding amount or range available
- **Sectors**: Relevant sectors (Energy, Sustainability, Infrastructure, etc.)
- **Registration Details**: Application process and timing
- **Eligibility**: Who can apply
- **Website**: Official program URL
- **Contact Info**: Contact details
- **Additional Notes**: Other relevant information
- **Source URL**: Where the information was found

## Installation

### Prerequisites

- Python 3.11 or higher
- UV package manager (recommended) or pip
- API keys for at least one LLM provider (OpenAI, Anthropic, etc.)
- API key for a search service (Tavily recommended, or use DuckDuckGo for free)

### Setup

1. **Clone and navigate to the project:**
```bash
cd funding-research-agent
```

2. **Create and activate virtual environment:**
```bash
# Using uv (recommended)
uv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Or using standard Python
python -m venv venv
source venv/bin/activate
```

3. **Install dependencies:**
```bash
# Using uv
uv pip install -e .

# Or using pip
pip install -e .
```

4. **Configure environment variables:**
```bash
cp .env.example .env
# Edit .env and add your API keys
```

Required in `.env`:
```bash
# Choose at least one LLM provider
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
GROQ_API_KEY=...

# Choose at least one search API (or use DuckDuckGo - no key needed)
TAVILY_API_KEY=tvly-...
EXA_API_KEY=...

# Optional: LangSmith for tracing
LANGSMITH_API_KEY=...
LANGSMITH_TRACING=true
```

## Usage

### Quick Start with LangGraph Studio

The easiest way to use the agent is with LangGraph Studio:

```bash
uvx langgraph dev
```

This opens an interactive UI where you can:
- Configure all settings through the UI
- Input project details
- Watch the research process in real-time
- Export results

### Python API Usage

```python
import asyncio
from funding_researcher.graph import graph
from funding_researcher.state import ResearchState

async def find_funding():
    initial_state: ResearchState = {
        "messages": [],
        "project_description": (
            "Solar farm project providing renewable energy to 5,000 homes. "
            "Includes battery storage and community benefits. Total cost: £40M."
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

    config = {
        "configurable": {
            "model_provider": "openai",
            "model_name": "gpt-4o-mini",
            "search_api": "tavily",
        }
    }

    result = await graph.ainvoke(initial_state, config)

    print(f"Found {result['total_funders_found']} funders")
    print(f"Regional: {len(result['regional_funders'])}")
    print(f"National: {len(result['national_funders'])}")
    print(f"Global: {len(result['global_funders'])}")
    print("\n" + result["final_report"])

asyncio.run(find_funding())
```

### Command Line Testing

Run the included test scripts:

```bash
# Test with solar farm example
bash run_test.sh

# Test with EV charging example
bash run_test.sh ev

# Or directly with Python
python tests/test_funding_research.py
python tests/test_funding_research.py ev
```

### Interactive Examples

```bash
python src/funding_researcher/examples/example_usage.py
```

## Configuration Options

### Model Configuration

- **model_provider**: `openai`, `anthropic`, `google`, or `groq`
- **model_name**: Specific model (e.g., `gpt-4o-mini`, `claude-3-5-sonnet-20241022`)
- **temperature**: 0.0 to 2.0 (default: 0.0 for consistency)
- **max_tokens**: Maximum response tokens (default: 4000)

### Search Configuration

- **search_api**: `tavily`, `exa`, or `duckduckgo`
- **max_results_per_query**: 5-20 (default: 10)
- **max_concurrent_searches**: 1-10 (default: 3)

### Via Configuration Object

```python
config = {
    "configurable": {
        "model_provider": "openai",
        "model_name": "gpt-4o-mini",
        "temperature": 0.0,
        "max_tokens": 4000,
        "search_api": "tavily",
        "max_results_per_query": 10,
        "max_concurrent_searches": 3,
    }
}
```

### Via Environment Variables

Set in `.env` file:
```bash
MODEL_PROVIDER=openai
MODEL_NAME=gpt-4o-mini
SEARCH_API=tavily
MAX_RESULTS_PER_QUERY=10
```

## How It Works

The agent operates in a systematic workflow:

1. **Initialize**: Sets up research state and parameters
2. **For Each Level (Regional → National → Global)**:
   - **Generate Queries**: Creates 5-8 targeted search queries using LLM
   - **Execute Searches**: Performs parallel web searches using configured API
   - **Extract Funders**: Uses LLM to parse search results into structured metadata
   - **Advance Level**: Moves to next geographic level
3. **Generate Report**: Creates comprehensive markdown report with all findings

### Search Strategy

- **Regional**: Local government schemes, regional development agencies, local sustainability funds
- **National**: National innovation programs, government departments, development banks
- **Global**: International climate finance, multinational development banks, global sustainability funds

## Example Output

```markdown
# Funding Research Report

## Executive Summary

Found 23 funding opportunities across regional, national, and global levels:
- Regional: 8 opportunities
- National: 10 opportunities
- Global: 5 opportunities

## Regional Funding Opportunities

### 1. Scottish Enterprise Green Growth Fund
- **Organization**: Scottish Enterprise
- **Type**: Grant
- **Award**: £25k - £2m
- **Sectors**: Energy, Sustainability, Manufacturing
- **Registration**: Applications open year-round
- **Eligibility**: Scottish SMEs and startups
- **Website**: https://...
- **Contact**: greenf unds@scotent.co.uk

[... more funders ...]

## Application Strategy Recommendations

1. **Priority Funders**: Start with Scottish Enterprise and Innovate UK
2. **Timeline**: Q1 2025 for regional, Q2 for national programs
3. **Success Tips**: Emphasize community benefits and job creation

[... detailed analysis ...]
```

## Project Structure

```
funding-research-agent/
├── src/
│   └── funding_researcher/
│       ├── __init__.py
│       ├── graph.py              # Main LangGraph implementation
│       ├── state.py              # State definitions
│       ├── configuration.py      # Configuration management
│       ├── prompts.py            # LLM prompts
│       ├── utils/
│       │   ├── search.py         # Search API integrations
│       │   └── __init__.py
│       └── examples/
│           └── example_usage.py  # Usage examples
├── tests/
│   └── test_funding_research.py  # Test scripts
├── pyproject.toml                # Project configuration
├── langgraph.json                # LangGraph configuration
├── .env.example                  # Environment template
├── README.md                     # This file
└── run_test.sh                   # Test runner script
```

## Development

### Running Tests

```bash
# With environment loaded
bash run_test.sh

# Direct Python execution
python -m pytest tests/
```

### Code Quality

```bash
# Linting
ruff check src/

# Type checking
mypy src/
```

### Adding New Features

The modular design makes it easy to extend:

- **New search APIs**: Add to `utils/search.py`
- **Additional metadata fields**: Update `FunderMetadata` in `state.py`
- **Custom prompts**: Modify `prompts.py`
- **Extra research levels**: Update workflow in `graph.py`

## Troubleshooting

### Common Issues

**"No API key found"**
- Ensure `.env` file exists and contains valid API keys
- Check that environment variables are properly loaded

**"Search failed"**
- Try switching to DuckDuckGo (no API key required): `search_api: "duckduckgo"`
- Check API key validity and rate limits

**"LLM returned invalid JSON"**
- The agent has fallbacks for this, but ensure you're using a capable model
- Try increasing `temperature` slightly (0.1-0.2) for more creative outputs

**"Rate limit errors"**
- Reduce `max_concurrent_searches` to 1 or 2
- Add delays between requests
- Upgrade API plan

### Getting Help

- Check the [examples](src/funding_researcher/examples/) for working code
- Review [LangGraph documentation](https://langchain-ai.github.io/langgraph/)
- Open an issue for bugs or feature requests

## Comparison with Open Deep Research

This agent is built on the same framework as [Open Deep Research](../open-deep-research) but specialized for funding research:

**Similarities:**
- LangGraph-based workflow
- Multi-provider LLM support
- Configurable search APIs
- Structured output

**Key Differences:**
- **Purpose-Built**: Specifically designed for funding research with funder-specific metadata
- **Multi-Level Search**: Regional → National → Global progression
- **Structured Extraction**: Custom schemas for funding opportunity data
- **Actionable Output**: Report format optimized for grant applications

## License

MIT License - see LICENSE file for details

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure code passes linting and type checks
5. Submit a pull request

## Acknowledgments

Built with:
- [LangGraph](https://github.com/langchain-ai/langgraph) - Workflow orchestration
- [LangChain](https://github.com/langchain-ai/langchain) - LLM integrations
- [Tavily](https://tavily.com/) - Web search API
- [OpenAI](https://openai.com/) / [Anthropic](https://anthropic.com/) - Language models

Inspired by the [Open Deep Research](https://github.com/langchain-ai/open-deep-research) project.
