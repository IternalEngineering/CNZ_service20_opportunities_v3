## AWS SQS Replication Guide

Complete guide to replicate Service20 SQS infrastructure in a new AWS account.

---

## Quick Start

### Windows (PowerShell)
```powershell
cd scripts
.\setup_aws_sqs.ps1 -Region "eu-west-2" -Environment "production"
```

### Linux/Mac (Bash)
```bash
cd scripts
chmod +x setup_aws_sqs.sh
./setup_aws_sqs.sh eu-west-2 production
```

---

## What Gets Created

### SQS Queues (4 total)

1. **Investment Opportunities Queue**
   - Name: `service20-investment-opportunities-{environment}`
   - Purpose: Receive investment opportunities for analysis
   - Settings:
     - Visibility Timeout: 300s (5 min)
     - Message Retention: 345600s (4 days)
     - Long Polling: 20s

2. **Funding Opportunities Queue**
   - Name: `service20-funding-opportunities-{environment}`
   - Purpose: Receive funding opportunities for analysis
   - Settings: Same as above

3. **Research Results Queue**
   - Name: `service20-research-results-{environment}`
   - Purpose: Store completed research outputs
   - Settings: Same as above

4. **Dead Letter Queue (DLQ)**
   - Name: `service20-dlq-{environment}`
   - Purpose: Failed message storage for debugging
   - Settings:
     - Visibility Timeout: 300s (5 min)
     - Message Retention: 1209600s (14 days)
     - Long Polling: 20s

### IAM Policy

- **Name:** `service20-sqs-access-{environment}`
- **Permissions:**
  - `sqs:SendMessage`
  - `sqs:ReceiveMessage`
  - `sqs:DeleteMessage`
  - `sqs:GetQueueAttributes`
  - `sqs:GetQueueUrl`
  - `sqs:ListQueues`
  - `sqs:PurgeQueue`
- **Resources:** All 4 queues created above

---

## Prerequisites

### 1. AWS CLI Installation

**Windows:**
```powershell
# Download and install AWS CLI v2
# https://awscli.amazonaws.com/AWSCLIV2.msi
```

**Linux/Mac:**
```bash
# Download and install
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

**Verify:**
```bash
aws --version
# Should show: aws-cli/2.x.x
```

### 2. AWS Account Setup

1. **Create IAM User** (if not exists)
   ```bash
   aws iam create-user --user-name service20-admin
   ```

2. **Create Access Keys**
   ```bash
   aws iam create-access-key --user-name service20-admin
   ```

   Save the output:
   - `AccessKeyId`
   - `SecretAccessKey`

3. **Configure AWS CLI**
   ```bash
   aws configure
   # Enter:
   #   AWS Access Key ID: AKIA...
   #   AWS Secret Access Key: ...
   #   Default region: eu-west-2
   #   Default output format: json
   ```

---

## Step-by-Step Setup

### Step 1: Run Setup Script

**PowerShell (Windows):**
```powershell
cd C:\Users\chriz\OneDrive\Documents\CNZ\UrbanZero2\UrbanZero\server_c\service20\scripts

# For production environment in eu-west-2
.\setup_aws_sqs.ps1 -Region "eu-west-2" -Environment "production"

# For development environment in us-east-1
.\setup_aws_sqs.ps1 -Region "us-east-1" -Environment "development"
```

**Bash (Linux/Mac):**
```bash
cd ~/projects/service20/scripts

# Make executable
chmod +x setup_aws_sqs.sh

# Run for production
./setup_aws_sqs.sh eu-west-2 production

# Run for development
./setup_aws_sqs.sh us-east-1 development
```

### Step 2: Review Generated Files

After running the script, you'll have:

```
scripts/
├── queue_mappings.txt          # Machine-readable resource IDs
├── RESOURCE_MAPPING.md         # Human-readable documentation
├── .env.{environment}          # Environment configuration template
└── sqs_policy.json            # IAM policy document
```

**queue_mappings.txt** format:
```
QueueName|QueueURL|QueueARN
service20-investment-opportunities-production|https://sqs....|arn:aws:sqs...
```

### Step 3: Update Environment Configuration

1. **Copy template:**
   ```bash
   cp .env.production ../.env
   ```

2. **Edit .env:**
   ```bash
   nano ../.env  # or notepad ../.env on Windows
   ```

3. **Add your credentials:**
   ```bash
   AWS_ACCESS_KEY_ID=AKIA...                    # Your access key
   AWS_SECRET_ACCESS_KEY=...                    # Your secret key
   OPENAI_API_KEY=sk-...                        # OpenAI API key
   TAVILY_API_KEY=tvly-...                      # Tavily API key
   DATABASE_URL=postgresql://user:pass@host/db  # Optional
   ```

### Step 4: Attach IAM Policy

**Get policy ARN from output:**
```bash
# From script output or RESOURCE_MAPPING.md
POLICY_ARN="arn:aws:iam::ACCOUNT_ID:policy/service20-sqs-access-production"
```

**Attach to your IAM user:**
```bash
aws iam attach-user-policy \
  --user-name service20-admin \
  --policy-arn $POLICY_ARN
