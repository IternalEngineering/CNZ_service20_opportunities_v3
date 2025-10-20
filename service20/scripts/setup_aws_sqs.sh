#!/bin/bash

# Service20 - AWS SQS Queue Setup Script
# This script creates all necessary SQS queues and IAM policies for Service20 agents
# Usage: ./setup_aws_sqs.sh [region] [environment]

set -e  # Exit on error

# Configuration
REGION="${1:-eu-west-2}"
ENVIRONMENT="${2:-production}"
SERVICE_NAME="service20"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Service20 AWS SQS Queue Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Region: ${GREEN}${REGION}${NC}"
echo -e "Environment: ${GREEN}${ENVIRONMENT}${NC}"
echo ""

# Check AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI not installed${NC}"
    echo "Install from: https://aws.amazon.com/cli/"
    exit 1
fi

# Check AWS credentials
echo -e "${YELLOW}Checking AWS credentials...${NC}"
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}Error: AWS credentials not configured${NC}"
    echo "Run: aws configure"
    exit 1
fi

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✓ Connected to AWS Account: ${AWS_ACCOUNT_ID}${NC}"
echo ""

# Function to create SQS queue
create_queue() {
    local queue_name=$1
    local visibility_timeout=$2
    local message_retention=$3
    local receive_wait_time=$4

    echo -e "${YELLOW}Creating queue: ${queue_name}${NC}"

    queue_url=$(aws sqs create-queue \
        --queue-name "${queue_name}" \
        --region "${REGION}" \
        --attributes \
            "VisibilityTimeout=${visibility_timeout},"\
"MessageRetentionPeriod=${message_retention},"\
"ReceiveMessageWaitTimeSeconds=${receive_wait_time}" \
        --query 'QueueUrl' \
        --output text 2>&1)

    if [[ $? -eq 0 ]]; then
        echo -e "${GREEN}✓ Created: ${queue_url}${NC}"

        # Get queue ARN
        queue_arn=$(aws sqs get-queue-attributes \
            --queue-url "${queue_url}" \
            --region "${REGION}" \
            --attribute-names QueueArn \
            --query 'Attributes.QueueArn' \
            --output text)

        echo -e "  ARN: ${queue_arn}"
        echo ""

        # Store mapping
        echo "${queue_name}|${queue_url}|${queue_arn}" >> queue_mappings.txt

        return 0
    else
        echo -e "${RED}✗ Failed to create queue${NC}"
        echo "${queue_url}"
        return 1
    fi
}

# Function to add tags to queue
tag_queue() {
    local queue_url=$1
    local queue_name=$2

    aws sqs tag-queue \
        --queue-url "${queue_url}" \
        --region "${REGION}" \
        --tags \
            "Service=service20" \
            "Environment=${ENVIRONMENT}" \
            "ManagedBy=terraform-or-script" \
            "QueueName=${queue_name}" \
        &> /dev/null

    if [[ $? -eq 0 ]]; then
        echo -e "${GREEN}✓ Tagged queue: ${queue_name}${NC}"
    fi
}

# Initialize mapping file
echo "# Service20 Queue Mappings" > queue_mappings.txt
echo "# Format: QueueName|QueueURL|QueueARN" >> queue_mappings.txt
echo "# Generated: $(date)" >> queue_mappings.txt
echo "" >> queue_mappings.txt

# Create queues
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Creating SQS Queues${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Queue 1: Investment Opportunities
INVESTMENT_QUEUE_NAME="${SERVICE_NAME}-investment-opportunities-${ENVIRONMENT}"
create_queue "${INVESTMENT_QUEUE_NAME}" 300 345600 20
INVESTMENT_QUEUE_URL=$(grep "${INVESTMENT_QUEUE_NAME}" queue_mappings.txt | cut -d'|' -f2)
tag_queue "${INVESTMENT_QUEUE_URL}" "${INVESTMENT_QUEUE_NAME}"

# Queue 2: Funding Opportunities
FUNDING_QUEUE_NAME="${SERVICE_NAME}-funding-opportunities-${ENVIRONMENT}"
create_queue "${FUNDING_QUEUE_NAME}" 300 345600 20
FUNDING_QUEUE_URL=$(grep "${FUNDING_QUEUE_NAME}" queue_mappings.txt | cut -d'|' -f2)
tag_queue "${FUNDING_QUEUE_URL}" "${FUNDING_QUEUE_NAME}"

# Queue 3: Research Results
RESULTS_QUEUE_NAME="${SERVICE_NAME}-research-results-${ENVIRONMENT}"
create_queue "${RESULTS_QUEUE_NAME}" 300 345600 20
RESULTS_QUEUE_URL=$(grep "${RESULTS_QUEUE_NAME}" queue_mappings.txt | cut -d'|' -f2)
tag_queue "${RESULTS_QUEUE_URL}" "${RESULTS_QUEUE_NAME}"

# Queue 4: Dead Letter Queue (optional but recommended)
DLQ_QUEUE_NAME="${SERVICE_NAME}-dlq-${ENVIRONMENT}"
create_queue "${DLQ_QUEUE_NAME}" 300 1209600 20  # 14 days retention
DLQ_QUEUE_URL=$(grep "${DLQ_QUEUE_NAME}" queue_mappings.txt | cut -d'|' -f2)
tag_queue "${DLQ_QUEUE_URL}" "${DLQ_QUEUE_NAME}"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Creating IAM Policy${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Create IAM policy for queue access
POLICY_NAME="${SERVICE_NAME}-sqs-access-${ENVIRONMENT}"

cat > sqs_policy.json <<EOF
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
                "$(grep ${INVESTMENT_QUEUE_NAME} queue_mappings.txt | cut -d'|' -f3)",
                "$(grep ${FUNDING_QUEUE_NAME} queue_mappings.txt | cut -d'|' -f3)",
                "$(grep ${RESULTS_QUEUE_NAME} queue_mappings.txt | cut -d'|' -f3)",
                "$(grep ${DLQ_QUEUE_NAME} queue_mappings.txt | cut -d'|' -f3)"
            ]
        }
    ]
}
EOF

