#!/usr/bin/env python3
"""
Visualize AWS IAM Identity Center Permission Sets
Creates a visual map showing relationships between groups, permission sets, and accounts.
"""

import boto3
import json
from typing import Dict, List, Set
from collections import defaultdict
import graphviz

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

def create_visual_map(group_data, permission_sets_data, accounts_map, output_format='png'):
    """Create a visual map using graphviz."""
    
    # Create main graph
    dot = graphviz.Digraph(comment='Identity Center Permission Structure', format=output_format)
    dot.attr(rankdir='LR', splines='ortho', nodesep='0.5', ranksep='1.0')
    dot.attr('node', shape='box', style='rounded,filled', fontname='Arial')
    
    # Create subgraphs for better organization
    with dot.subgraph(name='cluster_groups') as c:
        c.attr(label='Identity Center Groups', style='filled', color='lightgrey')
        c.attr('node', fillcolor='lightblue')
        
        for group_name in sorted(group_data.keys()):
            # Shorten group name for display
            display_name = group_name.replace('zzz_app_aws_', '')
            c.node(f'group_{group_name}', display_name)
    
    with dot.subgraph(name='cluster_permission_sets') as c:
        c.attr(label='Permission Sets', style='filled', color='lightgrey')
        c.attr('node', fillcolor='lightgreen')
        
        for ps_name in sorted(permission_sets_data.keys()):
            ps_data = permission_sets_data[ps_name]
            policies = ps_data['managed_policies'][:2]  # Show first 2 policies
            policy_text = '\\n'.join(policies)
            if len(ps_data['managed_policies']) > 2:
                policy_text += f"\\n+{len(ps_data['managed_policies']) - 2} more"
            
            label = f"{ps_name}"
            if policy_text:
                label += f"\\n---\\n{policy_text}"
            
            c.node(f'ps_{ps_name}', label)
    
    with dot.subgraph(name='cluster_accounts') as c:
        c.attr(label='AWS Accounts', style='filled', color='lightgrey')
        c.attr('node', fillcolor='lightyellow', shape='folder')
        
        # Collect all accounts that are assigned
        all_accounts = set()
        for ps_data in permission_sets_data.values():
            for assignment in ps_data['assignments']:
                all_accounts.add(assignment['AccountId'])
        
        for account_id in sorted(all_accounts):
            account_info = accounts_map.get(account_id, {'name': account_id, 'status': 'UNKNOWN'})
            account_name = account_info['name']
            status = account_info['status']
            
            color = 'lightyellow' if status == 'ACTIVE' else 'lightcoral'
            label = account_name
            if status != 'ACTIVE':
                label += f"\\n({status})"
            
            c.node(f'account_{account_id}', label, fillcolor=color)
    
    # Add edges: Groups -> Permission Sets -> Accounts
    for group_name, ps_assignments in group_data.items():
        for ps_name, accounts in ps_assignments.items():
            # Group to Permission Set
            dot.edge(f'group_{group_name}', f'ps_{ps_name}', color='blue')
            
            # Permission Set to Accounts
            for account_name, account_ids in accounts.items():
                account_id = account_ids[0]
                dot.edge(f'ps_{ps_name}', f'account_{account_id}', color='green')
    
    return dot

def create_hierarchy_map(permission_sets_data, output_format='png'):
    """Create a hierarchical view of permission sets based on policies."""
    
    dot = graphviz.Digraph(comment='Permission Set Hierarchy', format=output_format)
    dot.attr(rankdir='TB')
    dot.attr('node', shape='box', style='rounded,filled', fontname='Arial')
    
    # Group permission sets by their base policy
    policy_groups = defaultdict(list)
    for ps_name, ps_data in permission_sets_data.items():
        base_policies = tuple(sorted(ps_data['managed_policies']))
        policy_groups[base_policies].append(ps_name)
    
    # Find base permission sets (those with single policies)
    base_policies = {}
    for policies, ps_names in policy_groups.items():
        if len(policies) == 1:
            base_policies[policies[0]] = ps_names
    
    # Create nodes
    for ps_name, ps_data in permission_sets_data.items():
        policies = ps_data['managed_policies']
        color = 'lightblue' if len(policies) == 1 else 'lightgreen'
        
        label = f"{ps_name}\\n---"
        for policy in policies[:3]:
            label += f"\\n{policy}"
        if len(policies) > 3:
            label += f"\\n+{len(policies) - 3} more"
        
        dot.node(ps_name, label, fillcolor=color)
    
    # Find and create hierarchy edges
    for ps_name, ps_data in permission_sets_data.items():
        ps_policies = set(ps_data['managed_policies'])
        
        if len(ps_policies) > 1:
            # Find potential parent (subset)
            for other_name, other_data in permission_sets_data.items():
                if ps_name == other_name:
                    continue
                
                other_policies = set(other_data['managed_policies'])
                
                # If other is a strict subset, draw an edge
                if other_policies and other_policies < ps_policies:
                    # Check if it's the most direct parent (no intermediate)
                    is_direct = True
                    for intermediate_name, intermediate_data in permission_sets_data.items():
                        if intermediate_name in [ps_name, other_name]:
                            continue
                        intermediate_policies = set(intermediate_data['managed_policies'])
                        if other_policies < intermediate_policies < ps_policies:
                            is_direct = False
                            break
                    
                    if is_direct:
                        additional = ps_policies - other_policies
                        label = '+' + ', '.join(list(additional)[:2])
                        if len(additional) > 2:
                            label += f" +{len(additional) - 2} more"
                        dot.edge(other_name, ps_name, label=label, color='darkgreen')
    
    return dot

