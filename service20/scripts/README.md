# Monitoring Scripts for Service20 SQS Queues

This directory contains scripts for monitoring and managing SQS message queues.

## Available Scripts

### 1. Python Monitor (`monitor_queues.py`)

**Cross-platform Python script with multiple monitoring modes.**

#### Features:
- Monitor once or continuously
- Health check mode
- JSON output for integration
- Works with boto3 or AWS CLI
- Color-coded status indicators

#### Usage:

```bash
# Monitor once
python monitor_queues.py --mode once

# Monitor continuously (5 second refresh)
python monitor_queues.py --mode continuous --interval 5

# Health check (exits with code 0 if healthy, 1 if issues)
python monitor_queues.py --mode health

# JSON output (for scripting)
python monitor_queues.py --mode json

# Use AWS CLI instead of boto3
python monitor_queues.py --mode once --use-cli
```

#### Output Example:

```
============================================================
Queue Monitor - 2025-10-16 14:30:45
============================================================

🟢 service20-investment-opportunities
  Available: 12
  In Flight: 2
  Delayed: 0
  Oldest Message: 5 minutes ago

🟡 service20-funding-opportunities
  Available: 67
  In Flight: 5
  Delayed: 0
  Oldest Message: 15 minutes ago

🟢 service20-research-results
  Available: 8
  In Flight: 0
  Delayed: 0
```

### 2. Windows Batch Script (`monitor_queues.bat`)

**Interactive menu for Windows users.**

#### Usage:

```cmd
monitor_queues.bat
```

Select from menu:
1. Monitor once
2. Monitor continuously (5s)
3. Monitor continuously (30s)
4. Health check only
5. JSON output
6. Exit

### 3. Bash Shell Script (`monitor_queues.sh`)

**Interactive menu for Linux/Mac users.**

#### Usage:

```bash
chmod +x monitor_queues.sh
./monitor_queues.sh
```

Same menu options as Windows batch script.

### 4. Bash Helper Functions (`aws_cli_helpers.sh`)

**Collection of reusable shell functions for queue management.**

#### Setup:

```bash
# Load functions
source aws_cli_helpers.sh
```

#### Available Functions:

```bash
# View all functions
show_help

# Monitor all queues once
monitor_all

# Continuously monitor (5 second refresh)
watch_queues

# Continuously monitor (custom interval)
watch_queues 10

# Peek at messages (without deleting)
peek_messages service20-investment-opportunities 5

# Send test message
send_test_message service20-investment-opportunities

# Check health of all queues
check_all_health

# Check health of specific queue
check_health service20-investment-opportunities

# Purge queue (with confirmation)
purge_queue service20-investment-opportunities
```

### 5. PowerShell Helper Functions (`aws_cli_helpers.ps1`)

**Collection of reusable PowerShell functions for queue management.**

#### Setup:

```powershell
# Load functions
. .\aws_cli_helpers.ps1
```

#### Available Functions:

```powershell
# View all functions
Show-Help

# Monitor all queues once
Monitor-AllQueues

# Continuously monitor
Watch-Queues -Interval 5

# Peek at messages
Peek-Messages -QueueName "service20-investment-opportunities" -MaxMessages 5

# Send test message
Send-TestMessage -QueueName "service20-investment-opportunities"

# Check health
Test-AllQueuesHealth
Test-QueueHealth -QueueName "service20-investment-opportunities"

# Purge queue (with confirmation)
Purge-Queue -QueueName "service20-investment-opportunities"
```

## Quick Start

### Windows (PowerShell)

```powershell
# Option 1: Use Python script
python scripts\monitor_queues.py --mode continuous

# Option 2: Use interactive menu
scripts\monitor_queues.bat

# Option 3: Load helper functions
. .\scripts\aws_cli_helpers.ps1
Monitor-AllQueues
```

### Linux/Mac

```bash
# Option 1: Use Python script
python3 scripts/monitor_queues.py --mode continuous

# Option 2: Use interactive menu
chmod +x scripts/monitor_queues.sh
./scripts/monitor_queues.sh

# Option 3: Load helper functions
source scripts/aws_cli_helpers.sh
monitor_all
```

## Common Tasks

### Check Queue Status

```bash
# Python
python monitor_queues.py --mode once

# Bash
source aws_cli_helpers.sh
monitor_all

# PowerShell
. .\aws_cli_helpers.ps1
Monitor-AllQueues
```

