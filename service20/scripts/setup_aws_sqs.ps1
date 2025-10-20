# Service20 - AWS SQS Queue Setup Script (PowerShell)
# This script creates all necessary SQS queues and IAM policies for Service20 agents
# Usage: .\setup_aws_sqs.ps1 -Region "eu-west-2" -Environment "production"

param(
    [string]$Region = "eu-west-2",
    [string]$Environment = "production"
)

$ErrorActionPreference = "Stop"

# Configuration
$ServiceName = "service20"

Write-Host "========================================" -ForegroundColor Blue
Write-Host "Service20 AWS SQS Queue Setup" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue
Write-Host ""
Write-Host "Region: $Region" -ForegroundColor Green
Write-Host "Environment: $Environment" -ForegroundColor Green
Write-Host ""

# Check AWS CLI is installed
try {
    aws --version | Out-Null
} catch {
    Write-Host "Error: AWS CLI not installed" -ForegroundColor Red
    Write-Host "Install from: https://aws.amazon.com/cli/"
    exit 1
}

# Check AWS credentials
Write-Host "Checking AWS credentials..." -ForegroundColor Yellow
try {
    $AwsAccountId = aws sts get-caller-identity --query Account --output text
    Write-Host "✓ Connected to AWS Account: $AwsAccountId" -ForegroundColor Green
} catch {
    Write-Host "Error: AWS credentials not configured" -ForegroundColor Red
    Write-Host "Run: aws configure"
    exit 1
}
Write-Host ""

# Function to create SQS queue
function Create-Queue {
    param(
        [string]$QueueName,
        [int]$VisibilityTimeout,
        [int]$MessageRetention,
        [int]$ReceiveWaitTime
    )

    Write-Host "Creating queue: $QueueName" -ForegroundColor Yellow

    try {
        $QueueUrl = aws sqs create-queue `
            --queue-name $QueueName `
            --region $Region `
            --attributes "VisibilityTimeout=$VisibilityTimeout,MessageRetentionPeriod=$MessageRetention,ReceiveMessageWaitTimeSeconds=$ReceiveWaitTime" `
            --query 'QueueUrl' `
            --output text

        Write-Host "✓ Created: $QueueUrl" -ForegroundColor Green

        # Get queue ARN
        $QueueArn = aws sqs get-queue-attributes `
            --queue-url $QueueUrl `
            --region $Region `
            --attribute-names QueueArn `
            --query 'Attributes.QueueArn' `
            --output text

        Write-Host "  ARN: $QueueArn"
        Write-Host ""

        # Store mapping
        "$QueueName|$QueueUrl|$QueueArn" | Add-Content -Path "queue_mappings.txt"

        return @{
            Name = $QueueName
            Url = $QueueUrl
            Arn = $QueueArn
        }
    } catch {
        Write-Host "✗ Failed to create queue" -ForegroundColor Red
        Write-Host $_.Exception.Message
        throw
    }
}

# Function to tag queue
function Add-QueueTags {
    param(
        [string]$QueueUrl,
        [string]$QueueName
    )

    try {
        aws sqs tag-queue `
            --queue-url $QueueUrl `
            --region $Region `
            --tags "Service=service20" "Environment=$Environment" "ManagedBy=powershell-script" "QueueName=$QueueName" `
            2>&1 | Out-Null

        Write-Host "✓ Tagged queue: $QueueName" -ForegroundColor Green
    } catch {
        Write-Host "⚠ Failed to tag queue (non-critical)" -ForegroundColor Yellow
    }
}

# Initialize mapping file
"# Service20 Queue Mappings" | Set-Content -Path "queue_mappings.txt"
"# Format: QueueName|QueueURL|QueueARN" | Add-Content -Path "queue_mappings.txt"
"# Generated: $(Get-Date)" | Add-Content -Path "queue_mappings.txt"
"" | Add-Content -Path "queue_mappings.txt"

# Create queues
Write-Host "========================================" -ForegroundColor Blue
Write-Host "Creating SQS Queues" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue
Write-Host ""

# Queue 1: Investment Opportunities
$InvestmentQueueName = "$ServiceName-investment-opportunities-$Environment"
$InvestmentQueue = Create-Queue -QueueName $InvestmentQueueName -VisibilityTimeout 300 -MessageRetention 345600 -ReceiveWaitTime 20
Add-QueueTags -QueueUrl $InvestmentQueue.Url -QueueName $InvestmentQueueName

