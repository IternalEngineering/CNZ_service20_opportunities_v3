# PowerShell helper functions for monitoring SQS queues
# Usage: . .\aws_cli_helpers.ps1

# Queue names
$INVESTMENT_QUEUE = "service20-investment-opportunities"
$FUNDING_QUEUE = "service20-funding-opportunities"
$RESULTS_QUEUE = "service20-research-results"

# Function to get queue URL
function Get-QueueUrl {
    param([string]$QueueName)

    try {
        $result = aws sqs get-queue-url --queue-name $QueueName --query 'QueueUrl' --output text 2>$null
        return $result
    }
    catch {
        return $null
    }
}

# Function to get message count
function Get-MessageCount {
    param([string]$QueueUrl)

    $result = aws sqs get-queue-attributes `
        --queue-url $QueueUrl `
        --attribute-names ApproximateNumberOfMessages `
        --query 'Attributes.ApproximateNumberOfMessages' `
        --output text

    return [int]$result
}

# Function to get in-flight count
function Get-InFlightCount {
    param([string]$QueueUrl)

    $result = aws sqs get-queue-attributes `
        --queue-url $QueueUrl `
        --attribute-names ApproximateNumberOfMessagesNotVisible `
        --query 'Attributes.ApproximateNumberOfMessagesNotVisible' `
        --output text

    return [int]$result
}

# Function to display queue stats
function Show-QueueStats {
    param([string]$QueueName)

    $queueUrl = Get-QueueUrl -QueueName $QueueName

    if (-not $queueUrl) {
        Write-Host "❌ Queue not found: $QueueName" -ForegroundColor Red
        return
    }

    $available = Get-MessageCount -QueueUrl $queueUrl
    $inflight = Get-InFlightCount -QueueUrl $queueUrl

    Write-Host "📊 $QueueName" -ForegroundColor Green
    Write-Host "   Available: $available"
    Write-Host "   In Flight: $inflight"
    Write-Host ""
}

# Function to monitor all queues
function Monitor-AllQueues {
    Clear-Host
    Write-Host "============================================================"
    Write-Host "Service20 Queue Monitor - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    Write-Host "============================================================"
    Write-Host ""

    Show-QueueStats -QueueName $INVESTMENT_QUEUE
    Show-QueueStats -QueueName $FUNDING_QUEUE
    Show-QueueStats -QueueName $RESULTS_QUEUE
}

# Function to continuously monitor
function Watch-Queues {
    param([int]$Interval = 5)

    while ($true) {
        Monitor-AllQueues
        Write-Host "Refreshing every $Interval seconds... (Ctrl+C to stop)"
        Start-Sleep -Seconds $Interval
    }
}

# Function to peek at messages
function Peek-Messages {
    param(
        [string]$QueueName,
        [int]$MaxMessages = 3
    )

    $queueUrl = Get-QueueUrl -QueueName $QueueName

    if (-not $queueUrl) {
        Write-Host "❌ Queue not found: $QueueName" -ForegroundColor Red
        return
    }

    Write-Host "🔍 Peeking at $QueueName (up to $MaxMessages messages)" -ForegroundColor Green
    Write-Host ""

    $result = aws sqs receive-message `
        --queue-url $queueUrl `
        --max-number-of-messages $MaxMessages `
        --wait-time-seconds 5 `
        --output json

    $messages = $result | ConvertFrom-Json
    if ($messages.Messages) {
        foreach ($msg in $messages.Messages) {
            Write-Host $msg.Body
            Write-Host ""
        }
    }
    else {
        Write-Host "No messages available"
    }
}

# Function to purge queue (with confirmation)
function Purge-Queue {
    param([string]$QueueName)

    $queueUrl = Get-QueueUrl -QueueName $QueueName

    if (-not $queueUrl) {
        Write-Host "❌ Queue not found: $QueueName" -ForegroundColor Red
        return
    }

    Write-Host "⚠️  WARNING: This will delete ALL messages in $QueueName" -ForegroundColor Yellow
    $confirm = Read-Host "Are you sure? (type 'yes' to confirm)"

    if ($confirm -eq "yes") {
        aws sqs purge-queue --queue-url $queueUrl
        Write-Host "✅ Queue purged" -ForegroundColor Green
    }
    else {
        Write-Host "Cancelled"
    }
}

