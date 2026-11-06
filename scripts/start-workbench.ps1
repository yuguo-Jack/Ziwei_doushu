param([ValidateRange(1024,65535)][int]$Port=8765,[switch]$Foreground,[switch]$OpenBrowser,[switch]$Restart)
$ErrorActionPreference='Stop'
$taskRoot=(Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$pythonCommand=(Get-Command python -ErrorAction Stop).Source
if($Foreground -and $Restart){throw 'Use -Restart for the background workbench or -Foreground for a new foreground process, not both.'}
if ($Foreground) { & $pythonCommand -X utf8 (Join-Path $taskRoot 'ziwei.py') serve --port $Port; exit $LASTEXITCODE }
$url="http://127.0.0.1:$Port"
$health=$null
try { $health=Invoke-RestMethod -Uri "$url/api/health" -TimeoutSec 2 } catch { }
if ($health -and ($health.service -ne 'ziwei-workbench' -or $health.workspace -ne $taskRoot)) { throw 'Port is occupied by another service; choose a different -Port.' }
if ($health -and $Restart) {
    $connection=Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop
    $owned=Get-CimInstance Win32_Process -Filter "ProcessId=$($connection.OwningProcess)"
    if ($owned.CommandLine -notmatch [regex]::Escape((Join-Path $taskRoot 'ziwei.py')) -or $owned.CommandLine -notmatch '\bserve\b') { throw 'Process identity does not match this workspace.' }
    Stop-Process -Id $connection.OwningProcess
    for($attempt=0;$attempt -lt 30;$attempt++){
        if(-not (Get-NetTCPConnection -LocalPort $Port -LocalAddress 127.0.0.1 -State Listen -ErrorAction SilentlyContinue)){break}
        Start-Sleep -Milliseconds 100
    }
    $health=$null
}
if (-not $health) {
    if(Get-NetTCPConnection -LocalPort $Port -LocalAddress 127.0.0.1 -State Listen -ErrorAction SilentlyContinue){throw 'Port is occupied without matching workspace health; choose a different -Port.'}
    $logs=Join-Path $taskRoot 'logs';New-Item -ItemType Directory -Path $logs -ErrorAction SilentlyContinue | Out-Null
    Start-Process -FilePath $pythonCommand -ArgumentList @('-X','utf8',('"'+(Join-Path $taskRoot 'ziwei.py')+'"'),'serve','--port',"$Port") -WorkingDirectory $taskRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logs 'workbench.stdout.log') -RedirectStandardError (Join-Path $logs 'workbench.stderr.log')
    for ($attempt=0;$attempt -lt 25;$attempt++) {
        $probe=$null
        try { $probe=Invoke-RestMethod -Uri "$url/api/health" -TimeoutSec 2 } catch { }
        if($probe){
            if($probe.service -ne 'ziwei-workbench' -or $probe.workspace -ne $taskRoot){throw 'A different service answered on this port; no process was stopped.'}
            $health=$probe;break
        }
        Start-Sleep -Milliseconds 200
    }
    if (-not $health) { throw 'Workbench did not start; inspect logs/workbench.stderr.log.' }
}
if ($OpenBrowser) { Start-Process -FilePath $url }
Write-Output $url
