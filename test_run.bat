@echo off
chcp 65001 >nul
echo ========================================
echo   ❤️  测试运行（手动发一条）
echo ========================================
echo.

cd /d "%~dp0"

python send_daily_message.py

echo.
echo 按任意键退出...
pause >nul
