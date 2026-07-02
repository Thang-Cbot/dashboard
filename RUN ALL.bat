@echo off
chcp 65001 >nul
title RUN ALL - CBOT MASTER SYSTEM
echo ======================================================
echo          CBOT MASTER - TIEN TRINH KHOI DONG TONG
echo ======================================================
echo.

cd /d "%~dp0"

echo [1/3] DANG QUET VA LAY DU LIEU VE FOLDER DATA...
python Data\run_data_update.py
echo ======================================================
echo.

echo [2/3] KICH HOAT BOT ENTRY ALARM (GUI TIN NHAN TELEGRAM)...
:: Lenh 'start' giup mo bot o mot cua so moi chay ngam, khong lam dung tien trinh
start "CBOT Entry Alarm" run_alarm_bot.bat
echo Da mo cua so Bot Telegram thanh cong...
echo ======================================================
echo.

echo [3/3] CAP NHAT CBOT MASTER DASHBOARD HTML...
python run_pro_plus.py
echo ======================================================
echo.

echo HOAN TAT TOAN BO TIEU TRINH! 
echo Dashboard da duoc cap nhat va Bot dang chay ngam de canh bao ban.
pause
