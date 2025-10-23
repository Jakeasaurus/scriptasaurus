#!/bin/bash

# API Gateway Details Collection Script
# This script collects comprehensive API Gateway information and outputs it as structured JSON
# Useful for performing imports and understanding API Gateway configurations

set -euo pipefail

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI is not installed or not in PATH" >&2
    exit 1
fi

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo "Error: jq is not installed or not in PATH" >&2
    exit 1
fi

# Optional: Specify AWS region (defaults to configured region)
REGION="${1:-}"
if [ -n "$REGION" ]; then
    export AWS_DEFAULT_REGION="$REGION"
fi

echo "{"
echo "  \"collection_timestamp\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\","
echo "  \"aws_region\": \"${AWS_DEFAULT_REGION:-$(aws configure get region)}\","
echo "  \"api_gateway_details\": {"

# Initialize first command flag
first_command=true

# Function to add command output with header
add_command_output() {
    local header=$1
    local command=$2
    
    if [ "$first_command" = false ]; then
        echo ","
    fi
    first_command=false
    
    echo "    \"$header\": {"
    echo "      \"command\": \"$command\","
    echo "      \"output\": "
    
    # Execute command and capture output
    output=$(eval "$command" 2>/dev/null)
    if [ $? -eq 0 ] && [ -n "$output" ]; then
        echo "$output" | jq '.'
    else
        echo "      null"
    fi
    echo -n "    }"
}

# REST API Commands (API Gateway v1)
add_command_output "rest_apis_list" "aws apigateway get-rest-apis"

# Get details for each REST API
rest_api_ids=$(aws apigateway get-rest-apis --query 'items[].id' --output text 2>/dev/null)
if [ -n "$rest_api_ids" ]; then
    for api_id in $rest_api_ids; do
        add_command_output "rest_api_${api_id}_details" "aws apigateway get-rest-api --rest-api-id $api_id"
        add_command_output "rest_api_${api_id}_resources" "aws apigateway get-resources --rest-api-id $api_id"
        add_command_output "rest_api_${api_id}_deployments" "aws apigateway get-deployments --rest-api-id $api_id"
        add_command_output "rest_api_${api_id}_stages" "aws apigateway get-stages --rest-api-id $api_id"
        add_command_output "rest_api_${api_id}_authorizers" "aws apigateway get-authorizers --rest-api-id $api_id"
        add_command_output "rest_api_${api_id}_models" "aws apigateway get-models --rest-api-id $api_id"
        add_command_output "rest_api_${api_id}_request_validators" "aws apigateway get-request-validators --rest-api-id $api_id"
        
        # Get stage details including stage variables
        stage_names=$(aws apigateway get-stages --rest-api-id $api_id --query 'item[].stageName' --output text 2>/dev/null)
        if [ -n "$stage_names" ]; then
            for stage_name in $stage_names; do
                add_command_output "rest_api_${api_id}_stage_${stage_name}" "aws apigateway get-stage --rest-api-id $api_id --stage-name $stage_name"
            done
        fi
    done
fi

# HTTP/WebSocket API Commands (API Gateway v2)
add_command_output "http_websocket_apis_list" "aws apigatewayv2 get-apis"

# Get details for each HTTP/WebSocket API
api_ids=$(aws apigatewayv2 get-apis --query 'Items[].ApiId' --output text 2>/dev/null)
if [ -n "$api_ids" ]; then
    for api_id in $api_ids; do
        add_command_output "api_${api_id}_details" "aws apigatewayv2 get-api --api-id $api_id"
        add_command_output "api_${api_id}_routes" "aws apigatewayv2 get-routes --api-id $api_id"
        add_command_output "api_${api_id}_integrations" "aws apigatewayv2 get-integrations --api-id $api_id"
        add_command_output "api_${api_id}_stages" "aws apigatewayv2 get-stages --api-id $api_id"
        add_command_output "api_${api_id}_deployments" "aws apigatewayv2 get-deployments --api-id $api_id"
        add_command_output "api_${api_id}_authorizers" "aws apigatewayv2 get-authorizers --api-id $api_id"
        add_command_output "api_${api_id}_models" "aws apigatewayv2 get-models --api-id $api_id"
        add_command_output "api_${api_id}_api_mappings" "aws apigatewayv2 get-api-mappings --api-id $api_id 2>/dev/null || echo '{}'"
        
        # Get route details including integrations
        route_ids=$(aws apigatewayv2 get-routes --api-id $api_id --query 'Items[].RouteId' --output text 2>/dev/null)
        if [ -n "$route_ids" ]; then
            for route_id in $route_ids; do
                add_command_output "api_${api_id}_route_${route_id}" "aws apigatewayv2 get-route --api-id $api_id --route-id $route_id"
            done
        fi
        
        # Get integration details
        integration_ids=$(aws apigatewayv2 get-integrations --api-id $api_id --query 'Items[].IntegrationId' --output text 2>/dev/null)
        if [ -n "$integration_ids" ]; then
            for integration_id in $integration_ids; do
                add_command_output "api_${api_id}_integration_${integration_id}" "aws apigatewayv2 get-integration --api-id $api_id --integration-id $integration_id"
            done
        fi
    done
fi

# Additional API Gateway resources
add_command_output "domain_names_v1" "aws apigateway get-domain-names"
add_command_output "domain_names_v2" "aws apigatewayv2 get-domain-names"

# Get domain name mappings for v2
domain_names_v2=$(aws apigatewayv2 get-domain-names --query 'Items[].DomainName' --output text 2>/dev/null)
if [ -n "$domain_names_v2" ]; then
    for domain_name in $domain_names_v2; do
        add_command_output "domain_${domain_name//./_}_mappings" "aws apigatewayv2 get-api-mappings --domain-name $domain_name"
    done
fi

# API Keys and Usage Plans (v1 only)
add_command_output "api_keys" "aws apigateway get-api-keys --include-values"
add_command_output "usage_plans" "aws apigateway get-usage-plans"

# Get usage plan details
usage_plan_ids=$(aws apigateway get-usage-plans --query 'items[].id' --output text 2>/dev/null)
if [ -n "$usage_plan_ids" ]; then
    for plan_id in $usage_plan_ids; do
        add_command_output "usage_plan_${plan_id}_keys" "aws apigateway get-usage-plan-keys --usage-plan-id $plan_id"
    done
fi

# VPC Links
add_command_output "vpc_links_v1" "aws apigateway get-vpc-links"
add_command_output "vpc_links_v2" "aws apigatewayv2 get-vpc-links"

# Client Certificates (v1)
add_command_output "client_certificates" "aws apigateway get-client-certificates"

# Export information for import operations
add_command_output "account_info" "aws sts get-caller-identity"

echo ""
echo "  }"
echo "}"
