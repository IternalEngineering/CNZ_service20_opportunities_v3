#!/bin/bash
# AWS CLI helper functions for monitoring SQS queues
# Source this file: source aws_cli_helpers.sh

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Queue names
INVESTMENT_QUEUE="service20-investment-opportunities"
FUNDING_QUEUE="service20-funding-opportunities"
RESULTS_QUEUE="service20-research-results"

# Function to get queue URL
get_queue_url() {
    local queue_name=$1
    aws sqs get-queue-url --queue-name "$queue_name" --query 'QueueUrl' --output text 2>/dev/null
}

# Function to get message count
get_message_count() {
    local queue_url=$1
    aws sqs get-queue-attributes \
        --queue-url "$queue_url" \
        --attribute-names ApproximateNumberOfMessages \
        --query 'Attributes.ApproximateNumberOfMessages' \
        --output text
}

# Function to get in-flight count
get_inflight_count() {
    local queue_url=$1
    aws sqs get-queue-attributes \
        --queue-url "$queue_url" \
        --attribute-names ApproximateNumberOfMessagesNotVisible \
        --query 'Attributes.ApproximateNumberOfMessagesNotVisible' \
        --output text
}

# Function to display queue stats
show_queue_stats() {
    local queue_name=$1
    local queue_url=$(get_queue_url "$queue_name")

    if [ -z "$queue_url" ]; then
        echo -e "${RED}❌ Queue not found: $queue_name${NC}"
        return
    fi

    local available=$(get_message_count "$queue_url")
    local inflight=$(get_inflight_count "$queue_url")

    echo -e "${GREEN}📊 $queue_name${NC}"
    echo "   Available: $available"
    echo "   In Flight: $inflight"
    echo ""
}

# Function to monitor all queues
monitor_all() {
    clear
    echo "============================================================"
    echo "Service20 Queue Monitor - $(date '+%Y-%m-%d %H:%M:%S')"
    echo "============================================================"
    echo ""

    show_queue_stats "$INVESTMENT_QUEUE"
    show_queue_stats "$FUNDING_QUEUE"
    show_queue_stats "$RESULTS_QUEUE"
}

# Function to continuously monitor
watch_queues() {
    local interval=${1:-5}
    while true; do
        monitor_all
        echo "Refreshing every ${interval} seconds... (Ctrl+C to stop)"
        sleep "$interval"
    done
}

# Function to peek at messages
peek_messages() {
    local queue_name=$1
    local max_messages=${2:-3}
    local queue_url=$(get_queue_url "$queue_name")

    if [ -z "$queue_url" ]; then
        echo -e "${RED}❌ Queue not found: $queue_name${NC}"
        return
    fi

    echo -e "${GREEN}🔍 Peeking at $queue_name (up to $max_messages messages)${NC}"
    echo ""

    aws sqs receive-message \
        --queue-url "$queue_url" \
        --max-number-of-messages "$max_messages" \
        --wait-time-seconds 5 \
        --query 'Messages[*].Body' \
        --output text | head -n 20
}

# Function to purge queue (with confirmation)
purge_queue() {
    local queue_name=$1
    local queue_url=$(get_queue_url "$queue_name")

    if [ -z "$queue_url" ]; then
        echo -e "${RED}❌ Queue not found: $queue_name${NC}"
        return
    fi

    echo -e "${YELLOW}⚠️  WARNING: This will delete ALL messages in $queue_name${NC}"
    read -p "Are you sure? (type 'yes' to confirm): " confirm

    if [ "$confirm" = "yes" ]; then
        aws sqs purge-queue --queue-url "$queue_url"
        echo -e "${GREEN}✅ Queue purged${NC}"
    else
        echo "Cancelled"
    fi
}

# Function to send test message
send_test_message() {
    local queue_name=$1
    local queue_url=$(get_queue_url "$queue_name")

    if [ -z "$queue_url" ]; then
        echo -e "${RED}❌ Queue not found: $queue_name${NC}"
        return
    fi

    local message="{\"test\":true,\"timestamp\":\"$(date -Iseconds)\",\"message\":\"Test message\"}"

    aws sqs send-message \
        --queue-url "$queue_url" \
        --message-body "$message"

    echo -e "${GREEN}✅ Test message sent to $queue_name${NC}"
}

# Function to check queue health
check_health() {
    local queue_name=$1
    local queue_url=$(get_queue_url "$queue_name")

    if [ -z "$queue_url" ]; then
        echo -e "${RED}❌ $queue_name: NOT FOUND${NC}"
        return 1
    fi

    local available=$(get_message_count "$queue_url")
    local oldest=$(aws sqs get-queue-attributes \
        --queue-url "$queue_url" \
        --attribute-names ApproximateAgeOfOldestMessage \
        --query 'Attributes.ApproximateAgeOfOldestMessage' \
        --output text)

    # Health checks
    local healthy=true

    if [ "$available" -gt 100 ]; then
        echo -e "${RED}⚠️  $queue_name: High queue depth ($available messages)${NC}"
        healthy=false
    fi

    if [ ! -z "$oldest" ] && [ "$oldest" -gt 1800 ]; then
        local age_mins=$((oldest / 60))
        echo -e "${YELLOW}⚠️  $queue_name: Old messages (${age_mins} minutes)${NC}"
        healthy=false
    fi

    if [ "$healthy" = true ]; then
        echo -e "${GREEN}✅ $queue_name: Healthy${NC}"
    fi

    return 0
}

# Function to check all queues health
check_all_health() {
    echo "============================================================"
    echo "Service20 Queue Health Check"
    echo "============================================================"
    echo ""

    check_health "$INVESTMENT_QUEUE"
    check_health "$FUNDING_QUEUE"
    check_health "$RESULTS_QUEUE"

    echo ""
}

# Function to show help
show_help() {
    echo "Service20 SQS Helper Functions"
    echo "==============================="
    echo ""
    echo "Available functions:"
    echo "  monitor_all                    - Show stats for all queues once"
    echo "  watch_queues [interval]        - Continuously monitor (default: 5s)"
    echo "  peek_messages <queue> [count]  - Peek at messages (default: 3)"
    echo "  send_test_message <queue>      - Send a test message"
    echo "  purge_queue <queue>            - Delete all messages (with confirmation)"
    echo "  check_all_health               - Health check for all queues"
    echo "  check_health <queue>           - Health check for specific queue"
    echo ""
    echo "Queue names:"
    echo "  - service20-investment-opportunities"
    echo "  - service20-funding-opportunities"
    echo "  - service20-research-results"
    echo ""
    echo "Examples:"
    echo "  monitor_all"
    echo "  watch_queues 10"
    echo "  peek_messages service20-investment-opportunities 5"
    echo "  send_test_message service20-investment-opportunities"
    echo ""
}

# Display help on load
echo ""
echo "✅ Service20 SQS helper functions loaded"
echo "Type 'show_help' to see available commands"
echo ""
