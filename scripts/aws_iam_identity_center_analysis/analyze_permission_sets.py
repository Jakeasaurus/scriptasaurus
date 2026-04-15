#!/usr/bin/env python3
"""
Analyze AWS IAM Identity Center Permission Sets
Determines permission set hierarchy and specific permissions with read-only access.
"""

import boto3
import json
from typing import Dict, List, Set
from collections import defaultdict
from tabulate import tabulate

def get_identity_store_id(sso_admin_client):
    """Get the Identity Store ID for the organization."""
    instances = sso_admin_client.list_instances()
    if instances['Instances']:
        return instances['Instances'][0]['IdentityStoreId'], instances['Instances'][0]['InstanceArn']
    return None, None

def list_permission_sets(sso_admin_client, instance_arn):
    """List all permission sets in the Identity Center instance."""
    permission_sets = []
    paginator = sso_admin_client.get_paginator('list_permission_sets')
    
    for page in paginator.paginate(InstanceArn=instance_arn):
        permission_sets.extend(page['PermissionSets'])
    
    return permission_sets

def get_permission_set_details(sso_admin_client, instance_arn, permission_set_arn):
    """Get detailed information about a permission set."""
    response = sso_admin_client.describe_permission_set(
        InstanceArn=instance_arn,
        PermissionSetArn=permission_set_arn
    )
    return response['PermissionSet']

def get_managed_policies(sso_admin_client, instance_arn, permission_set_arn):
    """Get AWS managed policies attached to a permission set."""
    managed_policies = []
    paginator = sso_admin_client.get_paginator('list_managed_policies_in_permission_set')
    
    for page in paginator.paginate(
        InstanceArn=instance_arn,
        PermissionSetArn=permission_set_arn
    ):
        managed_policies.extend(page['AttachedManagedPolicies'])
    
    return managed_policies

def get_customer_managed_policies(sso_admin_client, instance_arn, permission_set_arn):
    """Get customer managed policies attached to a permission set."""
    customer_policies = []
    paginator = sso_admin_client.get_paginator('list_customer_managed_policy_references_in_permission_set')
    
    try:
        for page in paginator.paginate(
            InstanceArn=instance_arn,
            PermissionSetArn=permission_set_arn
        ):
            customer_policies.extend(page.get('CustomerManagedPolicyReferences', []))
    except Exception as e:
        # Some permission sets may not have customer managed policies
        pass
    
    return customer_policies

def get_inline_policy(sso_admin_client, instance_arn, permission_set_arn):
    """Get inline policy for a permission set."""
    try:
        response = sso_admin_client.get_inline_policy_for_permission_set(
            InstanceArn=instance_arn,
            PermissionSetArn=permission_set_arn
        )
        if response.get('InlinePolicy'):
            return json.loads(response['InlinePolicy'])
    except Exception as e:
        # No inline policy attached
        pass
    
    return None

def get_permissions_boundary(sso_admin_client, instance_arn, permission_set_arn):
    """Get permissions boundary for a permission set."""
    try:
        response = sso_admin_client.get_permissions_boundary_for_permission_set(
            InstanceArn=instance_arn,
            PermissionSetArn=permission_set_arn
        )
        return response.get('PermissionsBoundary')
    except Exception as e:
        # No permissions boundary
        pass
    
    return None

def analyze_policy_actions(inline_policy):
    """Extract actions from inline policy document."""
    actions = set()
    
    if not inline_policy or 'Statement' not in inline_policy:
        return actions
    
    for statement in inline_policy['Statement']:
        if statement.get('Effect') == 'Allow':
            action_list = statement.get('Action', [])
            if isinstance(action_list, str):
                actions.add(action_list)
            elif isinstance(action_list, list):
                actions.update(action_list)
    
    return actions

def list_identity_center_groups(identitystore_client, identity_store_id):
    """List all groups in Identity Center, filtering for zzz_ prefix."""
    groups = []
    paginator = identitystore_client.get_paginator('list_groups')
    
    for page in paginator.paginate(IdentityStoreId=identity_store_id):
        for group in page['Groups']:
            if group['DisplayName'].startswith('zzz_'):
                groups.append({
                    'GroupId': group['GroupId'],
                    'DisplayName': group['DisplayName'],
                    'Description': group.get('Description', '')
                })
    
    return groups

