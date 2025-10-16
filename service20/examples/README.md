# SQS Integration Examples

This directory contains example scripts demonstrating how to use the SQS message queue integration with the Open Deep Research service.

## Examples Overview

### 1. Basic Message Sending (`sqs_basic_example.py`)

**What it does:**
- Sends example investment opportunities to the queue
- Sends example funding opportunities to the queue
- Demonstrates message structure and payload format

**When to use:**
- Learning how to send messages
- Testing queue connectivity
- Understanding message formats

**Run it:**
```bash
python sqs_basic_example.py
```

**Example output:**
```
Sending Investment Opportunities...
✓ Sent solar farm opportunity: 12345...
✓ Sent wind farm opportunity: 67890...
✓ Sent retrofit opportunity: abcde...
```

### 2. Message Consumption (`sqs_consumer_example.py`)

**What it does:**
- Receives and processes messages from queues
- Demonstrates custom handlers
- Shows monitoring and queue management

**Features:**
1. Simple consumer (single queue)
2. Parallel consumer (all queues)
3. Custom handler with processing logic
4. Queue monitoring and statistics
5. Peek messages without deletion

**When to use:**
- Processing messages without research
- Building custom handlers
- Monitoring queue status
- Testing message flow

**Run it:**
```bash
python sqs_consumer_example.py
# Follow the interactive menu
```

### 3. Research Integration (`sqs_research_integration_example.py`)

**What it does:**
- Integrates SQS with deep research workflow
- Automatically triggers research for opportunities
- Demonstrates enhanced handlers

**Features:**
1. Manual research trigger
2. Enhanced handler (automatic research)
3. Parallel handlers (investment + funding)
4. Send and process workflow
5. Monitor research results

**When to use:**
- Conducting automated research
- Processing opportunities with AI analysis
- Generating comprehensive reports
- Production deployment

**Run it:**
```bash
python sqs_research_integration_example.py
# Follow the interactive menu
```

## Quick Start

### 1. Send Test Messages

```bash
python sqs_basic_example.py
```

### 2. View Messages in Queue

```bash
python sqs_consumer_example.py
# Select option 5: Peek messages
```

### 3. Process with Research

```bash
python sqs_research_integration_example.py
# Select option 2: Enhanced handler
```

## Example Workflows

### Workflow 1: Basic Testing

```bash
# Terminal 1: Send messages
python sqs_basic_example.py

# Terminal 2: Process messages
python sqs_consumer_example.py
# Select option 1: Simple consumer
```

### Workflow 2: Production Setup

```bash
# Terminal 1: Send opportunities (from your application)
python -c "
from open_deep_research.sqs_config import get_sqs_manager
sqs = get_sqs_manager()
sqs.send_investment_opportunity({...})
"

# Terminal 2: Run enhanced handlers continuously
python -c "
import asyncio
from open_deep_research.sqs_integration import run_enhanced_handlers_parallel
asyncio.run(run_enhanced_handlers_parallel())
"
```

### Workflow 3: Development and Debugging

```bash
# 1. Check queue status
python sqs_consumer_example.py  # Option 4

# 2. Send test message
python sqs_basic_example.py

# 3. Process one message with research
python sqs_research_integration_example.py  # Option 4

# 4. Check results
python sqs_research_integration_example.py  # Option 5
```

## Message Examples

### Investment Opportunity

```python
{
    "opportunity_id": "INV-2025-001",
    "title": "50MW Solar Farm Development",
    "description": "Large-scale solar project...",
    "location": "Bristol, UK",
    "sector": "Renewable Energy - Solar",
    "investment_amount": 25000000,
    "roi": 12.5,
    "risk_level": "medium",
    "timeline": "24 months",
    "net_zero_impact": {
        "co2_reduction_tons_per_year": 24750,
        "equivalent_homes_powered": 15000
    }
}
```

### Funding Opportunity

```python
{
    "funding_id": "FUND-2025-001",
    "title": "UK Net Zero Innovation Fund",
    "description": "Government funding program...",
    "funder": "UK Government",
    "amount_available": 50000000,
    "deadline": "2025-12-31",
    "eligible_sectors": ["Renewable Energy", "Carbon Capture"],
    "requirements": ["UK-based", "Net zero contribution"],
    "funding_range": {
        "min": 500000,
        "max": 5000000
    }
}
```

## Configuration

All examples use environment variables from `.env`:

```bash
# Required for basic examples
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=eu-west-2

# Required for research integration
OPENAI_API_KEY=your_openai_key
TAVILY_API_KEY=your_tavily_key

# Optional
SQS_INVESTMENT_QUEUE_URL=...
SQS_FUNDING_QUEUE_URL=...
SQS_RESULTS_QUEUE_URL=...
```

## Customization

### Custom Message Handler

```python
from open_deep_research.message_handlers import InvestmentOpportunityHandler

class MyHandler(InvestmentOpportunityHandler):
    async def handle_investment_opportunity(self, payload, message):
        # Your custom logic
        print(f"Processing: {payload['title']}")

        # Custom analysis
        score = self.calculate_score(payload)

        # Send to another queue
        self.sqs.send_message(...)

# Use it
handler = MyHandler()
await handler.poll_and_process(handler.sqs.config.investment_queue_url)
```

### Custom Research Prompt

```python
from open_deep_research.sqs_integration import ResearchOrchestrator

class MyOrchestrator(ResearchOrchestrator):
    def _build_investment_research_prompt(self, opportunity_data):
        # Custom prompt template
        return f"""
        Custom research prompt for {opportunity_data['title']}

        Focus areas:
        1. Market analysis
        2. Risk assessment
        3. ...
        """
```

## Tips and Best Practices

1. **Start Simple**: Use `sqs_basic_example.py` to test connectivity first
2. **Monitor Queues**: Regularly check queue depth and message age
3. **Handle Errors**: Always implement error handling in custom handlers
4. **Delete Messages**: Remember to delete processed messages
5. **Use Long Polling**: Default 20-second wait time is optimal
6. **Batch Processing**: Process multiple messages in parallel when possible
7. **Set Visibility Timeout**: Adjust based on research duration (default 300s)

## Troubleshooting

### No Messages Received

```python
# Check queue status first
python sqs_consumer_example.py  # Option 4: Monitor queue

# Verify messages were sent
from open_deep_research.sqs_config import get_sqs_manager
sqs = get_sqs_manager()
attrs = sqs.get_queue_attributes(sqs.config.investment_queue_url)
print(f"Messages: {attrs.get('ApproximateNumberOfMessages')}")
```

### Research Not Working

```python
# Test research manually first
python sqs_research_integration_example.py  # Option 1

# Check API keys
import os
print(f"OpenAI: {bool(os.getenv('OPENAI_API_KEY'))}")
print(f"Tavily: {bool(os.getenv('TAVILY_API_KEY'))}")
```

### Queue Permissions

```bash
# Test AWS credentials
python -c "
import boto3
sqs = boto3.client('sqs', region_name='eu-west-2')
print(sqs.list_queues(QueueNamePrefix='service20'))
"
```

## Next Steps

1. Review [SQS_INTEGRATION.md](../SQS_INTEGRATION.md) for detailed documentation
2. Check [QUICKSTART_SQS.md](../QUICKSTART_SQS.md) for setup guide
3. Customize handlers for your specific use case
4. Deploy to production with proper monitoring
5. Scale handlers based on message volume

## Support

For issues:
- Check example script comments
- Review error messages carefully
- Enable DEBUG logging
- Check AWS CloudWatch logs
