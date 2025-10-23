# AWS CLI Commands

This directory contains AWS CLI command templates and scripts for common AWS operations.

## API Gateway Information Collection

### Script: `api_gateway_info_collection.sh`

A comprehensive script that collects all API Gateway configuration details and outputs them as structured JSON. This is particularly useful for:

- Performing Terraform imports of existing API Gateway resources
- Documenting current API Gateway configurations
- Auditing API Gateway setups across accounts
- Migration planning and infrastructure-as-code conversion

#### Prerequisites

- AWS CLI installed and configured
- `jq` installed for JSON processing
- Appropriate AWS IAM permissions for API Gateway read operations

#### Usage

**Default region (from AWS CLI configuration):**
```bash
./api_gateway_info_collection.sh
```

**Specific region:**
```bash
./api_gateway_info_collection.sh us-east-1
```

**Save output to file:**
```bash
./api_gateway_info_collection.sh us-east-1 > api_gateway_info.json
```

#### What It Collects

**API Gateway v1 (REST APIs):**
- All REST APIs
- Resources and methods for each API
- Deployments and stages
- Stage variables and configurations
- Authorizers
- Models and request validators
- API keys and usage plans
- VPC links
- Client certificates
- Custom domain names

**API Gateway v2 (HTTP/WebSocket APIs):**
- All HTTP and WebSocket APIs
- Routes and route configurations
- Integrations and integration details
- Stages and deployments
- Authorizers
- Models
- API mappings
- VPC links
- Custom domain names

**Additional Information:**
- Account identity (for verification)
- Collection timestamp
- AWS region

#### Output Format

The script outputs a structured JSON document with the following top-level structure:

```json
{
  "collection_timestamp": "2025-10-01T20:23:29Z",
  "aws_region": "us-east-1",
  "api_gateway_details": {
    "rest_apis_list": { ... },
    "http_websocket_apis_list": { ... },
    ...
  }
}
```

Each section includes both the AWS CLI command used and the output, making it easy to reproduce specific queries.

#### Use Cases

**Terraform Import Preparation:**
The collected information provides all the necessary IDs and configurations needed to write Terraform import statements and configuration blocks.

**Configuration Auditing:**
Compare API Gateway configurations across different environments or accounts.

**Documentation:**
Generate comprehensive documentation of your API Gateway setup.

**Troubleshooting:**
Quickly gather all configuration details when investigating issues.

#### IAM Permissions Required

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "apigateway:GET",
        "sts:GetCallerIdentity"
      ],
      "Resource": "*"
    }
  ]
}
```

## EC2 Information

Additional AWS CLI command examples for EC2 operations can be found in this directory for common query patterns and filtering operations.
