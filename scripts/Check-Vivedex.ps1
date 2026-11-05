<#
.SYNOPSIS
    Vivédex Pre-flight and Environment Health Checker for Windows.
.DESCRIPTION
    Validates Python version, virtual environment, dependencies, database schema,
    and administrative configuration without modifying environment state.
.NOTES
    Style standard: ASD-STE100
#>

[CmdletBinding()]
param(
    [string]$DbPath = ""
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptRoot

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Vivédex Environment Diagnostic & Health Check" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$IssuesFound = 0

# 1. Locate Python
$PythonExe = $null
if (Test-Path "$ProjectRoot\.venv\Scripts\python.exe") {
    $PythonExe = "$ProjectRoot\.venv\Scripts\python.exe"
    Write-Host "[OK] Virtual environment found: .venv\Scripts\python.exe" -ForegroundColor Green
} else {
    Write-Host "[WARN] No virtual environment found at .venv" -ForegroundColor Yellow
    # Search for system python
    $PyCmd = Get-Command "py" -ErrorAction SilentlyContinue
    if ($PyCmd) {
        $PythonExe = "py"
        Write-Host "[OK] Windows Python Launcher detected: py" -ForegroundColor Green
    } else {
        $PyCmd = Get-Command "python" -ErrorAction SilentlyContinue
        if ($PyCmd) {
            $PythonExe = "python"
            Write-Host "[OK] Python command detected on PATH: python" -ForegroundColor Green
        }
    }
}

if (-not $PythonExe) {
    Write-Host "[FAIL] Python 3.10+ was not found on this system." -ForegroundColor Red
    Write-Host "       Please install Python 3.10 or later from https://www.python.org" -ForegroundColor Yellow
    exit 1
}

# 2. Check Python Version
try {
    $PyVerOutput = if ($PythonExe -eq "py") { & py -3 -V 2>&1 } else { & $PythonExe -V 2>&1 }
    Write-Host "[OK] Detected Python Version: $PyVerOutput" -ForegroundColor Green
} catch {
    Write-Host "[FAIL] Failed to execute Python executable: $_" -ForegroundColor Red
    $IssuesFound++
}

# 3. Check Dependencies if .venv is present
if (Test-Path "$ProjectRoot\.venv\Scripts\python.exe") {
    Write-Host "[INFO] Checking required packages in .venv..." -ForegroundColor Gray
    $RequiredPackages = @("streamlit", "pydantic", "PIL", "httpx", "pytest")
    foreach ($pkg in $RequiredPackages) {
        $CheckCmd = "& '$ProjectRoot\.venv\Scripts\python.exe' -c 'import $pkg' 2>&1"
        Invoke-Expression $CheckCmd | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  [OK] Module '$pkg' is available." -ForegroundColor Green
        } else {
            Write-Host "  [FAIL] Required module '$pkg' is missing." -ForegroundColor Red
            $IssuesFound++
        }
    }
} else {
    Write-Host "[WARN] Run scripts\Initialize-Vivedex.ps1 to configure .venv and install dependencies." -ForegroundColor Yellow
}

# 4. Check Database Integrity & Schema
$TargetDb = if ($DbPath) { $DbPath } else { "$ProjectRoot\data\vivedex.db" }
if (Test-Path $TargetDb) {
    $DbSize = (Get-Item $TargetDb).Length
    Write-Host "[OK] Database found: $TargetDb ($DbSize bytes)" -ForegroundColor Green
} else {
    Write-Host "[INFO] Database does not exist yet at: $TargetDb" -ForegroundColor Cyan
    Write-Host "       The application will initialize schema automatically upon start." -ForegroundColor Gray
}

# 5. Check Admin Account Status via CLI
if (Test-Path "$ProjectRoot\.venv\Scripts\python.exe") {
    $AdminCheckCmd = "& '$ProjectRoot\.venv\Scripts\python.exe' -m src.cli check-admin"
    $AdminCheckOutput = Invoke-Expression $AdminCheckCmd 2>&1
    Write-Host "$AdminCheckOutput" -ForegroundColor Gray
}

# Summary
Write-Host "------------------------------------------------------------" -ForegroundColor Gray
if ($IssuesFound -eq 0) {
    Write-Host "[SUCCESS] All pre-flight checks passed." -ForegroundColor Green
    exit 0
} else {
    Write-Host "[ALERT] Pre-flight found $IssuesFound issue(s). Please review messages above." -ForegroundColor Yellow
    exit 2
}
