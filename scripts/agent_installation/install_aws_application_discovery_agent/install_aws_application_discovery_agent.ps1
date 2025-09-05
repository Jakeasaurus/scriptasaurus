# AWS Discovery Agent Installation Script
# This script downloads and installs the AWS Discovery Agent with secure credential input

param(
    [string]$DownloadPath = ".\AWSDiscoveryAgentInstaller.exe"
)

Write-Host "AWS Discovery Agent Installation Script" -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Green

# Prompt for AWS region
Write-Host "`nPlease select an AWS region:" -ForegroundColor Cyan
$region = Read-Host "AWS Region (e.g., us-west-2, us-east-1, eu-west-1)"
if ([string]::IsNullOrWhiteSpace($region)) {
    Write-Error "AWS Region is required!"
    exit 1
}

# Download URL with dynamic region
$downloadUrl = "https://s3-$region.amazonaws.com/aws-discovery-agent.$region/windows/latest/AWSDiscoveryAgentInstaller.exe"

Write-Host "Downloading AWS Discovery Agent installer..." -ForegroundColor Yellow
try {
    # Download the installer
    Invoke-WebRequest -Uri $downloadUrl -OutFile $DownloadPath -UseBasicParsing
    Write-Host "Download completed successfully!" -ForegroundColor Green
} catch {
    Write-Error "Failed to download the installer: $_"
    exit 1
}

# Verify the file was downloaded
if (-not (Test-Path $DownloadPath)) {
    Write-Error "Installer file not found after download!"
    exit 1
}

Write-Host "File downloaded to: $DownloadPath" -ForegroundColor Green

# Prompt for AWS credentials securely
Write-Host "`nPlease enter your AWS credentials:" -ForegroundColor Cyan

# Get Access Key ID
$accessKeyId = Read-Host "AWS Access Key ID"
if ([string]::IsNullOrWhiteSpace($accessKeyId)) {
    Write-Error "Access Key ID is required!"
    exit 1
}

# Get Secret Access Key (secure input)
$secretAccessKey = Read-Host "AWS Secret Access Key" -AsSecureString
$secretAccessKeyPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($secretAccessKey))

if ([string]::IsNullOrWhiteSpace($secretAccessKeyPlain)) {
    Write-Error "Secret Access Key is required!"
    exit 1
}

Write-Host "`nInstalling AWS Discovery Agent..." -ForegroundColor Yellow

# Build the installation command
$installArgs = @(
    "REGION=`"$region`"",
    "KEY_ID=`"$accessKeyId`"",
    "KEY_SECRET=`"$secretAccessKeyPlain`"",
    "/q"
)

try {
    # Run the installer
    $process = Start-Process -FilePath $DownloadPath -ArgumentList $installArgs -Wait -PassThru -NoNewWindow
    
    if ($process.ExitCode -eq 0) {
        Write-Host "AWS Discovery Agent installed successfully!" -ForegroundColor Green
    } else {
        Write-Error "Installation failed with exit code: $($process.ExitCode)"
        exit $process.ExitCode
    }
} catch {
    Write-Error "Failed to run the installer: $_"
    # Clean up the installer file even on failure
    if (Test-Path $DownloadPath) {
        try {
            Remove-Item $DownloadPath -Force
            Write-Host "Cleaned up installer file: $DownloadPath" -ForegroundColor Gray
        } catch {
            Write-Warning "Could not delete installer file: $_"
        }
    }
    exit 1
} finally {
    # Clear the secret from memory
    $secretAccessKeyPlain = $null
    [System.GC]::Collect()
    
    # Clean up the installer file after installation
    if (Test-Path $DownloadPath) {
        try {
            Remove-Item $DownloadPath -Force
            Write-Host "Cleaned up installer file: $DownloadPath" -ForegroundColor Gray
        } catch {
            Write-Warning "Could not delete installer file: $_"
        }
    }
}

Write-Host "`nInstallation completed!" -ForegroundColor Green
