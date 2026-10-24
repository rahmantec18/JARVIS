# J.A.R.V.I.S. Personal AI Ecosystem - Windows Shutdown Script
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Write-Host "==========================================================" -ForegroundColor Red
Write-Host "       J.A.R.V.I.S. PERSONAL AI ECOSYSTEM - SHUTDOWN" -ForegroundColor Red
Write-Host "==========================================================" -ForegroundColor Red

$ports = @(8000, 8001, 5173)

foreach ($port in $ports) {
    Write-Host "[*] Checking port $port for active listeners..." -ForegroundColor Yellow
    try {
        $pids = (Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue).OwningProcess | Select-Object -Unique
        foreach ($pidToKill in $pids) {
            if ($pidToKill -and $pidToKill -gt 0) {
                Write-Host "[-] Terminating process tree $pidToKill on port $port..." -ForegroundColor Yellow
                taskkill /F /T /PID $pidToKill 2>$null
            }
        }
    } catch {
        # Fallback
    }
}

# Also ensure any lingering node, uvicorn, or companion processes are cleaned up
try {
    Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*desktop_companion.py*" -or $_.CommandLine -like "*vite*" } | ForEach-Object {
        taskkill /F /T /PID $_.ProcessId 2>$null
    }
} catch {}
Write-Host "[+] All J.A.R.V.I.S. subsystems have powered down." -ForegroundColor Green

