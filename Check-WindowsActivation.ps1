# Save as Check-WindowsActivation.ps1 and run as Administrator
# Collects activation info, slmgr output, SPP service status, DNS SRV, and tries activation (/ato) if requested.

param(
  [switch]$TryActivate = $false,
  [string]$DomainToCheck = ""
)

if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
  Write-Error "Please run this script from an elevated (Administrator) PowerShell session."
  exit 1
}

$slmgr = Join-Path $env:windir 'system32\slmgr.vbs'
$runCscript = { param($args) & cscript.exe //Nologo $args 2>&1 }

# 1) slmgr outputs
$dli = & cscript.exe //Nologo $slmgr /dli 2>&1
$dlv = & cscript.exe //Nologo $slmgr /dlv 2>&1
$xpr = & cscript.exe //Nologo $slmgr /xpr 2>&1

# 2) SoftwareLicensingProduct details
try {
  $slp = Get-CimInstance -ClassName SoftwareLicensingProduct -ErrorAction Stop |
    Where-Object { $_.PartialProductKey -ne $null } |
    Select-Object Name, Description, LicenseStatus, PartialProductKey, ApplicationId, Version
} catch {
  $slp = "Unable to query SoftwareLicensingProduct: $($_.Exception.Message)"
}

# 3) SPP service
try {
  $spp = Get-Service -Name sppsvc -ErrorAction Stop | Select-Object Name, Status, StartType
} catch {
  $spp = "SPP service not found or cannot query: $($_.Exception.Message)"
}

# 4) Recent SPP events (Operational if present)
try {
  $sppEvents = Get-WinEvent -MaxEvents 20 -ErrorAction Stop -FilterHashtable @{LogName='Microsoft-Windows-Security-SPP/Operational'} |
    Select-Object TimeCreated, Id, LevelDisplayName, Message
} catch {
  $sppEvents = "No Software Protection operational log or access denied: $($_.Exception.Message)"
}

# 5) Domain / KMS SRV lookup (if domain joined or DomainToCheck provided)
$domain = if ($DomainToCheck) { $DomainToCheck } else {
  try { (Get-WmiObject -Class Win32_ComputerSystem).Domain } catch { "" }
}
$dnsSrv = $null
$kmsTests = @()
if ($domain -and ($domain -ne $env:COMPUTERNAME)) {
  try {
    $dnsSrv = Resolve-DnsName -Name "_vlmcs._tcp.$domain" -Type SRV -ErrorAction Stop
    foreach ($r in $dnsSrv) {
      $target = $r.NameTarget.TrimEnd('.')
      $port = $r.Port
      $tcp = Test-NetConnection -ComputerName $target -Port $port -InformationLevel Quiet
      $kmsTests += [PSCustomObject]@{ Target = $target; Port = $port; TcpOpen = $tcp }
    }
  } catch {
    $dnsSrv = "No SRV record found for _vlmcs._tcp.$domain or lookup failed: $($_.Exception.Message)"
  }
} else {
  $domain = $null
  $dnsSrv = "No domain detected (workgroup) or no domain provided."
}

# 6) Optional: attempt activation (slmgr /ato)
$activationAttempt = $null
if ($TryActivate) {
  try {
    $activationAttempt = & cscript.exe //Nologo $slmgr /ato 2>&1
  } catch {
    $activationAttempt = "Activation attempt failed to run: $($_.Exception.Message)"
  }
}

# 7) Pack results
$result = [PSCustomObject]@{
  Timestamp = (Get-Date).ToString("o")
  Computer = $env:COMPUTERNAME
  UserDomain = $domain
  SLMGR_DLI = ($dli -join "`n")
  SLMGR_DLV = ($dlv -join "`n")
  SLMGR_XPR = ($xpr -join "`n")
  SoftwareLicensingProduct = $slp
  SPP_Service = $spp
  SPP_RecentEvents = $sppEvents
  KMS_SRV_Resolve = $dnsSrv
  KMS_Tests = $kmsTests
  ActivationAttemptOutput = $activationAttempt
}

# Output summary in console and save JSON
$result | ConvertTo-Json -Depth 5
$outFile = Join-Path "c:\Users\Admin\OneDrive - w2kfp\Thang_Docs\Dau tu thu dong\hang hoa tai sinh\Antigravity\Cbot" ("WindowsActivationCheck_" + $env:COMPUTERNAME + "_" + (Get-Date -Format 'yyyyMMddHHmmss') + ".json")
$result | ConvertTo-Json -Depth 5 | Out-File -FilePath $outFile -Encoding UTF8

Write-Host "`nSaved results to $outFile"