```

**Or attach to IAM role (for EC2/Lambda):**
```bash
aws iam attach-role-policy \
  --role-name service20-execution-role \
  --policy-arn $POLICY_ARN
```

### Step 5: Test Connection

```bash
cd ..
python scripts/test_sqs_connection.py
```

**Expected output:**
```
Testing SQS Connection
========================================

✓ AWS_ACCESS_KEY_ID: AKIA1234...
✓ AWS_REGION: eu-west-2

Testing queue access...

Investment Queue:
  URL: https://sqs.eu-west-2.amazonaws.com/...
  Messages Available: 0
  Messages In Flight: 0
  ✓ Queue accessible

...

✓ All tests passed!
```

---

## Resource Mapping

### Original → New Mapping Table

| Resource Type | Original | New (Production) | New (Development) |
|---------------|----------|------------------|-------------------|
| Investment Queue | `service20-investment-opportunities` | `service20-investment-opportunities-production` | `service20-investment-opportunities-development` |
| Funding Queue | `service20-funding-opportunities` | `service20-funding-opportunities-production` | `service20-funding-opportunities-development` |
| Results Queue | `service20-research-results` | `service20-research-results-production` | `service20-research-results-development` |
| DLQ | `service20-dlq` | `service20-dlq-production` | `service20-dlq-development` |
| IAM Policy | `service20-sqs-access` | `service20-sqs-access-production` | `service20-sqs-access-development` |
| Region | `eu-west-2` | Configurable | Configurable |

### Environment Variable Mapping

| Variable | Original Value | New Value (from script) |
|----------|---------------|-------------------------|
| `SQS_INVESTMENT_QUEUE_URL` | `https://sqs.eu-west-2.amazonaws.com/.../service20-investment-opportunities` | `https://sqs.{region}.amazonaws.com/.../service20-investment-opportunities-{env}` |
| `SQS_FUNDING_QUEUE_URL` | `https://sqs.eu-west-2.amazonaws.com/.../service20-funding-opportunities` | `https://sqs.{region}.amazonaws.com/.../service20-funding-opportunities-{env}` |
| `SQS_RESULTS_QUEUE_URL` | `https://sqs.eu-west-2.amazonaws.com/.../service20-research-results` | `https://sqs.{region}.amazonaws.com/.../service20-research-results-{env}` |
| `AWS_REGION` | `eu-west-2` | Parameter to script |

---

## Multi-Account Setup

### Scenario: Different AWS accounts for different environments

**Account 1 (Development):**
```bash
# Configure dev account credentials
aws configure --profile dev
aws configure set region us-east-1 --profile dev

# Run setup with dev profile
AWS_PROFILE=dev ./setup_aws_sqs.sh us-east-1 development
```

**Account 2 (Production):**
```bash
# Configure prod account credentials
aws configure --profile prod
aws configure set region eu-west-2 --profile prod

# Run setup with prod profile
AWS_PROFILE=prod ./setup_aws_sqs.sh eu-west-2 production
```

**Result:** Two separate `.env` files:
- `.env.development` (with dev account queue URLs)
- `.env.production` (with prod account queue URLs)

---

## Verification Steps

### 1. List Created Queues

```bash
aws sqs list-queues --queue-name-prefix service20
```

**Expected output:**
```json
{
    "QueueUrls": [
        "https://sqs.eu-west-2.amazonaws.com/.../service20-investment-opportunities-production",
        "https://sqs.eu-west-2.amazonaws.com/.../service20-funding-opportunities-production",
        "https://sqs.eu-west-2.amazonaws.com/.../service20-research-results-production",
        "https://sqs.eu-west-2.amazonaws.com/.../service20-dlq-production"
    ]
}
```

### 2. Verify Queue Attributes

```bash
QUEUE_URL="https://sqs.eu-west-2.amazonaws.com/.../service20-investment-opportunities-production"

aws sqs get-queue-attributes \
  --queue-url $QUEUE_URL \
  --attribute-names All
```

### 3. Test Send/Receive

```bash
# Send test message
aws sqs send-message \
  --queue-url $QUEUE_URL \
  --message-body '{"test": "message"}'

# Receive message
aws sqs receive-message \
  --queue-url $QUEUE_URL \
  --max-number-of-messages 1
```

### 4. Verify IAM Policy

```bash
POLICY_ARN="arn:aws:iam::ACCOUNT_ID:policy/service20-sqs-access-production"

aws iam get-policy --policy-arn $POLICY_ARN
aws iam get-policy-version \
  --policy-arn $POLICY_ARN \
  --version-id v1
```

---

## Monitoring

### CloudWatch Metrics