def get_account_assignments(sso_admin_client, instance_arn, permission_set_arn):
    """Get all account assignments for a permission set."""
    assignments = []
    
    try:
        paginator = sso_admin_client.get_paginator('list_account_assignments')
        
        # First, get list of accounts that have assignments
        accounts_response = sso_admin_client.list_accounts_for_provisioned_permission_set(
            InstanceArn=instance_arn,
            PermissionSetArn=permission_set_arn
        )
        
        for account_id in accounts_response.get('AccountIds', []):
            for page in paginator.paginate(
                InstanceArn=instance_arn,
                AccountId=account_id,
                PermissionSetArn=permission_set_arn
            ):
                for assignment in page.get('AccountAssignments', []):
                    assignments.append({
                        'AccountId': account_id,
                        'PrincipalType': assignment['PrincipalType'],
                        'PrincipalId': assignment['PrincipalId']
                    })
    except Exception as e:
        pass
    
    return assignments

def get_organizations_accounts(org_client):
    """Get all AWS accounts in the organization with their status."""
    accounts = {}
    paginator = org_client.get_paginator('list_accounts')
    
    for page in paginator.paginate():
        for account in page['Accounts']:
            accounts[account['Id']] = {
                'name': account['Name'],
                'status': account['Status']
            }
    
    return accounts

