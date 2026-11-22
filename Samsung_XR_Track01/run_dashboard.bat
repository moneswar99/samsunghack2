@echo off
setlocal
echo ========================================================
echo Starting Samsung XR Track 01 Interactive Web Dashboard
echo ========================================================
echo Dashboard will be available at: http://localhost:8000
start http://localhost:8000
python dashboard/server.py
pause
