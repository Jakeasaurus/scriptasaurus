#!/usr/bin/env bash
set -o pipefail

################################################################################
# AWS Resource Discovery Script for Terraform Imports
# Uses charmbracelet/gum for interactive prompts and pretty output
################################################################################

# Check if gum is installed
if ! command -v gum &> /dev/null; then
    echo "❌ gum is not installed. Install it with: brew install gum"
    exit 1
fi

# Check if aws CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ aws CLI is not installed. Install it with: brew install awscli"
    exit 1
fi

# Welcome message
gum style \
    --border normal \
    --margin "1" \
    --padding "1 2" \
    --border-foreground 212 \
    "AWS Resource Discovery for Terraform Imports" \
    "" \
    "This script will gather information about existing AWS resources" \
    "to help generate Terraform import blocks."

# Prompt for AWS credentials
gum style --foreground 212 "🔐 AWS Credentials"
echo ""

# Check if AWS credentials are already configured
if aws sts get-caller-identity &>/dev/null; then
    CURRENT_IDENTITY=$(aws sts get-caller-identity --query 'Arn' --output text 2>/dev/null)
    gum style --foreground 42 "✓ Found existing AWS credentials"
    gum style --foreground 250 "  Identity: $CURRENT_IDENTITY"
    echo ""
    
    if gum confirm "Use existing AWS credentials?"; then
        # Use existing credentials
        AWS_REGION=${AWS_REGION:-$(aws configure get region 2>/dev/null || echo "us-west-2")}
        gum style --foreground 42 "Using existing credentials"
    else
        # Prompt for new credentials
        AWS_ACCESS_KEY_ID=$(gum input --placeholder "AWS Access Key ID" --password)
        export AWS_ACCESS_KEY_ID
        
        AWS_SECRET_ACCESS_KEY=$(gum input --placeholder "AWS Secret Access Key" --password)
        export AWS_SECRET_ACCESS_KEY
        
        # Ask if using temporary credentials (session token)
        if gum confirm "Are you using temporary credentials (session token)?"; then
            AWS_SESSION_TOKEN=$(gum input --placeholder "AWS Session Token" --password)
            export AWS_SESSION_TOKEN
        fi
        
        AWS_REGION=$(gum input --placeholder "AWS Region (e.g., us-west-2)" --value "us-west-2")
        export AWS_REGION
    fi
else
    gum style --foreground 196 "✗ No existing AWS credentials found"
    echo ""
    
    AWS_ACCESS_KEY_ID=$(gum input --placeholder "AWS Access Key ID" --password)
    export AWS_ACCESS_KEY_ID
    
    AWS_SECRET_ACCESS_KEY=$(gum input --placeholder "AWS Secret Access Key" --password)
    export AWS_SECRET_ACCESS_KEY
    
    # Ask if using temporary credentials (session token)
    if gum confirm "Are you using temporary credentials (session token)?"; then
        AWS_SESSION_TOKEN=$(gum input --placeholder "AWS Session Token" --password)
        export AWS_SESSION_TOKEN
    fi
    
    AWS_REGION=$(gum input --placeholder "AWS Region (e.g., us-west-2)" --value "us-west-2")
    export AWS_REGION
fi

# Prompt for project/resource name filter
gum style --foreground 212 "🔍 Resource Filters"
echo ""
gum style --foreground 250 "Filter resources by project name (e.g., blend-prod, blend-dev)"
gum style --foreground 250 "Leave blank to fetch ALL resources in the region"
echo ""
PROJECT_NAME=$(gum input --placeholder "Project name (optional, press enter to skip)")

# Create output directory
OUTPUT_DIR="aws-resources-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$OUTPUT_DIR"

# Initialize warnings array
WARNINGS_FILE="$OUTPUT_DIR/.warnings.txt"
touch "$WARNINGS_FILE"

gum style --foreground 212 "📁 Saving output to: $OUTPUT_DIR"
echo ""