### Continuous Monitoring

```bash
# Python (5 second refresh)
python monitor_queues.py --mode continuous --interval 5

# Bash
source aws_cli_helpers.sh
watch_queues 5

# PowerShell
. .\aws_cli_helpers.ps1
Watch-Queues -Interval 5
```

### Health Check (for CI/CD)

```bash
# Exit code 0 if healthy, 1 if issues
python monitor_queues.py --mode health

# Use in scripts
if python monitor_queues.py --mode health; then
    echo "All queues healthy"
else
    echo "Queue issues detected!"
fi
```

### Get JSON Output (for automation)

```bash
# Get JSON data
python monitor_queues.py --mode json > queue_status.json

# Parse with jq
python monitor_queues.py --mode json | jq '.queues[] | select(.available > 50)'
```

### Peek at Messages

```bash
# Bash
peek_messages service20-investment-opportunities 5

# PowerShell
Peek-Messages -QueueName "service20-investment-opportunities" -MaxMessages 5
```

## Integration Examples

### Cron Job (Linux/Mac)

Monitor every 5 minutes and log to file:

```bash
# Add to crontab
*/5 * * * * /usr/bin/python3 /path/to/monitor_queues.py --mode json >> /var/log/service20_queues.log 2>&1
```

Health check with email alert:

```bash
#!/bin/bash
if ! python3 monitor_queues.py --mode health; then
    echo "Service20 queue health issues detected" | mail -s "Queue Alert" admin@example.com
fi
```

### Task Scheduler (Windows)

Create scheduled task:

```powershell
$action = New-ScheduledTaskAction -Execute "python.exe" -Argument "C:\path\to\monitor_queues.py --mode health"
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5)
Register-ScheduledTask -TaskName "Service20QueueMonitor" -Action $action -Trigger $trigger
```

### CI/CD Pipeline

```yaml
# GitHub Actions example
- name: Check Queue Health
  run: |
    python scripts/monitor_queues.py --mode health
  continue-on-error: true

# GitLab CI example
queue_health:
  script:
    - python scripts/monitor_queues.py --mode json
  only:
    - schedules
```

### Monitoring Dashboard

Create simple web dashboard:

```python
from flask import Flask, jsonify
import subprocess
import json

app = Flask(__name__)

@app.route('/queues')
def get_queue_status():
    result = subprocess.run(
        ['python', 'monitor_queues.py', '--mode', 'json'],
        capture_output=True,
        text=True
    )
    return jsonify(json.loads(result.stdout))

if __name__ == '__main__':
    app.run(port=5000)
```

## Troubleshooting

### AWS CLI Not Found

**Windows:**
```powershell
# Check if installed
aws --version

# Add to PATH if needed
$env:Path += ";C:\Program Files\Amazon\AWSCLIV2\"
```

**Linux/Mac:**
```bash
# Check if installed
aws --version

# Install if missing
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

### Boto3 Not Installed

```bash
# Install boto3
pip install boto3

# Or use --use-cli flag
python monitor_queues.py --mode once --use-cli
```

### Access Denied

```bash
# Check credentials
aws sts get-caller-identity

# Configure if needed
aws configure
```

### Queue Not Found

```bash
# List all queues
aws sqs list-queues

# Check region
aws configure get region

# Specify region explicitly
aws sqs list-queues --region eu-west-2
```

## Best Practices

1. **Regular Monitoring**: Set up automated monitoring every 5-15 minutes
2. **Health Checks**: Run health checks before deployments
3. **Alert on Issues**: Set up alerts for high queue depth or old messages
4. **Log Historical Data**: Save JSON output for trend analysis
5. **Test in Development**: Use test messages to verify setup

## Dependencies

### Python Script
- Python 3.7+
- boto3 (optional, falls back to AWS CLI)
- AWS CLI (if not using boto3)

### Shell Scripts
- AWS CLI
- bash (Linux/Mac) or PowerShell (Windows)
- jq (optional, for JSON parsing)

## Next Steps

1. Set up automated monitoring with cron/Task Scheduler
2. Create custom alerts based on your thresholds
3. Integrate with your existing monitoring systems
4. Build dashboards using the JSON output
5. Add CloudWatch alarms for critical metrics
