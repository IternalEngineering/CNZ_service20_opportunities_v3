# PowerShell script to install AWS CLI on Windows
# Run as Administrator

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "AWS CLI Installation Script for Windows" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "⚠️  Warning: Not running as Administrator" -ForegroundColor Yellow
    Write-Host "Installation may require administrator privileges" -ForegroundColor Yellow
    Write-Host ""
}

# Check if AWS CLI is already installed
Write-Host "Checking for existing AWS CLI installation..." -ForegroundColor Cyan
$existingAws = Get-Command aws -ErrorAction SilentlyContinue

if ($existingAws) {
    Write-Host "✅ AWS CLI is already installed" -ForegroundColor Green
    Write-Host "Version: " -NoNewline
    aws --version
    Write-Host ""

    $continue = Read-Host "Do you want to reinstall/update? (y/n)"
    if ($continue -ne "y") {
        Write-Host "Installation cancelled" -ForegroundColor Yellow
        exit
    }
}

# Download AWS CLI installer
Write-Host "Downloading AWS CLI installer..." -ForegroundColor Cyan
$installerPath = "$env:TEMP\AWSCLIV2.msi"

try {
    Invoke-WebRequest -Uri "https://awscli.amazonaws.com/AWSCLIV2.msi" -OutFile $installerPath
    Write-Host "✅ Download completed" -ForegroundColor Green
}
catch {
    Write-Host "❌ Download failed: $_" -ForegroundColor Red
    exit 1
}

# Install AWS CLI
Write-Host ""
Write-Host "Installing AWS CLI..." -ForegroundColor Cyan
Write-Host "This may take a few minutes..." -ForegroundColor Yellow
Write-Host ""

try {
    Start-Process msiexec.exe -Wait -ArgumentList "/i `"$installerPath`" /quiet /norestart"
    Write-Host "✅ Installation completed" -ForegroundColor Green
}
catch {
    Write-Host "❌ Installation failed: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Try manual installation:" -ForegroundColor Yellow
    Write-Host "1. Open the downloaded file: $installerPath" -ForegroundColor Yellow
    Write-Host "2. Follow the installation wizard" -ForegroundColor Yellow
    exit 1
}

# Clean up
Remove-Item $installerPath -ErrorAction SilentlyContinue

# Refresh environment variables
Write-Host ""
Write-Host "Refreshing environment variables..." -ForegroundColor Cyan
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

# Verify installation
Write-Host ""
Write-Host "Verifying installation..." -ForegroundColor Cyan

Start-Sleep -Seconds 2

# Try to find AWS CLI
$awsPath = Get-Command aws -ErrorAction SilentlyContinue

if (-not $awsPath) {
    Write-Host "⚠️  AWS CLI not found in PATH" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Possible solutions:" -ForegroundColor Yellow
    Write-Host "1. Close and reopen PowerShell" -ForegroundColor Yellow
    Write-Host "2. Restart your computer" -ForegroundColor Yellow
    Write-Host "3. Manually add to PATH: C:\Program Files\Amazon\AWSCLIV2\" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Default installation location: C:\Program Files\Amazon\AWSCLIV2\" -ForegroundColor Cyan
}
else {
    Write-Host "✅ AWS CLI installed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Version information:" -ForegroundColor Cyan
    aws --version
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Green
    Write-Host "1. Configure AWS credentials: aws configure" -ForegroundColor White
    Write-Host "2. Test connection: aws sts get-caller-identity" -ForegroundColor White
    Write-Host "3. List queues: aws sqs list-queues" -ForegroundColor White
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Installation complete!" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