# Function to run AWS command and save output
run_aws_command() {
    local description=$1
    local command=$2
    local filename=$3
    local error_file="$OUTPUT_DIR/${filename}.error"
    
    gum spin --spinner dot --title "Fetching $description..." -- \
        bash -c "$command > $OUTPUT_DIR/$filename 2>$error_file"
    
    local exit_code=$?
    
    # Always check stderr for errors, even if exit code is 0
    if [ -s "$error_file" ]; then
        local error_content=$(cat "$error_file")
        # Check for known non-critical errors
        if echo "$error_content" | grep -q "NoSuchTagSet\|NoSuchBucketPolicy\|NoSuchLifecycleConfiguration"; then
            gum style --foreground 214 "⚠ $description (with warning)"
            echo "$description: $(echo "$error_content" | grep -o 'An error occurred.*' | head -n 1)" >> "$WARNINGS_FILE"
        else
            # Real error
            gum style --foreground 196 "✗ Failed to fetch $description"
            gum style --foreground 196 "  Error: $(head -n 3 $error_file)"
            echo "$description: $(head -n 3 $error_file)" >> "$WARNINGS_FILE"
        fi
    elif [ $exit_code -eq 0 ]; then
        # Success with no errors
        if [ -s "$OUTPUT_DIR/$filename" ] && ! grep -q '"error"\|"Error"\|"errorMessage"' "$OUTPUT_DIR/$filename" 2>/dev/null; then
            gum style --foreground 42 "✓ $description"
        else
            gum style --foreground 196 "✗ Failed to fetch $description (empty or error in response)"
            echo "$description: Empty response or JSON error" >> "$WARNINGS_FILE"
        fi
    else
        gum style --foreground 196 "✗ Failed to fetch $description (exit code: $exit_code)"
        if [ -s "$error_file" ]; then
            gum style --foreground 196 "  Error details:"
            gum style --foreground 196 "  $(head -n 5 $error_file | sed 's/^/  /')"
            echo "$description: $(head -n 5 $error_file)" >> "$WARNINGS_FILE"
        fi
    fi
}

gum style \
    --border double \
    --margin "1" \
    --padding "1 2" \
    --border-foreground 42 \
    "Starting AWS Resource Discovery..."

# 1. API Gateway - REST APIs
if [ -n "$PROJECT_NAME" ]; then
    run_aws_command \
        "API Gateway REST APIs (filtered by: $PROJECT_NAME)" \
        "aws apigateway get-rest-apis --region $AWS_REGION --output json | jq '[.items[] | select(.name | contains(\"$PROJECT_NAME\"))]'" \
        "01-api-gateway-rest-apis.json"
else
    run_aws_command \
        "API Gateway REST APIs (all)" \
        "aws apigateway get-rest-apis --region $AWS_REGION --output json | jq '.items'" \
        "01-api-gateway-rest-apis.json"
fi

# 2. API Gateway - VPC Links
if [ -n "$PROJECT_NAME" ]; then
    run_aws_command \
        "API Gateway VPC Links (filtered by: $PROJECT_NAME)" \
        "aws apigateway get-vpc-links --region $AWS_REGION --output json | jq '[.items[] | select(.name | contains(\"$PROJECT_NAME\"))]'" \
        "02-api-gateway-vpc-links.json"
else
    run_aws_command \
        "API Gateway VPC Links (all)" \
        "aws apigateway get-vpc-links --region $AWS_REGION --output json | jq '.items'" \
        "02-api-gateway-vpc-links.json"
fi

# 3. API Gateway - Domain Names
if [ -n "$PROJECT_NAME" ]; then
    run_aws_command \
        "API Gateway Domain Names (filtered)" \
        "aws apigateway get-domain-names --region $AWS_REGION --output json | jq '[.items[] | select(.domainName | contains(\"gosunward.org\") or contains(\"$PROJECT_NAME\"))]'" \
        "03-api-gateway-domains.json"
else
    run_aws_command \
        "API Gateway Domain Names (all)" \
        "aws apigateway get-domain-names --region $AWS_REGION --output json | jq '.items'" \
        "03-api-gateway-domains.json"
fi

