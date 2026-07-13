@echo off
chcp 65001 >nul
title ❤️ 设置每日自动推送 - 定时任务

echo ========================================
echo   ❤️  设置 Windows 定时任务
echo   每天早 7:00 自动推送微信消息
echo ========================================
echo.

cd /d "%~dp0"

set SCRIPT_PATH=%~dp0send_daily_message.py
set TASK_NAME=DailyWeChatPush_ForWife

echo 📋 任务名称: %TASK_NAME%
echo 📂 脚本路径: %SCRIPT_PATH%
echo.

REM 检查当前用户是否有权限
echo 🔍 检查管理员权限...
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  需要管理员权限！
    echo 请右键点击 setup_schedule.bat，选择"以管理员身份运行"
    echo.
    pause
    exit /b 1
)
echo ✅ 管理员权限 OK
echo.

REM 创建定时任务 - 每天早上 7:00 运行
echo 📅 创建定时任务（每天 7:00）...
schtasks /create ^
    /tn "%TASK_NAME%" ^
    /tr "python \"%SCRIPT_PATH%\"" ^
    /sc daily ^
    /st 07:00 ^
    /rl highest ^
    /f

if %errorlevel% equ 0 (
    echo.
    echo ✅ 定时任务创建成功！
    echo.
    echo ========================================
    echo   ❤️  大功告成！每天早 7:00
    echo   老婆会自动收到你的暖心推送！
    echo ========================================
) else (
    echo.
    echo ❌ 定时任务创建失败，错误码: %errorlevel%
    echo 请尝试以管理员身份运行
)

echo.
pause
