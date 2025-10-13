# CLAUDE.md - Funding Research Agent

This file provides guidance to Claude Code when working with this repository.

## Project Overview

The Funding Research Agent is a specialized LangGraph-based agent for finding funding opportunities for Net Zero and sustainability projects. It systematically searches for funders at regional, national, and global levels, extracting structured metadata about each opportunity.

## Architecture

### Core Components

1. **graph.py** - Main LangGraph workflow with nodes for:
   - Query generation
   - Parallel search execution
   - Structured extraction
   - Report generation

2. **state.py** - Type-safe state management:
   - `ResearchState`: Workflow state
   - `FunderMetadata`: Structured funder information

3. **configuration.py** - Configuration management:
   - Follows LangGraph Studio UI config patterns
   - Supports environment variables and runtime config
   - Multi-provider LLM support

4. **prompts.py** - All LLM prompts:
   - Query generation for each level
   - Structured extraction prompts
   - Report generation templates

5. **utils/search.py** - Search API integrations:
   - Tavily (recommended)
   - Exa (alternative)
   - DuckDuckGo (free fallback)

### Workflow

```
Initialize → Generate Queries → Execute Searches → Extract Funders → Advance Level
                 ↑                                                           ↓
                 └──────────────── (loop for each level) ───────────────────┘
                                                                             ↓
                                                                    Generate Report
```

## Key Commands

```bash
# Development with LangGraph Studio
uvx langgraph dev

# Run tests
bash run_test.sh
python tests/test_funding_research.py

# Run examples
python src/funding_researcher/examples/example_usage.py

# Install dependencies
uv pip install -e .
```

## Development Guidelines

### Adding New Features

**New Search API:**
1. Add async search function to `utils/search.py`
2. Update `SearchAPI` enum in `configuration.py`
3. Add conditional logic in `execute_searches()` in `graph.py`

**New Metadata Fields:**
1. Update `FunderMetadata` model in `state.py`
2. Update extraction prompt in `prompts.py`
3. Update report generation to include new fields

**Custom Research Levels:**
1. Update `current_level` type in `state.py`
2. Add new funder list to state
3. Update workflow logic in `graph.py`

### Configuration Pattern

Always follow the LangGraph Studio UI config pattern:

```python
field_name: Type = Field(
    default=value,
    metadata={
        "x_oap_ui_config": {
            "type": "slider|select|text|number",
            "default": value,
            "description": "User-friendly description",
            # Additional UI-specific config...
        }
    }
)
```

### Testing

When adding new functionality:
1. Add test case to `tests/test_funding_research.py`
2. Add example to `src/funding_researcher/examples/`
3. Update README.md with usage instructions

### Code Style

- Use type hints throughout
- Follow async/await patterns for I/O operations
- Add docstrings to all functions and classes
- Use descriptive variable names
- Keep functions focused and modular

## Relationship to Open Deep Research

This project is a specialized implementation based on the [Open Deep Research](../open-deep-research) framework:

**Shared Patterns:**
- LangGraph workflow architecture
- Configuration management approach
- Multi-provider LLM support
- Async search operations

**Specializations:**
- Custom state for funding research
- Structured funder metadata extraction
- Multi-level (regional/national/global) search strategy
- Report format optimized for funding applications

## Common Tasks

### Adding a New LLM Provider

1. Update `model_provider` field options in `configuration.py`
2. Add provider case in `get_model()` method
3. Add API key field with UI config
4. Test with the provider's models

### Customizing Search Queries

Edit the `QUERY_GENERATOR_PROMPT` in `prompts.py` to:
- Add more query templates
- Target specific funding databases
- Include industry-specific terms

### Adjusting Extraction Logic

Modify `FUNDER_EXTRACTOR_PROMPT` in `prompts.py` to:
- Add more detailed extraction instructions
- Handle edge cases better
- Extract additional metadata fields

### Changing Report Format

Update `REPORT_GENERATOR_PROMPT` in `prompts.py` to:
- Add new sections
- Reorder content
- Change formatting style

## Troubleshooting

### Search Returning Empty Results

- Check API keys are valid
- Try switching search API (DuckDuckGo as fallback)
- Reduce `max_concurrent_searches` to avoid rate limits
- Check search queries are being generated correctly

### Extraction Failing

- Verify LLM has enough context (check `max_tokens`)
- Try a more capable model (e.g., gpt-4o instead of gpt-4o-mini)
- Check JSON parsing in `extract_funders()` node
- Add more examples to extraction prompt

### Configuration Not Loading

- Ensure `.env` file exists and is properly formatted
- Check `from_runnable_config()` implementation
- Verify field names match environment variables (uppercase)
- Check LangGraph Studio configurable values

## Dependencies

Key dependencies (see `pyproject.toml` for full list):
- `langgraph>=0.2.58` - Workflow orchestration
- `langchain>=0.3.15` - LLM abstractions
- `langchain-openai>=0.2.14` - OpenAI integration
- `langchain-anthropic>=0.3.2` - Anthropic integration
- `tavily-python>=0.5.0` - Tavily search
- `duckduckgo-search>=7.1.0` - Free search option
- `pydantic>=2.10.3` - Data validation

## Best Practices

1. **Always test with multiple search APIs** - Don't rely on a single provider
2. **Use structured outputs** - Leverage Pydantic models for type safety
3. **Handle LLM failures gracefully** - Add try/except and fallbacks
4. **Optimize for concurrency** - Use async/await for I/O operations
5. **Keep prompts specific** - More specific prompts yield better results
6. **Document configuration** - Use metadata for UI descriptions
7. **Test end-to-end** - Run full workflows, not just unit tests

## Environment Setup

Minimum required:
```bash
OPENAI_API_KEY=sk-...          # Or another LLM provider
TAVILY_API_KEY=tvly-...        # Or use DuckDuckGo (no key needed)
```

Recommended for production:
```bash
# Primary LLM
OPENAI_API_KEY=sk-...

# Search
TAVILY_API_KEY=tvly-...

# Observability
LANGSMITH_API_KEY=...
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=funding-research-agent

# Configuration
MODEL_PROVIDER=openai
MODEL_NAME=gpt-4o-mini
SEARCH_API=tavily
MAX_RESULTS_PER_QUERY=10
MAX_CONCURRENT_SEARCHES=3
```

## File Organization

```
src/funding_researcher/
├── __init__.py           # Package initialization
├── graph.py              # Main workflow (⚡ core logic here)
├── state.py              # State and data models
├── configuration.py      # Configuration management
├── prompts.py           # All LLM prompts
├── utils/
│   ├── __init__.py
│   └── search.py        # Search API integrations
└── examples/
    └── example_usage.py  # Usage examples

tests/
└── test_funding_research.py  # Test cases

# Configuration files
pyproject.toml           # Python project config
langgraph.json          # LangGraph config
.env.example            # Environment template
```

## Extension Points

The agent is designed to be extended:

1. **Custom Search Sources**: Add specialized funding databases
2. **Enhanced Extraction**: Use structured outputs for better parsing
3. **Multi-Agent**: Add specialist agents for different funding types
4. **Caching**: Add Redis/file cache for search results
5. **Filtering**: Add post-processing to filter by eligibility
6. **Ranking**: Score funders by relevance/fit
7. **Templates**: Generate application templates for top funders

## Related Projects

- [Open Deep Research](../open-deep-research) - General-purpose deep research agent
- [Service7](../service7) - Academic research agent for Net Zero topics

Both share similar architectures but serve different purposes.
