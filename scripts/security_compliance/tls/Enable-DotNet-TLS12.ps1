New-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\.NETFramework\v4.0.30319" 
  -Name "SystemDefaultTlsVersions" -Value 1 -PropertyType DWord -Force

New-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\.NETFramework\v4.0.30319" 
  -Name "SchUseStrongCrypto" -Value 1 -PropertyType DWord -Force

New-ItemProperty -Path "HKLM:\SOFTWARE\WOW6432Node\Microsoft\.NETFramework\v4.0.30319" 
  -Name "SystemDefaultTlsVersions" -Value 1 -PropertyType DWord -Force

New-ItemProperty -Path "HKLM:\SOFTWARE\WOW6432Node\Microsoft\.NETFramework\v4.0.30319" 
  -Name "SchUseStrongCrypto" -Value 1 -PropertyType DWord -Force