# Function to send test message
function Send-TestMessage {
    param([string]$QueueName)

    $queueUrl = Get-QueueUrl -QueueName $QueueName

    if (-not $queueUrl) {
        Write-Host "❌ Queue not found: $QueueName" -ForegroundColor Red
        return
    }

    $timestamp = (Get-Date).ToUniversalTime().ToString("o")
    $message = @{
        test      = $true
        timestamp = $timestamp
        message   = "Test message"
    } | ConvertTo-Json -Compress

    aws sqs send-message --queue-url $queueUrl --message-body $message

    Write-Host "✅ Test message sent to $QueueName" -ForegroundColor Green
}

# Function to check queue health
function Test-QueueHealth {
    param([string]$QueueName)

    $queueUrl = Get-QueueUrl -QueueName $QueueName

    if (-not $queueUrl) {
        Write-Host "❌ $QueueName : NOT FOUND" -ForegroundColor Red
        return $false
    }

    $available = Get-MessageCount -QueueUrl $queueUrl

    $oldestResult = aws sqs get-queue-attributes `
        --queue-url $queueUrl `
        --attribute-names ApproximateAgeOfOldestMessage `
        --query 'Attributes.ApproximateAgeOfOldestMessage' `
        --output text

    $oldest = if ($oldestResult) { [int]$oldestResult } else { 0 }

    $healthy = $true

    if ($available -gt 100) {
        Write-Host "⚠️  $QueueName : High queue depth ($available messages)" -ForegroundColor Red
        $healthy = $false
    }

    if ($oldest -gt 1800) {
        $ageMins = [math]::Floor($oldest / 60)
        Write-Host "⚠️  $QueueName : Old messages ($ageMins minutes)" -ForegroundColor Yellow
        $healthy = $false
    }

    if ($healthy) {
        Write-Host "✅ $QueueName : Healthy" -ForegroundColor Green
    }

    return $healthy
}

# Function to check all queues health
function Test-AllQueuesHealth {
    Write-Host "============================================================"
    Write-Host "Service20 Queue Health Check"
    Write-Host "============================================================"
    Write-Host ""

    Test-QueueHealth -QueueName $INVESTMENT_QUEUE
    Test-QueueHealth -QueueName $FUNDING_QUEUE
    Test-QueueHealth -QueueName $RESULTS_QUEUE

    Write-Host ""
}

# Function to show help
function Show-Help {
    Write-Host "Service20 SQS Helper Functions"
    Write-Host "==============================="
    Write-Host ""
    Write-Host "Available functions:"
    Write-Host "  Monitor-AllQueues                    - Show stats for all queues once"
    Write-Host "  Watch-Queues [-Interval 5]           - Continuously monitor"
    Write-Host "  Peek-Messages -QueueName <name>      - Peek at messages"
    Write-Host "  Send-TestMessage -QueueName <name>   - Send a test message"
    Write-Host "  Purge-Queue -QueueName <name>        - Delete all messages"
    Write-Host "  Test-AllQueuesHealth                 - Health check all queues"
    Write-Host "  Test-QueueHealth -QueueName <name>   - Health check specific queue"
    Write-Host ""
    Write-Host "Queue names:"
    Write-Host "  - service20-investment-opportunities"
    Write-Host "  - service20-funding-opportunities"
    Write-Host "  - service20-research-results"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host '  Monitor-AllQueues'
    Write-Host '  Watch-Queues -Interval 10'
    Write-Host '  Peek-Messages -QueueName "service20-investment-opportunities" -MaxMessages 5'
    Write-Host '  Send-TestMessage -QueueName "service20-investment-opportunities"'
    Write-Host ""
}

# Display help on load
Write-Host ""
Write-Host "✅ Service20 SQS helper functions loaded" -ForegroundColor Green
Write-Host "Type 'Show-Help' to see available commands"
Write-Host ""
