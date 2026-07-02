@echo off
title CBOT Dashboard Server — localhost:8080
color 0A
echo.
echo  ========================================
echo   CBOT LOCAL SERVER — http://localhost:8080
echo  ========================================
echo   Dang khoi dong... (Dung cua so nay lai de tat server)
echo.

cd /d "%~dp0"

:RESTART
echo  [%TIME%] Khoi dong server...
python server.py
echo.
echo  [%TIME%] Server bi tat. Tu dong khoi dong lai sau 3 giay...
timeout /t 3 /nobreak >nul
goto RESTART
