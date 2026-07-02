@echo off
chcp 65001 >nul
title KHOI DONG CBOT SYSTEM

echo ======================================================
echo    CBOT MASTER - TU DONG KHOI DONG KHI MO MAY TINH
echo ======================================================
echo.

cd /d "%~dp0"

echo [1/3] DANG KHOI DONG BOT ENTRY ALARM (TELEGRAM)...
start "CBOT Entry Alarm" cmd /k "run_alarm_bot.bat"
timeout /t 2 /nobreak >nul

echo [2/3] DANG KHOI DONG DATA SCHEDULER (CAP NHAT DU LIEU NGAM)...
start "CBOT Data Scheduler" cmd /k "START_SCHEDULER.bat"
timeout /t 2 /nobreak >nul

echo [3/3] DANG KHOI DONG GIAO DIEN STREAMLIT DASHBOARD...
start "CBOT Streamlit" cmd /k "START_STREAMLIT.bat"

echo.
echo ======================================================
echo HOAN TAT! Tat ca he thong dang duoc chay ngam trong cac cua so moi.
echo Ban co the dong cua so den (cmd) nay an toan.
echo ======================================================
timeout /t 5 >nul
exit
