# SQS Integration Guide for Service20

## Overview

Service20 now includes AWS SQS (Simple Queue Service) integration to enable communication between the investment opportunities agent and the funding opportunities agent. This allows agents to:

- Share discovered opportunities
- Trigger automated research tasks
- Match investments with funding sources
- Coordinate research workflows

## Architecture

### Components

1. **SQS Configuration** (`src/open_deep_research/sqs_config.py`)
   - Queue management and creation
   - Message sending/receiving
   - AWS client configuration

2. **Message Handlers** (`src/open_deep_research/message_handlers.py`)
   - Base message handler framework
   - Investment opportunity handler
   - Funding opportunity handler
   - Research result handler

3. **Integration Layer** (`src/open_deep_research/sqs_integration.py`)
   - Deep researcher orchestration
   - Enhanced handlers with automatic research
   - Research prompt generation

### Message Queues

Three SQS queues are used for different message types:

1. **Investment Opportunities Queue** (`service20-investment-opportunities`)
   - Receives investment opportunity discoveries
   - Triggers research and funding matching

2. **Funding Opportunities Queue** (`service20-funding-opportunities`)
   - Receives funding opportunity discoveries
   - Triggers research and investment matching

3. **Research Results Queue** (`service20-research-results`)
   - Receives completed research reports
   - Stores match results and findings

## Setup

### 1. Install Dependencies

Update `pyproject.toml` to include boto3:

```toml
dependencies = [
    # ... existing dependencies ...
    "boto3>=1.35.0",
]
```

Install with:

```bash
uv pip install boto3
```

### 2. Configure Environment Variables

Add to your `.env` file:

```bash
# AWS Configuration for SQS
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=eu-west-2

# SQS Queue URLs (optional - will be created if not provided)
SQS_INVESTMENT_QUEUE_URL=https://sqs.eu-west-2.amazonaws.com/...
SQS_FUNDING_QUEUE_URL=https://sqs.eu-west-2.amazonaws.com/...
SQS_RESULTS_QUEUE_URL=https://sqs.eu-west-2.amazonaws.com/...
```

### 3. AWS IAM Permissions

Ensure your AWS IAM user/role has these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sqs:CreateQueue",
        "sqs:GetQueueUrl",
        "sqs:GetQueueAttributes",
        "sqs:SendMessage",
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:PurgeQueue"
      ],
      "Resource": "arn:aws:sqs:eu-west-2:*:service20-*"
    }
  ]
}
```

## Usage

### Basic Usage

#### Send an Investment Opportunity

```python
from open_deep_research.sqs_config import get_sqs_manager

# Get SQS manager
sqs = get_sqs_manager()

# Send investment opportunity
opportunity = {
    "opportunity_id": "INV-001",
    "title": "Solar Farm Development in Bristol",
    "description": "50MW solar farm project requiring £25M investment",
    "location": "Bristol, UK",
    "sector": "Renewable Energy",
    "investment_amount": 25000000,
    "roi": 12.5,
    "risk_level": "medium",
    "timeline": "24 months"
}

message_id = sqs.send_investment_opportunity(opportunity)
print(f"Sent investment opportunity: {message_id}")
```

#### Send a Funding Opportunity

```python
# Send funding opportunity
funding = {
    "funding_id": "FUND-001",
    "title": "UK Net Zero Innovation Fund",
    "description": "Government funding for innovative net zero projects",
    "funder": "UK Government",
    "amount_available": 50000000,
    "deadline": "2025-12-31",
    "eligible_sectors": ["Renewable Energy", "Carbon Capture", "Green Transport"],
    "requirements": ["UK-based", "Net zero contribution", "Innovation focus"]
}

message_id = sqs.send_funding_opportunity(funding)
print(f"Sent funding opportunity: {message_id}")
```

### Advanced Usage with Deep Research

#### Run Enhanced Investment Handler

The enhanced handler automatically triggers deep research for each investment opportunity:

```python
import asyncio
from open_deep_research.sqs_integration import run_enhanced_investment_handler
from langchain_core.runnables import RunnableConfig

# Configure LangGraph
config = RunnableConfig(
    configurable={
        "research_model": "gpt-4o",
        "max_concurrent_research_units": 3,
        "allow_clarification": False
    }
)

# Run handler (processes messages until interrupted)
asyncio.run(run_enhanced_investment_handler(config))
```

#### Run Enhanced Funding Handler

```python
import asyncio
from open_deep_research.sqs_integration import run_enhanced_funding_handler

# Run handler with custom config
asyncio.run(run_enhanced_funding_handler(config, max_iterations=10))
```

#### Run Both Handlers in Parallel

```python
import asyncio
from open_deep_research.sqs_integration import run_enhanced_handlers_parallel

# Process both investment and funding queues simultaneously
asyncio.run(run_enhanced_handlers_parallel(config))
```

### Custom Message Handlers

#### Create Custom Handler

```python
from open_deep_research.message_handlers import MessageHandler
from open_deep_research.sqs_config import MessageType

