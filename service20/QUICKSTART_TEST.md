# Quick Test - Service20 Agents

## Step-by-Step Test Commands

### 1. Navigate to Service20
```bash
cd C:\Users\chriz\OneDrive\Documents\CNZ\UrbanZero2\UrbanZero\server_c\service20
```

### 2. Activate Virtual Environment (if using uv)
```bash
# Create venv if not exists
uv venv

# Activate on Windows
.venv\Scripts\activate

# Or on Linux/Mac
source .venv/bin/activate
```

### 3. Install Dependencies (if needed)
```bash
pip install -r requirements-sqs.txt
```

### 4. Check Environment Variables
```bash
# Make sure these are set in .env file
type .env
```

**Required variables:**
```
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=eu-west-2
```

---

## Test Scenario: Full Workflow

### Test Case: Solar Farm Investment + Government Funding Match

**Scenario:** You have a 50MW solar farm project in Bristol that needs funding. Test if the agents can:
1. Research the investment opportunity
2. Research available government funding
3. Generate project proposals for both

---

## Step 1: Send Test Investment Opportunity

```bash
python examples/sqs_basic_example.py
```

**What this does:**
- Sends 3 investment opportunities to the queue
- Sends 3 funding opportunities to the queue

**Expected output:**
```
Sending Investment Opportunities...
✓ Sent solar farm opportunity: msg-abc123
✓ Sent wind farm opportunity: msg-def456
✓ Sent retrofit opportunity: msg-ghi789

Sending Funding Opportunities...
✓ Sent government funding opportunity: msg-jkl012
✓ Sent bank funding opportunity: msg-mno345
✓ Sent EU funding opportunity: msg-pqr678

✓ All messages sent successfully!
```

---

## Step 2: Check Queue Status

```bash
python query_results.py
```

Choose: **3** (Monitor Queue Status)

**Expected output:**
```
Investment Opportunities
Messages Available: 3
Messages In Flight: 0

Funding Opportunities
Messages Available: 3
Messages In Flight: 0

Research Results
Messages Available: 0
Messages In Flight: 0
```

---

## Step 3: Peek at Queue Messages (Optional)

```bash
python query_results.py
```

Choose: **4** (Peek Queue Messages)

**Expected output:**
```
Investment Opportunities
Found 3 message(s):

1. investment_opportunity
   ID: INV-2025-001
   Title: 50MW Solar Farm Development in Bristol
   Location: Bristol, UK
   Investment: £25,000,000
   ROI: 12.5%

2. investment_opportunity
   ID: INV-2025-002
   Title: Offshore Wind Farm Expansion
   Location: Scottish Coast
   Investment: £180,000,000
   ROI: 15.2%

3. investment_opportunity
   ID: INV-2025-003
   Title: Commercial Building Energy Retrofit Program
   Location: London, UK
   Investment: £8,500,000
   ROI: 18.5%
```

---

## Step 4: Process ONE Investment Opportunity

```bash
python examples/sqs_research_integration_example.py
```

Choose: **4** (Send and process)

**What this does:**
- Sends a green hydrogen project to the queue
- Immediately processes it with the enhanced handler
- Triggers deep researcher workflow
- Generates project proposal

**Expected output:**
```
Sending investment opportunity to queue...
✓ Sent with message ID: msg-xyz123

Now processing the message with enhanced handler...

Starting deep research for investment opportunity
Research prompt: Research the following Net Zero investment...

This will take 2-5 minutes...

[Deep researcher runs...]

Research completed. Report length: 12,458 characters
Research results sent with message ID: msg-result-123

✓ Processing completed
```

**Time:** 2-5 minutes (depends on model and research depth)

---

## Step 5: View Research Results

```bash
python query_results.py
```

Choose: **1** (Query SQS Results Queue)

**Expected output:**
```
Messages Available: 1

Found 1 research result(s):

Result 1: INV-DEMO-001
Research ID: INV-DEMO-001
Type: investment
Timestamp: 2025-10-16T15:45:23Z

Research Brief:
Research on Green Hydrogen Production Facility project in North East
England. Analysis covers market conditions, competitive landscape,
regulatory environment, and funding opportunities.

Report Length: 12,458 characters
Findings Count: 8

Report Preview:
# Green Hydrogen Production Facility - Investment Proposal

## Executive Summary
This project represents a compelling investment opportunity in the
rapidly growing green hydrogen sector...

## Market Opportunity
The UK hydrogen market is projected to reach £11 billion by 2030...

## Project Description
Development of a 10MW green hydrogen production facility powered by
renewable energy...

Save full report to file? (y/N):
```

Type **y** to save the full report.

**Report saved to:** `research_results/research_INV-DEMO-001_20251016_154530.md`

---

## Step 6: Process a Funding Opportunity

```bash
python examples/sqs_research_integration_example.py
```

Choose: **2** (Enhanced handler - auto research)

**What this does:**
- Runs the enhanced funding handler
- Processes up to 5 messages from funding queue
- Each message triggers deep research

**Expected output:**
```
Starting enhanced investment handler...
This will automatically research any investment opportunities in the queue.

Configuration:
  Research Model: gpt-4o
  Compression Model: gpt-4o-mini
  Max Research Units: 2

Press Ctrl+C to stop

Processing funding opportunity: FUND-2025-001
Starting deep research for funding opportunity

[Deep researcher runs for each funding opportunity...]

Research completed. Report length: 15,234 characters
Research results sent with message ID: msg-result-456

✓ Completed processing
```

