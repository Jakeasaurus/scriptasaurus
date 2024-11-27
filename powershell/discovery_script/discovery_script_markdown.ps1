# Define a function to convert PowerShell objects to Markdown tables
function ConvertTo-MarkdownTable {
    param(
        [Parameter(Mandatory = $true)]
        [PSObject]$Object,
        [Parameter(Mandatory = $true)]
        [string]$Title
    )

    # Start the Markdown table with the title
    $MarkdownTable = "## $Title`n`n"

    # Add the headers to the table (property names)
    $Headers = $Object.PSObject.Properties.Name -join " | "
    $Separator = ($Object.PSObject.Properties.Name | ForEach-Object { "---" }) -join " | "
    $MarkdownTable += "| $Headers |`n| $Separator |`n"

    # Add the data to the table (property values)
    $Object | ForEach-Object {
        $Row = $_.PSObject.Properties.Value -join " | "
        $MarkdownTable += "| $Row |`n"
    }

    $MarkdownTable += "`n"
    return $MarkdownTable
}

# Define a function to write Markdown content to a file
function Write-Markdown {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Markdown,
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    # Append the Markdown content to the file
    Add-Content -Path $Path -Value $Markdown
}

# Define the path for the output Markdown file (on the desktop)
$MarkdownFilePath = [Environment]::GetFolderPath("Desktop") + "\SystemInformation.md"

# Create the Markdown file
New-Item -Path $MarkdownFilePath -ItemType File -Force

# Section 1: Windows OS version, hostname, domain, and network information
$WinOS = Get-WmiObject -Class Win32_OperatingSystem | ForEach-Object {
    [PSCustomObject]@{
        OSVersion = $_.Version
        OSName = $_.Caption
        Hostname = $_.CSName
        Domain = if ($_.Domain -eq $_.CSName) {"Not Joined to a domain"} else {$_.Domain}
    }
}

$WinOSMarkdown = ConvertTo-MarkdownTable -Object $WinOS -Title "Windows OS Version Information"
Write-Markdown -Markdown $WinOSMarkdown -Path $MarkdownFilePath