# Queue 2: Funding Opportunities
$FundingQueueName = "$ServiceName-funding-opportunities-$Environment"
$FundingQueue = Create-Queue -QueueName $FundingQueueName -VisibilityTimeout 300 -MessageRetention 345600 -ReceiveWaitTime 20
Add-QueueTags -QueueUrl $FundingQueue.Url -QueueName $FundingQueueName

# Queue 3: Research Results
$ResultsQueueName = "$ServiceName-research-results-$Environment"
$ResultsQueue = Create-Queue -QueueName $ResultsQueueName -VisibilityTimeout 300 -MessageRetention 345600 -ReceiveWaitTime 20
Add-QueueTags -QueueUrl $ResultsQueue.Url -QueueName $ResultsQueueName

# Queue 4: Dead Letter Queue
$DlqQueueName = "$ServiceName-dlq-$Environment"
$DlqQueue = Create-Queue -QueueName $DlqQueueName -VisibilityTimeout 300 -MessageRetention 1209600 -ReceiveWaitTime 20
Add-QueueTags -QueueUrl $DlqQueue.Url -QueueName $DlqQueueName

Write-Host ""
Write-Host "========================================" -ForegroundColor Blue
Write-Host "Creating IAM Policy" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue
Write-Host ""

# Create IAM policy for queue access
$PolicyName = "$ServiceName-sqs-access-$Environment"

$PolicyDocument = @"
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "Service20SQSAccess",
            "Effect": "Allow",
            "Action": [
                "sqs:SendMessage",
                "sqs:ReceiveMessage",
                "sqs:DeleteMessage",
                "sqs:GetQueueAttributes",
                "sqs:GetQueueUrl",
                "sqs:ListQueues",
                "sqs:PurgeQueue"
            ],
            "Resource": [
                "$($InvestmentQueue.Arn)",
                "$($FundingQueue.Arn)",
                "$($ResultsQueue.Arn)",
                "$($DlqQueue.Arn)"
            ]
        }
    ]
}
"@

$PolicyDocument | Set-Content -Path "sqs_policy.json"

Write-Host "Creating IAM policy: $PolicyName" -ForegroundColor Yellow

try {
    $PolicyArn = aws iam create-policy `
        --policy-name $PolicyName `
        --policy-document file://sqs_policy.json `
        --description "Service20 SQS queue access policy for $Environment" `
        --query 'Policy.Arn' `
        --output text

    Write-Host "✓ Created IAM policy: $PolicyArn" -ForegroundColor Green
    "IAM_POLICY|$PolicyName|$PolicyArn" | Add-Content -Path "queue_mappings.txt"
} catch {
    Write-Host "⚠ Policy might already exist or failed to create" -ForegroundColor Yellow
    # Try to get existing policy
    $PolicyArn = aws iam list-policies --query "Policies[?PolicyName=='$PolicyName'].Arn" --output text
    if ($PolicyArn) {
        Write-Host "✓ Found existing policy: $PolicyArn" -ForegroundColor Green
        "IAM_POLICY|$PolicyName|$PolicyArn" | Add-Content -Path "queue_mappings.txt"
    }
}

Write-Host ""

# Create .env template
Write-Host "========================================" -ForegroundColor Blue
Write-Host "Generating Configuration Files" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue
Write-Host ""

$EnvContent = @"
# Service20 AWS Configuration - $Environment
# Generated: $(Get-Date)

# AWS Credentials
AWS_REGION=$Region
AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY_HERE
AWS_SECRET_ACCESS_KEY=YOUR_SECRET_KEY_HERE

# SQS Queue URLs
SQS_INVESTMENT_QUEUE_URL=$($InvestmentQueue.Url)
SQS_FUNDING_QUEUE_URL=$($FundingQueue.Url)
SQS_RESULTS_QUEUE_URL=$($ResultsQueue.Url)

# AI Model APIs (required for research)
OPENAI_API_KEY=YOUR_OPENAI_KEY_HERE
ANTHROPIC_API_KEY=YOUR_ANTHROPIC_KEY_HERE
TAVILY_API_KEY=YOUR_TAVILY_KEY_HERE

# PostgreSQL Database (optional)
DATABASE_URL=postgresql://user:password@host:5432/dbname

# LangSmith (optional - for monitoring)
LANGSMITH_API_KEY=YOUR_LANGSMITH_KEY_HERE
LANGSMITH_PROJECT=service20-$Environment
LANGSMITH_TRACING=true
"@

$EnvContent | Set-Content -Path ".env.$Environment"
Write-Host "✓ Created .env.$Environment" -ForegroundColor Green
Write-Host ""

# Create resource mapping document
$MappingDoc = @"
# Service20 AWS Resource Mapping

**Generated:** $(Get-Date)
**AWS Account:** $AwsAccountId
**Region:** $Region
**Environment:** $Environment

