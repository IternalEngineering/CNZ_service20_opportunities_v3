# AWS CLI Setup and Monitoring Guide

Complete guide to setting up AWS CLI and monitoring SQS queues for service20.

## Installation

### Windows Installation

#### Option 1: MSI Installer (Recommended)

1. Download the AWS CLI installer:
   - Visit: https://awscli.amazonaws.com/AWSCLIV2.msi
   - Or use PowerShell:
   ```powershell
   # Download installer
   Invoke-WebRequest -Uri "https://awscli.amazonaws.com/AWSCLIV2.msi" -OutFile "AWSCLIV2.msi"

   # Install (may require admin)
   Start-Process msiexec.exe -Wait -ArgumentList '/i AWSCLIV2.msi /quiet'
   ```

2. Verify installation:
   ```bash
   aws --version
   # Should show: aws-cli/2.x.x Python/3.x.x Windows/...
   ```

#### Option 2: Using Python pip

```bash
pip install awscli
aws --version
```

### Linux/Mac Installation

```bash
# Linux
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Mac
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /
```

## Configuration

### 1. Configure AWS Credentials

```bash
aws configure
```

You'll be prompted for:
```
AWS Access Key ID [None]: YOUR_ACCESS_KEY
AWS Secret Access Key [None]: YOUR_SECRET_KEY
Default region name [None]: eu-west-2
Default output format [None]: json
```

Or set environment variables:
```bash
# Windows PowerShell
$env:AWS_ACCESS_KEY_ID="YOUR_ACCESS_KEY"
$env:AWS_SECRET_ACCESS_KEY="YOUR_SECRET_KEY"
$env:AWS_DEFAULT_REGION="eu-west-2"

# Windows CMD
set AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY
set AWS_SECRET_ACCESS_KEY=YOUR_SECRET_KEY
set AWS_DEFAULT_REGION=eu-west-2

# Linux/Mac
export AWS_ACCESS_KEY_ID="YOUR_ACCESS_KEY"
export AWS_SECRET_ACCESS_KEY="YOUR_SECRET_KEY"
export AWS_DEFAULT_REGION="eu-west-2"
```

### 2. Verify Configuration

```bash
# Test credentials
aws sts get-caller-identity

# Should return:
{
    "UserId": "...",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/youruser"
}
```

## Basic SQS Monitoring Commands

### List All Queues

```bash
# List all queues
aws sqs list-queues

# List service20 queues only
aws sqs list-queues --queue-name-prefix service20
```

### Get Queue URL

```bash
# Get investment queue URL
aws sqs get-queue-url --queue-name service20-investment-opportunities

# Get funding queue URL
aws sqs get-queue-url --queue-name service20-funding-opportunities

# Get results queue URL
aws sqs get-queue-url --queue-name service20-research-results
```

### Get Queue Attributes

```bash
# Get all attributes
aws sqs get-queue-attributes \
  --queue-url https://sqs.eu-west-2.amazonaws.com/ACCOUNT_ID/service20-investment-opportunities \
  --attribute-names All

# Get specific attributes
aws sqs get-queue-attributes \
  --queue-url QUEUE_URL \
  --attribute-names ApproximateNumberOfMessages ApproximateNumberOfMessagesNotVisible
```

Key attributes to monitor:
- `ApproximateNumberOfMessages` - Messages available for processing
- `ApproximateNumberOfMessagesNotVisible` - Messages being processed
- `ApproximateNumberOfMessagesDelayed` - Delayed messages
- `ApproximateAgeOfOldestMessage` - Age of oldest message (seconds)

### Receive Messages

```bash
# Receive up to 10 messages
aws sqs receive-message \
  --queue-url QUEUE_URL \
  --max-number-of-messages 10 \
  --wait-time-seconds 20

# Receive with all attributes
aws sqs receive-message \
  --queue-url QUEUE_URL \
  --attribute-names All \
  --message-attribute-names All
```

### Send Test Message

```bash
# Send simple message
aws sqs send-message \
  --queue-url QUEUE_URL \
  --message-body "Test message"

# Send JSON message
aws sqs send-message \
  --queue-url QUEUE_URL \
  --message-body '{"opportunity_id":"TEST-001","title":"Test Opportunity"}'
```

### Delete Message

```bash
# After receiving a message, delete it using receipt handle
aws sqs delete-message \
  --queue-url QUEUE_URL \
  --receipt-handle "RECEIPT_HANDLE_FROM_RECEIVE"
```

### Purge Queue (Development Only!)

```bash
# WARNING: Deletes ALL messages in queue
aws sqs purge-queue --queue-url QUEUE_URL
```

## Advanced Monitoring

### Monitor Queue Depth (Loop)

```bash
# Windows PowerShell
while ($true) {
  aws sqs get-queue-attributes `
    --queue-url QUEUE_URL `
    --attribute-names ApproximateNumberOfMessages ApproximateNumberOfMessagesNotVisible `
    --query 'Attributes' --output table
  Start-Sleep -Seconds 5
}

# Linux/Mac
while true; do
  aws sqs get-queue-attributes \
    --queue-url $QUEUE_URL \
    --attribute-names ApproximateNumberOfMessages ApproximateNumberOfMessagesNotVisible \
    --query 'Attributes' --output table
  sleep 5
