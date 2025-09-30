#!/usr/bin/env python3
"""
AWS Terraform Coverage Audit

Scans all accounts in an AWS Organization to identify which resources are managed
by Terraform (tagged with terraform=true) and which are not.

Outputs summary statistics and detailed resource lists in console or HTML format.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import datetime as dt
import logging
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

try:
    import boto3
    from botocore.config import Config
    from botocore.exceptions import ClientError
except ImportError:
    print("ERROR: boto3 is required. Install with: pip3 install boto3 botocore")
    sys.exit(1)

try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.table import Table
except ImportError:
    print("ERROR: rich is required. Install with: pip3 install rich")
    sys.exit(1)

try:
    from jinja2 import Template
except ImportError:
    print("ERROR: jinja2 is required for HTML output. Install with: pip3 install jinja2")
    sys.exit(1)

# AWS retry configuration with adaptive mode for better throughput
AWS_RETRY_CONFIG = Config(
    retries={"max_attempts": 10, "mode": "adaptive"},
    read_timeout=60,
    connect_timeout=10
)

console = Console()
logger = logging.getLogger(__name__)


@dataclass
class ResourceRecord:
    """Represents a single AWS resource discovered during scanning."""
    arn: str
    resource_id: str
    resource_name: Optional[str]
    resource_type: str
    region: str
    account_id: str
    account_name: str
    managed: bool  # True if terraform=true tag is present


@dataclass
class AccountResult:
    """Results from scanning a single AWS account."""
    account_id: str
    account_name: str
    managed: List[ResourceRecord] = field(default_factory=list)
    unmanaged: List[ResourceRecord] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    p = argparse.ArgumentParser(
        description="AWS Terraform coverage audit across an Organization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic scan with console output
  %(prog)s --profile default

  # Generate HTML report
  %(prog)s --output html --output-dir ~/Desktop

  # Scan specific accounts and regions
  %(prog)s --accounts 111111111111,222222222222 --regions us-east-1,us-west-2

  # Filter by resource types
  %(prog)s --resource-types ec2:instance,s3:bucket,rds:db

  # Both console and HTML with verbose logging
  %(prog)s --output both --verbose
        """
    )
    p.add_argument(
        "--profile",
        default="default",
        help="AWS profile name (default: default)"
    )
    p.add_argument(
        "--output",
        choices=["console", "html", "both"],
        default="console",
        help="Output format (default: console)"
    )
    p.add_argument(
        "--output-dir",
        default=os.path.expanduser("~/Desktop"),
        help="Directory for HTML report (default: ~/Desktop)"
    )
    p.add_argument(
        "--accounts",
        help="Comma-separated account IDs to scan (default: all accounts)"
    )
    p.add_argument(
        "--regions",
        help="Comma-separated region names (default: all enabled regions)"
    )
    p.add_argument(
        "--role-name",
        default="OrganizationAccountAccessRole",
        help="IAM role name to assume in member accounts (default: OrganizationAccountAccessRole)"
    )
    p.add_argument(
        "--resource-types",
        help="Comma-separated resource types for Tagging API filter (e.g., ec2:instance,s3:bucket)"
    )
    p.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging"
    )
    return p.parse_args()