echo -e "${YELLOW}Creating IAM policy: ${POLICY_NAME}${NC}"

policy_arn=$(aws iam create-policy \
    --policy-name "${POLICY_NAME}" \
    --policy-document file://sqs_policy.json \
    --description "Service20 SQS queue access policy for ${ENVIRONMENT}" \
    --query 'Policy.Arn' \
    --output text 2>&1)

if [[ $? -eq 0 ]]; then
    echo -e "${GREEN}✓ Created IAM policy: ${policy_arn}${NC}"
    echo "IAM_POLICY|${POLICY_NAME}|${policy_arn}" >> queue_mappings.txt
else
    echo -e "${YELLOW}⚠ Policy might already exist or failed to create${NC}"
    # Try to get existing policy
    policy_arn=$(aws iam list-policies \
        --query "Policies[?PolicyName=='${POLICY_NAME}'].Arn" \
        --output text)
    if [[ -n "$policy_arn" ]]; then
        echo -e "${GREEN}✓ Found existing policy: ${policy_arn}${NC}"
        echo "IAM_POLICY|${POLICY_NAME}|${policy_arn}" >> queue_mappings.txt
    fi
fi

echo ""

# Create .env template
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Generating Configuration Files${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

cat > .env.${ENVIRONMENT} <<EOF
# Service20 AWS Configuration - ${ENVIRONMENT}
# Generated: $(date)

# AWS Credentials
AWS_REGION=${REGION}
AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY_HERE
AWS_SECRET_ACCESS_KEY=YOUR_SECRET_KEY_HERE

# SQS Queue URLs
SQS_INVESTMENT_QUEUE_URL=${INVESTMENT_QUEUE_URL}
SQS_FUNDING_QUEUE_URL=${FUNDING_QUEUE_URL}
SQS_RESULTS_QUEUE_URL=${RESULTS_QUEUE_URL}

# AI Model APIs (required for research)
OPENAI_API_KEY=YOUR_OPENAI_KEY_HERE
ANTHROPIC_API_KEY=YOUR_ANTHROPIC_KEY_HERE
TAVILY_API_KEY=YOUR_TAVILY_KEY_HERE

# PostgreSQL Database (optional)
DATABASE_URL=postgresql://user:password@host:5432/dbname

# LangSmith (optional - for monitoring)
LANGSMITH_API_KEY=YOUR_LANGSMITH_KEY_HERE
LANGSMITH_PROJECT=service20-${ENVIRONMENT}
LANGSMITH_TRACING=true
EOF

echo -e "${GREEN}✓ Created .env.${ENVIRONMENT}${NC}"
echo ""

# Create resource mapping document
cat > RESOURCE_MAPPING.md <<EOF
# Service20 AWS Resource Mapping

**Generated:** $(date)
**AWS Account:** ${AWS_ACCOUNT_ID}
**Region:** ${REGION}
**Environment:** ${ENVIRONMENT}

## SQS Queues

### Investment Opportunities Queue
- **Name:** ${INVESTMENT_QUEUE_NAME}
- **URL:** ${INVESTMENT_QUEUE_URL}
- **ARN:** $(grep ${INVESTMENT_QUEUE_NAME} queue_mappings.txt | cut -d'|' -f3)
- **Original Name:** service20-investment-opportunities

### Funding Opportunities Queue
- **Name:** ${FUNDING_QUEUE_NAME}
- **URL:** ${FUNDING_QUEUE_URL}
- **ARN:** $(grep ${FUNDING_QUEUE_NAME} queue_mappings.txt | cut -d'|' -f3)
- **Original Name:** service20-funding-opportunities

### Research Results Queue
- **Name:** ${RESULTS_QUEUE_NAME}
- **URL:** ${RESULTS_QUEUE_URL}
- **ARN:** $(grep ${RESULTS_QUEUE_NAME} queue_mappings.txt | cut -d'|' -f3)
- **Original Name:** service20-research-results

### Dead Letter Queue
- **Name:** ${DLQ_QUEUE_NAME}
- **URL:** ${DLQ_QUEUE_URL}
- **ARN:** $(grep ${DLQ_QUEUE_NAME} queue_mappings.txt | cut -d'|' -f3)
- **Original Name:** service20-dlq

## IAM Policy

- **Policy Name:** ${POLICY_NAME}
- **Policy ARN:** ${policy_arn}
- **Original Name:** service20-sqs-access

## Configuration Mapping

| Resource Type | Original Identifier | New Identifier | Environment Variable |
|---------------|---------------------|----------------|---------------------|
| SQS Queue | service20-investment-opportunities | ${INVESTMENT_QUEUE_NAME} | SQS_INVESTMENT_QUEUE_URL |
| SQS Queue | service20-funding-opportunities | ${FUNDING_QUEUE_NAME} | SQS_FUNDING_QUEUE_URL |
| SQS Queue | service20-research-results | ${RESULTS_QUEUE_NAME} | SQS_RESULTS_QUEUE_URL |
| IAM Policy | service20-sqs-access | ${POLICY_NAME} | N/A |
| Region | eu-west-2 | ${REGION} | AWS_REGION |

## Queue Settings

All queues are configured with:
- **Visibility Timeout:** 300 seconds (5 minutes)
- **Message Retention:** 345600 seconds (4 days)
- **Receive Wait Time:** 20 seconds (long polling enabled)
- **Dead Letter Queue Retention:** 1209600 seconds (14 days)

## Next Steps

1. Update your \`.env\` file with credentials:
   \`\`\`bash
   cp .env.${ENVIRONMENT} .env
   nano .env  # Add your AWS credentials and API keys
   \`\`\`

2. Test queue connectivity:
   \`\`\`bash
   python scripts/test_sqs_connection.py
   \`\`\`

3. Attach IAM policy to your IAM user/role:
   \`\`\`bash
   aws iam attach-user-policy \\
     --user-name YOUR_IAM_USER \\
     --policy-arn ${policy_arn}
   \`\`\`

4. Start processing messages:
   \`\`\`bash
   python examples/sqs_research_integration_example.py
   \`\`\`

## Cleanup Commands

To delete all resources created by this script:

\`\`\`bash
# Delete queues
aws sqs delete-queue --queue-url ${INVESTMENT_QUEUE_URL}
aws sqs delete-queue --queue-url ${FUNDING_QUEUE_URL}
aws sqs delete-queue --queue-url ${RESULTS_QUEUE_URL}
aws sqs delete-queue --queue-url ${DLQ_QUEUE_URL}

# Delete IAM policy (detach from users first)
aws iam delete-policy --policy-arn ${policy_arn}
\`\`\`

## Monitoring

Monitor queue metrics:
\`\`\`bash
python scripts/monitor_queues.py
\`\`\`

View CloudWatch metrics:
\`\`\`bash
aws cloudwatch get-metric-statistics \\
  --namespace AWS/SQS \\
  --metric-name NumberOfMessagesSent \\
  --dimensions Name=QueueName,Value=${INVESTMENT_QUEUE_NAME} \\
  --start-time \$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \\
  --end-time \$(date -u +%Y-%m-%dT%H:%M:%S) \\
  --period 300 \\
  --statistics Sum
\`\`\`
EOF

echo -e "${GREEN}✓ Created RESOURCE_MAPPING.md${NC}"
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Setup Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}✓ Created 4 SQS queues${NC}"
echo -e "${GREEN}✓ Created IAM policy${NC}"
echo -e "${GREEN}✓ Generated configuration files${NC}"
echo ""
echo -e "${YELLOW}Files created:${NC}"
echo -e "  - queue_mappings.txt (machine-readable mappings)"
echo -e "  - RESOURCE_MAPPING.md (human-readable documentation)"
echo -e "  - .env.${ENVIRONMENT} (environment configuration)"
echo -e "  - sqs_policy.json (IAM policy document)"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "  1. Review RESOURCE_MAPPING.md"
echo -e "  2. Update .env.${ENVIRONMENT} with your credentials"
echo -e "  3. Attach IAM policy to your user/role:"
echo -e "     ${BLUE}aws iam attach-user-policy --user-name YOUR_USER --policy-arn ${policy_arn}${NC}"
echo -e "  4. Test connectivity:"
echo -e "     ${BLUE}python scripts/test_sqs_connection.py${NC}"
echo ""