# Extract API ID for subsequent commands
API_ID=$(jq -r '.[0].id // empty' "$OUTPUT_DIR/01-api-gateway-rest-apis.json" 2>/dev/null || echo "")

if [ -n "$API_ID" ]; then
    # 4. API Gateway - Stages
    run_aws_command \
        "API Gateway Stages (API: $API_ID)" \
        "aws apigateway get-stages --rest-api-id $API_ID --region $AWS_REGION --output json" \
        "04-api-gateway-stages.json"
    
    # 5. API Gateway - Resources
    run_aws_command \
        "API Gateway Resources (API: $API_ID)" \
        "aws apigateway get-resources --rest-api-id $API_ID --region $AWS_REGION --output json" \
        "05-api-gateway-resources.json"
    
    # Extract root resource ID
    ROOT_RESOURCE_ID=$(jq -r '.items[] | select(.path == "/") | .id' "$OUTPUT_DIR/05-api-gateway-resources.json" 2>/dev/null || echo "")
    
    if [ -n "$ROOT_RESOURCE_ID" ]; then
        echo "$ROOT_RESOURCE_ID" > "$OUTPUT_DIR/root-resource-id.txt"
        gum style --foreground 42 "  → Root Resource ID: $ROOT_RESOURCE_ID"
    fi
fi

# 6. Load Balancers
if [ -n "$PROJECT_NAME" ]; then
    run_aws_command \
        "Network Load Balancers (filtered by: $PROJECT_NAME)" \
        "aws elbv2 describe-load-balancers --region $AWS_REGION --output json | jq '[.LoadBalancers[] | select(.LoadBalancerName | contains(\"$PROJECT_NAME\"))]'" \
        "06-load-balancers.json"
else
    run_aws_command \
        "Network Load Balancers (all)" \
        "aws elbv2 describe-load-balancers --region $AWS_REGION --output json | jq '.LoadBalancers'" \
        "06-load-balancers.json"
fi

# Extract NLB ARN for subsequent commands
NLB_ARN=$(jq -r '.[0].LoadBalancerArn // empty' "$OUTPUT_DIR/06-load-balancers.json" 2>/dev/null || echo "")

if [ -n "$NLB_ARN" ]; then
    # 7. Target Groups
    if [ -n "$PROJECT_NAME" ]; then
        run_aws_command \
            "Target Groups (filtered by: $PROJECT_NAME)" \
            "aws elbv2 describe-target-groups --region $AWS_REGION --output json | jq '[.TargetGroups[] | select(.TargetGroupName | contains(\"$PROJECT_NAME\"))]'" \
            "07-target-groups.json"
    else
        run_aws_command \
            "Target Groups (all)" \
            "aws elbv2 describe-target-groups --region $AWS_REGION --output json | jq '.TargetGroups'" \
            "07-target-groups.json"
    fi
    
    # 8. Listeners
    run_aws_command \
        "Load Balancer Listeners" \
        "aws elbv2 describe-listeners --load-balancer-arn $NLB_ARN --region $AWS_REGION --output json" \
        "08-listeners.json"
    
    # Extract listener ARN
    LISTENER_ARN=$(jq -r '.Listeners[0].ListenerArn // empty' "$OUTPUT_DIR/08-listeners.json" 2>/dev/null || echo "")
    if [ -n "$LISTENER_ARN" ]; then
        echo "$LISTENER_ARN" > "$OUTPUT_DIR/listener-arn.txt"
        gum style --foreground 42 "  → Listener ARN saved"
    fi
    
    # Extract VPC ID from NLB
    VPC_ID=$(jq -r '.[0].VpcId // empty' "$OUTPUT_DIR/06-load-balancers.json" 2>/dev/null || echo "")
    
    if [ -n "$VPC_ID" ]; then
        # 9. Security Groups
        if [ -n "$PROJECT_NAME" ]; then
            run_aws_command \
                "Security Groups (VPC: $VPC_ID, filtered by: $PROJECT_NAME)" \
                "aws ec2 describe-security-groups --region $AWS_REGION --filters \"Name=vpc-id,Values=$VPC_ID\" --output json | jq '[.SecurityGroups[] | select(.GroupName | contains(\"$PROJECT_NAME\")) or select(.Description | contains(\"$PROJECT_NAME\"))]'" \
                "09-security-groups.json"
        else
            run_aws_command \
                "Security Groups (VPC: $VPC_ID, all)" \
                "aws ec2 describe-security-groups --region $AWS_REGION --filters \"Name=vpc-id,Values=$VPC_ID\" --output json | jq '.SecurityGroups'" \
                "09-security-groups.json"
        fi
    fi