done
```

### Get Message Count

```bash
# Investment queue count
aws sqs get-queue-attributes \
  --queue-url $(aws sqs get-queue-url --queue-name service20-investment-opportunities --query 'QueueUrl' --output text) \
  --attribute-names ApproximateNumberOfMessages \
  --query 'Attributes.ApproximateNumberOfMessages' \
  --output text
```

### Monitor All Service20 Queues

```bash
# Get all queue URLs
for queue in service20-investment-opportunities service20-funding-opportunities service20-research-results; do
  url=$(aws sqs get-queue-url --queue-name $queue --query 'QueueUrl' --output text 2>/dev/null)
  if [ ! -z "$url" ]; then
    echo "Queue: $queue"
    aws sqs get-queue-attributes --queue-url $url \
      --attribute-names ApproximateNumberOfMessages ApproximateNumberOfMessagesNotVisible \
      --query 'Attributes' --output table
    echo ""
  fi
done
```

## CloudWatch Integration

### View CloudWatch Metrics

```bash
# Get number of messages sent (last hour)
aws cloudwatch get-metric-statistics \
  --namespace AWS/SQS \
  --metric-name NumberOfMessagesSent \
  --dimensions Name=QueueName,Value=service20-investment-opportunities \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum

# Get approximate number of messages visible
aws cloudwatch get-metric-statistics \
  --namespace AWS/SQS \
  --metric-name ApproximateNumberOfMessagesVisible \
  --dimensions Name=QueueName,Value=service20-investment-opportunities \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Average
```

### Create CloudWatch Alarm

```bash
# Alarm when queue depth > 100
aws cloudwatch put-metric-alarm \
  --alarm-name service20-investment-queue-high-depth \
  --alarm-description "Alert when investment queue has >100 messages" \
  --metric-name ApproximateNumberOfMessagesVisible \
  --namespace AWS/SQS \
  --statistic Average \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 100 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=QueueName,Value=service20-investment-opportunities
```

## Useful Commands Reference

### Queue Management

```bash
# Create queue
aws sqs create-queue --queue-name my-queue

# Delete queue
aws sqs delete-queue --queue-url QUEUE_URL

# Set queue attributes
aws sqs set-queue-attributes \
  --queue-url QUEUE_URL \
  --attributes VisibilityTimeout=300,MessageRetentionPeriod=345600
```

### Message Operations

```bash
# Send batch messages
aws sqs send-message-batch \
  --queue-url QUEUE_URL \
  --entries \
    Id=msg1,MessageBody='Message 1' \
    Id=msg2,MessageBody='Message 2'

# Change message visibility
aws sqs change-message-visibility \
  --queue-url QUEUE_URL \
  --receipt-handle "RECEIPT_HANDLE" \
  --visibility-timeout 600
```

### Query and Filter

```bash
# Get queue URL and attributes in one command
aws sqs get-queue-url --queue-name service20-investment-opportunities | \
  jq -r '.QueueUrl' | \
  xargs -I {} aws sqs get-queue-attributes --queue-url {} --attribute-names All

# Filter output with jq
aws sqs list-queues | jq '.QueueUrls[] | select(contains("service20"))'
```

## Output Formats

AWS CLI supports multiple output formats:

```bash
# JSON (default)
aws sqs list-queues --output json

# Table
aws sqs list-queues --output table

# Text
aws sqs list-queues --output text

# YAML
aws sqs list-queues --output yaml
```

## Troubleshooting

### Command Not Found

```bash
# Windows: Add to PATH
# Go to: System Properties > Environment Variables
# Add: C:\Program Files\Amazon\AWSCLIV2\

# Or use full path
"C:\Program Files\Amazon\AWSCLIV2\aws.exe" --version
```

### Access Denied

```bash
# Check credentials
aws sts get-caller-identity

# Check IAM permissions
aws iam get-user

# Verify region
aws configure get region
```

### Invalid Queue URL

```bash
# Get correct URL
aws sqs get-queue-url --queue-name service20-investment-opportunities

# Verify region matches
aws sqs list-queues --region eu-west-2
```

## Best Practices

1. **Use Named Profiles**: Set up multiple profiles for different environments
   ```bash
   aws configure --profile production
   aws configure --profile development

   # Use specific profile
   aws sqs list-queues --profile production
   ```

2. **Use Query and Filter**: Extract specific fields
   ```bash
   aws sqs get-queue-attributes \
     --queue-url $URL \
     --attribute-names All \
     --query 'Attributes.ApproximateNumberOfMessages'
   ```

3. **Script Common Tasks**: Create shell scripts for repeated operations

4. **Monitor with CloudWatch**: Set up alarms for critical metrics

5. **Use JSON Output for Scripting**: Parse with jq or Python

## Next Steps

1. Run the monitoring scripts in `scripts/` directory
2. Set up CloudWatch alarms for your queues
3. Create custom monitoring dashboards
4. Integrate with your CI/CD pipeline
5. Set up automated alerts

## Resources

- [AWS CLI Documentation](https://docs.aws.amazon.com/cli/)
- [SQS CLI Reference](https://docs.aws.amazon.com/cli/latest/reference/sqs/)
- [CloudWatch CLI Reference](https://docs.aws.amazon.com/cli/latest/reference/cloudwatch/)
