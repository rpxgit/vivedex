<#
.SYNOPSIS
    Vivédex Windows Environment Initializer.
.DESCRIPTION
    Sets up a local Python virtual environment, installs project dependencies,
    validates database schemas safely without data loss, and verifies environment readiness.
.NOTES
    Style standard: ASD-STE100
#>

[CmdletBinding()]
param(
    [switch]$ForceReinstall
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptRoot

Set-Location -Path $ProjectRoot

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Vivédex Environment Initializer" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Detect System Python
$SystemPython = $null
$PyLauncher = Get-Command "py" -ErrorAction SilentlyContinue
if ($PyLauncher) {
    try {
        $Ver = & py -3 -V 2>&1
        if ($LASTEXITCODE -eq 0) {
            $SystemPython = "py -3"
            Write-Host "[OK] Using Python Launcher: $Ver" -ForegroundColor Green
        }
    } catch {}
}

if (-not $SystemPython) {
    $PyCmd = Get-Command "python" -ErrorAction SilentlyContinue
    if ($PyCmd) {
        try {
            $Ver = & python -V 2>&1
            if ($LASTEXITCODE -eq 0) {
                $SystemPython = "python"
                Write-Host "[OK] Using system python on PATH: $Ver" -ForegroundColor Green
            }
        } catch {}
    }
}

if (-not $SystemPython) {
    # Check common installation locations
    $CommonPaths = @(
        "$env:LOCALAPPDATA\Programs\Python\Python314\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe",
        "$env:ProgramFiles\Python314\python.exe",
        "$env:ProgramFiles\Python313\python.exe",
        "$env:ProgramFiles\Python312\python.exe",
        "$env:ProgramFiles\Python311\python.exe"
    )
    foreach ($p in $CommonPaths) {
        if (Test-Path $p) {
            $SystemPython = "`"$p`""
            Write-Host "[OK] Found Python at: $p" -ForegroundColor Green
            break
        }
    }
}

if (-not $SystemPython) {
    Write-Host "[ERROR] Could not find Python 3.10+ installation." -ForegroundColor Red
    Write-Host "        Please install Python from https://www.python.org and add it to PATH." -ForegroundColor Yellow
    exit 1
}

# 2. Create or verify Virtual Environment
$VenvDir = Join-Path $ProjectRoot ".venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host "[INFO] Creating virtual environment at .venv..." -ForegroundColor Cyan
    Invoke-Expression "$SystemPython -m venv `"$VenvDir`""
    if (-not (Test-Path $VenvPython)) {
        Write-Host "[ERROR] Failed to create virtual environment." -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] Virtual environment created successfully." -ForegroundColor Green
} else {
    Write-Host "[OK] Existing virtual environment found at .venv" -ForegroundColor Green
}

# 3. Upgrade pip and install dependencies
Write-Host "[INFO] Installing / updating required dependencies from requirements.txt..." -ForegroundColor Cyan
& "$VenvPython" -m pip install --upgrade pip --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARN] Pip self-upgrade failed or was skipped. Continuing..." -ForegroundColor Yellow
}

$ReqFile = Join-Path $ProjectRoot "requirements.txt"
if (Test-Path $ReqFile) {
    & "$VenvPython" -m pip install -r "$ReqFile"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to install requirements from requirements.txt." -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] Dependencies installed successfully." -ForegroundColor Green
} else {
    Write-Host "[WARN] requirements.txt not found at $ReqFile" -ForegroundColor Yellow
}

# 4. Safely verify database schema without wiping existing data
Write-Host "[INFO] Checking database initialization..." -ForegroundColor Cyan
$DataDir = Join-Path $ProjectRoot "data"
if (-not (Test-Path $DataDir)) {
    New-Item -ItemType Directory -Path $DataDir -Force | Out-Null
}

& "$VenvPython" -c "from src.database import Database, DEFAULT_DB_PATH; db = Database(DEFAULT_DB_PATH); db.initialize_schema(); print('[OK] Database schema initialized and verified safely.')"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Database schema validation failed." -ForegroundColor Red
    exit 1
}

# 5. Check administrator status (Never create an administrator account automatically)
Write-Host "[INFO] Checking administrator provisioning status..." -ForegroundColor Cyan
& "$VenvPython" -m src.cli check-admin
Write-Host ""
Write-Host "NOTE: To create or manage an administrator account, run:" -ForegroundColor Gray
Write-Host "  .venv\Scripts\python.exe -m src.cli create-admin --username <USER> --password <PASS>" -ForegroundColor DarkCyan

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "[SUCCESS] Vivédex environment is initialized and ready to launch." -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
exit 0
