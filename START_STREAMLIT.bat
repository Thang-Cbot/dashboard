@echo off
chcp 65001 >nul
title CBOT Streamlit Dashboard
echo.
echo  =============================================
echo    CBOT Dashboard - Khoi dong Streamlit
echo  =============================================
echo.
echo  Dang mo Dashboard tai: http://localhost:8501
echo  Nhan Ctrl+C de dung.
echo.
cd /d "%~dp0"
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8501.*LISTENING"') do taskkill /F /PID %%a >nul 2>&1
python -m streamlit run "%~dp0app.py" --server.port 8501 --server.headless false --browser.gatherUsageStats false
pause