def setup_logging(verbose: bool) -> None:
    """Configure logging based on verbosity."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )


def boto3_session(profile: str) -> boto3.Session:
    """Create a boto3 session with the specified profile."""
    try:
        # If AWS credentials are in environment variables, use them directly
        if os.environ.get('AWS_ACCESS_KEY_ID') and os.environ.get('AWS_SECRET_ACCESS_KEY'):
            logger.debug("Using AWS credentials from environment variables")
            return boto3.session.Session()
        # Otherwise use the specified profile
        return boto3.session.Session(profile_name=profile)
    except Exception as e:
        logger.error(f"Failed to create boto3 session with profile '{profile}': {e}")
        sys.exit(1)


def list_org_accounts(sess: boto3.Session) -> Dict[str, str]:
    """
    List all active accounts in the AWS Organization.
    
    Returns:
        Dict mapping account_id -> account_name
    """
    logger.info("Discovering AWS Organization accounts...")
    try:
        org = sess.client("organizations", config=AWS_RETRY_CONFIG)
        token = None
        accounts = {}
        
        while True:
            kwargs = {"NextToken": token} if token else {}
            resp = org.list_accounts(**kwargs)
            
            for a in resp.get("Accounts", []):
                status = a.get("Status")
                if status == "SUSPENDED":
                    logger.debug(f"Skipping suspended account: {a.get('Name')} ({a.get('Id')})")
                    continue
                accounts[a["Id"]] = a["Name"]
            
            token = resp.get("NextToken")
            if not token:
                break
        
        logger.info(f"Found {len(accounts)} active accounts")
        return accounts
        
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        if error_code == "AccessDeniedException":
            logger.error(
                "Access denied when listing organization accounts. "
                "Ensure you have organizations:ListAccounts permission."
            )
        else:
            logger.error(f"Failed to list organization accounts: {e}")
        sys.exit(2)


def assume_role(sess: boto3.Session, account_id: str, role_name: str) -> Optional[boto3.Session]:
    """
    Assume a role in the target account.
    
    Returns:
        boto3.Session with assumed role credentials, or None if assumption fails
    """
    sts = sess.client("sts", config=AWS_RETRY_CONFIG)
    role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
    session_name = f"TerraformCoverageAudit-{dt.datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    try:
        logger.debug(f"Assuming role {role_arn}")
        resp = sts.assume_role(
            RoleArn=role_arn,
            RoleSessionName=session_name,
            DurationSeconds=3600,
        )
        
        creds = resp["Credentials"]
        return boto3.session.Session(
            aws_access_key_id=creds["AccessKeyId"],
            aws_secret_access_key=creds["SecretAccessKey"],
            aws_session_token=creds["SessionToken"],
        )
        
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        logger.warning(f"AssumeRole failed for account {account_id}: {error_code}")
        return None


def discover_regions(sess: boto3.Session, region_filter: Optional[List[str]]) -> List[str]:
    """
    Discover all enabled AWS regions.
    
    Args:
        sess: boto3 session
        region_filter: Optional list of regions to filter to
        
    Returns:
        List of region names
    """
    logger.info("Discovering AWS regions...")
    try:
        ec2 = sess.client("ec2", config=AWS_RETRY_CONFIG)
        resp = ec2.describe_regions(AllRegions=True)
        
        # Include only opted-in or default regions
        regions = [
            r["RegionName"] for r in resp["Regions"]
            if r.get("OptInStatus") in ("opt-in-not-required", "opted-in")
        ]
        
        if region_filter:
            invalid = set(region_filter) - set(regions)
            if invalid:
                logger.warning(f"Invalid or disabled regions will be skipped: {invalid}")
            regions = [r for r in regions if r in set(region_filter)]
        
        logger.info(f"Scanning {len(regions)} regions")
        logger.debug(f"Regions: {', '.join(regions)}")
        return regions
        
    except Exception as e:
        logger.error(f"Failed to discover regions: {e}")
        sys.exit(1)


def is_terraform_managed(tags: List[Dict[str, str]]) -> bool:
    """
    Check if resource is managed by Terraform.
    
    Looks for tag with key 'terraform' (case-insensitive) and value 'true' (case-insensitive).
    """
    for t in tags or []:
        key = t.get("Key", "")
        value = t.get("Value", "")
        if key.lower() == "terraform" and value.lower() == "true":
            return True
    return False


# Regex for parsing ARNs
_ARN_RE = re.compile(
    r"^arn:(?P<partition>[^:]*):(?P<service>[^:]*):(?P<region>[^:]*):(?P<account>[^:]*):(?P<resource>.*)$"
)


def parse_arn(arn: str) -> Tuple[str, str, str, str, str]:
    """
    Parse an AWS ARN into components.
    
    Returns:
        (partition, service, region, account, resource)
    """
    m = _ARN_RE.match(arn)
    if not m:
        return "", "", "", "", arn
    d = m.groupdict()
    return d["partition"], d["service"], d["region"], d["account"], d["resource"]


def split_resource(resource: str) -> Tuple[str, str]:
    """
    Split ARN resource component into type and ID.
    
    Examples:
        'instance/i-1234567890abcdef0' -> ('instance', 'i-1234567890abcdef0')
        'bucket:my-bucket' -> ('bucket', 'my-bucket')
    """
    if "/" in resource:
        parts = resource.split("/", 1)
        return parts[0], parts[1]
    if ":" in resource:
        parts = resource.split(":", 1)
        return parts[0], parts[1]
    return "", resource


def get_name_from_tags(tags: List[Dict[str, str]]) -> Optional[str]:
    """Extract the Name tag value (case-insensitive)."""
    if not tags:
        return None
    
    # Try exact match first
    for t in tags:
        if t.get("Key") == "Name":
            return t.get("Value")
    
    # Fall back to case-insensitive match
    for t in tags:
        if t.get("Key", "").lower() == "name":
            return t.get("Value")
    
    return None


def scan_account(
    account_id: str,
    account_name: str,
    mgmt_sess: boto3.Session,
    regions: List[str],
    role_name: str,
    resource_types: Optional[List[str]]
) -> AccountResult:
    """
    Scan a single AWS account for tagged resources.
    
    Args:
        account_id: AWS account ID
        account_name: AWS account name
        mgmt_sess: Management account boto3 session
        regions: List of regions to scan
        role_name: IAM role name to assume
        resource_types: Optional list of resource type filters
        
    Returns:
        AccountResult with managed and unmanaged resources
    """
    logger.info(f"Scanning account: {account_name} ({account_id})")
    result = AccountResult(account_id=account_id, account_name=account_name)
    
    # Attempt to assume role in target account
    sess = assume_role(mgmt_sess, account_id, role_name)
    
    # Fallback: if assume role fails but we're already in the target account
    if sess is None:
        try:
            sts = mgmt_sess.client("sts", config=AWS_RETRY_CONFIG)
            ident = sts.get_caller_identity()
            if ident.get("Account") == account_id:
                logger.debug(f"Using management session credentials for account {account_id}")
                sess = mgmt_sess
        except Exception:
            pass
    
    if sess is None:
        msg = f"AccessDenied: Unable to assume role {role_name}"
        result.errors.append(msg)
        logger.error(f"{account_name} ({account_id}): {msg}")
        return result
    
    # Scan each region
    for region in regions:
        logger.debug(f"Scanning {account_name} in {region}")
        try:
            tag_client = sess.client(
                "resourcegroupstaggingapi",
                region_name=region,
                config=AWS_RETRY_CONFIG
            )
            
            token = None
            region_resource_count = 0
            
            while True:
                kwargs = {"ResourcesPerPage": 100}
                if token:
                    kwargs["PaginationToken"] = token
                if resource_types:
                    kwargs["ResourceTypeFilters"] = resource_types
                
                resp = tag_client.get_resources(**kwargs)
                
                for mapping in resp.get("ResourceTagMappingList", []):
                    arn = mapping.get("ResourceARN", "")
                    tags = mapping.get("Tags", [])
                    
                    # Parse ARN components
                    _, service, arn_region, arn_account, resource = parse_arn(arn)
                    rtype, rid = split_resource(resource)
                    name = get_name_from_tags(tags)
                    managed = is_terraform_managed(tags)
                    
                    # Build resource record
                    rec = ResourceRecord(
                        arn=arn,
                        resource_id=rid or arn,
                        resource_name=name,
                        resource_type=f"{service}:{rtype}" if rtype else service,
                        region=arn_region or region,
                        account_id=arn_account or account_id,
                        account_name=account_name,
                        managed=managed,
                    )
                    
                    # Categorize resource
                    if managed:
                        result.managed.append(rec)
                    else:
                        result.unmanaged.append(rec)
                    
                    region_resource_count += 1
                
                token = resp.get("PaginationToken")
                if not token:
                    break
            
            if region_resource_count > 0:
                logger.debug(
                    f"Found {region_resource_count} resources in {account_name}/{region}"
                )
        
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            msg = f"{region}: {error_code}"
            result.errors.append(msg)
            logger.warning(f"{account_name}: {msg}")
        
        except Exception as e:
            msg = f"{region}: {type(e).__name__}: {e}"
            result.errors.append(msg)
            logger.warning(f"{account_name}: {msg}")
    
    total = len(result.managed) + len(result.unmanaged)
    logger.info(
        f"Completed {account_name}: {total} resources "
        f"({len(result.managed)} managed, {len(result.unmanaged)} unmanaged)"
    )
    
    return result


def print_console(results: List[AccountResult]) -> None:
    """Print results to console using rich tables."""
    console.print("\n")
    
    # Summary table by account
    table = Table(title="Terraform Coverage by Account", show_lines=True)
    table.add_column("Account", style="cyan")
    table.add_column("Account ID", style="dim")
    table.add_column("Managed", justify="right", style="green")
    table.add_column("Unmanaged", justify="right", style="red")
    table.add_column("Total", justify="right")
    table.add_column("Coverage %", justify="right")
    
    total_m = total_u = 0
    
    for r in results:
        m, u = len(r.managed), len(r.unmanaged)
        t = m + u
        cov = (m / t * 100) if t else 0
        total_m += m
        total_u += u
        
        coverage_str = f"{cov:.1f}%"
        if cov >= 80:
            coverage_style = "bold green"
        elif cov >= 50:
            coverage_style = "yellow"
        else:
            coverage_style = "bold red"
        
        table.add_row(
            r.account_name,
            r.account_id,
            str(m),
            str(u),
            str(t),
            f"[{coverage_style}]{coverage_str}[/{coverage_style}]"
        )
    
    console.print(table)
    
    # Organization summary
    grand_t = total_m + total_u
    org_cov = (total_m / grand_t * 100) if grand_t else 0
    console.print(
        f"\n[bold]Organization Coverage:[/bold] [cyan]{org_cov:.1f}%[/cyan] "
        f"([green]Managed: {total_m}[/green], [red]Unmanaged: {total_u}[/red], Total: {grand_t})\n"
    )
    
    # Managed resources table
    if total_m > 0:
        mt = Table(title="Managed Resources (terraform=true)", show_header=True, header_style="bold green")
        mt.add_column("Account", style="cyan")
        mt.add_column("Region")
        mt.add_column("Type")
        mt.add_column("Name")
        mt.add_column("ID", style="dim")
        mt.add_column("ARN", style="dim", max_width=60)
        
        for r in results:
            for rec in r.managed:
                mt.add_row(
                    r.account_name,
                    rec.region,
                    rec.resource_type,
                    rec.resource_name or "",
                    rec.resource_id,
                    rec.arn
                )
        
        console.print(mt)
        console.print()
    
    # Unmanaged resources table
    if total_u > 0:
        ut = Table(title="Unmanaged Resources (no terraform tag)", show_header=True, header_style="bold red")
        ut.add_column("Account", style="cyan")
        ut.add_column("Region")
        ut.add_column("Type")
        ut.add_column("Name")
        ut.add_column("ID", style="dim")
        ut.add_column("ARN", style="dim", max_width=60)
        
        for r in results:
            for rec in r.unmanaged:
                ut.add_row(
                    r.account_name,
                    rec.region,
                    rec.resource_type,
                    rec.resource_name or "",
                    rec.resource_id,
                    rec.arn
                )
        
        console.print(ut)
        console.print()
    
    # Account errors
    failed = [r for r in results if r.errors]
    if failed:
        console.print("[bold yellow]Accounts with Errors:[/bold yellow]")
        for r in failed:
            console.print(f"  [cyan]{r.account_name}[/cyan] ({r.account_id}): {'; '.join(r.errors)}")
        console.print()


def render_html(results: List[AccountResult], profile: str, out_dir: str) -> str:
    """
    Render results as an HTML report.
    
    Returns:
        Path to generated HTML file
    """
    ts = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_m = sum(len(r.managed) for r in results)
    total_u = sum(len(r.unmanaged) for r in results)
    total = total_m + total_u
    org_cov = (total_m / total * 100) if total else 0
    
    # Inline HTML template with sortable tables and CSS
    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Terraform Coverage Report</title>
<style>
* { box-sizing: border-box; }
body { 
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    margin: 0;
    padding: 20px;
    background: #f5f5f5;
}
.container { 
    max-width: 1400px; 
    margin: 0 auto; 
    background: white;
    padding: 30px;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
h1 { 
    margin: 0 0 10px 0;
    color: #333;
    font-size: 32px;
}
.summary { 
    margin: 10px 0 30px;
    padding: 15px;
    background: #f9f9f9;
    border-radius: 4px;
    border-left: 4px solid #0066cc;
}
.summary div { margin: 5px 0; color: #666; }
.summary .stat { font-size: 18px; color: #333; }
table { 
    border-collapse: collapse;
    width: 100%;
    margin-bottom: 30px;
    font-size: 14px;
}
th, td { 
    border: 1px solid #ddd;
    padding: 10px;
    text-align: left;
}
th { 
    cursor: pointer;
    background: #f2f2f2;
    font-weight: 600;
    color: #333;
    user-select: none;
}
th:hover { background: #e6e6e6; }
tr:nth-child(even) { background: #fafafa; }
tr:hover { background: #f0f7ff; }
.badge { 
    display: inline-block;
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 13px;
    font-weight: 600;
}
.badge.green { 
    background: #d4edda;
    color: #155724;
}
.badge.red { 
    background: #f8d7da;
    color: #721c24;
}
.bar { 
    background: #e0e0e0;
    width: 100%;
    height: 20px;
    border-radius: 10px;
    overflow: hidden;
}
.fill { 
    height: 20px;
    background: linear-gradient(90deg, #28a745 0%, #20c997 100%);
    transition: width 0.3s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 11px;
    font-weight: 600;
}
.small { 
    color: #666;
    font-size: 12px;
    word-break: break-all;
}
h2 { 
    margin: 30px 0 15px 0;
    color: #333;
    border-bottom: 2px solid #0066cc;
    padding-bottom: 8px;
}
.error-section {
    background: #fff3cd;
    border: 1px solid #ffc107;
    border-radius: 4px;
    padding: 15px;
    margin: 20px 0;
}
.error-section h2 {
    margin-top: 0;
    color: #856404;
    border-bottom: none;
}
.error-section ul {
    margin: 10px 0;
    padding-left: 20px;
}
.error-section li {
    margin: 5px 0;
    color: #856404;
}
</style>
<script>
function sortTable(tableId, colIndex) {
    var table = document.getElementById(tableId);
    var rows = Array.from(table.querySelectorAll('tbody tr'));
    var isAsc = table.dataset.sortCol == colIndex && table.dataset.sortDir == 'asc';
    
    rows.sort(function(a, b) {
        var aVal = a.cells[colIndex].innerText;
        var bVal = b.cells[colIndex].innerText;
        
        // Try numeric comparison
        var aNum = parseFloat(aVal.replace(/[^0-9.-]/g, ''));
        var bNum = parseFloat(bVal.replace(/[^0-9.-]/g, ''));
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return isAsc ? bNum - aNum : aNum - bNum;
        }
        
        // String comparison
        return isAsc ? bVal.localeCompare(aVal) : aVal.localeCompare(bVal);
    });
    
    var tbody = table.querySelector('tbody');
    rows.forEach(function(row) { tbody.appendChild(row); });
    
    table.dataset.sortCol = colIndex;
    table.dataset.sortDir = isAsc ? 'desc' : 'asc';
}
</script>
</head>
<body>
<div class="container">
<h1>🔍 Terraform Coverage Report</h1>
<div class="summary">
  <div><strong>AWS Profile:</strong> {{ profile }}</div>
  <div><strong>Generated:</strong> {{ ts }}</div>
  <div class="stat">
    <strong>Total:</strong> 
    <span class="badge green">{{ total_m }} Managed</span>
    <span class="badge red">{{ total_u }} Unmanaged</span>
    &nbsp;|&nbsp; <strong>Organization Coverage:</strong> {{ "%.1f"|format(org_cov) }}%
  </div>
</div>

<h2>📊 Account Coverage Summary</h2>
<table id="acct" data-sort-col="-1" data-sort-dir="asc">
<thead>
<tr>
<th onclick="sortTable('acct', 0)">Account Name ▲▼</th>
<th onclick="sortTable('acct', 1)">Account ID ▲▼</th>
<th onclick="sortTable('acct', 2)">Managed ▲▼</th>
<th onclick="sortTable('acct', 3)">Unmanaged ▲▼</th>
<th onclick="sortTable('acct', 4)">Total ▲▼</th>
<th onclick="sortTable('acct', 5)">Coverage % ▲▼</th>
<th>Visual</th>
</tr>
</thead>
<tbody>
{% for r in results %}
{% set m = r.managed|length %}
{% set u = r.unmanaged|length %}
{% set t = m + u %}
{% set cov = (m / t * 100) if t else 0 %}
<tr>
<td><strong>{{ r.account_name }}</strong></td>
<td>{{ r.account_id }}</td>
<td>{{ m }}</td>
<td>{{ u }}</td>
<td>{{ t }}</td>
<td>{{ "%.1f"|format(cov) }}%</td>
<td>
<div class="bar">
<div class="fill" style="width: {{ cov }}%">{% if cov > 15 %}{{ "%.0f"|format(cov) }}%{% endif %}</div>
</div>
</td>
</tr>
{% endfor %}
</tbody>
</table>

<h2>✅ Managed Resources (terraform=true)</h2>
<table id="managed" data-sort-col="-1" data-sort-dir="asc">
<thead>
<tr>
<th onclick="sortTable('managed', 0)">Account ▲▼</th>
<th onclick="sortTable('managed', 1)">Region ▲▼</th>
<th onclick="sortTable('managed', 2)">Type ▲▼</th>
<th onclick="sortTable('managed', 3)">Name ▲▼</th>
<th onclick="sortTable('managed', 4)">Resource ID ▲▼</th>
<th onclick="sortTable('managed', 5)">ARN ▲▼</th>
</tr>
</thead>
<tbody>
{% for r in results %}
{% for rec in r.managed %}
<tr>
<td>{{ r.account_name }}</td>
<td>{{ rec.region }}</td>
<td>{{ rec.resource_type }}</td>
<td>{{ rec.resource_name or "" }}</td>
<td>{{ rec.resource_id }}</td>
<td class="small">{{ rec.arn }}</td>
</tr>
{% endfor %}
{% endfor %}
</tbody>
</table>

<h2>❌ Unmanaged Resources (no terraform tag)</h2>
<table id="unmanaged" data-sort-col="-1" data-sort-dir="asc">
<thead>
<tr>
<th onclick="sortTable('unmanaged', 0)">Account ▲▼</th>
<th onclick="sortTable('unmanaged', 1)">Region ▲▼</th>
<th onclick="sortTable('unmanaged', 2)">Type ▲▼</th>
<th onclick="sortTable('unmanaged', 3)">Name ▲▼</th>
<th onclick="sortTable('unmanaged', 4)">Resource ID ▲▼</th>
<th onclick="sortTable('unmanaged', 5)">ARN ▲▼</th>
</tr>
</thead>
<tbody>
{% for r in results %}
{% for rec in r.unmanaged %}
<tr>
<td>{{ r.account_name }}</td>
<td>{{ rec.region }}</td>
<td>{{ rec.resource_type }}</td>
<td>{{ rec.resource_name or "" }}</td>
<td>{{ rec.resource_id }}</td>
<td class="small">{{ rec.arn }}</td>
</tr>
{% endfor %}
{% endfor %}
</tbody>
</table>

{% set failed = results | selectattr("errors") | list %}
{% if failed %}
<div class="error-section">
<h2>⚠️ Accounts with Errors</h2>
<ul>
{% for r in results if r.errors %}
<li><strong>{{ r.account_name }} ({{ r.account_id }})</strong>: {{ r.errors | join("; ") }}</li>
{% endfor %}
</ul>
</div>
{% endif %}

</div>
</body>
</html>
"""
    
    template = Template(html_template)
    html = template.render(
        results=results,
        profile=profile,
        ts=ts,
        total_m=total_m,
        total_u=total_u,
        total=total,
        org_cov=org_cov
    )
    
    # Save HTML file
    os.makedirs(out_dir, exist_ok=True)
    filename = f"terraform_coverage_report_{dt.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.html"
    filepath = os.path.join(out_dir, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    
    return filepath


def main():
    """Main entry point."""
    args = parse_args()
    setup_logging(args.verbose)
    
    logger.info("Starting AWS Terraform Coverage Audit")
    logger.info(f"Profile: {args.profile}")
    logger.info(f"Output: {args.output}")
    
    # Create boto3 session
    mgmt_sess = boto3_session(args.profile)
    
    # Discover organization accounts
    accounts_map = list_org_accounts(mgmt_sess)
    
    # Filter accounts if specified
    if args.accounts:
        filter_accounts = {a.strip() for a in args.accounts.split(",") if a.strip()}
        accounts_map = {k: v for k, v in accounts_map.items() if k in filter_accounts}
        logger.info(f"Filtered to {len(accounts_map)} specified accounts")
    
    if not accounts_map:
        logger.error("No accounts to scan")
        sys.exit(1)
    
    # Discover regions
    region_filter = [r.strip() for r in args.regions.split(",")] if args.regions else None
    regions = discover_regions(mgmt_sess, region_filter)
    
    # Parse resource type filters
    rtypes = [t.strip() for t in args.resource_types.split(",")] if args.resource_types else None
    if rtypes:
        logger.info(f"Filtering to resource types: {', '.join(rtypes)}")
    
    # Scan accounts concurrently
    results: List[AccountResult] = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task(
            f"Scanning {len(accounts_map)} accounts across {len(regions)} regions...",
            total=len(accounts_map)
        )
        
        def worker(item):
            aid, aname = item
            return scan_account(aid, aname, mgmt_sess, regions, args.role_name, rtypes)
        
        max_workers = min(32, max(4, (os.cpu_count() or 4) * 2))
        
        with cf.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(worker, item): item for item in accounts_map.items()}
            
            for future in cf.as_completed(futures):
                try:
                    res = future.result()
                    results.append(res)
                except Exception as e:
                    logger.error(f"Unexpected error scanning account: {e}")
                finally:
                    progress.update(task, advance=1)
    
    # Sort results by account name
    results.sort(key=lambda r: r.account_name.lower())
    
    logger.info(f"Scan complete. Processed {len(results)} accounts")
    
    # Output results
    if args.output in ("console", "both"):
        print_console(results)
    
    if args.output in ("html", "both"):
        output_dir = os.path.expanduser(args.output_dir)
        filepath = render_html(results, args.profile, output_dir)
        console.print(f"\n[bold green]✓[/bold green] HTML report written to: [cyan]{filepath}[/cyan]\n")
    
    logger.info("Terraform coverage audit complete")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        logger.exception("Unexpected error")
        sys.exit(1)
