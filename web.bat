@echo off
REM ==============================================================================
REM OS-SimBench: Interactive Web Dashboard Launcher for Windows
REM ==============================================================================

set PORT=8080
if not "%~1"=="" set PORT=%~1

echo ==================================================================
echo           Launching OS-SimBench Web Dashboard
echo           Opening: http://localhost:%PORT%
echo ==================================================================

start "" "http://localhost:%PORT%"
python "%~dp0web_server.py" %PORT%
pause