def main():
    # Initialize AWS clients
    sso_admin_client = boto3.client('sso-admin', region_name='us-east-1')
    identitystore_client = boto3.client('identitystore', region_name='us-east-1')
    org_client = boto3.client('organizations', region_name='us-east-1')
    
    print("Fetching Identity Center instance...")
    identity_store_id, instance_arn = get_identity_store_id(sso_admin_client)
    
    if not instance_arn:
        print("Error: Could not find Identity Center instance")
        return
    
    print(f"Instance ARN: {instance_arn}\n")
    
    print("Fetching AWS Organization accounts...")
    accounts_map = get_organizations_accounts(org_client)
    print(f"Found {len(accounts_map)} accounts\n")
    
    print("Fetching permission sets...")
    permission_set_arns = list_permission_sets(sso_admin_client, instance_arn)
    print(f"Found {len(permission_set_arns)} permission sets\n")
    
    print("Fetching Identity Center groups...")
    groups = list_identity_center_groups(identitystore_client, identity_store_id)
    print(f"Found {len(groups)} groups\n")
    
    group_map = {g['GroupId']: g['DisplayName'] for g in groups}
    
    print("Analyzing permission sets and assignments...\n")
    permission_sets_data = {}
    
    for ps_arn in permission_set_arns:
        details = get_permission_set_details(sso_admin_client, instance_arn, ps_arn)
        ps_name = details['Name']
        
        managed_policies = get_managed_policies(sso_admin_client, instance_arn, ps_arn)
        managed_policy_names = [p['Name'] for p in managed_policies]
        
        customer_policies = get_customer_managed_policies(sso_admin_client, instance_arn, ps_arn)
        customer_policy_names = [p.get('Name', 'Unknown') for p in customer_policies]
        
        inline_policy = get_inline_policy(sso_admin_client, instance_arn, ps_arn)
        inline_actions = analyze_policy_actions(inline_policy)
        
        assignments = get_account_assignments(sso_admin_client, instance_arn, ps_arn)
        
        permission_sets_data[ps_name] = {
            'arn': ps_arn,
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
                    group_data[group_name][ps_name][account_name].append(account_id)
    
    print("Generating visualizations...\n")
    
    # Create main relationship map
    print("Creating relationship map (identity_center_map.png)...")
    relationship_graph = create_visual_map(group_data, permission_sets_data, accounts_map, 'png')
    relationship_graph.render('identity_center_map', cleanup=True)
    print(f"✓ Saved: identity_center_map.png\n")
    
    # Create hierarchy map
    print("Creating hierarchy map (permission_set_hierarchy.png)...")
    hierarchy_graph = create_hierarchy_map(permission_sets_data, 'png')
    hierarchy_graph.render('permission_set_hierarchy', cleanup=True)
    print(f"✓ Saved: permission_set_hierarchy.png\n")
    
    # Also create SVG versions for better zoom/quality
    print("Creating SVG versions for high-quality viewing...")
    relationship_graph_svg = create_visual_map(group_data, permission_sets_data, accounts_map, 'svg')
    relationship_graph_svg.render('identity_center_map', cleanup=True)
    print(f"✓ Saved: identity_center_map.svg")
    
    hierarchy_graph_svg = create_hierarchy_map(permission_sets_data, 'svg')
    hierarchy_graph_svg.render('permission_set_hierarchy', cleanup=True)
    print(f"✓ Saved: permission_set_hierarchy.svg\n")
    
    print("=" * 80)
    print("Visualization complete!")
    print("=" * 80)
    print("\nGenerated files:")
    print("  1. identity_center_map.png/svg - Shows Groups → Permission Sets → Accounts")
    print("  2. permission_set_hierarchy.png/svg - Shows Permission Set hierarchy based on policies")
    print("\nYou can open these in any image viewer or browser.")

if __name__ == "__main__":
    main()