# Section 2: Network Information
$NetworkInfo = Get-WmiObject -Class Win32_NetworkAdapterConfiguration | Where-Object { $_.IPEnabled -eq $true } | ForEach-Object {
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

$NetworkInfoMarkdown = ConvertTo-MarkdownTable -Object $NetworkInfo -Title "Network Information"
Write-Markdown -Markdown $NetworkInfoMarkdown -Path $MarkdownFilePath

# Section 3: CPU Information
$CPU = Get-WmiObject -Class Win32_Processor | ForEach-Object {
    [PSCustomObject]@{
        Name                 = $_.Name
        MaxClockSpeedInGHz   = [math]::Round(($_.MaxClockSpeed / 1000), 2)
        NumberOfCores        = $_.NumberOfCores
    }
}
$CPUMarkdown = ConvertTo-MarkdownTable -Object $CPU -Title "CPU Information"
Write-Markdown -Markdown $CPUMarkdown -Path $MarkdownFilePath

# Section 4: RAM Information
$RAM = Get-WmiObject -Class Win32_PhysicalMemory | ForEach-Object {
    [PSCustomObject]@{
        Manufacturer  = if ($_.Manufacturer) { $_.Manufacturer } else { "N/A" }
        PartNumber    = if ($_.PartNumber) { $_.PartNumber } else { "N/A" }
        Speed         = if ($_.Speed) { "$($_.Speed) MHz" } else { "N/A" }
        CapacityInGB  = if ($_.Capacity) { [math]::Round($_.Capacity / 1GB, 2) } else { "N/A" }
    }
} 

$RAMMarkdown = ConvertTo-MarkdownTable -Object $RAM -Title "RAM Information"
Write-Markdown -Markdown $RAMMarkdown -Path $MarkdownFilePath

$TotalRAM = Get-WmiObject -Class Win32_ComputerSystem | ForEach-Object {
    [PSCustomObject]@{
        TotalRAMInGB = if ($_.TotalPhysicalMemory) { [math]::Round($_.TotalPhysicalMemory / 1GB, 2) } else { "N/A" }
    }
}
$TotalRAMMarkdown = ConvertTo-MarkdownTable -Object $TotalRAM -Title "Total RAM"
Write-Markdown -Markdown $TotalRAMMarkdown -Path $MarkdownFilePath

# Section 5: Drives Information
$Drives = Get-WmiObject -Class Win32_LogicalDisk -Filter "DriveType=3" | ForEach-Object {
    [PSCustomObject]@{
        "Drive Letter"   = if ($_.DeviceID) { $_.DeviceID } else { "N/A" }
        "Drive Size (GB)" = if ($_.Size) { [math]::Round($_.Size / 1GB, 2) } else { "N/A" }
        "Free Space (GB)" = if ($_.FreeSpace) { [math]::Round($_.FreeSpace / 1GB, 2) } else { "N/A" }
        "Used Space (GB)" = if ($_.Size - $_.FreeSpace) { [math]::Round(($_.Size - $_.FreeSpace) / 1GB, 2) } else { "N/A" }
        "Free Space (%)"  = if ($_.Size -and $_.FreeSpace) { [math]::Round(($_.FreeSpace / $_.Size) * 100, 2) } else { "N/A" }
    }
}

$DrivesMarkdown = ConvertTo-MarkdownTable -Object $Drives -Title "Drives Information"
Write-Markdown -Markdown $DrivesMarkdown -Path $MarkdownFilePath

# Section 6: Services Information
$Services = Get-Service | ForEach-Object {
    [PSCustomObject]@{
        "Service Name" = if ($_.Name) { $_.Name } else { "N/A" }
        "Display Name" = if ($_.DisplayName) { $_.DisplayName } else { "N/A" }
        "Status"       = if ($_.Status) { $_.Status } else { "N/A" }
        "Startup Type" = if ($_.StartType) { $_.StartType } else { "N/A" }
    }
}

$ServicesMarkdown = ConvertTo-MarkdownTable -Object $Services -Title "Services Information"
Write-Markdown -Markdown $ServicesMarkdown -Path $MarkdownFilePath

# Section 7: Active TCP Connections
$IPGlobalProperties = [System.Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties()
$TCPConnections = $IPGlobalProperties.GetActiveTcpConnections()

$TCPConnectionsMarkdown = "## Active TCP Connections`n`n| Local Address | Local Port | Remote Address | Remote Port | Remote Hostname |`n| --- | --- | --- | --- | --- |`n"
foreach ($TCPConnection in $TCPConnections) {
    try {
        $HostName = [System.Net.Dns]::GetHostEntry($TCPConnection.RemoteEndPoint.Address).HostName
    }
    catch {
        $HostName = "Could not resolve hostname"
    }
    $TCPConnectionsMarkdown += "| $($TCPConnection.LocalEndPoint.Address.IPAddressToString) | $($TCPConnection.LocalEndPoint.Port) | $($TCPConnection.RemoteEndPoint.Address.IPAddressToString) | $($TCPConnection.RemoteEndPoint.Port) | $HostName |`n"
}

Write-Markdown -Markdown $TCPConnectionsMarkdown -Path $MarkdownFilePath

# Section 8: Active UDP Listeners
$UDPListeners = $IPGlobalProperties.GetActiveUdpListeners() | ForEach-Object {
    [PSCustomObject]@{
        LocalAddress = $_.Address.IPAddressToString
        LocalPort    = $_.Port
    }
}

$UDPListenersMarkdown = ConvertTo-MarkdownTable -Object $UDPListeners -Title "Active UDP Listeners"
Write-Markdown -Markdown $UDPListenersMarkdown -Path $MarkdownFilePath

# Section 9: Installed Programs
$InstalledPrograms32 = Get-ItemProperty "HKLM:\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*" | Select-Object DisplayName, DisplayVersion, Publisher, InstallDate
$InstalledPrograms64 = Get-ItemProperty "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*" | Select-Object DisplayName, DisplayVersion, Publisher, InstallDate
$AllInstalledPrograms = $InstalledPrograms32 + $InstalledPrograms64 | Where-Object { $_.DisplayName -ne $null } | Sort-Object DisplayName

$InstalledProgramsMarkdown = ConvertTo-MarkdownTable -Object $AllInstalledPrograms -Title "Installed Programs"
Write-Markdown -Markdown $InstalledProgramsMarkdown -Path $MarkdownFilePath

# Section 10: SQL Server Information
$SQLServerInstance = Get-Service | Where-Object { $_.Name -like 'MSSQL$*' }

if ($SQLServerInstance) {
    $SQLServerVersion = Invoke-Sqlcmd -Query "SELECT SERVERPROPERTY('productversion'), SERVERPROPERTY ('productlevel'), SERVERPROPERTY ('edition')" -ServerInstance $SQLServerInstance.Name.Substring(6) -Database "master" -OutputSqlErrors $true

    $SQLServerInfo = [PSCustomObject]@{
        InstanceName = $SQLServerInstance.Name.Substring(6)
        Status       = $SQLServerInstance.Status
        Version      = $SQLServerVersion.Column1
        Level        = $SQLServerVersion.Column2
        Edition      = $SQLServerVersion.Column3
    }

    $SQLServerMarkdown = ConvertTo-MarkdownTable -Object $SQLServerInfo -Title "SQL Server Information"
} else {
    $SQLServerMarkdown = "## SQL Server Information`n`n| SQL Server Status |`n| --- |`n| No SQL Server installed on this server |`n"
}

Write-Markdown -Markdown $SQLServerMarkdown -Path $MarkdownFilePath

# Completion Message
Write-Output "Markdown report has been generated at $MarkdownFilePath"
