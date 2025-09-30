# Terraform Coverage Audit

A Python tool to analyze AWS Organizations and identify which resources are managed by Terraform versus those that are not.

## Overview

This tool scans all accounts in your AWS Organization to determine **Terraform management coverage** across your infrastructure. It identifies resources tagged with `terraform=true` (case-insensitive) and generates comprehensive reports showing:

- **Per-account coverage statistics** - How much of each account is under Terraform management
- **Organization-wide coverage** - Overall Terraform adoption across all accounts
- **Detailed resource lists** - Managed vs. unmanaged resources with full metadata
- **Interactive reports** - Both console output and HTML reports with sortable tables

### Key Features

- ✅ **Cross-account scanning** - Automatically discovers and scans all AWS Organization accounts
- ✅ **Case-insensitive tag matching** - Detects `terraform=true`, `Terraform=True`, etc.
- ✅ **Multi-region support** - Scans all enabled regions or specific regions
- ✅ **Concurrent execution** - Fast parallel scanning of multiple accounts
- ✅ **Flexible filtering** - Filter by accounts, regions, or resource types
- ✅ **Multiple output formats** - Console tables or HTML reports
- ✅ **Robust error handling** - Continues scanning even if some accounts fail

## Prerequisites

### Python Dependencies

```bash
pip3 install boto3 botocore rich jinja2
```

### Required AWS Permissions

#### In the Management Account (where you run the script):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "organizations:ListAccounts",
        "organizations:DescribeOrganization"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": "sts:AssumeRole",
      "Resource": "arn:aws:iam::*:role/OrganizationAccountAccessRole"
    },
    {
      "Effect": "Allow",
      "Action": "ec2:DescribeRegions",
      "Resource": "*"
    }
  ]
}
```

#### In Member Accounts (the role being assumed):

The default role name is `OrganizationAccountAccessRole`, but this can be customized with the `--role-name` flag.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "tag:GetResources",
        "resourcegroupstaggingapi:GetResources"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": "ec2:DescribeRegions",
      "Resource": "*"
    }
  ]
}
```

**Trust Relationship** for the role in member accounts:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::MANAGEMENT_ACCOUNT_ID:root"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

## Usage

### Basic Usage

```bash
# Scan all accounts with console output
python3 terraform_coverage_audit.py

# With specific AWS profile
python3 terraform_coverage_audit.py --profile production
```

### Output Options

```bash
# Generate HTML report
python3 terraform_coverage_audit.py --output html

# Both console and HTML
python3 terraform_coverage_audit.py --output both

# Custom output directory for HTML
python3 terraform_coverage_audit.py --output html --output-dir ~/reports
```

### Filtering Options

```bash
# Scan specific accounts only
python3 terraform_coverage_audit.py --accounts 111111111111,222222222222

# Scan specific regions
python3 terraform_coverage_audit.py --regions us-east-1,us-west-2,eu-west-1

# Filter by resource types
python3 terraform_coverage_audit.py --resource-types ec2:instance,s3:bucket,rds:db

# Combine filters
python3 terraform_coverage_audit.py \
  --accounts 111111111111 \
  --regions us-east-1,us-west-2 \
  --resource-types ec2:instance \
  --output both
```

### Advanced Options

```bash
# Use custom IAM role name
python3 terraform_coverage_audit.py --role-name CustomOrgAccessRole

# Enable verbose logging
python3 terraform_coverage_audit.py --verbose

# Full example with all options
python3 terraform_coverage_audit.py \
  --profile production \
  --accounts 111111111111,222222222222,333333333333 \
  --regions us-east-1,us-west-2 \
  --resource-types ec2:instance,s3:bucket \
  --role-name OrganizationAccountAccessRole \
  --output both \
  --output-dir ~/Desktop \
  --verbose
```

### Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--profile` | AWS profile name | `default` |
| `--output` | Output format: `console`, `html`, or `both` | `console` |
| `--output-dir` | Directory for HTML reports | `~/Desktop` |
| `--accounts` | Comma-separated account IDs to scan | All accounts |
| `--regions` | Comma-separated region names | All enabled regions |
| `--role-name` | IAM role name to assume in member accounts | `OrganizationAccountAccessRole` |
| `--resource-types` | Comma-separated resource type filters | All resource types |
| `--verbose` | Enable debug logging | `false` |

## Tag Detection

The tool identifies Terraform-managed resources by looking for tags with:

- **Key**: `terraform` (case-insensitive)
- **Value**: `true` (case-insensitive)

### Supported Tag Variations

All of these variations are detected:

- `terraform=true`
- `Terraform=true`
- `terraform=True`
- `Terraform=True`
- `TERRAFORM=TRUE`
- Any other case combination

### Tag Examples

**Detected as managed:**
```hcl
tags = {
  terraform = "true"
  Name      = "my-resource"
}
```

**Not detected (wrong value):**
```hcl
tags = {
  terraform = "yes"    # ❌ Value must be "true"
  terraform = "1"      # ❌ Value must be "true"
}
```

## Output Examples

### Console Output

```
Terraform Coverage by Account
┌─────────────┬──────────────┬─────────┬───────────┬───────┬────────────┐
│ Account     │ Account ID   │ Managed │ Unmanaged │ Total │ Coverage % │
├─────────────┼──────────────┼─────────┼───────────┼───────┼────────────┤
│ Production  │ 123456789012 │ 450     │ 50        │ 500   │ 90.0%      │
│ Development │ 234567890123 │ 120     │ 80        │ 200   │ 60.0%      │
│ Sandbox     │ 345678901234 │ 30      │ 70        │ 100   │ 30.0%      │
└─────────────┴──────────────┴─────────┴───────────┴───────┴────────────┘

Organization Coverage: 75.0% (Managed: 600, Unmanaged: 200, Total: 800)
```

### HTML Report

The HTML report includes:

- **Summary section** with organization-wide statistics
- **Account coverage table** with visual progress bars
- **Sortable tables** for managed and unmanaged resources (click column headers)
- **Error section** listing accounts that couldn't be scanned
- **Responsive design** that works on desktop and mobile

HTML files are named with timestamps: `terraform_coverage_report_2025-09-30_14-32-01.html`

## Resource Information

For each resource, the following information is collected:

| Field | Description | Example |
|-------|-------------|---------|
| **ARN** | Full Amazon Resource Name | `arn:aws:ec2:us-east-1:123456789012:instance/i-1234567890abcdef0` |
| **Resource ID** | Resource identifier | `i-1234567890abcdef0` |
| **Name** | Value of the "Name" tag | `web-server-01` |
| **Type** | Resource type | `ec2:instance` |
| **Region** | AWS region | `us-east-1` |
| **Account ID** | AWS account ID | `123456789012` |
| **Account Name** | AWS account name | `Production` |

## Performance

The tool is optimized for large AWS Organizations:

- **Concurrent account scanning** - Scans multiple accounts simultaneously
- **Pagination handling** - Efficiently handles large resource sets
- **Adaptive retry logic** - Automatically retries throttled requests
- **Progress tracking** - Real-time progress bar during execution

Typical performance:
- **Small org** (5 accounts, 3 regions): ~30-60 seconds
- **Medium org** (20 accounts, 5 regions): ~2-5 minutes
- **Large org** (100+ accounts, all regions): ~10-20 minutes

## Troubleshooting

### Access Denied Errors

**Problem**: `AccessDenied: Unable to assume role OrganizationAccountAccessRole`

**Solutions**:
1. Verify the role exists in the target account
2. Check the trust relationship allows your management account
3. Ensure the role has the required permissions
4. Try specifying a different role with `--role-name`

### No Resources Found

**Problem**: Script completes but shows 0 resources