fi

# 10. S3 Buckets
if [ -n "$PROJECT_NAME" ]; then
    run_aws_command \
        "S3 Buckets (filtered by: $PROJECT_NAME + truststore)" \
        "aws s3api list-buckets --output json | jq '[.Buckets[] | select(.Name | contains(\"$PROJECT_NAME\") and contains(\"truststore\"))]'" \
        "10-s3-buckets.json"
else
    run_aws_command \
        "S3 Buckets (all with 'truststore')" \
        "aws s3api list-buckets --output json | jq '[.Buckets[] | select(.Name | contains(\"truststore\"))]'" \
        "10-s3-buckets.json"
fi

# Extract bucket name for detailed info
BUCKET_NAME=$(jq -r '.[0].Name // empty' "$OUTPUT_DIR/10-s3-buckets.json" 2>/dev/null || echo "")

if [ -n "$BUCKET_NAME" ]; then
    run_aws_command \
        "S3 Bucket Versioning ($BUCKET_NAME)" \
        "aws s3api get-bucket-versioning --bucket $BUCKET_NAME --region $AWS_REGION --output json" \
        "11-s3-bucket-versioning.json"
    
    run_aws_command \
        "S3 Bucket Encryption ($BUCKET_NAME)" \
        "aws s3api get-bucket-encryption --bucket $BUCKET_NAME --region $AWS_REGION --output json" \
        "12-s3-bucket-encryption.json"
    
    run_aws_command \
        "S3 Bucket Public Access Block ($BUCKET_NAME)" \
        "aws s3api get-public-access-block --bucket $BUCKET_NAME --region $AWS_REGION --output json" \
        "13-s3-bucket-public-access.json"
    
    run_aws_command \
        "S3 Bucket Tags ($BUCKET_NAME)" \
        "aws s3api get-bucket-tagging --bucket $BUCKET_NAME --region $AWS_REGION --output json" \
        "14-s3-bucket-tags.json"
fi

# 11. VPC Information
run_aws_command \
    "VPC Information" \
    "aws ec2 describe-vpcs --region $AWS_REGION --filters \"Name=tag:Name,Values=*${PROJECT_NAME}*\" --output json" \
    "15-vpcs.json"

# If no VPC found by name, try by CIDR if we have VPC_ID
if [ -n "${VPC_ID:-}" ]; then
    run_aws_command \
        "VPC Details (ID: $VPC_ID)" \
        "aws ec2 describe-vpcs --region $AWS_REGION --vpc-ids $VPC_ID --output json" \
        "15-vpc-details.json"
fi

# 12. ACM Certificates
if [ -n "$PROJECT_NAME" ]; then
    run_aws_command \
        "ACM Certificates (filtered)" \
        "aws acm list-certificates --region $AWS_REGION --output json | jq '[.CertificateSummaryList[] | select(.DomainName | contains(\"gosunward.org\") or contains(\"$PROJECT_NAME\"))]'" \
        "16-acm-certificates.json"
else
    run_aws_command \
        "ACM Certificates (all)" \
        "aws acm list-certificates --region $AWS_REGION --output json | jq '.CertificateSummaryList'" \
        "16-acm-certificates.json"
fi

# Extract certificate ARN for details
CERT_ARN=$(jq -r '.[0].CertificateArn // empty' "$OUTPUT_DIR/16-acm-certificates.json" 2>/dev/null || echo "")

if [ -n "$CERT_ARN" ]; then
    run_aws_command \
        "ACM Certificate Details" \
        "aws acm describe-certificate --certificate-arn $CERT_ARN --region $AWS_REGION --output json" \
        "17-acm-certificate-details.json"