## SQS Queues

### Investment Opportunities Queue
- **Name:** $InvestmentQueueName
- **URL:** $($InvestmentQueue.Url)
- **ARN:** $($InvestmentQueue.Arn)
- **Original Name:** service20-investment-opportunities

### Funding Opportunities Queue
- **Name:** $FundingQueueName
- **URL:** $($FundingQueue.Url)
- **ARN:** $($FundingQueue.Arn)
- **Original Name:** service20-funding-opportunities

### Research Results Queue
- **Name:** $ResultsQueueName
- **URL:** $($ResultsQueue.Url)
- **ARN:** $($ResultsQueue.Arn)
- **Original Name:** service20-research-results

### Dead Letter Queue
- **Name:** $DlqQueueName
- **URL:** $($DlqQueue.Url)
- **ARN:** $($DlqQueue.Arn)
- **Original Name:** service20-dlq

## IAM Policy

- **Policy Name:** $PolicyName
- **Policy ARN:** $PolicyArn
- **Original Name:** service20-sqs-access

## Configuration Mapping

| Resource Type | Original Identifier | New Identifier | Environment Variable |
|---------------|---------------------|----------------|---------------------|
| SQS Queue | service20-investment-opportunities | $InvestmentQueueName | SQS_INVESTMENT_QUEUE_URL |
| SQS Queue | service20-funding-opportunities | $FundingQueueName | SQS_FUNDING_QUEUE_URL |
| SQS Queue | service20-research-results | $ResultsQueueName | SQS_RESULTS_QUEUE_URL |
| IAM Policy | service20-sqs-access | $PolicyName | N/A |
| Region | eu-west-2 | $Region | AWS_REGION |

## Queue Settings

All queues are configured with:
- **Visibility Timeout:** 300 seconds (5 minutes)
- **Message Retention:** 345600 seconds (4 days)
- **Receive Wait Time:** 20 seconds (long polling enabled)
- **Dead Letter Queue Retention:** 1209600 seconds (14 days)

## Next Steps

1. Update your ``.env`` file with credentials:
   ``````powershell
   Copy-Item .env.$Environment .env
   notepad .env  # Add your AWS credentials and API keys
   ``````

2. Test queue connectivity:
   ``````powershell
   python scripts\test_sqs_connection.py
   ``````

3. Attach IAM policy to your IAM user/role:
   ``````powershell
   aws iam attach-user-policy ``
     --user-name YOUR_IAM_USER ``
     --policy-arn $PolicyArn
   ``````

4. Start processing messages:
   ``````powershell
   python examples\sqs_research_integration_example.py
   ``````

## Cleanup Commands

To delete all resources created by this script:

``````powershell
# Delete queues
aws sqs delete-queue --queue-url $($InvestmentQueue.Url)
aws sqs delete-queue --queue-url $($FundingQueue.Url)
aws sqs delete-queue --queue-url $($ResultsQueue.Url)
aws sqs delete-queue --queue-url $($DlqQueue.Url)

# Delete IAM policy (detach from users first)
aws iam delete-policy --policy-arn $PolicyArn
``````

## Monitoring

Monitor queue metrics:
``````powershell
python scripts\monitor_queues.py
``````

View CloudWatch metrics in AWS Console or use AWS CLI.
"@

$MappingDoc | Set-Content -Path "RESOURCE_MAPPING.md"
Write-Host "✓ Created RESOURCE_MAPPING.md" -ForegroundColor Green
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Blue
Write-Host "Setup Complete!" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue
Write-Host ""
Write-Host "✓ Created 4 SQS queues" -ForegroundColor Green
Write-Host "✓ Created IAM policy" -ForegroundColor Green
Write-Host "✓ Generated configuration files" -ForegroundColor Green
Write-Host ""
Write-Host "Files created:" -ForegroundColor Yellow
Write-Host "  - queue_mappings.txt (machine-readable mappings)"
Write-Host "  - RESOURCE_MAPPING.md (human-readable documentation)"
Write-Host "  - .env.$Environment (environment configuration)"
Write-Host "  - sqs_policy.json (IAM policy document)"
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Review RESOURCE_MAPPING.md"
Write-Host "  2. Update .env.$Environment with your credentials"
Write-Host "  3. Attach IAM policy to your user/role:"
Write-Host "     aws iam attach-user-policy --user-name YOUR_USER --policy-arn $PolicyArn" -ForegroundColor Blue
Write-Host "  4. Test connectivity:"
Write-Host "     python scripts\test_sqs_connection.py" -ForegroundColor Blue
Write-Host ""
