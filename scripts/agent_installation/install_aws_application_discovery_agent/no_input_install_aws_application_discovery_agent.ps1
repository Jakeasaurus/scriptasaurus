# AWS Discovery Agent Installation Script - No Input Version
# This script downloads and installs the AWS Discovery Agent without user prompts
# Configure the variables below before running the script

#region Configuration Variables - MODIFY THESE BEFORE RUNNING
# AWS Region where you want to register the agent
$region = "us-west-2"

# AWS Access Key ID
$accessKeyId = "YOUR_ACCESS_KEY_ID_HERE"

# AWS Secret Access Key
$secretAccessKey = "YOUR_SECRET_ACCESS_KEY_HERE"

# Download path for the installer (optional to modify)
$downloadPath = ".\AWSDiscoveryAgentInstaller.exe"
#endregion

Write-Host "AWS Discovery Agent Installation Script (No Input Version)" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green

# Validate configuration
if ($region -eq "" -or $accessKeyId -eq "YOUR_ACCESS_KEY_ID_HERE" -or $secretAccessKey -eq "YOUR_SECRET_ACCESS_KEY_HERE") {
    Write-Error "Configuration Error: Please set the region, accessKeyId, and secretAccessKey variables at the top of the script before running."
    Write-Host "Edit the following variables:" -ForegroundColor Yellow
    Write-Host "  - `$region" -ForegroundColor Yellow
    Write-Host "  - `$accessKeyId" -ForegroundColor Yellow
    Write-Host "  - `$secretAccessKey" -ForegroundColor Yellow
    exit 1
}

Write-Host "Configuration:" -ForegroundColor Cyan
Write-Host "  Region: $region" -ForegroundColor Gray
Write-Host "  Access Key: $($accessKeyId.Substring(0, [Math]::Min(4, $accessKeyId.Length)))****" -ForegroundColor Gray
Write-Host "  Download Path: $downloadPath" -ForegroundColor Gray
Write-Host ""

# Download URL with dynamic region
$downloadUrl = "https://s3-$region.amazonaws.com/aws-discovery-agent.$region/windows/latest/AWSDiscoveryAgentInstaller.exe"

Write-Host "Downloading AWS Discovery Agent installer..." -ForegroundColor Yellow
try {
    # Download the installer
    Invoke-WebRequest -Uri $downloadUrl -OutFile $downloadPath -UseBasicParsing
    Write-Host "Download completed successfully!" -ForegroundColor Green
} catch {
    Write-Error "Failed to download the installer: $_"
    exit 1
}

# Verify the file was downloaded
if (-not (Test-Path $downloadPath)) {
    Write-Error "Installer file not found after download!"
    exit 1
}

Write-Host "File downloaded to: $downloadPath" -ForegroundColor Green

Write-Host "`nInstalling AWS Discovery Agent..." -ForegroundColor Yellow

# Build the installation command
$installArgs = @(
    "REGION=`"$region`"",
    "KEY_ID=`"$accessKeyId`"",
    "KEY_SECRET=`"$secretAccessKey`"",
    "/q"
)

try {
    # Run the installer
    $process = Start-Process -FilePath $downloadPath -ArgumentList $installArgs -Wait -PassThru -NoNewWindow
    
    if ($process.ExitCode -eq 0) {
        Write-Host "AWS Discovery Agent installed successfully!" -ForegroundColor Green
    } else {
        Write-Error "Installation failed with exit code: $($process.ExitCode)"
        exit $process.ExitCode
    }
} catch {
    Write-Error "Failed to run the installer: $_"
    # Clean up the installer file even on failure
    if (Test-Path $downloadPath) {
        try {
            Remove-Item $downloadPath -Force
            Write-Host "Cleaned up installer file: $downloadPath" -ForegroundColor Gray
        } catch {
            Write-Warning "Could not delete installer file: $_"
        }
    }
    exit 1
} finally {
    # Clear the secret from memory
    $secretAccessKey = $null
    [System.GC]::Collect()
    
    # Clean up the installer file after installation
    if (Test-Path $downloadPath) {
        try {
            Remove-Item $downloadPath -Force
            Write-Host "Cleaned up installer file: $downloadPath" -ForegroundColor Gray
        } catch {
            Write-Warning "Could not delete installer file: $_"
        }
    }
}

Write-Host "`nInstallation completed!" -ForegroundColor Green
