@echo off
title CBOT Entry Alarm (Telegram Bot)
echo ===================================================
echo      CBOT ENTRY ALARM - H1 MSS SCANNER
echo ===================================================
echo.
echo Dang khoi dong he thong quet tin hieu chay ngam...
echo Luu y: Chi tat cua so nay khi ban muon dung nhan canh bao tren dien thoai.
echo.

pushd "%~dp0"

:: Set encoding to support UTF-8 characters in Python print
set PYTHONIOENCODING=utf-8

:: Chay bot bang python he thong (hoac .venv neu tuong thich)
python "%~dp0entry_alarm.py"

pause
