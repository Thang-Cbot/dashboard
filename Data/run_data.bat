@echo off
chcp 65001 >nul
title CBOT DATA PROJECT — RUN UPDATE
echo.
echo  ======================================================
echo    CBOT Data Project - Cap nhat Du lieu Trung tam
echo  ======================================================
echo.
echo  Dang khoi dong... (qua trinh nay mat khoang 3-5 phut)
echo.

REM Chạy từ thư mục gốc Cbot (cha của Data/)
cd /d "%~dp0.."

python Data\run_data_update.py

echo.
echo  ======================================================
echo  Nhan phim bat ky de dong cua so nay...
echo  ======================================================
pause >nul
