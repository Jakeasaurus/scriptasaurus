# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Repository Overview

Scriptasaurus is a collection of automation scripts and tools for IT infrastructure management, primarily focused on Windows environments with some Linux and AWS tooling. The repository contains utility scripts for system administration, migration, monitoring, and security enforcement.

## Repository Structure

The codebase is organized by script type and platform:

- **`powershell/`** - Windows PowerShell scripts for system administration
  - System discovery and inventory scripts
  - Software installation and management
  - Active Directory operations
  - Network configuration
  - TLS/SSL configuration utilities
  
- **`bash/`** - Linux shell scripts for system operations
  - Agent installation scripts
  - Migration utilities
  
- **`batch/`** - Windows batch files for file operations
  - Robocopy utilities with permission preservation
  
- **`aws_cli_commands/`** - AWS CLI command templates and examples
  - EC2 instance queries and management
  
- **`aws_iam_policies/`** - AWS IAM security policies
  - MFA enforcement policies with comprehensive documentation

## Key Components

### PowerShell Scripts
- **Discovery Scripts**: Comprehensive system information gathering (`discovery_script/`) that generates HTML reports with network, hardware, and software details
- **Software Management**: Automated installation scripts for SSM Agent, Cloudamize, Datto, and AWS MGN
- **System Utilities**: DNS configuration, service management, disk information gathering
- **Security Tools**: TLS configuration and checking utilities

### AWS Components
- **IAM Policies**: Production-ready MFA enforcement policy with detailed documentation
- **CLI Templates**: Reusable AWS CLI commands for common EC2 operations

### Cross-Platform Tools
- **Migration Utilities**: Scripts for installing migration agents on both Windows and Linux
- **File Operations**: Batch scripts for copying files while preserving permissions

## Common Development Tasks

### Working with PowerShell Scripts
```powershell
# Test PowerShell scripts locally
PowerShell -ExecutionPolicy Bypass -File script_name.ps1

# Run discovery script and generate HTML report
.\powershell\discovery_script\discovery_script.ps1
```

### Working with Bash Scripts
```bash
# Make scripts executable
chmod +x bash/script_name.sh

# Run bash scripts
./bash/script_name.sh
```

### AWS Operations
```bash
# Use AWS CLI templates
aws ec2 describe-instances \
    --filters Name=tag-key,Values=Name \
    --query 'Reservations[*].Instances[*].{Instance:InstanceId,AZ:Placement.AvailabilityZone,Name:Tags[?Key==`Name`]|[0].Value}' \
    --output table
```

### Version Control
```bash
# Standard git operations
git add .
git commit -m "Description of changes"
git push origin master
```

## Script Organization Patterns

Each script directory typically follows this structure:
```
script_name/
├── script_name.ps1|.sh|.bat    # Main script file
└── README.md                   # Documentation (where available)
```

## Important Notes

- **Security**: The MFA enforcement IAM policy in `aws_iam_policies/mfa_enforcement/` is production-ready and includes comprehensive documentation
- **PowerShell Execution Policy**: Scripts may require bypassing execution policy for testing
- **Cross-Platform Compatibility**: The repository includes utilities for Windows, Linux, and cloud environments
- **HTML Reports**: Discovery scripts generate detailed HTML reports on the user's desktop
- **Agent Installation**: Multiple scripts handle automated installation of various monitoring and migration agents

## Script Categories

### System Discovery & Inventory
- Network configuration discovery
- Hardware information gathering  
- Software inventory collection
- Service status reporting

### Software Installation & Management
- SSM Agent installation
- Migration agent deployment
- Third-party tool installation

### Security & Compliance
- TLS/SSL configuration management
- MFA policy enforcement
- Domain trust relationship fixes

### File & Data Operations
- Permission-preserving file copies
- Bulk file operations
- Data migration utilities

## Development Guidelines

- Follow existing naming conventions for new scripts
- Include README.md files for complex scripts
- Test PowerShell scripts with different execution policies
- Validate AWS policies in test environments before production use
- Consider cross-platform compatibility when adding new utilities
