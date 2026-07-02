@echo off
chcp 65001 >nul
title RUN CBOT DATA — Cap nhat Du lieu Trung tam
echo.
echo  ======================================================
echo    CBOT Data Project - Cap nhat Du lieu Dong bo
echo  ======================================================
echo.
echo  Dang khoi dong... (qua trinh nay mat khoang 1-3 phut)
echo.

cd /d "%~dp0"
python Data\run_data_now.py

echo.
echo  ======================================================
echo  Nhan phim bat ky de dong cua so nay...
echo  ======================================================
pause >nul