fi

# 13. Transit Gateway (if exists)
run_aws_command \
    "Transit Gateway" \
    "aws ec2 describe-transit-gateways --region $AWS_REGION --output json" \
    "18-transit-gateways.json"

# Generate summary report
gum style \
    --border double \
    --margin "1" \
    --padding "1 2" \
    --border-foreground 42 \
    "Generating Summary Report..."

cat > "$OUTPUT_DIR/SUMMARY.md" << EOF
# AWS Resource Discovery Summary

**Generated:** $(date)
**Region:** $AWS_REGION
**Project Filter:** $PROJECT_NAME

## Key Resources Found

### API Gateway
EOF

if [ -n "$API_ID" ]; then
    echo "- **API ID:** \`$API_ID\`" >> "$OUTPUT_DIR/SUMMARY.md"
    echo "- **Root Resource ID:** \`${ROOT_RESOURCE_ID:-N/A}\`" >> "$OUTPUT_DIR/SUMMARY.md"
fi

cat >> "$OUTPUT_DIR/SUMMARY.md" << EOF

### Load Balancer
EOF

if [ -n "$NLB_ARN" ]; then
    echo "- **NLB ARN:** \`$NLB_ARN\`" >> "$OUTPUT_DIR/SUMMARY.md"
    echo "- **Listener ARN:** \`${LISTENER_ARN:-N/A}\`" >> "$OUTPUT_DIR/SUMMARY.md"
fi

cat >> "$OUTPUT_DIR/SUMMARY.md" << EOF

### S3
EOF

if [ -n "$BUCKET_NAME" ]; then
    echo "- **Bucket Name:** \`$BUCKET_NAME\`" >> "$OUTPUT_DIR/SUMMARY.md"
fi

cat >> "$OUTPUT_DIR/SUMMARY.md" << EOF

### ACM Certificate
EOF

if [ -n "$CERT_ARN" ]; then
    echo "- **Certificate ARN:** \`$CERT_ARN\`" >> "$OUTPUT_DIR/SUMMARY.md"
fi

cat >> "$OUTPUT_DIR/SUMMARY.md" << EOF

### VPC
EOF

if [ -n "${VPC_ID:-}" ]; then
    echo "- **VPC ID:** \`$VPC_ID\`" >> "$OUTPUT_DIR/SUMMARY.md"
fi

cat >> "$OUTPUT_DIR/SUMMARY.md" << EOF

## Files Generated

All JSON output files are stored in this directory. Review each file for detailed resource information.

## Next Steps

1. Review the JSON files for complete resource details
2. Use the resource IDs to create Terraform import blocks
3. Run \`terraform plan\` to verify the import configuration

EOF

# Display summary
gum style \
    --border double \
    --margin "1" \
    --padding "1 2" \
    --border-foreground 42 \
    "✅ Resource Discovery Complete!"

echo ""
gum style --foreground 212 "📊 Summary:"
cat "$OUTPUT_DIR/SUMMARY.md"

# Display warnings if any
if [ -s "$WARNINGS_FILE" ]; then
    echo ""
    gum style \
        --border normal \
        --margin "1" \
        --padding "1 2" \
        --border-foreground 214 \
        --foreground 214 \
        "⚠️  Warnings Encountered"
    
    echo ""
    gum style --foreground 214 "The following non-critical issues were encountered:"
    echo ""
    
    while IFS= read -r warning; do
        gum style --foreground 214 "  • $warning"
    done < "$WARNINGS_FILE"
    
    echo ""
    gum style --foreground 250 "These are typically expected (e.g., resources without tags)."
    gum style --foreground 250 "Check the .error files in the output directory for details."
fi

echo ""
gum style --foreground 42 "💾 All outputs saved to: $OUTPUT_DIR/"
echo ""

# Offer to open the directory
if gum confirm "Open output directory?" 2>/dev/null; then
    open "$OUTPUT_DIR"
fi

# Exit with success code
exit 0
