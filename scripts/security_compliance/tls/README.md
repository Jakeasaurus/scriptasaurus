# TLS Registry Configuration and Verification Toolkit (PowerShell)

This toolkit includes PowerShell scripts to check and configure TLS settings on Windows systems. It ensures `.NET Framework` applications and system-level components default to **TLS 1.2**, in compliance with modern security standards.

---

## 📁 Included Scripts

### 1. `Check-TLS12.ps1`

**Purpose**: Checks if TLS 1.2 is enabled in both `.NET Framework` and OS-level (Schannel) registry settings.

**Checks:**
- `.NET Framework`:
  - `SystemDefaultTlsVersions`
  - `SchUseStrongCrypto`
- Schannel:
  - `HKLM\SYSTEM\CurrentControlSet\Control\SecurityProviders\SCHANNEL\Protocols\TLS 1.2\Client`
  - `HKLM\SYSTEM\CurrentControlSet\Control\SecurityProviders\SCHANNEL\Protocols\TLS 1.2\Server`

**Usage:**
```powershell
.\Check-TLS12.ps1
```

---

### 2. `Check-TLS11.ps1`

**Purpose**: Checks if TLS 1.1 is enabled or disabled at the OS level via Schannel registry keys.

**Checks:**
- `HKLM\SYSTEM\CurrentControlSet\Control\SecurityProviders\SCHANNEL\Protocols\TLS 1.1\Client`
- `HKLM\SYSTEM\CurrentControlSet\Control\SecurityProviders\SCHANNEL\Protocols\TLS 1.1\Server`

**Usage:**
```powershell
.\Check-TLS11.ps1
```

---

### 3. `Enable-DotNet-TLS12.ps1`

**Purpose**: Enables TLS 1.2 as the default for `.NET Framework` (both 64-bit and 32-bit) by setting the appropriate registry values.

**Modifies:**
- `HKLM\SOFTWARE\Microsoft\.NETFramework\v4.0.30319`
- `HKLM\SOFTWARE\WOW6432Node\Microsoft\.NETFramework\v4.0.30319`

**Sets:**
- `SystemDefaultTlsVersions = 1`
- `SchUseStrongCrypto = 1`

**Usage:**
```powershell
.\Enable-DotNet-TLS12.ps1
```

---

### 4. `Enable-TLS12-Everything.ps1`

**Purpose**: Enables TLS 1.2 system-wide by modifying both `.NET Framework` and Schannel settings. Also includes optional logic to disable TLS 1.0 and 1.1 (commented out).

**Modifies:**
- `.NET Framework` registry keys (64-bit and 32-bit)
- Schannel keys for:
  - `TLS 1.2\Client`
  - `TLS 1.2\Server`

**Optional:**
- Disables `TLS 1.0` and `TLS 1.1` if desired

**Usage:**
```powershell
.\Enable-TLS12-Everything.ps1
```

---

## ✅ Requirements

- All scripts should be run in a **PowerShell session with Administrator privileges**.
- Some changes may require a **system reboot** or **service restart** to take effect.

---

## 🔍 Use Cases

- Auditing system and .NET TLS readiness
- Hardening legacy servers
- Enforcing TLS 1.2 as baseline for secure communications
- Disabling outdated protocols (TLS 1.0 / 1.1)

---

## 🚡 Security Note

- **TLS 1.0** and **1.1** are deprecated.
- It is strongly recommended to **disable** them unless legacy software requires them.
- You may need to **restart services or reboot** the system for changes to fully apply.

---

## 📚 References

- [Microsoft TLS Registry Settings](https://learn.microsoft.com/en-us/windows-server/security/tls/tls-registry-settings)
- [Schannel Protocol Documentation](https://learn.microsoft.com/en-us/windows/win32/secauthn/protocols-in-tls-ssl--schannel-ssp-)
- [.NET Framework TLS Configuration](https://learn.microsoft.com/en-us/dotnet/framework/network-programming/tls#configure-your-appl)