**Possible causes**:
1. Resources don't have any tags (Tagging API only returns tagged resources)
2. Resources are in regions not being scanned
3. Resource types are filtered out with `--resource-types`

**Solutions**:
- Remove `--resource-types` filter to scan all resource types
- Check resources actually have tags in the AWS Console
- Verify you're scanning the correct regions

### Throttling Errors

**Problem**: `ThrottlingException` or `RequestLimitExceeded`

**Solutions**:
- The tool automatically retries with exponential backoff
- If persistent, scan fewer accounts at a time with `--accounts`
- Scan specific regions with `--regions` to reduce API calls

### Suspended Accounts

**Problem**: Warning about suspended accounts

**Solution**: The tool automatically skips suspended accounts. This is expected behavior and not an error.

### Region Not Opted-In

**Problem**: Errors scanning certain regions

**Solution**: The tool automatically skips regions not opted-in for your account. Use `--regions` to explicitly specify which regions to scan.

## Common Use Cases

### 1. Initial Assessment

Get a baseline of Terraform adoption across your organization:

```bash
python3 terraform_coverage_audit.py --output both
```

### 2. Track Migration Progress

Monitor specific accounts as you migrate to Terraform:

```bash
python3 terraform_coverage_audit.py \
  --accounts 111111111111,222222222222 \
  --output html \
  --output-dir ~/terraform-migration
```

### 3. Focus on Critical Resources

Audit only production compute resources:

```bash
python3 terraform_coverage_audit.py \
  --accounts 123456789012 \
  --resource-types ec2:instance,rds:db,elasticloadbalancing:loadbalancer \
  --output html
```

### 4. Regional Compliance

Check Terraform coverage in specific compliance regions:

```bash
python3 terraform_coverage_audit.py \
  --regions us-gov-west-1,us-gov-east-1 \
  --output both
```

## Limitations

1. **Tagged Resources Only**: The AWS Resource Groups Tagging API only returns resources that have at least one tag. Resources with no tags won't appear in results.

2. **Resource Type Support**: Some AWS resource types may not support tagging or may not be indexed by the Tagging API.

3. **IAM Resources**: Global IAM resources (users, roles, policies) may only appear in one region and require special handling.

4. **Rate Limits**: The Tagging API has rate limits. The tool implements retry logic, but very large organizations may need to scan in batches.

5. **Cross-Account Roles**: The tool requires a consistent cross-account role name across all accounts (configurable with `--role-name`).

## Integration Examples

### Scheduled Audits

Run weekly audits with cron:

```bash
# Add to crontab
0 2 * * 1 cd /path/to/scriptasaurus && python3 scripts/aws_resource_analysis/terraform_coverage_audit/terraform_coverage_audit.py --output html --output-dir ~/weekly-reports
```

### CI/CD Pipeline

Fail builds if coverage drops below threshold:

```bash
#!/bin/bash
python3 terraform_coverage_audit.py --output console > audit.log
COVERAGE=$(grep "Organization Coverage" audit.log | grep -oE '[0-9]+\.[0-9]+%' | cut -d'%' -f1)
if (( $(echo "$COVERAGE < 80.0" | bc -l) )); then
    echo "Terraform coverage is below 80%: $COVERAGE%"
    exit 1
fi
```

### Slack Notifications

Send results to Slack after audit:

```bash
python3 terraform_coverage_audit.py --output html
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Terraform coverage audit complete! Report: ~/Desktop/terraform_coverage_report_*.html"}' \
  YOUR_SLACK_WEBHOOK_URL
```

## Contributing

When adding features or fixing bugs:

1. Follow PEP 8 style guidelines
2. Add docstrings to new functions
3. Test with both small and large organizations
4. Update this README with new features
5. Consider backwards compatibility

## License

Part of the Scriptasaurus repository. See repository root for license information.

## Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review AWS CloudTrail logs for permission issues
3. Enable `--verbose` logging for detailed diagnostics
4. Check the Issues section of the Scriptasaurus repository
