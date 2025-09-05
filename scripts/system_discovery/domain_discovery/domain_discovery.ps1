#Create directory
New-Item -Path C:\domain_discovery -ItemType directory
New-Item -Path C:\dhcp_backup -ItemType directory
Start-Sleep 5

#query fsmo roles, features, dcdiag, and dfsr replication. Also export DHCP. 
netdom query fsmo > c:\domain_discovery\query_fsmo.txt
get-windowsfeature | where-object {$_.InstallState -eq 'Installed'} > c:\domain_discovery\installed_features.txt
dcdiag > c:\domain_discovery\dcdiag.txt
repadmin /showrepl > c:\domain_discovery\repadmin_showrepl.txt
export-DhcpServer -ComputerName "THISCOMPUTERNAME" -File "C:\dhcp_backup\dhcpexport.xml"

#Create backup directory
New-Item -Path C:\ad_backups -ItemType directory

###############
#AD User Export
###############
Get-ADUser -Filter * -SearchBase "DC=lsfcu,DC=org" -Properties * | Select-Object name,description,office,streetAddress,userPrincipalName,whenCreated,whenChanged,enabled | export-csv -path c:\ad_backups\userexport.csv

###############
#AD Group Export
###############
#// Get year and month for csv export file 
$DateTime = Get-Date -f "yyyy-MM" 
 
#// Set CSV file name 
$CSVFile = "c:\ad_backups\AD_Groups"+$DateTime+".csv" 
 
#// Create emy array for CSV data 
$CSVOutput = @() 
 
#// Get all AD groups in the domain 
$ADGroups = Get-ADGroup -Filter * 
 
#// Set progress bar variables 
$i=0 
$tot = $ADGroups.count 
 
foreach ($ADGroup in $ADGroups) { 
    #// Set up progress bar 
    $i++ 
    $status = "{0:N0}" -f ($i / $tot * 100) 
    Write-Progress -Activity "Exporting AD Groups" -status "Processing Group $i of $tot : $status% Completed" -PercentComplete ($i / $tot * 100) 
 
    #// Ensure Members variable is empty 
    $Members = "" 
 
    #// Get group members which are also groups and add to string 
    $MembersArr = Get-ADGroup -filter {Name -eq $ADGroup.Name} | Get-ADGroupMember | select Name, objectClass, distinguishedName 
    if ($MembersArr) {  
        foreach ($Member in $MembersArr) {  
            if ($Member.objectClass -eq "user") { 
                $MemDN = $Member.distinguishedName 
                $UserObj = Get-ADUser -filter {DistinguishedName -eq $MemDN} 
                if ($UserObj.Enabled -eq $False) { 
                    continue 
                } 
            } 
            $Members = $Members + "," + $Member.Name  
        } 
        #// Check for members to avoid error for empty groups 
        if ($Members) { 
            $Members = $Members.Substring(1,($Members.Length) -1) 
        } 
    } 
 
    #// Set up hash table and add values 
    $HashTab = $NULL 
    $HashTab = [ordered]@{ 
        "Name" = $ADGroup.Name 
        "Category" = $ADGroup.GroupCategory 
        "Scope" = $ADGroup.GroupScope 
        "Members" = $Members 
    } 
 
    #// Add hash table to CSV data array 
    $CSVOutput += New-Object PSObject -Property $HashTab 
} 
 
#// Export to CSV files 
$CSVOutput | Sort-Object Name | Export-Csv $CSVFile -NoTypeInformation 
 
#// End of script

###############
#OU Export
###############
$results = Get-ADOrganizationalUnit -Properties CanonicalName -Filter * | Sort-Object CanonicalName |
ForEach-Object {
    [pscustomobject]@{
        Name          = Split-Path $_.CanonicalName -Leaf
        CanonicalName = $_.CanonicalName
        UserCount     = @(Get-AdUser -Filter * -SearchBase $_.DistinguishedName -SearchScope OneLevel).Count
        ComputerCount = @(Get-AdComputer -Filter * -SearchBase $_.DistinguishedName -SearchScope OneLevel).Count
    }
}
$results | Out-File c:\ad_backups\export_OUs.txt -Encoding UTF8

###############
#Group Policy Object Export
###############
Get-GPOReport -All -ReportType html c:\ad_backups\gporeport.html

###############
#Group Policy Object Export
###############
Get-ADComputer -Filter * -Properties * | sort DNSHostname | select * | Export-Csv -Path c:\ad_backups\computer_export.csv

