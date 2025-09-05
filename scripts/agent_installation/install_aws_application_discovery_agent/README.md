# AWS Application Discovery Agent Installation Script

This PowerShell script automates the download and installation of the AWS Application Discovery Agent on Windows systems. The AWS Application Discovery Service helps you plan application migration projects by gathering information about your on-premises data centers.

## Features

- **Interactive Region Selection**: Prompts user to select their preferred AWS region
- **Secure Credential Input**: Uses PowerShell's secure string functionality for AWS credentials
- **Automatic Download**: Downloads the latest installer from AWS S3
- **Silent Installation**: Performs unattended installation with user-provided credentials
- **Automatic Cleanup**: Removes downloaded installer file after installation (success or failure)
- **Error Handling**: Comprehensive error checking throughout the process

## Prerequisites

- Windows operating system
- PowerShell 3.0 or higher
- Internet connectivity to download the installer
- Administrative privileges (recommended)
- Valid AWS credentials (Access Key ID and Secret Access Key)

## Usage

### Basic Usage
```powershell
.\install_aws_application_discovery_agent.ps1
```

### Custom Download Path
```powershell
.\install_aws_application_discovery_agent.ps1 -DownloadPath "C:\temp\AWSDiscoveryInstaller.exe"
```

## Interactive Prompts

When you run the script, it will prompt you for:

1. **AWS Region**: Enter your preferred AWS region (e.g., `us-west-2`, `us-east-1`, `eu-west-1`)
2. **AWS Access Key ID**: Your AWS access key ID
3. **AWS Secret Access Key**: Your secret access key (input is masked for security)

## Supported AWS Regions

The script supports all AWS regions where the Application Discovery Service is available. Common regions include:

- `us-east-1` (US East - N. Virginia)
- `us-west-2` (US West - Oregon)
- `eu-west-1` (Europe - Ireland)
- `ap-southeast-1` (Asia Pacific - Singapore)
- And many more...

## What the Script Does

1. **Region Input**: Prompts for and validates AWS region selection
2. **Download**: Downloads the AWS Discovery Agent installer from the appropriate regional S3 bucket
3. **Verification**: Confirms the installer was downloaded successfully
4. **Credential Collection**: Securely prompts for AWS credentials
5. **Installation**: Runs the installer silently with the provided credentials
6. **Cleanup**: Automatically removes the downloaded installer file
7. **Memory Cleanup**: Clears sensitive credential data from memory

## Installation Parameters

The script passes the following parameters to the AWS installer:

- `REGION`: The AWS region you specified
- `KEY_ID`: Your AWS Access Key ID
- `KEY_SECRET`: Your AWS Secret Access Key
- `/q`: Silent installation flag

## Error Handling

The script includes comprehensive error handling for:

- Failed downloads
- Missing installer files
- Invalid or missing credentials
- Installation failures
- File cleanup issues

## Security Considerations

- **Secure Input**: Secret access keys are captured using PowerShell's secure string functionality
- **Memory Cleanup**: Sensitive data is cleared from memory after use
- **Temporary Storage**: Installer file is automatically deleted after use
- **No Logging**: Credentials are not logged or stored permanently

## Troubleshooting

### Common Issues

**Download Fails**
- Check internet connectivity
- Verify the region exists and supports Application Discovery Service
- Ensure Windows can access AWS S3 endpoints

**Installation Fails**
- Run PowerShell as Administrator
- Verify AWS credentials are valid and have necessary permissions
- Check that the region supports Application Discovery Service

**Permission Errors**
- Ensure you have administrative privileges
- Check that the download path is writable
- Verify antivirus software isn't blocking the installer

### Required IAM Permissions

Your AWS credentials need the following permissions:
- `application-discovery:RegisterAgent`
- `application-discovery:StartDataCollectionByAgentIds`
- Additional permissions may be required depending on your use case

## AWS Application Discovery Service

The AWS Application Discovery Service helps enterprise customers plan migration projects by gathering information about their on-premises data centers. The Discovery Agent collects:

- System configuration data
- System performance data
- Running processes
- Network connections between systems

## Files Created

After successful installation, the agent creates various files and services on the system. Consult AWS documentation for details on agent file locations and configuration.

## Support

For issues specific to the AWS Application Discovery Agent itself, consult the [AWS Application Discovery Service documentation](https://docs.aws.amazon.com/application-discovery/).

For script-related issues, check the error messages and ensure all prerequisites are met.