class CustomHandler(MessageHandler):
    def __init__(self):
        super().__init__()

        # Register custom handler
        self.register_handler(
            MessageType.INVESTMENT_OPPORTUNITY,
            self.custom_investment_handler
        )

    async def custom_investment_handler(self, payload, message):
        # Custom processing logic
        print(f"Custom processing: {payload['title']}")

        # Your logic here...

        # Send result to results queue
        result = {
            "research_id": payload["opportunity_id"],
            "status": "processed",
            "custom_data": "..."
        }
        self.sqs.send_research_result(result)

# Run custom handler
handler = CustomHandler()
asyncio.run(
    handler.poll_and_process(
        handler.sqs.config.investment_queue_url,
        max_iterations=5
    )
)
```

## Message Types

### Investment Opportunity Message

```python
{
    "opportunity_id": str,       # Unique identifier
    "title": str,                # Opportunity title
    "description": str,          # Detailed description
    "location": str,             # Geographic location
    "sector": str,               # Industry sector
    "investment_amount": float,  # Required investment (USD)
    "roi": float,                # Expected ROI (%)
    "risk_level": str,           # low, medium, high
    "timeline": str,             # Project timeline
    # Additional custom fields...
}
```

### Funding Opportunity Message

```python
{
    "funding_id": str,                    # Unique identifier
    "title": str,                         # Funding title
    "description": str,                   # Detailed description
    "funder": str,                        # Funding organization
    "amount_available": float,            # Available amount (USD)
    "deadline": str,                      # Application deadline
    "eligible_sectors": List[str],        # Eligible sectors
    "requirements": List[str],            # Eligibility requirements
    # Additional custom fields...
}
```

### Research Result Message

```python
{
    "research_id": str,          # Source opportunity ID
    "opportunity_type": str,     # "investment" or "funding"
    "research_brief": str,       # Research brief/question
    "final_report": str,         # Complete research report
    "findings": List[str],       # Key findings
    "opportunity_data": dict,    # Original opportunity data
    # Additional custom fields...
}
```

## Research Prompts

The integration automatically generates comprehensive research prompts based on opportunity data:

### Investment Research Topics

- Market analysis for sector and location
- Competitive landscape
- Regulatory environment
- Risk factors and mitigation
- Potential funding matches
- ROI projections
- Environmental impact
- Key stakeholders

### Funding Research Topics

- Funder background and history
- Application requirements
- Success factors
- Competition analysis
- Eligible project types
- Potential investment matches
- Strategic approach
- Past awards and outcomes

## Queue Management

### Check Queue Status

```python
from open_deep_research.sqs_config import get_sqs_manager

sqs = get_sqs_manager()

# Get queue attributes
attrs = sqs.get_queue_attributes(sqs.config.investment_queue_url)
print(f"Messages available: {attrs.get('ApproximateNumberOfMessages')}")
print(f"Messages in flight: {attrs.get('ApproximateNumberOfMessagesNotVisible')}")
```

### Purge Queue (Development Only)

```python
# WARNING: This deletes all messages!
sqs.purge_queue(sqs.config.investment_queue_url)
```

### Receive Messages Without Processing

```python
# Receive without automatic deletion
messages = sqs.receive_messages(sqs.config.investment_queue_url, max_messages=5)

for msg in messages:
    print(f"Type: {msg['type']}")
    print(f"Payload: {msg['payload']}")

    # Manually delete after processing
    sqs.delete_message(
        sqs.config.investment_queue_url,
        msg['receipt_handle']
    )
```

## Monitoring and Logging

The SQS integration includes comprehensive logging:

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Or configure specific logger
logger = logging.getLogger('open_deep_research.sqs_config')
logger.setLevel(logging.INFO)
```

Log messages include:

- Queue creation/initialization
- Message sending/receiving
- Research workflow execution
- Handler processing status
- Error details

## Error Handling

The integration includes automatic error handling:

- **Connection Errors**: Automatically retries with exponential backoff
- **Message Processing Errors**: Logs error but continues processing
- **Research Failures**: Returns error message and continues
- **Token Limit Exceeded**: Automatic truncation and retry

## Best Practices

1. **Use Long Polling**: Default configuration uses 20-second wait time
2. **Delete Messages**: Always delete messages after successful processing
3. **Handle Duplicates**: Implement idempotency in your handlers
4. **Monitor Queue Depth**: Set up CloudWatch alarms for queue metrics
5. **Batch Processing**: Process multiple messages in parallel when possible
6. **Error Queues**: Consider setting up Dead Letter Queues (DLQ)

## Troubleshooting

### Queue Not Found

- Check AWS credentials
- Verify region is correct (eu-west-2)
- Ensure IAM permissions include sqs:GetQueueUrl

### Messages Not Received

- Check queue URLs in environment variables
- Verify visibility timeout (default 300 seconds)
- Ensure messages haven't expired (retention period)

### Research Not Triggering

- Check LangGraph configuration
- Verify OpenAI/Anthropic API keys
- Check logs for error messages

## Next Steps

1. Implement matching algorithm between investments and funding
2. Add database persistence for research results
3. Create web interface for monitoring queues
4. Set up CloudWatch metrics and alarms
5. Implement Dead Letter Queue for failed messages
6. Add authentication for queue access
