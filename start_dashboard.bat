@echo off
title FantaAsta - Dashboard Live
echo ========================================================
echo   Avvio FantaAsta Live Dashboard (Streamlit)
echo ========================================================
echo.

set STREAMLIT_CMD=streamlit
if exist ".venv\Scripts\streamlit.exe" (
    set STREAMLIT_CMD=.venv\Scripts\streamlit.exe
)

%STREAMLIT_CMD% run dashboard.py
pause
