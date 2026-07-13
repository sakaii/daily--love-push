@echo off
chcp 65001 >nul
echo ========================================
echo   ❤️  安装依赖...
echo ========================================
echo.

cd /d "%~dp0"

python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

echo.
echo ✅ 依赖安装完成！
pause