def main():
    # Initialize AWS clients
    sso_admin_client = boto3.client('sso-admin', region_name='us-east-1')
    identitystore_client = boto3.client('identitystore', region_name='us-east-1')
    org_client = boto3.client('organizations', region_name='us-east-1')
    
    # Get Identity Center instance
    print("Fetching Identity Center instance...")
    identity_store_id, instance_arn = get_identity_store_id(sso_admin_client)
    
    if not instance_arn:
        print("Error: Could not find Identity Center instance")
        return
    
    print(f"Instance ARN: {instance_arn}")
    print(f"Identity Store ID: {identity_store_id}\n")
    
    # Get AWS accounts
    print("Fetching AWS Organization accounts...")
    accounts_map = get_organizations_accounts(org_client)
    active_count = sum(1 for a in accounts_map.values() if a['status'] == 'ACTIVE')
    print(f"Found {len(accounts_map)} total accounts ({active_count} active)\n")
    
    # List all permission sets
    print("Fetching permission sets...")
    permission_set_arns = list_permission_sets(sso_admin_client, instance_arn)
    print(f"Found {len(permission_set_arns)} permission sets\n")
    
    # Get groups
    print("Fetching Identity Center groups (zzz_*)...")
    groups = list_identity_center_groups(identitystore_client, identity_store_id)
    print(f"Found {len(groups)} groups\n")
    
    # Create group ID to name mapping
    group_map = {g['GroupId']: g['DisplayName'] for g in groups}
    
    # Analyze each permission set
    print("Analyzing permission sets and assignments...\n")
    permission_sets_data = {}
    
    for ps_arn in permission_set_arns:
        details = get_permission_set_details(sso_admin_client, instance_arn, ps_arn)
        ps_name = details['Name']
        
        # Get managed policies
        managed_policies = get_managed_policies(sso_admin_client, instance_arn, ps_arn)
        managed_policy_names = [p['Name'] for p in managed_policies]
        
        # Get customer managed policies
        customer_policies = get_customer_managed_policies(sso_admin_client, instance_arn, ps_arn)
        customer_policy_names = [p.get('Name', 'Unknown') for p in customer_policies]
        
        # Get inline policy
        inline_policy = get_inline_policy(sso_admin_client, instance_arn, ps_arn)
        inline_actions = analyze_policy_actions(inline_policy)
        
        # Get account assignments
        assignments = get_account_assignments(sso_admin_client, instance_arn, ps_arn)
        
        # Store data
        permission_sets_data[ps_name] = {
            'arn': ps_arn,
            'description': details.get('Description', ''),
            'managed_policies': managed_policy_names,
            'customer_policies': customer_policy_names,
            'inline_actions': inline_actions,
            'assignments': assignments
        }
    
    # Build group-centric view
    group_data = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    
    for ps_name, ps_data in permission_sets_data.items():
        for assignment in ps_data['assignments']:
            if assignment['PrincipalType'] == 'GROUP':
                group_id = assignment['PrincipalId']
                if group_id in group_map:
                    group_name = group_map[group_id]
                    account_id = assignment['AccountId']
                    account_info = accounts_map.get(account_id, {'name': account_id, 'status': 'UNKNOWN'})
                    account_name = account_info['name']
                    account_status = account_info['status']
                    display_name = f"{account_name} ({account_status})" if account_status != 'ACTIVE' else account_name
                    group_data[group_name][ps_name][display_name].append(account_id)
    
    # Display results
    print("=" * 100)
    print("PERMISSION SETS OVERVIEW")
    print("=" * 100)
    print()
    
    # Table 1: Permission Sets and their Policies
    ps_table = []
    for ps_name in sorted(permission_sets_data.keys()):
        ps_data = permission_sets_data[ps_name]
        policies = ', '.join(ps_data['managed_policies']) if ps_data['managed_policies'] else 'None'
        customer = ', '.join(ps_data['customer_policies']) if ps_data['customer_policies'] else 'None'
        inline = f"{len(ps_data['inline_actions'])} actions" if ps_data['inline_actions'] else 'None'
        
        ps_table.append([
            ps_name,
            policies,
            customer,
            inline
        ])
    
    print(tabulate(ps_table, 
                   headers=['Permission Set', 'AWS Managed Policies', 'Customer Policies', 'Inline Policy'],
                   tablefmt='pipe',
                   maxcolwidths=[25, 40, 25, 15]))
    
    print("\n" + "=" * 100)
    print("GROUPS AND THEIR PERMISSION SETS")
    print("=" * 100)
    print()
    
    # Table 2: Groups, Permission Sets, and Accounts
    for group_name in sorted(group_data.keys()):
        print(f"\n{'='*100}")
        print(f"GROUP: {group_name}")
        print(f"{'='*100}\n")
        
        group_assignments = group_data[group_name]
        
        for ps_name in sorted(group_assignments.keys()):
            ps_data = permission_sets_data[ps_name]
            accounts = group_assignments[ps_name]
            
            print(f"Permission Set: {ps_name}")
            print(f"  Description: {ps_data['description']}")
            
            if ps_data['managed_policies']:
                print(f"  AWS Managed Policies: {', '.join(ps_data['managed_policies'])}")
            
            if ps_data['customer_policies']:
                print(f"  Customer Managed Policies: {', '.join(ps_data['customer_policies'])}")
            
            if ps_data['inline_actions']:
                print(f"  Inline Policy Actions ({len(ps_data['inline_actions'])}):")
                for action in sorted(list(ps_data['inline_actions'])):
                    print(f"    - {action}")
            
            print(f"\n  Assigned to {len(accounts)} account(s):\n")
            account_table = [[name, ids[0]] for name, ids in sorted(accounts.items())]
            print(tabulate(account_table, 
                         headers=['Account Name', 'Account ID'],
                         tablefmt='pipe',
                         colalign=('left', 'left')))
            print()
    
    print("\n" + "=" * 100)
    print("PERMISSION SET TO ACCOUNTS MAPPING")
    print("=" * 100)
    print()
    
    # Table 3: Permission Sets and their Account Assignments
    for ps_name in sorted(permission_sets_data.keys()):
        ps_data = permission_sets_data[ps_name]
        
        if not ps_data['assignments']:
            continue
        
        # Get unique accounts for this permission set
        accounts_for_ps = set()
        groups_for_ps = defaultdict(list)
        
        for assignment in ps_data['assignments']:
            account_id = assignment['AccountId']
            account_info = accounts_map.get(account_id, {'name': account_id, 'status': 'UNKNOWN'})
            account_name = account_info['name']
            account_status = account_info['status']
            display_name = f"{account_name} ({'⚠️ ' if account_status != 'ACTIVE' else ''}{account_status})"
            accounts_for_ps.add((display_name, account_id, account_status))
            
            if assignment['PrincipalType'] == 'GROUP' and assignment['PrincipalId'] in group_map:
                groups_for_ps[display_name].append(group_map[assignment['PrincipalId']])
        
        if accounts_for_ps:
            active_accounts = sum(1 for _, _, status in accounts_for_ps if status == 'ACTIVE')
            inactive_accounts = len(accounts_for_ps) - active_accounts
            
            print(f"\nPermission Set: {ps_name}")
            print(f"Policies: {', '.join(ps_data['managed_policies']) if ps_data['managed_policies'] else 'None'}")
            account_summary = f"Assigned to {len(accounts_for_ps)} account(s)"
            if inactive_accounts > 0:
                account_summary += f" ({active_accounts} active, {inactive_accounts} inactive)"
            print(f"{account_summary}:\n")
            
            account_table = []
            for account_name, account_id, _ in sorted(accounts_for_ps):
                groups_list = ', '.join(sorted(set(groups_for_ps.get(account_name, [])))) or 'Direct assignment'
                account_table.append([account_name, account_id, groups_list])
            
            print(tabulate(account_table,
                         headers=['Account Name', 'Account ID', 'Via Groups'],
                         tablefmt='pipe',
                         maxcolwidths=[30, 15, 50]))

if __name__ == "__main__":
    main()
