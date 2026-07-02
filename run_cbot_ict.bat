@echo off
echo ===================================================
echo      CBOT ICT - Smart Money Analysis Dashboard
echo ===================================================
echo.
echo [1/3] Dang tai du lieu gia moi nhat (Real-time update)...
cd /d "%~dp0"
python update_active_data.py

echo.
echo [2/3] Dang dong goi du lieu cho bieu do...
cd /d "%~dp0ict_chart"
python build_data.py

echo.
echo [3/3] Dang mo Dashboard tren trinh duyet...
start index.html

echo.
echo Hoan thanh!

