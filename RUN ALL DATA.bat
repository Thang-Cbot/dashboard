@echo off
title RUN ALL DATA - Cap nhat va chay ngam
color 0B
echo ======================================================
echo   RUN ALL DATA
echo   (1) Cap nhat toan bo du lieu tuc thoi
echo   (2) Khoi dong he thong chay ngam (Scheduler)
echo ======================================================
echo.
echo Buoc 1: Dang cap nhat du lieu tuc thoi...
cd /d "%~dp0"
python Data\run_data_now.py

echo.
echo Buoc 2: Dang khoi dong he thong chay ngam...
start "CBOT Data Scheduler" cmd /c "START_SCHEDULER.bat"

echo.
echo ======================================================
echo Hoan thanh! He thong chay ngam dang hoat dong o mot cua so khac.
echo Nhan phim bat ky de dong cua so nay...
pause >nul
