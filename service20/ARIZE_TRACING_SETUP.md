# Arize Phoenix Tracing Setup Guide

## Overview

This guide explains how to add Arize Phoenix tracing to Service20 to monitor LLM calls and research operations.

## Prerequisites

1. Arize account with API access
2. Space ID: `U3BhY2U6MjUwOk15bW0=`
3. Arize API Key (obtain from Arize dashboard)

## Installation

The required packages have been added to `pyproject.toml`:

```toml
"arize-phoenix>=5.0.0",
"openinference-instrumentation-langchain>=0.1.0",
"opentelemetry-sdk>=1.20.0",
"opentelemetry-exporter-otlp>=1.20.0",
```

Install them with:

```bash
pip install arize-phoenix openinference-instrumentation-langchain opentelemetry-sdk opentelemetry-exporter-otlp
```

## Configuration

### Step 1: Add API Key to .env

Add these lines to your `.env` file:

```bash
# Arize Phoenix Configuration
ARIZE_API_KEY=your_actual_arize_api_key_here
ARIZE_SPACE_ID=U3BhY2U6MjUwOk15bW0=
```

**Important:** Replace `your_actual_arize_api_key_here` with your real Arize API key.

### Step 2: Get Your Arize API Key

1. Go to https://app.arize.com
2. Navigate to Settings → API Keys
3. Create a new API key or copy an existing one
4. Paste it into your `.env` file

## Testing the Integration

### Quick Test

Run the test script to verify tracing is working:

```bash
python test_arize_tracing.py
```

This will:
1. Initialize Arize Phoenix tracing
2. Run a simple research query about Copenhagen renewable energy
3. Send traces to Arize
4. Display results and confirmation

### Expected Output

```
================================================================================
Setting up Arize Phoenix Tracing
================================================================================

Arize Configuration:
  Space ID: U3BhY2U6MjUwOk15bW0=
  API Key: ****abcd...

✓ Phoenix tracer registered with Arize
✓ LangChain instrumented

================================================================================
Running Simple Research Test
================================================================================

[... research output ...]

✓ Research completed successfully
✓ Traces should now be visible in Arize
```

## Viewing Traces in Arize

1. Go to https://app.arize.com
2. Select Space: `U3BhY2U6MjUwOk15bW0=`
3. Navigate to the "Traces" section
4. Look for project: `service20-research`
5. You should see traces for:
   - LLM calls (OpenAI, Anthropic, etc.)
   - Research iterations
   - Tool calls (Tavily search, etc.)
   - Database operations

## Integration with Existing Scripts

### Adding Tracing to Any Script

To add Arize tracing to any Python script that uses LangChain:

```python
import os
from phoenix.otel import register
from openinference.instrumentation.langchain import LangChainInstrumentor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup Arize tracing
def setup_arize_tracing():
    ARIZE_API_KEY = os.getenv("ARIZE_API_KEY")
    ARIZE_SPACE_ID = os.getenv("ARIZE_SPACE_ID", "U3BhY2U6MjUwOk15bW0=")

    if not ARIZE_API_KEY:
        print("WARNING: ARIZE_API_KEY not found, skipping tracing")
        return None

    # Register Phoenix with Arize
    tracer_provider = register(
        project_name="your-project-name",
        endpoint="https://app.arize.com/v1/traces",
        headers={
            "space-id": ARIZE_SPACE_ID,
            "api-key": ARIZE_API_KEY
        }
    )

    # Instrument LangChain
    LangChainInstrumentor().instrument(tracer_provider=tracer_provider)

    return tracer_provider

# Call this at the start of your script
setup_arize_tracing()

# Your existing code here...
```

### Example: Adding to research_city_opportunity.py

Add these lines after the imports:

```python
from phoenix.otel import register
from openinference.instrumentation.langchain import LangChainInstrumentor

# Setup Arize tracing (before running research)
ARIZE_API_KEY = os.getenv("ARIZE_API_KEY")
if ARIZE_API_KEY:
    tracer_provider = register(
        project_name="service20-city-research",
        endpoint="https://app.arize.com/v1/traces",
        headers={
            "space-id": os.getenv("ARIZE_SPACE_ID", "U3BhY2U6MjUwOk15bW0="),
            "api-key": ARIZE_API_KEY
        }
    )
    LangChainInstrumentor().instrument(tracer_provider=tracer_provider)
```

## What Gets Traced

With this setup, Arize will automatically capture:

### LLM Calls
- Model used (GPT-4, Claude, etc.)
- Prompts sent
- Responses received
- Token usage
- Latency
- Cost (if configured)

### Tool Calls
- Tavily searches
- PostgreSQL queries
- Custom tools
- MCP server calls

### Research Workflow
- Research iterations
- Search queries
- Summarization steps
- Report generation

### Metadata
- Thread IDs
- User information (if available)
- Configuration settings
- Error messages and stack traces

## Monitoring and Alerts

### Key Metrics to Watch

1. **Latency**: How long do research queries take?
2. **Token Usage**: Are we staying within budget?
3. **Error Rate**: Are LLM calls failing?
4. **Tool Usage**: Which tools are being used most?
5. **Cost**: How much are we spending on LLM calls?

### Setting Up Alerts

In Arize dashboard:
1. Go to Alerts
2. Create alerts for:
   - High latency (> 60 seconds)
   - High error rate (> 5%)
   - Unusual token usage spikes
   - Failed API calls

## Troubleshooting

### Traces Not Appearing

1. **Check API Key**: Verify `ARIZE_API_KEY` is set correctly
2. **Check Network**: Ensure https://app.arize.com is accessible
3. **Check Space ID**: Verify you're looking in the correct space
4. **Check Project Name**: Traces are organized by project name
5. **Wait a Moment**: Traces may take 10-30 seconds to appear

### Import Errors

If you see `ModuleNotFoundError`:

```bash
pip install --upgrade arize-phoenix openinference-instrumentation-langchain
```

### Authentication Errors

If you see `401 Unauthorized`:
- Verify your `ARIZE_API_KEY` is correct
- Check that the API key hasn't expired
- Ensure you have access to the space

## Best Practices

1. **Always Include Context**: Add meaningful metadata to traces
2. **Use Descriptive Project Names**: Makes filtering easier
3. **Monitor Costs**: Set up budget alerts in Arize
4. **Review Traces Regularly**: Look for optimization opportunities
5. **Test in Dev First**: Verify tracing works before production

## Next Steps

1. ✅ Add `ARIZE_API_KEY` to `.env` file
2. ✅ Run `python test_arize_tracing.py` to verify setup
3. ⏳ Add tracing to `research_city_opportunity.py`
4. ⏳ Add tracing to `matching_agent.py`
5. ⏳ Add tracing to other agent scripts
6. ⏳ Set up monitoring and alerts in Arize dashboard

## References

- Arize Dashboard: https://app.arize.com
- Arize Documentation: https://docs.arize.com
- Phoenix Documentation: https://docs.arize.com/phoenix
- OpenInference: https://github.com/Arize-ai/openinference

## Support

For issues or questions:
- Arize Support: support@arize.com
- Phoenix GitHub: https://github.com/Arize-ai/phoenix/issues
