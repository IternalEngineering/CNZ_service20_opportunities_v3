# Query Scripts - Quick Reference

## Main Query Script: `query_results.py`

**All-in-one script to query research results from both SQS queues and PostgreSQL database.**

### Run It:
```bash
python query_results.py
```

### Menu Options:

1. **Query SQS Results Queue** - View latest research outputs
2. **Query PostgreSQL Database** - View historical research
3. **Monitor Queue Status** - Check pending messages
4. **Peek Queue Messages** - View queued opportunities (without deletion)
5. **Search by Keyword** - Search database by keyword

---

## Option 1: Query SQS Results Queue

**What it does:** Retrieves completed research results from the results queue

**Use when:** You want to see the latest research outputs from both agents

**Output format:**
- Research ID
- Opportunity type (investment or funding)
- Research brief
- Full project proposal report
- Findings list
- Source citations

**Features:**
- Preview reports (first 500 chars)
- Save full reports to file
- Delete messages after viewing

**Example:**
```bash
python query_results.py
# Choose: 1
```

**Output:**
```
Result 1: INV-2025-001
Research ID: INV-2025-001
Type: investment
Timestamp: 2025-10-16T15:30:00Z

Research Brief:
Research on 50MW Solar Farm Development project...

Report Length: 12,458 characters
Findings Count: 8

Report Preview:
# 50MW Solar Farm Development in Bristol - Investment Proposal

## Executive Summary
This project represents a compelling investment opportunity...
```

---

## Option 2: Query PostgreSQL Database

**What it does:** Retrieves historical research results stored in database

**Use when:** You want to search through past research or analyze trends

**Database table:** `service20_investment_opportunities`

**Fields returned:**
- ID
- Query text
- Created timestamp
- Tool calls count
- Tools used (database, web)
- Report length

**Features:**
- View up to 20 most recent results
- Filter by ID
- View full reports
- Save reports to file

**Example:**
```bash
python query_results.py
# Choose: 2
```

---

## Option 3: Monitor Queue Status

**What it does:** Shows real-time status of all SQS queues

**Use when:** You want to check if messages are pending or being processed

**Queues monitored:**
- Investment Opportunities Queue
- Funding Opportunities Queue
- Research Results Queue

**Metrics shown:**
- Messages Available (ready to process)
- Messages In Flight (currently being processed)
- Oldest Message Age

**Example:**
```bash
python query_results.py
# Choose: 3
```

**Output:**
```
Investment Opportunities
URL: https://sqs.eu-west-2.amazonaws.com/.../service20-investment-opportunities
Messages Available: 3
Messages In Flight: 1
Oldest Message Age: 2m 34s

Funding Opportunities
URL: https://sqs.eu-west-2.amazonaws.com/.../service20-funding-opportunities
Messages Available: 1
Messages In Flight: 0
```

---

## Option 4: Peek Queue Messages

**What it does:** Views messages in queues WITHOUT deleting them

**Use when:** You want to see what's pending without consuming messages

**Features:**
- View up to 5 messages per queue
- Shows opportunity/funding details
- Messages remain in queue (not deleted)
- Messages become visible again after timeout

**Example:**
```bash
python query_results.py
# Choose: 4
```

**Output:**
```
Investment Opportunities
Found 2 message(s):

1. investment_opportunity
   ID: INV-2025-001
   Title: 50MW Solar Farm Development
   Location: Bristol, UK
   Investment: £25,000,000
   ROI: 12.5%

2. investment_opportunity
   ID: INV-2025-002
   Title: Offshore Wind Farm Expansion
   Location: Scottish Coast
   Investment: £180,000,000
   ROI: 15.2%
```

---

## Option 5: Search by Keyword

**What it does:** Searches database for specific keywords

**Use when:** You want to find research about specific topics, locations, or technologies

**Search fields:**
- Query text
- Final report content

**Example:**
```bash
python query_results.py
# Choose: 5
# Enter keyword: solar
```

**Output:**
```
Found 3 result(s):

1. ID 42: Solar farm development in Bristol
   Created: 2025-10-16 14:23:00 | Report: 12,458 chars

2. ID 38: Community solar energy project
   Created: 2025-10-15 09:15:00 | Report: 8,234 chars

3. ID 31: Solar + battery storage system
   Created: 2025-10-14 16:45:00 | Report: 15,123 chars
```

---

## Other Available Scripts

### 1. `view_research_results.py`
**Simple database viewer (legacy)**

```bash
python view_research_results.py
```

Lists all database records with summary info. Good for quick checks.

