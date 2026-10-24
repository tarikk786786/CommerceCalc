@echo off
setlocal
chcp 65001 >nul
title CommerceCalc - All-in-One E-Commerce Profit and Pricing Suite

echo ===============================================================================
echo Starting CommerceCalc - All-in-One E-Commerce Profit and Pricing Suite...
echo ===============================================================================
echo.

cd /d "%~dp0"

:: Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in system PATH.
    echo Please install Python 3.10 or higher.
    pause
    exit /b 1
)

:: Run CommerceCalc
python main.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Application exited with error code %errorlevel%.
    pause
)

endlocal
