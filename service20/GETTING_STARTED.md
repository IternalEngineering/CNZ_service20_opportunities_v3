# Getting Started with Service20

**Complete beginner-friendly guide - no prior knowledge needed.**

---

## What is This?

Service20 is an AI system that researches Net Zero investment and funding opportunities.

**Input:** "50MW Solar Farm in Bristol needs £25M"
**Output:** 15-page research report with market analysis, ROI, risks, and funding matches

---

## Setup (30 minutes)

### 1. Install Prerequisites (5 min)

**Check what you have:**
```bash
python --version   # Need 3.11+
git --version      # Need 2.0+
aws --version      # Need 2.0+
```

**Missing something?**
- Python: https://www.python.org/downloads/
- Git: https://git-scm.com/downloads
- AWS CLI: https://aws.amazon.com/cli/

### 2. Get API Keys (10 min)

You need these:
- **AWS credentials**: https://console.aws.amazon.com → Security credentials → Create access key
- **OpenAI API key**: https://platform.openai.com/api-keys
- **Tavily API key**: https://tavily.com (free tier: 1000 searches/month)

**Save these somewhere - you'll need them in step 5!**

### 3. Clone Repository (2 min)

```bash
git clone <your-repo-url>
cd service20
```

### 4. Set Up Python Environment (3 min)

```bash
# Create virtual environment
python -m venv .venv

# Activate it
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements-sqs.txt
```

### 5. Create AWS Infrastructure (5 min)

```bash
# Configure AWS
aws configure
# Enter your AWS keys from step 2

# Run setup script
cd scripts

# Windows:
.\setup_aws_sqs.ps1 -Region "eu-west-2" -Environment "dev"

# Mac/Linux:
chmod +x setup_aws_sqs.sh
./setup_aws_sqs.sh eu-west-2 dev
```

This creates 4 message queues and an IAM policy. Takes ~30 seconds.

### 6. Configure Environment (3 min)

```bash
cd ..  # Back to project root

# Copy template
cp .env.dev .env

# Edit file (use notepad, nano, or your editor)
notepad .env
```

**Add your keys from step 2:**
```bash
AWS_ACCESS_KEY_ID=AKIA...           # From step 2
AWS_SECRET_ACCESS_KEY=...           # From step 2
OPENAI_API_KEY=sk-...               # From step 2
TAVILY_API_KEY=tvly-...             # From step 2
```

Queue URLs are already filled in by the setup script!

### 7. Attach IAM Policy (2 min)

```bash
# Find your username
aws sts get-caller-identity --query Arn --output text
# Shows: arn:aws:iam::123456789:user/your-name
#                                      ^^^ this ^^^

# Get policy ARN from RESOURCE_MAPPING.md (in scripts folder)
# Look for line: "Policy ARN: arn:aws:iam::..."

# Attach policy
aws iam attach-user-policy \
  --user-name YOUR_USERNAME \
  --policy-arn arn:aws:iam::ACCOUNT_ID:policy/service20-sqs-access-dev
```

### 8. Test It Works (2 min)

```bash
python scripts/test_sqs_connection.py
```

**Should see:**
```
✓ AWS_ACCESS_KEY_ID: AKIA...
✓ AWS_REGION: eu-west-2
✓ Queue accessible
✓ All tests passed!
```

**If it fails:** Check your `.env` file and IAM policy attachment.

---

## Quick Test (5 minutes)

### Send Test Messages

```bash
python examples/sqs_basic_example.py
```

**Output:**
```
✓ Sent solar farm opportunity: msg-123
✓ Sent wind farm opportunity: msg-456
✓ All messages sent successfully!
```

### Run Research (costs ~$0.05)

```bash
python examples/sqs_research_integration_example.py
```

Choose option **4** (Send and process)

Wait 2-3 minutes for AI research to complete.

### View Results

```bash
python query_results.py
```

Choose option **1** (Query SQS Results Queue)

You'll see the research report!

---

## Daily Usage

### Send an Investment Opportunity

```python
# Create file: send_opportunity.py
from open_deep_research.sqs_config import get_sqs_manager

sqs = get_sqs_manager()

opportunity = {
    "opportunity_id": "INV-001",
    "title": "Solar Farm Project",
    "description": "100MW solar farm in Scotland",
    "location": "Scotland, UK",
    "sector": "Renewable Energy",
    "investment_amount": 50000000,
    "roi": 14.5
}

msg_id = sqs.send_investment_opportunity(opportunity)
print(f"Sent: {msg_id}")
```

Run it:
```bash
python send_opportunity.py
```

### Process Opportunities

```bash
# Run the agent to process messages
python examples/sqs_research_integration_example.py
# Choose: 2 or 3
```

### View Results

```bash
python query_results.py
# Choose: 1
```

---

## Understanding the Flow

```
1. Send opportunity → SQS Queue
2. Agent polls queue → Receives opportunity
3. AI researches it → Generates report (2-3 min)
4. Results saved → SQS + PostgreSQL
5. Query results → View report
```

---

## Important Files

**Scripts you'll use:**
- `examples/sqs_basic_example.py` - Send test data
- `examples/sqs_research_integration_example.py` - Run agents
- `query_results.py` - View research outputs
- `scripts/test_sqs_connection.py` - Test connectivity

**Configuration:**
- `.env` - Your API keys and settings
- `RESOURCE_MAPPING.md` - AWS resource IDs

**Documentation:**
- `README.md` - Project overview
- `AGENT_INPUTS.md` - Input format details
- `AWS_REPLICATION_GUIDE.md` - AWS setup details

---

## Troubleshooting

### "AWS credentials not found"
```bash
aws configure
# Re-enter your keys
```

### "Access Denied"
```bash
# Check policy is attached
aws iam list-attached-user-policies --user-name YOUR_USER

# Re-attach if needed
aws iam attach-user-policy --user-name YOUR_USER --policy-arn ARN_FROM_RESOURCE_MAPPING
```

### "OpenAI API Error"
- Check key in `.env` is correct
- Verify you have credits: https://platform.openai.com/usage

### "Queue not found"
- Check queue URLs in `.env` match `scripts/RESOURCE_MAPPING.md`
- Verify AWS region in `.env` is correct

---

## Next Steps

**Learn more:**
1. Read `AGENT_INPUTS.md` for input format details
2. Read `AGENT_IO_FORMATS.md` for complete API docs
3. Explore `examples/` folder for more examples

**Customize:**
- Edit prompts in `src/open_deep_research/prompts.py`
- Change models in research config
- Add new message types in `message_handlers.py`

---

## Costs

**Per research:**
- AI: ~$0.15-0.50 (GPT-4o) or ~$0.02-0.05 (GPT-4o-mini)
- AWS SQS: Free (first 1M requests/month)

**Monthly estimate (1000 researches):**
- AI: ~$150-500 (GPT-4o) or ~$20-50 (GPT-4o-mini)
- AWS: $0

---

## Quick Commands

```bash
# Activate environment
source .venv/bin/activate  # Mac/Linux
.venv\Scripts\activate     # Windows

# Send test messages
python examples/sqs_basic_example.py

# Run agents
python examples/sqs_research_integration_example.py

# View results
python query_results.py

# Check queues
python scripts/monitor_queues.py
```

---

**You're ready!** Start by running the Quick Test above. 🚀
