@echo off
chcp 65001 >nul
title 方程组自动化简软件
cd /d "%~dp0"
echo ========================================
echo   方程组自动化简软件
echo ========================================
echo.
echo 正在启动桌面窗口...
echo.
python app.py
if errorlevel 1 (
    echo.
    echo ========================================
    echo  启动失败！上面是错误信息。
    echo  请尝试双击 run_web.bat 使用浏览器模式。
    echo ========================================
    echo.
    pause
)
