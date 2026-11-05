<#
.SYNOPSIS
    Vivédex Application Launcher for Windows.
.DESCRIPTION
    Checks virtual environment, initializes environment if missing, launches Streamlit,
    and opens the application in the default web browser.
.NOTES
    Style standard: ASD-STE100
#>

[CmdletBinding()]
param(
    [int]$Port = 8501,
    [switch]$NoBrowser,
    [switch]$Headless
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptRoot

Set-Location -Path $ProjectRoot

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Vivédex Platform Launcher" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

# If .venv is missing, automatically invoke Initialize-Vivedex.ps1
if (-not (Test-Path $VenvPython)) {
    Write-Host "[WARN] Virtual environment not found. Initializing now..." -ForegroundColor Yellow
    $InitScript = Join-Path $ScriptRoot "Initialize-Vivedex.ps1"
    & "$InitScript"
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $VenvPython)) {
        Write-Host "[ERROR] Automatic environment initialization failed." -ForegroundColor Red
        exit 1
    }
}

# Check if port is already in use by another service
$PortInUse = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($PortInUse) {
    Write-Host "[WARN] Port $Port is currently in use by PID $($PortInUse.OwningProcess)." -ForegroundColor Yellow
    Write-Host "       Attempting to bind or use next available port if conflict occurs." -ForegroundColor Gray
}

# Open browser if requested
if (-not $NoBrowser) {
    Start-Job -ScriptBlock {
        param($TargetUrl)
        Start-Sleep -Seconds 2
        Start-Process $TargetUrl
    } -ArgumentList "http://localhost:$Port" | Out-Null
}

$HeadlessFlag = if ($Headless) { "true" } else { "false" }

Write-Host "[INFO] Starting Streamlit application on http://localhost:$Port ..." -ForegroundColor Green
Write-Host "[INFO] Press Ctrl+C in this terminal window to stop the server." -ForegroundColor Gray
Write-Host ""

try {
    & "$VenvPython" -m streamlit run "$ProjectRoot\app.py" `
        --server.port $Port `
        --server.headless $HeadlessFlag `
        --browser.gatherUsageStats false
} catch {
    Write-Host "[ERROR] Failed to start Vivédex application: $_" -ForegroundColor Red
    exit 1
}
