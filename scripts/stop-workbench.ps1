param([ValidateRange(1024,65535)][int]$Port=8765)
$ErrorActionPreference='Stop'
$taskRoot=(Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$listeners=@(Get-NetTCPConnection -LocalPort $Port -LocalAddress 127.0.0.1 -State Listen -ErrorAction SilentlyContinue)
if($listeners.Count -eq 0){Write-Output 'Workbench is already stopped.';exit 0}
if($listeners.Count -ne 1){throw 'Cannot uniquely identify the loopback listener; no process was stopped.'}
try{$health=Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/health" -TimeoutSec 3}catch{throw 'The listener did not provide workspace identity; no process was stopped.'}
if($health.service -ne 'ziwei-workbench' -or $health.workspace -ne $taskRoot){throw 'Listener belongs to another service/workspace; no process was stopped.'}
$listener=$listeners[0]
$owned=Get-CimInstance Win32_Process -Filter "ProcessId=$($listener.OwningProcess)"
if($owned.CommandLine -notmatch [regex]::Escape((Join-Path $taskRoot 'ziwei.py')) -or $owned.CommandLine -notmatch '\bserve\b'){throw 'Process command does not match this workbench; no process was stopped.'}
Stop-Process -Id $listener.OwningProcess
Write-Output "Stopped Ziwei workbench on port $Port. Skill/CLI and local data remain available."