**View in AWS Console:**
- Go to: CloudWatch → Metrics → SQS
- Select metrics for your queues

**Via CLI:**
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/SQS \
  --metric-name NumberOfMessagesSent \
  --dimensions Name=QueueName,Value=service20-investment-opportunities-production \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

### Application-Level Monitoring

```bash
# Use the monitoring script
python scripts/monitor_queues.py
```

---

## Cleanup

### Delete All Resources

**PowerShell:**
```powershell
# Get queue URLs from RESOURCE_MAPPING.md
$InvestmentQueue = "https://sqs..."
$FundingQueue = "https://sqs..."
$ResultsQueue = "https://sqs..."
$DlqQueue = "https://sqs..."

# Delete queues
aws sqs delete-queue --queue-url $InvestmentQueue
aws sqs delete-queue --queue-url $FundingQueue
aws sqs delete-queue --queue-url $ResultsQueue
aws sqs delete-queue --queue-url $DlqQueue

# Detach and delete policy
$PolicyArn = "arn:aws:iam::ACCOUNT:policy/service20-sqs-access-production"
aws iam detach-user-policy --user-name service20-admin --policy-arn $PolicyArn
aws iam delete-policy --policy-arn $PolicyArn
```

**Bash:**
```bash
# Source the queue URLs from mapping file
source <(grep -v '^#' queue_mappings.txt | awk -F'|' '{print "export " $1 "=" $2}')

# Delete queues
aws sqs delete-queue --queue-url $INVESTMENT_QUEUE_URL
aws sqs delete-queue --queue-url $FUNDING_QUEUE_URL
aws sqs delete-queue --queue-url $RESULTS_QUEUE_URL
aws sqs delete-queue --queue-url $DLQ_QUEUE_URL

# Delete policy
POLICY_ARN=$(grep IAM_POLICY queue_mappings.txt | cut -d'|' -f3)
aws iam detach-user-policy --user-name service20-admin --policy-arn $POLICY_ARN
aws iam delete-policy --policy-arn $POLICY_ARN
```

---

## Troubleshooting

### Issue: "Queue already exists"

**Solution:** Queues have the same name. Either:
1. Delete existing queue first
2. Use different environment name: `-Environment "prod2"`

### Issue: "Access Denied"

**Solutions:**
1. Check IAM policy is attached: `aws iam list-attached-user-policies --user-name service20-admin`
2. Verify credentials: `aws sts get-caller-identity`
3. Check policy permissions: Review `sqs_policy.json`

### Issue: "Invalid queue URL"

**Solutions:**
1. Verify region matches queue region
2. Check queue URL format in `.env`
3. Test with: `aws sqs get-queue-attributes --queue-url <URL>`

### Issue: "Connection timeout"

**Solutions:**
1. Check network connectivity
2. Verify security groups (if using VPC)
3. Check AWS service health: https://status.aws.amazon.com

---

## Cost Estimation

### SQS Pricing (as of 2024)

- **First 1M requests/month:** Free
- **After 1M requests:** $0.40 per million requests

### Example: Service20 Usage

**Assumptions:**
- 100 opportunities/day
- 3 messages per opportunity (request + result + confirmation)
- 30 days/month

**Calculation:**
- Total messages: 100 × 3 × 30 = 9,000/month
- Cost: **Free** (under 1M requests)

**At scale (1,000 opportunities/day):**
- Total messages: 1,000 × 3 × 30 = 90,000/month
- Cost: **Free** (still under 1M)

**Very high scale (10,000 opportunities/day):**
- Total messages: 10,000 × 3 × 30 = 900,000/month
- Cost: **Free** (still under 1M!)

### Additional Costs

- **Data Transfer:** Free within same region
- **CloudWatch Logs:** ~$0.50/GB ingested
- **AI API Calls:** Main cost driver
  - OpenAI GPT-4o: ~$0.15-0.50 per research
  - Per opportunity: ~$0.50-1.00

**Total Monthly Cost Estimate:**
- SQS: $0 (free tier)
- 1,000 opportunities: ~$500-1,000 (AI costs)
- 10,000 opportunities: ~$5,000-10,000 (AI costs)

---

## Support

### Documentation
- **AWS SQS:** https://docs.aws.amazon.com/sqs/
- **AWS CLI:** https://docs.aws.amazon.com/cli/
- **Service20:** See `README.md` and `SERVICE_OVERVIEW.md`

### Scripts Location
- `scripts/setup_aws_sqs.ps1` (Windows)
- `scripts/setup_aws_sqs.sh` (Linux/Mac)
- `scripts/test_sqs_connection.py` (Test connectivity)
- `scripts/monitor_queues.py` (Monitor queue status)

### Generated Files
- `RESOURCE_MAPPING.md` - Complete resource documentation
- `queue_mappings.txt` - Machine-readable mappings
- `.env.{environment}` - Environment configuration
