# Complete Monitoring Setup Guide

This guide will walk you through setting up AWS CLI and monitoring tools for your Service20 SQS queues.

## Quick Start (5 Minutes)

### Step 1: Install AWS CLI

**Windows (PowerShell as Administrator):**
```powershell
# Download and install
Invoke-WebRequest -Uri "https://awscli.amazonaws.com/AWSCLIV2.msi" -OutFile "$env:TEMP\AWSCLIV2.msi"
Start-Process msiexec.exe -Wait -ArgumentList "/i $env:TEMP\AWSCLIV2.msi /quiet"

# Verify
aws --version
```

**Linux:**
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
aws --version
```

**Mac:**
```bash
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /
aws --version
```

### Step 2: Configure AWS Credentials

```bash
aws configure
```

Enter your credentials:
```
AWS Access Key ID: YOUR_ACCESS_KEY
AWS Secret Access Key: YOUR_SECRET_KEY
Default region name: eu-west-2
Default output format: json
```

### Step 3: Test Connection

```bash
# Test AWS credentials
aws sts get-caller-identity

# List SQS queues
aws sqs list-queues --queue-name-prefix service20
```

### Step 4: Start Monitoring

**Option A: Python Script (Recommended)**
```bash
# Monitor continuously
python scripts/monitor_queues.py --mode continuous --interval 5
```

**Option B: Interactive Menu**

Windows:
```cmd
scripts\monitor_queues.bat
```

Linux/Mac:
```bash
./scripts/monitor_queues.sh
```

**Option C: Helper Functions**

PowerShell:
```powershell
. .\scripts\aws_cli_helpers.ps1
Watch-Queues -Interval 5
```

Bash:
```bash
source scripts/aws_cli_helpers.sh
watch_queues 5
```

## Detailed Setup

### Prerequisites

1. **Python 3.10+** (for Python monitoring script)
2. **AWS Account** with SQS access
3. **AWS Credentials** (Access Key ID and Secret Access Key)

### Installation

#### 1. Install Dependencies

```bash
# Install boto3 for Python monitoring
pip install boto3

# Or install from requirements
pip install -r requirements-sqs.txt
```

#### 2. Verify AWS CLI Installation

```bash
# Check version
aws --version

# Should show: aws-cli/2.x.x Python/3.x.x ...
```

#### 3. Configure AWS Credentials

**Method 1: Using aws configure (Recommended)**
```bash
aws configure
```

**Method 2: Environment Variables**

Windows PowerShell:
```powershell
$env:AWS_ACCESS_KEY_ID="YOUR_KEY"
$env:AWS_SECRET_ACCESS_KEY="YOUR_SECRET"
$env:AWS_DEFAULT_REGION="eu-west-2"
```

Linux/Mac:
```bash
export AWS_ACCESS_KEY_ID="YOUR_KEY"
export AWS_SECRET_ACCESS_KEY="YOUR_SECRET"
export AWS_DEFAULT_REGION="eu-west-2"
```

**Method 3: Credentials File**

Create/edit `~/.aws/credentials`:
```ini
[default]
aws_access_key_id = YOUR_KEY
aws_secret_access_key = YOUR_SECRET
```

Create/edit `~/.aws/config`:
```ini
[default]
region = eu-west-2
output = json
```

### Testing

#### Test 1: AWS Connection

```bash
# Get account identity
aws sts get-caller-identity

# Expected output:
{
    "UserId": "AIDAXXXXXXXXXX",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/youruser"
}
```

#### Test 2: List Queues

```bash
# List all SQS queues
aws sqs list-queues

# List service20 queues only
aws sqs list-queues --queue-name-prefix service20
```

#### Test 3: Get Queue Attributes

```bash
# Get investment queue URL
QUEUE_URL=$(aws sqs get-queue-url --queue-name service20-investment-opportunities --query 'QueueUrl' --output text)

# Get queue attributes
aws sqs get-queue-attributes --queue-url $QUEUE_URL --attribute-names All
```

#### Test 4: Python Monitoring

```bash
# Test once
python scripts/monitor_queues.py --mode once

# Test health check
python scripts/monitor_queues.py --mode health

# Test JSON output
python scripts/monitor_queues.py --mode json
```

## Usage Scenarios

### Scenario 1: Development Monitoring

Monitor queues while developing:

```bash
# Terminal 1: Run enhanced handlers
python examples/sqs_research_integration_example.py

# Terminal 2: Monitor queues
python scripts/monitor_queues.py --mode continuous --interval 5
```

### Scenario 2: Production Monitoring

Set up automated monitoring:

**Linux/Mac Cron:**
```bash
# Edit crontab
crontab -e

# Add health check every 5 minutes
*/5 * * * * cd /path/to/service20 && python scripts/monitor_queues.py --mode health || echo "Queue health issues" | mail -s "Alert" admin@example.com
```

**Windows Task Scheduler:**
```powershell
# Create scheduled task
$action = New-ScheduledTaskAction -Execute "python.exe" -Argument "C:\path\to\service20\scripts\monitor_queues.py --mode health"
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5)
Register-ScheduledTask -TaskName "Service20Monitor" -Action $action -Trigger $trigger
```

### Scenario 3: Quick Queue Check

Use helper functions for quick checks:

**PowerShell:**
```powershell
# Load functions once
. .\scripts\aws_cli_helpers.ps1

# Quick check anytime
Monitor-AllQueues

