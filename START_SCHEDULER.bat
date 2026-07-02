@echo off
title DAEMON: CBOT Data Scheduler
color 0A
echo ======================================================
echo   CBOT DATA SCHEDULER - HE THONG CHAY NGAM
echo ======================================================
echo.
echo Dang khoi dong trinh quan ly lich trinh...
echo KHONG DONG CUA SO NAY! Hay thu nho no xuong Taskbar.
echo Nhan Ctrl+C de dung he thong.
echo.
cd /d "%~dp0\Data"
python data_scheduler.py
pause
