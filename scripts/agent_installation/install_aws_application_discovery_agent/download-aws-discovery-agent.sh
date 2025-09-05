#!/bin/bash

# AWS Discovery Agent Download Script
# This script downloads the AWS Discovery Agent installer
# Note: The installer is for Windows and cannot be executed on Unix systems

set -e

REGION="${1:-us-west-2}"
DOWNLOAD_PATH="${2:-./AWSDiscoveryAgentInstaller.exe}"
DOWNLOAD_URL="https://s3-us-west-2.amazonaws.com/aws-discovery-agent.us-west-2/windows/latest/AWSDiscoveryAgentInstaller.exe"

echo "🚀 AWS Discovery Agent Download Script"
echo "======================================"

echo "📥 Downloading AWS Discovery Agent installer..."

# Check if curl or wget is available
if command -v curl >/dev/null 2>&1; then
    curl -L -o "$DOWNLOAD_PATH" "$DOWNLOAD_URL"
elif command -v wget >/dev/null 2>&1; then
    wget -O "$DOWNLOAD_PATH" "$DOWNLOAD_URL"
else
    echo "❌ Error: Neither curl nor wget is available. Please install one of them."
    exit 1
fi

# Verify download
if [ -f "$DOWNLOAD_PATH" ]; then
    echo "✅ Download completed successfully!"
    echo "📁 File saved to: $DOWNLOAD_PATH"
    
    # Get file size
    if command -v ls >/dev/null 2>&1; then
        FILE_SIZE=$(ls -lh "$DOWNLOAD_PATH" | awk '{print $5}')
        echo "📊 File size: $FILE_SIZE"
    fi
    
    echo ""
    echo "⚠️  Note: This is a Windows executable that cannot be run on macOS/Linux."
    echo "🖥️  To install on Windows, transfer this file and run the PowerShell script:"
    echo "   install-aws-discovery-agent.ps1"
    echo ""
    echo "📋 Or run manually on Windows with:"
    echo "   .\\AWSDiscoveryAgentInstaller.exe REGION=\"$REGION\" KEY_ID=\"<YOUR_ACCESS_KEY>\" KEY_SECRET=\"<YOUR_SECRET_KEY>\" /q"
else
    echo "❌ Download failed - file not found!"
    exit 1
fi
