# SQS Integration Quick Start Guide

Get started with SQS message queues for investment and funding opportunity communication in under 5 minutes.

## Prerequisites

- Python 3.10+
- AWS account with SQS access
- OpenAI or Anthropic API key (for research)

## Installation

### 1. Install Dependencies

```bash
# Using uv (recommended)
uv pip install boto3

# Or using pip
pip install boto3
```

### 2. Configure Environment

Create or update your `.env` file:

```bash
# API Keys for research
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
TAVILY_API_KEY=your_tavily_key

# AWS Credentials
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=eu-west-2

# Optional: Queue URLs (will be auto-created if not provided)
# SQS_INVESTMENT_QUEUE_URL=https://sqs.eu-west-2.amazonaws.com/...
# SQS_FUNDING_QUEUE_URL=https://sqs.eu-west-2.amazonaws.com/...
# SQS_RESULTS_QUEUE_URL=https://sqs.eu-west-2.amazonaws.com/...
```

### 3. Test Configuration

```bash
python examples/sqs_basic_example.py
```

This will create the queues and send test messages.

## Basic Usage

### Send Messages

```python
from open_deep_research.sqs_config import get_sqs_manager

# Get SQS manager
sqs = get_sqs_manager()

# Send investment opportunity
investment = {
    "opportunity_id": "INV-001",
    "title": "Solar Farm Development",
    "description": "50MW solar farm project",
    "location": "Bristol, UK",
    "sector": "Renewable Energy",
    "investment_amount": 25000000,
    "roi": 12.5
}

message_id = sqs.send_investment_opportunity(investment)
print(f"Sent: {message_id}")
```

### Process Messages

```python
import asyncio
from open_deep_research.message_handlers import process_investment_opportunities_queue

# Process messages from queue
asyncio.run(process_investment_opportunities_queue(max_iterations=5))
```

### Process with Automatic Research

```python
import asyncio
from langchain_core.runnables import RunnableConfig
from open_deep_research.sqs_integration import run_enhanced_investment_handler

# Configure research
config = RunnableConfig(
    configurable={
        "research_model": "gpt-4o",
        "allow_clarification": False
    }
)

# Run handler with automatic research
asyncio.run(run_enhanced_investment_handler(config, max_iterations=3))
```

## Example Workflow

### 1. Send Test Opportunities

```bash
cd examples
python sqs_basic_example.py
```

Output:
```
Sending Investment Opportunities...
✓ Sent solar farm opportunity: abc123...
✓ Sent wind farm opportunity: def456...
✓ Sent retrofit opportunity: ghi789...
```

### 2. Process with Research

```bash
python sqs_research_integration_example.py
# Select option 2: Enhanced handler (auto research)
```

This will:
- Poll the investment queue
- Trigger deep research for each opportunity
- Send results to the results queue

### 3. Monitor Results

```bash
python sqs_consumer_example.py
# Select option 4: Monitor queue status
```

Or programmatically:

```python
from open_deep_research.sqs_config import get_sqs_manager

sqs = get_sqs_manager()
messages = sqs.receive_research_results()

for msg in messages:
    print(f"Research: {msg['payload']['research_brief']}")
    print(f"Report: {msg['payload']['final_report'][:200]}...")
```

## Common Patterns

### Pattern 1: Fire and Forget

Send messages without waiting for processing:

```python
# Send multiple opportunities
for opportunity in opportunities:
    sqs.send_investment_opportunity(opportunity)

# Messages will be processed by background handlers
```

### Pattern 2: Process and Wait

Send and immediately process:

```python
# Send message
message_id = sqs.send_investment_opportunity(opportunity)

# Wait for availability
await asyncio.sleep(2)

# Process
await run_enhanced_investment_handler(config, max_iterations=1)
```

### Pattern 3: Continuous Processing

Run handlers continuously in background:

```python
# Start both handlers in parallel
await run_enhanced_handlers_parallel(config)  # Runs until interrupted
```

### Pattern 4: Batch Processing

Process multiple messages efficiently:

```python
# Receive batch
messages = sqs.receive_messages(queue_url, max_messages=10)

# Process in parallel
tasks = [process_message(msg) for msg in messages]
results = await asyncio.gather(*tasks)

# Delete processed messages
for msg, success in zip(messages, results):
    if success:
        sqs.delete_message(queue_url, msg['receipt_handle'])
```

## Next Steps

1. **Customize Handlers**: Create custom message handlers for your use case
2. **Add Matching**: Implement logic to match investments with funding
3. **Database Integration**: Store opportunities and research in PostgreSQL
4. **Monitoring**: Set up CloudWatch alarms for queue metrics
5. **Scaling**: Deploy handlers as separate services or Lambda functions

## Troubleshooting

### Queues Not Created

**Problem**: Queues don't appear in AWS console

**Solution**: Check IAM permissions include `sqs:CreateQueue`

### Messages Not Received

**Problem**: `receive_messages()` returns empty list

**Solution**:
- Check queue URL is correct
- Verify messages were sent successfully
- Wait for message visibility timeout to expire

### Research Not Triggering

**Problem**: Enhanced handler receives messages but doesn't research

**Solution**:
- Check API keys are set correctly
- Verify LangGraph configuration
- Check logs for error messages

### Rate Limiting

**Problem**: "Rate limit exceeded" errors

**Solution**:
- Reduce `max_concurrent_research_units` in config
- Add delays between research tasks
- Use cheaper models (gpt-4o-mini)

## Resources

- [Full Documentation](SQS_INTEGRATION.md)
- [Examples Directory](examples/)
- [AWS SQS Documentation](https://docs.aws.amazon.com/sqs/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review example scripts
3. Check AWS CloudWatch logs
4. Review application logs (set `logging.DEBUG`)
