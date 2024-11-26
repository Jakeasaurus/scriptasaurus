$HTMLHeader = @"
<html>
<head>
    <title>System Information</title>
    <style>
        body {font-family: Arial, sans-serif;}
        h2 {color: #2E4053;}
        table {border-collapse: collapse;}
        th, td {border: 1px solid #ddd; padding: 8px;}
        tr:nth-child(even) {background-color: #f2f2f2;}
        th {padding-top: 12px; padding-bottom: 12px; text-align: left; background-color: #4CAF50; color: white;}
    </style>
</head>
<body>
"@

# Define the HTML footer
$HTMLFooter = @"
</body>
</html>
"@

# Define a function to convert PowerShell objects to HTML tables
function ConvertTo-HTMLTable {
    param(
        [Parameter(Mandatory = $true)]
        [PSObject]$Object,
        [Parameter(Mandatory = $true)]
        [string]$Title
    )

    # Start the HTML table with the title
    $HTMLTable = @"
    <h2>$Title</h2>
    <table>
        <tr>
"@

    # Add the headers to the table (property names)
    $Object.PSObject.Properties | ForEach-Object {
        $HTMLTable += "<th>$($_.Name)</th>"
    }

    $HTMLTable += "</tr>"

    # Add the data to the table (property values)
    $Object | ForEach-Object {
        $HTMLTable += "<tr>"
        $_.PSObject.Properties | ForEach-Object {
            $HTMLTable += "<td>$($_.Value)</td>"
        }
        $HTMLTable += "</tr>"
    }

    # Close the HTML table
    $HTMLTable += "</table><br>"

    return $HTMLTable
}

# Define a function to write HTML content to a file
function Write-HTML {
    param(
        [Parameter(Mandatory = $true)]
        [string]$HTML,
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    # Append the HTML content to the file
    Add-Content -Path $Path -Value $HTML
}

# Define the path for the output HTML file (on the desktop)
$HTMLFilePath = [Environment]::GetFolderPath("Desktop") + "\SystemInformation.html"

# Create the HTML file
New-Item -Path $HTMLFilePath -ItemType File -Force

# Write the HTML header to the file
Write-HTML -HTML $HTMLHeader -Path $HTMLFilePath

# ConvertTo-Cidr function definition
function ConvertTo-Cidr {
    param(
        [Parameter(Mandatory=$true)]
        [string] $SubnetMask
    )

    $binaryStr = ([IPAddress]$SubnetMask).GetAddressBytes() | ForEach-Object { [Convert]::ToString($_, 2).PadLeft(8, '0') }
    return ($binaryStr -join '').TrimEnd('0').Length
}

###############################
# SCRIPT FUNCTIONS
###############################
# Section 1: Windows OS version, hostname, domain, and network information
$WinOS = Get-WmiObject -Class Win32_OperatingSystem | ForEach-Object {
    [PSCustomObject]@{
        OSVersion = $_.Version
        OSName = $_.Caption
        Hostname = $_.CSName
        Domain = if ($_.Domain -eq $_.CSName) {"Not Joined to a domain"} else {$_.Domain}
    }
}

$WinOSHTML = ConvertTo-HTMLTable -Object $WinOS -Title "Windows OS Version Information"
Write-HTML -HTML $WinOSHTML -Path $HTMLFilePath

# Section: Network Information
$NetworkInfo = Get-WmiObject -Class Win32_NetworkAdapterConfiguration | Where-Object { $_.IPEnabled -eq $true } | ForEach-Object {
    # Ensure the properties are handled gracefully
    [PSCustomObject]@{
        Description    = $_.Description
        IPAddress      = if ($_.IPAddress) { $_.IPAddress -join ", " } else { "N/A" }
        SubnetMask     = if ($_.IPSubnet) { $_.IPSubnet -join ", " } else { "N/A" }
        SubnetCIDR     = if ($_.IPSubnet) { ConvertTo-Cidr -SubnetMask $_.IPSubnet[0] } else { "N/A" }
        DefaultGateway = if ($_.DefaultIPGateway) { $_.DefaultIPGateway -join ", " } else { "N/A" }
        DHCPServer     = if ($_.DHCPServer) { $_.DHCPServer } else { "N/A" }
        DHCPEnabled    = if ($_.DHCPEnabled -eq $true) { "Yes" } else { "No" }
        DNSServers     = if ($_.DNSServerSearchOrder) { $_.DNSServerSearchOrder -join ", " } else { "N/A" }
        MACAddress     = if ($_.MACAddress) { $_.MACAddress } else { "N/A" }
    }
}

$NetworkInfoHTML = ConvertTo-HTMLTable -Object $NetworkInfo -Title "Network Information"
Write-HTML -HTML $NetworkInfoHTML -Path $HTMLFilePath

# Section 2: Get the CPU information and write it to the HTML file
$CPU = Get-WmiObject -Class Win32_Processor | ForEach-Object {
    [PSCustomObject]@{
        Name                 = $_.Name
        MaxClockSpeedInGHz   = [math]::Round(($_.MaxClockSpeed / 1000), 2)
        NumberOfCores        = $_.NumberOfCores
    }
}
$CPUHTML = ConvertTo-HTMLTable -Object $CPU -Title "CPU Information"
Write-HTML -HTML $CPUHTML -Path $HTMLFilePath

# Section: RAM Information

# Detailed Physical Memory Information
$RAM = Get-WmiObject -Class Win32_PhysicalMemory | ForEach-Object {
    [PSCustomObject]@{
        Manufacturer  = if ($_.Manufacturer) { $_.Manufacturer } else { "N/A" }
        PartNumber    = if ($_.PartNumber) { $_.PartNumber } else { "N/A" }
        Speed         = if ($_.Speed) { "$($_.Speed) MHz" } else { "N/A" }
        CapacityInGB  = if ($_.Capacity) { [math]::Round($_.Capacity / 1GB, 2) } else { "N/A" }
    }
}

# Total RAM Information
$TotalRAM = Get-WmiObject -Class Win32_ComputerSystem | ForEach-Object {
    [PSCustomObject]@{
        TotalRAMInGB = if ($_.TotalPhysicalMemory) { [math]::Round($_.TotalPhysicalMemory / 1GB, 2) } else { "N/A" }
    }
}

# Convert Detailed RAM Information to HTML
$RAMHTML = ConvertTo-HTMLTable -Object $RAM -Title "RAM Information"
Write-HTML -HTML $RAMHTML -Path $HTMLFilePath

# Convert Total RAM Information to HTML
$TotalRAMHTML = ConvertTo-HTMLTable -Object $TotalRAM -Title "Total RAM"
Write-HTML -HTML $TotalRAMHTML -Path $HTMLFilePath


# Section: Drives Information
$Drives = Get-WmiObject -Class Win32_LogicalDisk -Filter "DriveType=3" | ForEach-Object {
    [PSCustomObject]@{
        "Drive Letter"         = if ($_.DeviceID) { $_.DeviceID } else { "N/A" }
        "Drive Size (GB)"      = if ($_.Size) { [math]::Round($_.Size / 1GB, 2) } else { "N/A" }
        "Free Space (GB)"      = if ($_.FreeSpace) { [math]::Round($_.FreeSpace / 1GB, 2) } else { "N/A" }
        "Used Space (GB)"      = if ($_.Size - $_.FreeSpace) { [math]::Round(($_.Size - $_.FreeSpace) / 1GB, 2) } else { "N/A" }
        "Free Space (%)"       = if ($_.Size -and $_.FreeSpace) { [math]::Round(($_.FreeSpace / $_.Size) * 100, 2) } else { "N/A" }
    }
}

$DrivesHTML = ConvertTo-HTMLTable -Object $Drives -Title "Drives Information"
Write-HTML -HTML $DrivesHTML -Path $HTMLFilePath


# Section: Services Information
$Services = Get-Service | ForEach-Object {
    [PSCustomObject]@{
        "Service Name"     = if ($_.Name) { $_.Name } else { "N/A" }
        "Display Name"     = if ($_.DisplayName) { $_.DisplayName } else { "N/A" }
        "Status"           = if ($_.Status) { $_.Status } else { "N/A" }
        "Startup Type"     = if ($_.StartType) { $_.StartType } else { "N/A" }
    }
}

$ServicesHTML = ConvertTo-HTMLTable -Object $Services -Title "Services Information"
Write-HTML -HTML $ServicesHTML -Path $HTMLFilePath


# Section 5: Get the TCP and UDP ports in use and write them to the HTML file
$IPGlobalProperties = [System.Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties()
$TCPConnections = $IPGlobalProperties.GetActiveTcpConnections()
$UDPListeners = $IPGlobalProperties.GetActiveUdpListeners()

# TCP connections details need special handling due to hostname resolution
$TCPConnectionsHTML = "<h2>Active TCP Connections</h2><table><tr><th>Local Address</th><th>Local Port</th><th>Remote Address</th><th>Remote Port</th><th>Remote Hostname</th></tr>"
foreach($TCPConnection in $TCPConnections) {
    try {
        $HostName = [System.Net.Dns]::GetHostEntry($TCPConnection.RemoteEndPoint.Address).HostName
    }
    catch {
        $HostName = "Could not resolve hostname"
    }
    $TCPConnectionsHTML += "<tr><td>$($TCPConnection.LocalEndPoint.Address.IPAddressToString)</td><td>$($TCPConnection.LocalEndPoint.Port)</td><td>$($TCPConnection.RemoteEndPoint.Address.IPAddressToString)</td><td>$($TCPConnection.RemoteEndPoint.Port)</td><td>$HostName</td></tr>"
}
$TCPConnectionsHTML += "</table><br>"
Write-HTML -HTML $TCPConnectionsHTML -Path $HTMLFilePath

$UDPListeners = $UDPListeners | ForEach-Object {
    [PSCustomObject]@{
        LocalAddress = $_.Address.IPAddressToString
        LocalPort    = $_.Port
    }
}
$UDPListenersHTML = ConvertTo-HTMLTable -Object $UDPListeners -Title "Active UDP Listeners"
# Write the UDP Listeners HTML to the file
Write-HTML -HTML $UDPListenersHTML -Path $HTMLFilePath

# Section 6: Server Roles
# Get-WindowsFeature cmdlet is used to retrieve roles, role services, and features that are available or installed on a computer that is running Windows Server 2012 R2.
# We filter out the ones that are installed. We also format the output to include name, display name, description, and sub features.
$ServerRoles = Get-WindowsFeature | Where-Object {$_.InstallState -eq "Installed"} | ForEach-Object {
    $SubFeatures = if ($_.SubFeatures) { ($_.SubFeatures -join ", ") } else { "No sub features" }
    [PSCustomObject]@{
        Name = $_.Name
        DisplayName = $_.DisplayName
        Description = $_.Description
        SubFeatures = $SubFeatures
    }
}

$ServerRolesHTML = ConvertTo-HTMLTable -Object $ServerRoles -Title "Server Roles Installed"
Write-HTML -HTML $ServerRolesHTML -Path $HTMLFilePath

# Section 7: Get the Installed Programs and write them to the HTML file
$InstalledPrograms32 = Get-ItemProperty "HKLM:\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*" | Select-Object DisplayName, DisplayVersion, Publisher, InstallDate
$InstalledPrograms64 = Get-ItemProperty "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*" | Select-Object DisplayName, DisplayVersion, Publisher, InstallDate
$AllInstalledPrograms = $InstalledPrograms32 + $InstalledPrograms64 | Where-Object { $_.DisplayName -ne $null } | Sort-Object DisplayName
$InstalledProgramsHTML = ConvertTo-HTMLTable -Object $AllInstalledPrograms -Title "Installed Programs"

Write-HTML -HTML $InstalledProgramsHTML -Path $HTMLFilePath

# Section 8: Check if SQL Server is installed
$SQLServerInstance = Get-Service | Where-Object { $_.Name -like 'MSSQL$*' }

if ($SQLServerInstance) {
    $SQLServerVersion = Invoke-Sqlcmd -Query "SELECT SERVERPROPERTY('productversion'), SERVERPROPERTY ('productlevel'), SERVERPROPERTY ('edition')" -ServerInstance $SQLServerInstance.Name.Substring(6) -Database "master" -OutputSqlErrors $true

    $SQLServerInfo = [PSCustomObject]@{
        InstanceName = $SQLServerInstance.Name.Substring(6)
        Status = $SQLServerInstance.Status
        Version = $SQLServerVersion.Column1
        Level = $SQLServerVersion.Column2
        Edition = $SQLServerVersion.Column3
    }

    $SQLServerHTML = ConvertTo-HTMLTable -Object $SQLServerInfo -Title "SQL Server Information"
}
else {
    $SQLServerHTML = @"
<h2>SQL Server Information</h2>
<table>
<tr><th>SQL Server Status</th></tr>
<tr><td>No SQL Server installed on this server</td></tr>
</table>
"@
}

Write-HTML -HTML $SQLServerHTML -Path $HTMLFilePath

# Write the HTML footer to the file
Write-HTML -HTML $HTMLFooter -Path $HTMLFilePath
