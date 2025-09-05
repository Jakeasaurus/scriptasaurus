# Check for .NET Framework strong cryptography settings (TLS 1.2 support)

# Define registry paths for both 64-bit and 32-bit .NET Framework settings
$paths = @(
  "HKLM:\SOFTWARE\Microsoft\.NETFramework\v4.0.30319",
  "HKLM:\SOFTWARE\WOW6432Node\Microsoft\.NETFramework\v4.0.30319"
)

# Loop through each path and check if TLS-related registry keys are set
foreach ($path in $paths) {
  Write-Host "`nChecking path: $path"
  foreach ($name in "SystemDefaultTlsVersions", "SchUseStrongCrypto") {
    $value = Get-ItemProperty -Path $path -Name $name -ErrorAction SilentlyContinue
    if ($value) {
      Write-Host "$name = $($value.$name)"
    } else {
      Write-Host "$name not set"
    }
  }
}

# Check if TLS 1.2 is enabled at the OS level under Schannel settings

# Define base registry path for TLS 1.2 protocol
$schannelPath = "HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\SCHANNEL\Protocols\TLS 1.2"

# Define subkeys for both client and server TLS settings
$clientKey = "$schannelPath\Client"
$serverKey = "$schannelPath\Server"

# Function to check if TLS 1.2 is enabled or disabled in the given key path
function Check-TlsKey($keyPath) {
  Write-Host "`nChecking TLS 1.2 at: $keyPath"
  foreach ($name in "Enabled", "DisabledByDefault") {
    $val = Get-ItemProperty -Path $keyPath -Name $name -ErrorAction SilentlyContinue
    if ($val) {
      Write-Host "$name = $($val.$name)"
    } else {
      Write-Host "$name not set"
    }
  }
}

# Run the check for both client and server TLS 1.2 registry keys
Check-TlsKey -keyPath $clientKey
Check-TlsKey -keyPath $serverKey
