@echo off
cd /d "%~dp0"
py main.py
if errorlevel 1 (
    echo.
    echo Python launcher failed. Trying python...
    python main.py
)
if errorlevel 1 pause
