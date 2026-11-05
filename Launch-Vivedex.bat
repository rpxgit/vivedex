@echo off
setlocal
chcp 65001 >nul
title Vivédex - Biodiversity Discovery Platform

cd /d "%~dp0"

echo ============================================================
echo   Vivédex - Biodiversity Discovery Platform Launcher
echo ============================================================
echo.

where powershell >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] PowerShell was not found on this system.
    echo Please run scripts\Start-Vivedex.ps1 manually.
    pause
    exit /b 1
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Start-Vivedex.ps1" %*

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Launcher exited with code %ERRORLEVEL%.
    pause
)