### 2. `examples/sqs_consumer_example.py`
**SQS consumer examples**

```bash
python examples/sqs_consumer_example.py
```

Interactive menu with 5 examples:
1. Simple consumer (single queue)
2. Parallel consumer (all queues)
3. Custom handler
4. Monitor queue status
5. Peek messages (no deletion)

### 3. `examples/sqs_research_integration_example.py`
**Deep research integration examples**

```bash
python examples/sqs_research_integration_example.py
```

Interactive menu with 5 examples:
1. Manual research trigger
2. Enhanced handler (auto research)
3. Parallel handlers
4. Send and process
5. Monitor results queue

---

## Direct Python Usage

### Query SQS Results
```python
from open_deep_research.sqs_config import get_sqs_manager

sqs = get_sqs_manager()

# Get research results
messages = sqs.receive_research_results()

for msg in messages:
    payload = msg['payload']
    print(f"Research ID: {payload['research_id']}")
    print(f"Type: {payload['opportunity_type']}")
    print(f"Report:\n{payload['final_report']}")

    # Delete after processing
    sqs.delete_message(
        sqs.config.results_queue_url,
        msg['receipt_handle']
    )
```

### Query Database
```python
import asyncio
import asyncpg
import os

async def query_db():
    conn = await asyncpg.connect(os.getenv("DATABASE_URL"))

    rows = await conn.fetch("""
        SELECT id, query, final_report, created_at
        FROM service20_investment_opportunities
        ORDER BY created_at DESC
        LIMIT 10;
    """)

    for row in rows:
        print(f"ID: {row['id']}")
        print(f"Query: {row['query']}")
        print(f"Report:\n{row['final_report']}\n")

    await conn.close()

asyncio.run(query_db())
```

### Monitor Queues
```python
from open_deep_research.sqs_config import get_sqs_manager

sqs = get_sqs_manager()

queues = {
    "Investment": sqs.config.investment_queue_url,
    "Funding": sqs.config.funding_queue_url,
    "Results": sqs.config.results_queue_url,
}

for name, url in queues.items():
    attrs = sqs.get_queue_attributes(url)
    print(f"{name} Queue:")
    print(f"  Available: {attrs.get('ApproximateNumberOfMessages')}")
    print(f"  In Flight: {attrs.get('ApproximateNumberOfMessagesNotVisible')}")
```

---

## Output Directory

All saved reports go to: `research_results/`

Filename format:
- SQS results: `research_{research_id}_{timestamp}.md`
- Database results: `database_report_{id}_{timestamp}.md`

---

## Prerequisites

### Environment Variables
```bash
# Required for SQS querying
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=eu-west-2

# Required for database querying
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Queue URLs (optional - auto-created)
SQS_INVESTMENT_QUEUE_URL=https://...
SQS_FUNDING_QUEUE_URL=https://...
SQS_RESULTS_QUEUE_URL=https://...
```

### Python Dependencies
```bash
pip install boto3 asyncpg python-dotenv colorama
```

---

## Quick Start Workflow

### 1. Send Test Messages
```bash
python examples/sqs_basic_example.py
```

### 2. Process Messages (Generate Research)
```bash
python examples/sqs_research_integration_example.py
# Choose option 4 (Send and process)
```

### 3. Query Results
```bash
python query_results.py
# Choose option 1 (Query SQS Results Queue)
```

---

## Troubleshooting

### No Results in SQS Queue?
- Check if handlers are running: `python examples/sqs_research_integration_example.py` → Option 2
- Monitor queue status: `python query_results.py` → Option 3
- Messages expire after 4 days

### No Results in Database?
- Check if DATABASE_URL is set
- Verify database connection: `python test_postgres_integration.py`
- Results are only stored if configured in handlers

### Queue Access Errors?
- Verify AWS credentials are correct
- Check AWS region matches queue region (eu-west-2)
- Ensure IAM permissions for SQS operations

### Empty Messages?
- Check visibility timeout hasn't expired
- Messages may be "in flight" (being processed)
- Use Option 4 to peek without consuming

---

## Performance Tips

- Use **Option 1** for real-time results
- Use **Option 2** for historical analysis
- Use **Option 3** to avoid polling empty queues
- Use **Option 4** to inspect without deleting
- Save reports to files for offline analysis

---

## Best Practices

1. **Delete messages after reading** to avoid reprocessing
2. **Save important reports** before deleting from queue
3. **Monitor queue status** before processing to check workload
4. **Use peek mode** when debugging to avoid consuming messages
5. **Search database** for historical trend analysis
