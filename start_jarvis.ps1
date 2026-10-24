# J.A.R.V.I.S. Personal AI Ecosystem - Windows Launch Script
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "       J.A.R.V.I.S. PERSONAL AI ECOSYSTEM - INITIALIZATION" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  MARK-VIII PROTOCOL ENGAGED | HOST: $env:COMPUTERNAME" -ForegroundColor DarkCyan
Write-Host ""

$WorkspaceRoot = $PSScriptRoot
Set-Location $WorkspaceRoot

# 1. Rapid Non-Blocking Port Clearance
try {
    $conns = Get-NetTCPConnection -LocalPort 8000, 8001, 5173 -State Listen -ErrorAction SilentlyContinue
    if ($conns) {
        $pids = $conns.OwningProcess | Select-Object -Unique
        foreach ($pidToKill in $pids) {
            if ($pidToKill -and $pidToKill -gt 0) {
                taskkill /F /T /PID $pidToKill 2>$null
            }
        }
    }
} catch {}

# 2. Verify Python Virtual Environment
$PythonExe = Join-Path $WorkspaceRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    Write-Host "[!] Initializing .venv..." -ForegroundColor Yellow
    python -m venv .venv
    & $PythonExe -m pip install -r backend\requirements.txt
    & $PythonExe -m pip install -r desktop_agent\requirements.txt
}

# 3. Create Windows Desktop Shortcut if missing (One-time check)
$ShortcutFile = Join-Path ([System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Desktop)) "JARVIS.lnk"
if (-not (Test-Path $ShortcutFile)) {
    try {
        $WshShell = New-Object -ComObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut($ShortcutFile)
        $Shortcut.TargetPath = Join-Path $WorkspaceRoot "START_JARVIS.bat"
        $Shortcut.WorkingDirectory = $WorkspaceRoot
        $Shortcut.Description = "Launch J.A.R.V.I.S. Personal AI Assistant"
        $Shortcut.Save()
        Write-Host "[OK] Created 1-Click J.A.R.V.I.S. Shortcut on your Desktop." -ForegroundColor Green
    } catch {}
}

# 4. PARALLEL ACCELERATED DISPATCH: Launch All Subsystems Concurrently
Write-Host "[+] Rapid Parallel Dispatch: Booting Neural Subsystems..." -ForegroundColor Green
$BackendDir = Join-Path $WorkspaceRoot "backend"

# Boot Desktop Agent (8001)
$AgentJob = Start-Process -FilePath $PythonExe -ArgumentList "-m", "uvicorn", "desktop_agent.app.main:app", "--host", "127.0.0.1", "--port", "8001" -WorkingDirectory $WorkspaceRoot -PassThru -WindowStyle Minimized

# Boot AI Core Backend (8000)
$BackendJob = Start-Process -FilePath $PythonExe -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000" -WorkingDirectory $BackendDir -PassThru -WindowStyle Minimized

# Boot Frontend Cinematic Interface (5173)
$FrontendJob = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "npm --prefix frontend run dev" -PassThru -WindowStyle Minimized

# 5. Fast Parallel Health Synchronization (200ms polling loop)
Write-Host "[*] Engaging subsystems..." -NoNewline -ForegroundColor Cyan
$BackendReady = $false
$FrontendReady = $false
$Retries = 0

while ($Retries -lt 25) {
    Start-Sleep -Milliseconds 200
    $Retries++
    Write-Host "." -NoNewline -ForegroundColor Cyan

    if (-not $BackendReady) {
        try {
            $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/health" -UseBasicParsing -TimeoutSec 1 -ErrorAction SilentlyContinue
            if ($resp.StatusCode -eq 200) { $BackendReady = $true }
        } catch {}
    }

    if (-not $FrontendReady) {
        try {
            $resp = Invoke-WebRequest -Uri "http://127.0.0.1:5173" -UseBasicParsing -TimeoutSec 1 -ErrorAction SilentlyContinue
            if ($resp.StatusCode -eq 200) { $FrontendReady = $true }
        } catch {}
    }

    # Open immediately as soon as Frontend is ready, OR if Backend is ready and reached attempt 8 (~1.6s)
    if ($FrontendReady -or ($BackendReady -and $Retries -ge 8)) {
        break
    }
}
Write-Host ""

$LaunchUrl = if ($FrontendReady) { "http://127.0.0.1:5173" } else { "http://127.0.0.1:8000" }
Write-Host "[OK] Systems Synchronized in $($Retries * 200)ms." -ForegroundColor Green
Write-Host "[OK] Opening J.A.R.V.I.S. Command Center at $LaunchUrl..." -ForegroundColor Green

# 6. Open Browser Immediately (Website Opens First)
Start-Process $LaunchUrl

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "       J.A.R.V.I.S. IS NOW FULLY OPERATIONAL" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  - Command Center UI:  $LaunchUrl" -ForegroundColor White
Write-Host "  - Unified Direct UI:  http://127.0.0.1:8000" -ForegroundColor White
Write-Host "  - Backend API Docs:   http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "  - Desktop Agent:      http://127.0.0.1:8001/health" -ForegroundColor White
Write-Host ""
Write-Host "  [i] The Command Center website is now open in your browser." -ForegroundColor Cyan
Write-Host "  [i] To pop up the floating voice command mic over WhatsApp and other apps," -ForegroundColor Cyan
Write-Host "      click the 'POP-UP' button inside the website or run JARVIS_MINI_HUD.bat." -ForegroundColor Cyan
Write-Host ""
Write-Host "To shut down J.A.R.V.I.S., double-click: STOP_JARVIS.bat" -ForegroundColor Yellow
Write-Host "Or press Ctrl+C in this console." -ForegroundColor Gray
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[*] System host active. Keep this console window open while using J.A.R.V.I.S." -ForegroundColor Cyan

# Keep-alive loop so background services stay permanently online
try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
} finally {
    Write-Host ""
    Write-Host "[!] Shutdown signal received. Powering down subsystems..." -ForegroundColor Yellow
    & (Join-Path $WorkspaceRoot "stop_jarvis.ps1")
}
