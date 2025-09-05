# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Repository Overview

Scriptasaurus is a collection of automation scripts and tools for IT infrastructure management, primarily focused on Windows environments with some Linux and AWS tooling. The repository contains utility scripts for system administration, migration, monitoring, and security enforcement.

## Repository Structure

The codebase is organized by **use case** rather than script type, making it easier to find tools for specific IT tasks:

- **`scripts/`** - All automation scripts organized by purpose
  - `system_discovery/` - System inventory and discovery tools
  - `agent_installation/` - Software agent installation and management
  - `network_management/` - DNS, networking, and connectivity tools
  - `active_directory/` - Active Directory operations
  - `security_compliance/` - Security configurations and compliance
  - `file_operations/` - File copying and permissions management
  - `system_maintenance/` - System services and maintenance
  - `monitoring_tools/` - System monitoring and reporting
  
- **`aws_cli_commands/`** - AWS CLI command templates and examples
  - EC2 instance queries and management
  
- **`aws_iam_policies/`** - AWS IAM security policies
  - MFA enforcement policies with comprehensive documentation

## Key Components

### System Discovery
- **Discovery Scripts**: Comprehensive system information gathering (`scripts/system_discovery/discovery_script/`) that generates HTML reports with network, hardware, and software details
- **Domain Discovery**: Active Directory domain discovery tools
- **System Inventory**: Disk information, software lists, and hardware details

### Agent Installation
- **AWS Agents**: SSM Agent, MGN Agent, and Application Discovery Agent installation
- **Third-Party Agents**: Cloudamize (Windows/Linux), Datto, CloudEndure management
- **Cross-Platform**: Automated installation scripts for both Windows and Linux

### Network & Infrastructure
- **DNS Management**: Static and dynamic DNS configuration tools
- **Connectivity Testing**: Bulk ping testing and network diagnostics
- **File Operations**: Permission-preserving file copying utilities

### Security & Compliance
- **TLS Configuration**: TLS 1.2 enablement and verification scripts
- **Domain Management**: Trust relationship fixes and AD operations
- **AWS Security**: Production-ready MFA enforcement IAM policies

### AWS Components
- **IAM Policies**: Production-ready MFA enforcement policy with detailed documentation
- **CLI Templates**: Reusable AWS CLI commands for common EC2 operations

## Common Development Tasks

### Working with PowerShell Scripts
```powershell
# Test PowerShell scripts locally
PowerShell -ExecutionPolicy Bypass -File script_name.ps1

# Run discovery script and generate HTML report
.\scripts\system_discovery\discovery_script\discovery_script.ps1
```

### Working with Bash Scripts
```bash
# Make scripts executable
chmod +x scripts/agent_installation/script_name.sh

# Run bash scripts
./scripts/agent_installation/script_name.sh
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
