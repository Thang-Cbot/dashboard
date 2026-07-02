@echo off
chcp 65001 >nul
title Auto Update CBOT Dashboard
echo ======================================================
echo    Tu Dong Cap Nhat Du Lieu CBOT va Dashboard
echo ======================================================
echo.

cd /d "%~dp0"

echo [1/2] Dang tai du lieu tu mang (Macro, Fundamental, Price, COT)...
python Data\run_data_update.py

echo.
echo [2/2] Dang chay AI cap nhat Bieu do va Dashboard...
python run_pro_plus.py

echo.
echo Hoan tat! Dashboard da duoc cap nhat.