---

## Step 7: View All Results

```bash
python query_results.py
```

Choose: **1** (Query SQS Results Queue)

**Expected output:**
```
Found 4 research result(s):

Result 1: INV-DEMO-001 (investment)
Result 2: FUND-2025-001 (funding)
Result 3: FUND-2025-002 (funding)
Result 4: FUND-2025-003 (funding)
```

---

## Alternative: Run Both Agents in Parallel

```bash
python examples/sqs_research_integration_example.py
```

Choose: **3** (Parallel handlers)

**What this does:**
- Runs both investment AND funding handlers simultaneously
- Processes all messages from both queues
- Generates research for everything

**Expected output:**
```
Starting both investment and funding handlers in parallel...
Each will automatically trigger research for opportunities.

Press Ctrl+C to stop

[Investment Handler] Processing investment opportunity: INV-2025-001
[Funding Handler] Processing funding opportunity: FUND-2025-001
[Investment Handler] Research completed for INV-2025-001
[Funding Handler] Research completed for FUND-2025-001
[Investment Handler] Processing investment opportunity: INV-2025-002
[Funding Handler] Processing funding opportunity: FUND-2025-002
...

✓ Completed processing
```

**Time:** Processes everything in parallel, faster than sequential

---

## Step 8: Search Results by Keyword

```bash
python query_results.py
```

Choose: **5** (Search by Keyword)

Enter keyword: **solar**

**Expected output:**
```
Enter search keyword: solar

Found 2 result(s):

1. ID 42: Research on 50MW Solar Farm Development
   Created: 2025-10-16 14:23:00 | Report: 12,458 chars

2. ID 38: Commercial solar + battery storage analysis
   Created: 2025-10-15 09:15:00 | Report: 8,234 chars
```

---

## Step 9: Monitor Queue Activity

```bash
# Open terminal 1
python query_results.py
# Choose: 3 (Monitor Queue Status)

# Open terminal 2
python examples/sqs_research_integration_example.py
# Choose: 3 (Parallel handlers)

# Switch back to terminal 1 and run query again
python query_results.py
# Choose: 3
```

**Watch the queue metrics change in real-time:**
```
Before:
Investment Queue - Available: 3, In Flight: 0

During:
Investment Queue - Available: 2, In Flight: 1

After:
Investment Queue - Available: 0, In Flight: 0
Results Queue - Available: 3, In Flight: 0
```

---

## Complete Test Sequence (Copy & Paste)

```bash
# Navigate to service20
cd C:\Users\chriz\OneDrive\Documents\CNZ\UrbanZero2\UrbanZero\server_c\service20

# Activate venv (Windows)
.venv\Scripts\activate

# Send test data
python examples/sqs_basic_example.py

# Check what was sent
python query_results.py
# Choose: 4 (Peek messages)

# Process everything in parallel
python examples/sqs_research_integration_example.py
# Choose: 3 (Parallel handlers)
# Wait 5-10 minutes for research to complete

# View all results
python query_results.py
# Choose: 1 (Query SQS Results)
# Type: y to save reports

# Check saved reports
dir research_results
type research_results\research_INV-2025-001_*.md
```

---

## Quick Single Test (3 minutes)

If you just want to test one opportunity quickly:

```bash
cd C:\Users\chriz\OneDrive\Documents\CNZ\UrbanZero2\UrbanZero\server_c\service20
.venv\Scripts\activate

# Process a single opportunity
python examples/sqs_research_integration_example.py
# Choose: 1 (Manual research trigger)

# Wait 2-3 minutes

# View the result
python query_results.py
# Choose: 1
```

---

## Troubleshooting

### Issue: "No module named 'open_deep_research'"
```bash
# Make sure you're in the right directory
cd C:\Users\chriz\OneDrive\Documents\CNZ\UrbanZero2\UrbanZero\server_c\service20

# Install package in editable mode
pip install -e .
```

### Issue: "DATABASE_URL not set"
```bash
# Edit .env file
notepad .env

# Add this line:
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

### Issue: "AWS credentials not found"
```bash
# Check .env file has:
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=eu-west-2
```

### Issue: "No messages in queue"
```bash
# Send test messages first
python examples/sqs_basic_example.py
```

### Issue: Research taking too long
```bash
# Use cheaper/faster model in config:
config = RunnableConfig(
    configurable={
        "research_model": "gpt-4o-mini",  # Faster & cheaper
        "compression_model": "gpt-4o-mini",
        "max_concurrent_research_units": 1,  # Less parallel research
    }
)
```

---

## Expected Costs

**Per research run (with GPT-4o):**
- Input tokens: ~5,000 - 10,000
- Output tokens: ~3,000 - 8,000
- Cost: ~$0.15 - $0.50 per research

**Full test (6 opportunities):**
- Total cost: ~$1 - $3

**Using GPT-4o-mini:**
- Cost: ~$0.02 - $0.10 per research
- Full test: ~$0.10 - $0.60

---

## Success Criteria

✅ **Test passed if you see:**

1. Messages sent successfully
2. Queue status shows messages
3. Research completes without errors
4. Results appear in results queue
5. Reports are well-formatted markdown
6. Reports include:
   - Executive Summary
   - Market Opportunity
   - Financial Analysis
   - Sources with citations

✅ **Bonus points if:**
- Investment research mentions potential funding sources
- Funding research mentions compatible investment types
- Reports are comprehensive (8,000+ characters)
- Multiple sources cited (10+ sources)
