@echo off
title FantaAsta - Avvio Completo
echo ========================================================
echo   Avvio FantaAsta Live: Dashboard Web + CLI Terminal
echo ========================================================
echo.

set PYTHON_CMD=python
set STREAMLIT_CMD=streamlit

if exist ".venv\Scripts\python.exe" (
    set PYTHON_CMD=.venv\Scripts\python.exe
)
if exist ".venv\Scripts\streamlit.exe" (
    set STREAMLIT_CMD=.venv\Scripts\streamlit.exe
)

echo [1/2] Avvio della Dashboard Streamlit su secondo monitor...
start "FantaAsta Dashboard Live" cmd /c "%STREAMLIT_CMD% run dashboard.py --server.headless true"

echo [2/2] Avvio della CLI FantaAsta...
echo.
%PYTHON_CMD% fantaasta_cli.py

pause
