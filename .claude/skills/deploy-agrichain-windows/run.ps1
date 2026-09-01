<#
.SYNOPSIS
    Launch AgriChain (FastAPI backend + Streamlit dashboard) on Windows.
.DESCRIPTION
    Run from anywhere after setup.ps1 has created .venv. Opens the backend and the
    dashboard in two new PowerShell windows, optionally seeds demo data, and prints
    the localhost URLs. Requires setup.ps1 to have been run first.
.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\.claude\skills\deploy-agrichain-windows\run.ps1
.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\.claude\skills\deploy-agrichain-windows\run.ps1 -NoSeed
#>
param(
    [switch]$NoSeed
)
$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$venvPy = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPy)) {
    throw "venv not found at $venvPy. Run setup.ps1 first."
}

# 1. Backend in its own window (stays open so you can read logs / Ctrl-C to stop).
$backendCmd = "Set-Location `"$projectRoot`"; & `"$venvPy`" -m uvicorn backend.main:app --host 127.0.0.1 --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd
Write-Host "Backend starting on http://127.0.0.1:8000 ..." -ForegroundColor Cyan

# 2. Give the API a few seconds to bind before seeding / launching the UI.
Start-Sleep -Seconds 5

# 3. Optional demo seed (needs the API up).
if (-not $NoSeed) {
    Write-Host "Seeding demo data..." -ForegroundColor Cyan
    try {
        & $venvPy (Join-Path $projectRoot "scripts\seed_demo.py")
    } catch {
        Write-Host "Seed step failed (is the backend up yet?). You can re-run: python scripts\seed_demo.py" -ForegroundColor Yellow
    }
}

# 4. Dashboard in its own window.
$uiCmd = "Set-Location `"$projectRoot`"; & `"$venvPy`" -m streamlit run frontend\dashboard.py --server.port 8501 --server.address 127.0.0.1"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $uiCmd
Write-Host "Dashboard starting on http://127.0.0.1:8501 ..." -ForegroundColor Cyan

Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host " Dashboard : http://127.0.0.1:8501   <- open this" -ForegroundColor Green
Write-Host " API docs  : http://127.0.0.1:8000/docs" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host "Close the two spawned windows (or Ctrl-C in each) to stop the app."
