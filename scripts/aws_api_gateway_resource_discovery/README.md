# AWS API Gateway Resource Discovery

Interactive script to discover and document existing AWS resources for Terraform import operations. Uses [gum](https://github.com/charmbracelet/gum) for an enhanced terminal UI experience.

## Overview

This script automates the discovery of AWS infrastructure components commonly used with API Gateway deployments, including:

- API Gateway REST APIs, VPC Links, Domain Names, Stages, Resources, and Methods
- Network Load Balancers (NLB), Target Groups, and Listeners
- S3 Buckets (truststore configurations)
- Security Groups
- ACM Certificates
- VPC Information
- Transit Gateways

The script generates JSON files with complete resource details, making it easy to create Terraform import blocks and configurations.

## Prerequisites

### Required Tools

- **AWS CLI** - Install with: `brew install awscli`
- **gum** - Install with: `brew install gum`
- **jq** - Install with: `brew install jq`

### AWS Credentials

The script can use:
- Existing AWS credentials configured via `aws configure` or environment variables
- Temporary credentials (with session token) for MFA-enabled accounts
- Manual credential entry with password-masked prompts

## Usage

### Basic Usage

```bash
./gather-aws-resources.sh
```

The script will:
1. Check for existing AWS credentials
2. Prompt for credentials if none are found (or if you choose to override)
3. Ask for an AWS region (defaults to `us-west-2`)
4. Ask for an optional project name filter (e.g., `blend-prod`, `blend-dev`)
5. Discover all matching resources
6. Generate a timestamped output directory with JSON files
7. Create a summary report
8. Display any warnings encountered

### Interactive Prompts

**AWS Credentials:**
- If credentials are detected, you can choose to use them or enter new ones
- Supports temporary credentials with session tokens

**Project Name Filter:**
- Enter a project name (e.g., `blend-prod`) to filter resources
- Leave blank to fetch ALL resources in the region
- Filtering is case-sensitive and uses substring matching

**Region Selection:**
- Defaults to `us-west-2`
- Can be changed to any AWS region

## Output

### Directory Structure

The script creates a timestamped directory with the following structure:

```
aws-resources-20251023-140530/
├── 01-api-gateway-rest-apis.json
├── 02-api-gateway-vpc-links.json
├── 03-api-gateway-domains.json
├── 04-api-gateway-stages.json
├── 05-api-gateway-resources.json
├── 06-load-balancers.json
├── 07-target-groups.json
├── 08-listeners.json
├── 09-security-groups.json
├── 10-s3-buckets.json
├── 11-s3-bucket-versioning.json
├── 12-s3-bucket-encryption.json
├── 13-s3-bucket-public-access.json
├── 14-s3-bucket-tags.json
├── 15-vpcs.json
├── 16-acm-certificates.json
├── 17-acm-certificate-details.json
├── 18-transit-gateways.json
├── listener-arn.txt
├── root-resource-id.txt
└── SUMMARY.md
```

### Error Files

If errors occur, `.error` files are created alongside the JSON outputs:
- `14-s3-bucket-tags.json.error` - Contains error details

### Status Indicators

During execution, the script shows:
- ✅ **Green checkmark** - Resource fetched successfully
- ⚠️ **Orange warning** - Non-critical error (e.g., NoSuchTagSet for buckets without tags)
- ❌ **Red X** - Critical error

### Warnings Summary

At the end of execution, the script displays a summary of non-critical warnings:

```
┌──────────────────────────────┐
│ ⚠️  Warnings Encountered      │
└──────────────────────────────┘

The following non-critical issues were encountered:

  • S3 Bucket Tags: An error occurred (NoSuchTagSet) when calling 
    the GetBucketTagging operation: The TagSet does not exist

These are typically expected (e.g., resources without tags).
Check the .error files in the output directory for details.
```

## Example Use Cases

### 1. Import Existing API Gateway Infrastructure

```bash
# Run script and filter by project name
./gather-aws-resources.sh
# Enter: blend-prod

# Review the output
cd aws-resources-*/
cat SUMMARY.md

# Use the JSON files to create Terraform import blocks
```

### 2. Audit All Resources in a Region

```bash
# Run script without filtering
./gather-aws-resources.sh
# Leave project name blank

# Review all discovered resources
cd aws-resources-*/
jq '.[] | {name: .name, id: .id}' 01-api-gateway-rest-apis.json
```

### 3. Document Infrastructure for DR Planning

```bash
# Run for production region
./gather-aws-resources.sh
# Enter: us-west-2 and blend-prod

# Run for DR region
./gather-aws-resources.sh
# Enter: us-east-2 and blend-prod

# Compare the two output directories
```

## Terraform Import Workflow

After running the script, use the discovered resource IDs to create Terraform import blocks:

1. **Review SUMMARY.md** for key resource IDs
2. **Check individual JSON files** for detailed resource configurations
3. **Create Terraform configuration** matching the existing resources
4. **Create import blocks** using the discovered IDs:

```hcl
import {
  to = module.api_gateway.aws_api_gateway_rest_api.this
  id = "5s0y0953z6"  # From 01-api-gateway-rest-apis.json
}

import {
  to = module.nlb.aws_lb.load_balancer
  id = "arn:aws:elasticloadbalancing:..."  # From listener-arn.txt
}
```

5. **Run `terraform plan`** to verify the import configuration
6. **Execute imports** to bring resources under Terraform management

## Common Warnings

### NoSuchTagSet
**Meaning:** S3 bucket has no tags  
**Action:** None required - this is expected for untagged resources

### NoSuchBucketPolicy
**Meaning:** S3 bucket has no bucket policy  
**Action:** None required - this is expected for buckets without policies

### NoSuchLifecycleConfiguration
**Meaning:** S3 bucket has no lifecycle rules  
**Action:** None required - this is expected for buckets without lifecycle policies

## Troubleshooting

### Script shows red border in Warp
**Cause:** Script exited with non-zero exit code  
**Solution:** Check the error output; the script now explicitly exits with code 0 on completion

### Empty JSON files
**Cause:** No resources match the filter, or insufficient AWS permissions  
**Solution:** 
- Try running without a project name filter
- Verify your AWS credentials have read permissions

### "Access Denied" errors
**Cause:** AWS credentials lack necessary permissions  
**Solution:** Ensure your IAM user/role has the following permissions:
```json
{
  "Effect": "Allow",
  "Action": [
    "apigateway:GET",
    "ec2:Describe*",
    "elasticloadbalancing:Describe*",
    "s3:GetBucket*",
    "s3:ListBucket*",
    "acm:List*",
    "acm:Describe*"
  ],
  "Resource": "*"
}
```

## Features

- ✅ Interactive credential management with existing credential detection
- ✅ Optional project name filtering
- ✅ Automatic resource chaining (e.g., fetch VPC ID from NLB, then query security groups)
- ✅ Pretty formatted output with colors and borders
- ✅ Non-critical error handling with warnings summary
- ✅ Timestamped output directories
- ✅ Summary report generation
- ✅ Key resource IDs saved to separate files for easy reference

## Contributing

This script is part of the [Scriptasaurus](https://github.com/jakeasaurus/scriptasaurus) collection. Contributions welcome!

## License

MIT License - See repository root for details