# Peek at messages
Peek-Messages -QueueName "service20-investment-opportunities" -MaxMessages 3
```

**Bash:**
```bash
# Load functions once
source scripts/aws_cli_helpers.sh

# Quick check anytime
monitor_all

# Peek at messages
peek_messages service20-investment-opportunities 3
```

### Scenario 4: CI/CD Integration

```yaml
# .github/workflows/queue-health.yml
name: Queue Health Check
on:
  schedule:
    - cron: '*/15 * * * *'  # Every 15 minutes

jobs:
  health-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Configure AWS
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: eu-west-2

      - name: Check Queue Health
        run: |
          python scripts/monitor_queues.py --mode health
```

## Monitoring Commands Reference

### Basic Commands

```bash
# Monitor once
python scripts/monitor_queues.py --mode once

# Monitor continuously (5s refresh)
python scripts/monitor_queues.py --mode continuous --interval 5

# Health check (exit code 0=healthy, 1=issues)
python scripts/monitor_queues.py --mode health

# JSON output (for scripting)
python scripts/monitor_queues.py --mode json
```

### AWS CLI Direct Commands

```bash
# Get queue URL
aws sqs get-queue-url --queue-name service20-investment-opportunities

# Get message count
aws sqs get-queue-attributes \
  --queue-url QUEUE_URL \
  --attribute-names ApproximateNumberOfMessages \
  --query 'Attributes.ApproximateNumberOfMessages'

# Receive messages (peek, don't delete)
aws sqs receive-message \
  --queue-url QUEUE_URL \
  --max-number-of-messages 10 \
  --wait-time-seconds 20
```

### Helper Function Commands

**PowerShell:**
```powershell
Monitor-AllQueues                    # Show all queue stats
Watch-Queues -Interval 5             # Continuous monitoring
Test-AllQueuesHealth                 # Health check
Peek-Messages -QueueName "..."       # View messages
Send-TestMessage -QueueName "..."    # Send test
```

**Bash:**
```bash
monitor_all                          # Show all queue stats
watch_queues 5                       # Continuous monitoring
check_all_health                     # Health check
peek_messages queue_name 5           # View messages
send_test_message queue_name         # Send test
```

## Alerting Setup

### Email Alerts (Linux/Mac)

```bash
#!/bin/bash
# save as: queue_alert.sh

if ! python3 scripts/monitor_queues.py --mode health; then
    python3 scripts/monitor_queues.py --mode json | mail -s "Service20 Queue Alert" admin@example.com
fi
```

Add to cron:
```bash
*/10 * * * * /path/to/queue_alert.sh
```

### Slack Alerts

```python
# save as: scripts/slack_alert.py
import requests
import subprocess
import json

def check_and_alert():
    result = subprocess.run(
        ['python', 'monitor_queues.py', '--mode', 'json'],
        capture_output=True,
        text=True
    )

    data = json.loads(result.stdout)

    # Check for issues
    for queue, stats in data['queues'].items():
        if stats.get('available', 0) > 100:
            send_slack_alert(
                f"⚠️ High queue depth in {queue}: {stats['available']} messages"
            )

def send_slack_alert(message):
    webhook_url = "YOUR_SLACK_WEBHOOK_URL"
    requests.post(webhook_url, json={'text': message})

if __name__ == '__main__':
    check_and_alert()
```

### CloudWatch Alarms

```bash
# Create alarm for high queue depth
aws cloudwatch put-metric-alarm \
  --alarm-name service20-investment-high-depth \
  --alarm-description "Alert when >100 messages" \
  --metric-name ApproximateNumberOfMessagesVisible \
  --namespace AWS/SQS \
  --statistic Average \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 100 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=QueueName,Value=service20-investment-opportunities
```

## Troubleshooting

### Issue: AWS CLI not found

**Solution:**
```bash
# Check installation
which aws  # Linux/Mac
where aws  # Windows

# If not found, reinstall or add to PATH
```

### Issue: Access Denied

**Solution:**
```bash
# Verify credentials
aws sts get-caller-identity

# Reconfigure if needed
aws configure

# Check IAM permissions
```

### Issue: Queue Not Found

**Solution:**
```bash
# List all queues
aws sqs list-queues

# Check region
aws configure get region

# Verify queue name
aws sqs get-queue-url --queue-name service20-investment-opportunities
```

### Issue: Python Script Fails

**Solution:**
```bash
# Install dependencies
pip install boto3

# Or use CLI mode
python scripts/monitor_queues.py --mode once --use-cli

# Check Python version
python --version  # Should be 3.7+
```

## Next Steps

1. ✅ **Set up automated monitoring** (cron/Task Scheduler)
2. ✅ **Configure alerts** (email/Slack/PagerDuty)
3. ✅ **Create CloudWatch alarms** for critical metrics
4. ✅ **Build a dashboard** using JSON output
5. ✅ **Integrate with CI/CD** for deployment checks
6. ✅ **Document runbooks** for common issues

## Resources

- [AWS CLI Setup Guide](AWS_CLI_SETUP.md)
- [Scripts Documentation](scripts/README.md)
- [SQS Integration Guide](SQS_INTEGRATION.md)
- [Quick Start Guide](QUICKSTART_SQS.md)
- [AWS SQS Documentation](https://docs.aws.amazon.com/sqs/)

## Support

For monitoring issues:
1. Check troubleshooting section above
2. Verify AWS credentials and permissions
3. Test with direct AWS CLI commands
4. Check CloudWatch logs if available
5. Enable DEBUG logging: `export LOG_LEVEL=DEBUG`
