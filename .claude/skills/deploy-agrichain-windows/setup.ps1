<#
.SYNOPSIS
    One-time AgriChain setup on Windows: virtualenv + dependencies (+ optional ML models).
.DESCRIPTION
    Run from the AgriChain project root (the folder containing config.py and requirements.txt).
    Creates .venv if missing, installs requirements, and trains the ML models unless -SkipModels.
.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\.claude\skills\deploy-agrichain-windows\setup.ps1
.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\.claude\skills\deploy-agrichain-windows\setup.ps1 -SkipModels
#>
param(
    [switch]$SkipModels
)
$ErrorActionPreference = "Stop"

# Resolve project root as two levels up from this script (.claude\skills\deploy-agrichain-windows\).
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
Set-Location $projectRoot
Write-Host "AgriChain setup in: $projectRoot" -ForegroundColor Cyan

# 0. Sanity-check we actually have the code (the submission zip is docs-only).
foreach ($f in @("config.py", "requirements.txt", "backend\main.py", "frontend\dashboard.py")) {
    if (-not (Test-Path $f)) {
        throw "Missing '$f'. You need the FULL AgriChain project folder, not the docs-only submission zip."
    }
}

# 1. Pick a Python launcher (prefer 'py -3', fall back to 'python').
$pyCmd = $null
if (Get-Command py -ErrorAction SilentlyContinue)     { $pyCmd = @("py", "-3") }
elseif (Get-Command python -ErrorAction SilentlyContinue) { $pyCmd = @("python") }
else { throw "Python not found on PATH. Install Python 3.11+ from python.org (tick 'Add to PATH')." }
# Trailing args (empty for @("python"), "-3" for @("py","-3")). Select-Object -Skip 1 is
# safe for a 1-element array; a $pyCmd[1..$n] slice is NOT (1..0 counts DOWN in PowerShell).
$pyArgs = @($pyCmd | Select-Object -Skip 1)
Write-Host "Using launcher: $($pyCmd -join ' ')" -ForegroundColor DarkGray
& $pyCmd[0] @pyArgs --version

# 2. Create the virtualenv if it does not exist.
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtualenv (.venv)..." -ForegroundColor Cyan
    & $pyCmd[0] @pyArgs -m venv .venv
} else {
    Write-Host ".venv already exists - reusing it." -ForegroundColor DarkGray
}
$venvPy = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPy)) { throw "venv Python not found at $venvPy" }

# 3. Install dependencies into the venv.
Write-Host "Upgrading pip + installing requirements..." -ForegroundColor Cyan
& $venvPy -m pip install --upgrade pip
& $venvPy -m pip install -r requirements.txt

# 4. Train models (optional; the app has a rule-based fallback without them).
if (-not $SkipModels) {
    if (Test-Path "ai\models\risk_model.joblib") {
        Write-Host "Models already present - skipping training." -ForegroundColor DarkGray
    } else {
        Write-Host "Training ML models (dataset + risk + anomaly)..." -ForegroundColor Cyan
        & $venvPy -m data.generate_dataset
        & $venvPy -m scripts.train_models
    }
} else {
    Write-Host "Skipping model training (-SkipModels). Rule-based risk will be used." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Setup complete. Next: run.ps1  (or run the two commands in SKILL.md)." -ForegroundColor Green
