# Enable TLS 1.2 in .NET Framework (64-bit and 32-bit)
$dotNetPaths = @(
  "HKLM:\SOFTWARE\Microsoft\.NETFramework\v4.0.30319",
  "HKLM:\SOFTWARE\WOW6432Node\Microsoft\.NETFramework\v4.0.30319"
)

foreach ($path in $dotNetPaths) {
  New-ItemProperty -Path $path -Name "SystemDefaultTlsVersions" -Value 1 -PropertyType DWord -Force
  New-ItemProperty -Path $path -Name "SchUseStrongCrypto" -Value 1 -PropertyType DWord -Force
  Write-Host "Configured TLS 1.2 settings for .NET at: $path"
}

# Enable TLS 1.2 in Schannel for both client and server
$basePath = "HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\SCHANNEL\Protocols\TLS 1.2"
$clientPath = "$basePath\Client"
$serverPath = "$basePath\Server"

foreach ($key in @($clientPath, $serverPath)) {
  if (-not (Test-Path $key)) {
    New-Item -Path $key -Force | Out-Null
  }
  New-ItemProperty -Path $key -Name "Enabled" -Value 1 -PropertyType DWord -Force
  New-ItemProperty -Path $key -Name "DisabledByDefault" -Value 0 -PropertyType DWord -Force
  Write-Host "Enabled TLS 1.2 in: $key"
}

# OPTIONAL: Disable TLS 1.0 and 1.1 (Uncomment if you want to enforce TLS 1.2+)
# $oldVersions = @("TLS 1.0", "TLS 1.1")
# foreach ($version in $oldVersions) {
#   foreach ($role in @("Client", "Server")) {
#     $key = "HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\SCHANNEL\Protocols\$version\$role"
#     if (-not (Test-Path $key)) {
#       New-Item -Path $key -Force | Out-Null
#     }
#     New-ItemProperty -Path $key -Name "Enabled" -Value 0 -PropertyType DWord -Force
#     New-ItemProperty -Path $key -Name "DisabledByDefault" -Value 1 -PropertyType DWord -Force
#     Write-Host "Disabled $version in: $key"
#   }
# }

Write-Host "`nTLS 1.2 has been successfully enabled across the system."
