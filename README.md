# Scriptasaurus

A collection of automation scripts and tools for IT infrastructure management, organized by use case for better discoverability and maintenance.

## Repository Overview

Scriptasaurus provides utility scripts for system administration, migration, monitoring, and security enforcement across Windows, Linux, and AWS environments.

## Repository Structure

The repository is organized by **use case** rather than script type, making it easier to find tools for specific tasks:

```
scriptasaurus/
├── scripts/                        # All automation scripts organized by purpose
│   ├── system_discovery/           # System inventory & discovery tools
│   ├── agent_installation/         # Software agent installation & management
│   ├── network_management/         # DNS, networking, and connectivity tools
│   ├── active_directory/           # Active Directory operations
│   ├── security_compliance/        # Security configurations and compliance
│   ├── file_operations/            # File copying and permissions management
│   ├── system_maintenance/         # System services and maintenance
│   └── monitoring_tools/           # System monitoring and reporting
├── aws_cli_commands/               # AWS CLI command templates and examples
└── aws_iam_policies/               # AWS IAM security policies
```

## Use Case Categories

### 🔍 System Discovery
**Path:** `scripts/system_discovery/`

Scripts for gathering comprehensive system information:
- **discovery_script** - Generates detailed HTML reports with network, hardware, and software details
- **domain_discovery** - Active Directory domain discovery tools
- **get_logical_disks** - Disk information and volume details
- **get_software_list** - Installed software inventory

### 📦 Agent Installation
**Path:** `scripts/agent_installation/`

Automated installation and management of monitoring/migration agents:
- **install_ssm_agent** - AWS Systems Manager Agent installation
- **install_aws_mgn** - AWS Migration Hub agent installation
- **install_aws_application_discovery_agent** - AWS Application Discovery Service agent (Interactive & Non-interactive versions)
- **cloudamize_install_windows** - Cloudamize agent for Windows
- **cloudamize_install_linux** - Cloudamize agent for Linux (includes AWS MGN sub-component)
- **install_datto_windows** - Datto backup agent installation
- **uninstall_cloudendure_agent** - CloudEndure agent removal

### 🌐 Network Management
**Path:** `scripts/network_management/`

Network configuration and connectivity tools:
- **set_dns_static** - Configure static DNS settings
- **update_dns** - Dynamic DNS configuration updates
- **ping_list_of_computers** - Bulk ping testing for multiple hosts

### 👥 Active Directory
**Path:** `scripts/active_directory/`

Active Directory administration scripts:
- **update_ad_home_drives** - Bulk update user home drive mappings
- **ad_backup** - Active Directory backup utilities

### 🔒 Security & Compliance
**Path:** `scripts/security_compliance/`

Security configuration and compliance tools:
- **tls** - TLS/SSL configuration and verification scripts
  - Check TLS 1.1/1.2 support
  - Enable .NET TLS 1.2 support
  - Comprehensive TLS enablement
- **trust_relationship_fix** - Domain trust relationship repair

### 📁 File Operations
**Path:** `scripts/file_operations/`

File management and data migration utilities:
- **robocopy_files_with_permissions** - Copy files while preserving NTFS permissions
- **robocopy_missing_files_with_permissions** - Incremental file copying with permission preservation

### 🔧 System Maintenance
**Path:** `scripts/system_maintenance/`

System service and maintenance scripts:
- **get_services** - Service enumeration and management

### 📊 Monitoring Tools
**Path:** `scripts/monitoring_tools/`

System monitoring and reporting utilities:
- **get_services_list_for_list_of_computers** - Remote service monitoring across multiple systems

### ☁️ AWS Components

#### CLI Commands
**Path:** `aws_cli_commands/`
- Pre-built AWS CLI command templates for common EC2 operations
- Instance querying and management commands

#### IAM Policies  
**Path:** `aws_iam_policies/`
- **mfa_enforcement** - Production-ready MFA enforcement policy with comprehensive documentation

## Cross-Platform Compatibility

Scripts support multiple platforms:
- **Windows**: PowerShell scripts (.ps1)
- **Linux**: Bash scripts (.sh) 
- **Windows Batch**: Batch files (.bat)
- **AWS**: CLI commands and IAM policies

## Usage Examples

### Running PowerShell Scripts
```powershell
# Test PowerShell scripts locally
PowerShell -ExecutionPolicy Bypass -File script_name.ps1

# Run discovery script and generate HTML report
.\scripts\system_discovery\discovery_script\discovery_script.ps1
```

### Running Bash Scripts
```bash
# Make scripts executable
chmod +x scripts/agent_installation/cloudamize_install_linux/cloudamize_install.sh

# Run bash scripts
./scripts/agent_installation/cloudamize_install_linux/cloudamize_install.sh
```

### AWS Operations
```bash
# Use AWS CLI templates
aws ec2 describe-instances \
    --filters Name=tag-key,Values=Name \
    --query 'Reservations[*].Instances[*].{Instance:InstanceId,AZ:Placement.AvailabilityZone,Name:Tags[?Key==`Name`]|[0].Value}' \
    --output table
```

## Development Guidelines

- **Naming Conventions**: Follow existing patterns for new scripts
- **Documentation**: Include README.md files for complex script collections
- **Testing**: Test PowerShell scripts with different execution policies
- **AWS Policies**: Validate IAM policies in test environments before production use
- **Cross-Platform**: Consider compatibility when adding new utilities
- **Use-Case Organization**: Place new scripts in the appropriate use-case folder

## Security Considerations

- Scripts that handle credentials use secure input methods where possible
- AWS policies follow security best practices
- PowerShell scripts may require execution policy adjustments for testing
- Always validate scripts in test environments before production deployment

## Contributing

When adding new scripts:
1. Choose the appropriate use-case folder under `scripts/`
2. Create a dedicated subfolder for complex scripts
3. Include documentation (README.md) for multi-file scripts
4. Follow existing naming conventions
5. Test across target platforms where applicable

## Support

For script-specific issues, check individual README files within each script folder. For AWS-related components, consult the AWS documentation for the respective services.
